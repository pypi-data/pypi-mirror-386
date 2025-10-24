import { default as log } from '@/logger';
import {
  escapePathForUrl,
  getFileContentPath,
  getFileBrowsePath,
  getFileURL,
  getFullPath,
  getLastSegmentFromPath,
  getPreferredPathForDisplay,
  joinPaths,
  makeBrowseLink,
  makePathSegmentArray,
  removeLastSegmentFromPath
} from './pathHandling';
import { shouldTriggerHealthCheck } from './serverHealth';

// Health check reporter registry with robust type safety
export type HealthCheckReporter = (
  apiPath: string,
  responseStatus?: number
) => Promise<void>;

class HealthCheckRegistry {
  private reporter: HealthCheckReporter | null = null;
  private isEnabled: boolean = true;

  setReporter(reporter: HealthCheckReporter): void {
    if (typeof reporter !== 'function') {
      throw new Error('Health check reporter must be a function');
    }
    this.reporter = reporter;
  }

  clearReporter(): void {
    this.reporter = null;
  }

  getReporter(): HealthCheckReporter | null {
    return this.isEnabled ? this.reporter : null;
  }

  disable(): void {
    this.isEnabled = false;
  }

  enable(): void {
    this.isEnabled = true;
  }

  isReporterSet(): boolean {
    return this.reporter !== null;
  }
}

// Create singleton instance
const healthCheckRegistry = new HealthCheckRegistry();

// Export convenience functions for backward compatibility
export function setHealthCheckReporter(reporter: HealthCheckReporter): void {
  healthCheckRegistry.setReporter(reporter);
}

export function clearHealthCheckReporter(): void {
  healthCheckRegistry.clearReporter();
}

// Export registry for advanced usage
export { healthCheckRegistry };

const formatFileSize = (sizeInBytes: number): string => {
  if (sizeInBytes < 1024) {
    return `${sizeInBytes} bytes`;
  } else if (sizeInBytes < 1024 * 1024) {
    return `${(sizeInBytes / 1024).toFixed(0)} KB`;
  } else if (sizeInBytes < 1024 * 1024 * 1024) {
    return `${(sizeInBytes / (1024 * 1024)).toFixed(0)} MB`;
  } else {
    return `${(sizeInBytes / (1024 * 1024 * 1024)).toFixed(0)} GB`;
  }
};

const formatUnixTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
};

const formatDateString = (dateStr: string) => {
  // If dateStr does not end with 'Z' or contain a timezone offset, treat as UTC
  let normalized = dateStr;
  if (!/Z$|[+-]\d{2}:\d{2}$/.test(dateStr)) {
    normalized = dateStr + 'Z';
  }
  const date = new Date(normalized);
  return date.toLocaleString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    month: 'numeric',
    day: 'numeric',
    year: 'numeric'
  });
};

class HTTPError extends Error {
  responseCode: number;

  constructor(message: string, responseCode: number) {
    super(message);
    this.responseCode = responseCode;
  }
}

async function checkSessionValidity(): Promise<boolean> {
  try {
    const response = await fetch(getFullPath('/api/profile'), {
      method: 'GET',
      credentials: 'include'
    });
    return response.ok;
  } catch (error) {
    log.error('Error checking session validity:', error);
    return false;
  }
}

// Define a more specific type for request body
type RequestBody = Record<string, unknown>;

async function sendFetchRequest(
  apiPath: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  body?: RequestBody
): Promise<Response> {
  const options: RequestInit = {
    method,
    credentials: 'include',
    headers: {
      ...(method !== 'GET' &&
        method !== 'DELETE' && { 'Content-Type': 'application/json' })
    },
    ...(method !== 'GET' &&
      method !== 'DELETE' &&
      body && { body: JSON.stringify(body) })
  };

  let response: Response;
  try {
    response = await fetch(getFullPath(apiPath), options);
  } catch (error) {
    // Report network errors to central server health monitoring if applicable
    const reporter = healthCheckRegistry.getReporter();
    if (reporter && shouldTriggerHealthCheck(apiPath)) {
      try {
        await reporter(apiPath);
      } catch (healthError) {
        // Don't let health check errors interfere with the original request
        log.debug(
          'Error reporting network failure to health checker:',
          healthError
        );
      }
    }
    throw error;
  }

  // Check for 403 Forbidden - could be permission denied or session expired
  if (response.status === 403) {
    // Check if session is still valid by testing a stable endpoint
    const sessionValid = await checkSessionValidity();
    if (!sessionValid) {
      // Session has expired, redirect to logout
      window.location.href = `${window.location.origin}/logout`;
      throw new HTTPError('Session expired', 401);
    }
    // If session is valid, this is just a permission denied for this specific resource
  }

  // Report failed requests to central server health monitoring if applicable
  if (!response.ok) {
    const reporter = healthCheckRegistry.getReporter();
    if (reporter && shouldTriggerHealthCheck(apiPath, response.status)) {
      try {
        await reporter(apiPath, response.status);
      } catch (error) {
        // Don't let health check errors interfere with the original request
        log.debug('Error reporting failed request to health checker:', error);
      }
    }
  }

  return response;
}

// Parse the Unix-style permissions string (e.g., "drwxr-xr-x")
const parsePermissions = (permissionString: string) => {
  // Owner permissions (positions 1-3)
  const ownerRead = permissionString[1] === 'r';
  const ownerWrite = permissionString[2] === 'w';

  // Group permissions (positions 4-6)
  const groupRead = permissionString[4] === 'r';
  const groupWrite = permissionString[5] === 'w';

  // Others/everyone permissions (positions 7-9)
  const othersRead = permissionString[7] === 'r';
  const othersWrite = permissionString[8] === 'w';

  return {
    owner: { read: ownerRead, write: ownerWrite },
    group: { read: groupRead, write: groupWrite },
    others: { read: othersRead, write: othersWrite }
  };
};

/**
 * Used to access objects in the ZonesAndFileSharePathsMap or in the zone, fsp, or folder preference maps
 * @param type zone, fsp, or folder
 * @param name for zones or FSPs, use zone.name or fsp.name. For folders, the name is defined as `${fsp.name}_${folder.path}`
 * @returns a map key string
 */
function makeMapKey(type: 'zone' | 'fsp' | 'folder', name: string): string {
  return `${type}_${name}`;
}

async function fetchFileContent(
  fspName: string,
  path: string
): Promise<Uint8Array> {
  const url = getFileContentPath(fspName, path);
  const response = await sendFetchRequest(url, 'GET');
  if (!response.ok) {
    throw new Error(`Failed to fetch file: ${response.statusText}`);
  }
  const fileBuffer = await response.arrayBuffer();
  return new Uint8Array(fileBuffer);
}

async function fetchFileAsText(fspName: string, path: string): Promise<string> {
  const fileContent = await fetchFileContent(fspName, path);
  const decoder = new TextDecoder('utf-8');
  return decoder.decode(fileContent);
}

async function fetchFileAsJson(fspName: string, path: string): Promise<object> {
  const fileText = await fetchFileAsText(fspName, path);
  return JSON.parse(fileText);
}

function isLikelyTextFile(buffer: ArrayBuffer | Uint8Array): boolean {
  const view = buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer;

  let controlCount = 0;
  for (const b of view) {
    if (b < 9 || (b > 13 && b < 32)) {
      controlCount++;
    }
  }

  return controlCount / view.length < 0.01;
}

async function fetchFileWithTextDetection(
  fspName: string,
  path: string
): Promise<{ isText: boolean; content: string; rawData: Uint8Array }> {
  const rawData = await fetchFileContent(fspName, path);
  const isText = isLikelyTextFile(rawData);

  let content: string;
  if (isText) {
    content = new TextDecoder('utf-8', { fatal: false }).decode(rawData);
  } else {
    content = 'Binary file';
  }

  return { isText, content, rawData };
}

export {
  checkSessionValidity,
  escapePathForUrl,
  fetchFileAsJson,
  fetchFileAsText,
  fetchFileContent,
  fetchFileWithTextDetection,
  getFullPath,
  formatDateString,
  formatUnixTimestamp,
  formatFileSize,
  getFileContentPath,
  getFileBrowsePath,
  getFileURL,
  getLastSegmentFromPath,
  getPreferredPathForDisplay,
  HTTPError,
  isLikelyTextFile,
  joinPaths,
  makeBrowseLink,
  makeMapKey,
  makePathSegmentArray,
  parsePermissions,
  removeLastSegmentFromPath,
  sendFetchRequest
};

// Re-export retry utility
export { createRetryWithBackoff } from './retryWithBackoff';
export type {
  RetryOptions,
  RetryCallbacks,
  RetryState
} from './retryWithBackoff';
