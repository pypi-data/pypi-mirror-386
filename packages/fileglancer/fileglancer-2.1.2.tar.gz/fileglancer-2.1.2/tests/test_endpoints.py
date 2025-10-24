import os
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from fileglancer.settings import Settings
from fileglancer.app import create_app
from fileglancer.database import *
from fileglancer.model import TicketComment

# Test user constant for authentication override
TEST_USERNAME = "testuser"

@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {temp_dir}")
    yield temp_dir
    # Clean up the temp directory
    print(f"Cleaning up temp directory: {temp_dir}")
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_app(temp_dir):
    """Create test FastAPI app"""

    # Create temp directory for test database
    db_path = os.path.join(temp_dir, "test.db")
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    Base.metadata.create_all(engine)

    fsp = FileSharePathDB(
        name="tempdir",
        zone="testzone",
        group="testgroup",
        storage="local",
        mount_path=temp_dir,
        mac_path="smb://tempdir/test/path",
        windows_path="\\\\tempdir\\test\\path",
        linux_path="/tempdir/test/path"
    )
    db_session.add(fsp)
    db_session.commit()
    print(f"Created file share path {fsp.name} with mount path {fsp.mount_path}")

    # Create directory for testing proxied paths
    test_proxied_path = os.path.join(temp_dir, "test_proxied_path")
    os.makedirs(test_proxied_path, exist_ok=True)
    test_proxied_path = os.path.join(temp_dir, "new_test_proxied_path")
    os.makedirs(test_proxied_path, exist_ok=True)

    settings = Settings(db_url=db_url, file_share_mounts=[])

    # Monkey-patch get_settings to return our test settings
    import fileglancer.settings
    import fileglancer.database

    # Save original functions and clear cache
    original_get_settings = fileglancer.settings.get_settings

    # Replace with test settings
    fileglancer.settings.get_settings = lambda: settings
    fileglancer.database.get_settings = lambda: settings

    app = create_app(settings)

    yield app

    # Cleanup: close all database connections
    db_session.close()
    engine.dispose()
    # Dispose the cached engine from the database module
    from fileglancer.database import dispose_engine
    dispose_engine(db_url)

    # Restore original get_settings and clear cache
    fileglancer.settings.get_settings = original_get_settings
    fileglancer.database.get_settings = original_get_settings


@pytest.fixture
def test_client(test_app):
    """Create test client with authentication bypass"""
    # Override the get_current_user dependency to return a test user
    from fileglancer.app import get_current_user

    def override_get_current_user():
        return TEST_USERNAME

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(test_app)

    yield client

    # Clean up the override after tests
    test_app.dependency_overrides.clear()


def test_robots_txt(test_client):
    """Test robots.txt endpoint"""
    response = test_client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get('content-type', '')
    assert "User-agent: *" in response.text
    assert "Disallow: /" in response.text


def test_version_endpoint(test_client):
    """Test /api/version endpoint"""
    response = test_client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


def test_root_endpoint(test_client):
    """Test root endpoint - should redirect to /fg/"""
    response = test_client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers.get('location') == '/fg/'

def test_fg_endpoint(test_client):
    """Test /fg/ endpoint - should serve SPA index.html"""
    response = test_client.get("/fg/", follow_redirects=False)
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

def test_fg_spa_routing(test_client):
    """Test /fg/browse and other SPA routes - should serve SPA index.html"""
    response = test_client.get("/fg/browse", follow_redirects=False)
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

    response = test_client.get("/fg/browse/some/path", follow_redirects=False)
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')

def test_api_404_returns_json(test_client):
    """Test that invalid API endpoints return JSON 404, not HTML"""
    response = test_client.get("/api/nonexistent", follow_redirects=False)
    assert response.status_code == 404
    assert 'application/json' in response.headers.get('content-type', '')
    data = response.json()
    assert 'error' in data


def test_get_preferences(test_client):
    """Test getting user preferences"""
    response = test_client.get("/api/preference")
    assert response.status_code == 200
    value = response.json()
    assert isinstance(value, dict)
    assert value == {}


def test_get_specific_preference(test_client):
    """Test getting specific user preference"""
    response = test_client.get("/api/preference/unknown_key")
    assert response.status_code == 404


def test_set_preference(test_client):
    """Test setting user preference"""
    pref_data = {"test": "value"}
    response = test_client.put("/api/preference/test_key", json=pref_data)
    assert response.status_code == 200

    response = test_client.get("/api/preference/test_key")
    assert response.status_code == 200
    assert response.json() == pref_data


def test_delete_preference(test_client):
    """Test deleting user preference"""
    pref_data = {"test": "value"}
    response = test_client.put("/api/preference/test_key", json=pref_data)

    response = test_client.delete("/api/preference/test_key")
    assert response.status_code == 200

    response = test_client.delete("/api/preference/unknown_key")
    assert response.status_code == 404


def test_create_proxied_path(test_client, temp_dir):
    """Test creating a new proxied path"""
    path = "test_proxied_path"

    response = test_client.post(f"/api/proxied-path?fsp_name=tempdir&path={path}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == TEST_USERNAME
    assert data["path"] == path
    assert "sharing_key" in data
    assert "sharing_name" in data


def test_get_proxied_paths(test_client):
    """Test retrieving proxied paths for a user"""
    path = "test_proxied_path"
    response = test_client.post(f"/api/proxied-path?fsp_name=tempdir&path={path}")
    assert response.status_code == 200
    response = test_client.get(f"/api/proxied-path")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "paths" in data
    assert isinstance(data["paths"], list)


def test_update_proxied_path(test_client):
    """Test updating a proxied path"""
    # First, create a proxied path to update
    path = "test_proxied_path"
    response = test_client.post(f"/api/proxied-path?fsp_name=tempdir&path={path}")
    assert response.status_code == 200
    data = response.json()
    sharing_key = data["sharing_key"]

    # Update the proxied path
    new_path = "new_test_proxied_path"

    response = test_client.put(f"/api/proxied-path/{sharing_key}?fsp_name=tempdir&path={new_path}")
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["path"] == new_path


def test_delete_proxied_path(test_client):
    """Test deleting a proxied path"""
    # First, create a proxied path to delete
    path = "test_proxied_path"
    response = test_client.post(f"/api/proxied-path?fsp_name=tempdir&path={path}")
    assert response.status_code == 200
    data = response.json()
    sharing_key = data["sharing_key"]

    # Delete the proxied path
    response = test_client.delete(f"/api/proxied-path/{sharing_key}")
    assert response.status_code == 200

    # Verify deletion
    response = test_client.get(f"/api/proxied-path/{sharing_key}")
    assert response.status_code == 404


def test_get_external_buckets(test_client):
    """Test getting external buckets"""
    response = test_client.get("/api/external-buckets")
    assert response.status_code == 200
    data = response.json()
    assert "buckets" in data
    assert isinstance(data["buckets"], list)
    # Should contain external buckets from the database
    # The actual number depends on what's in the database
    assert len(data["buckets"]) >= 0

    # Verify structure of returned buckets if any exist
    if data["buckets"]:
        bucket = data["buckets"][0]
        assert "id" in bucket
        assert "fsp_name" in bucket
        # full_path and external_url are now required fields
        assert "full_path" in bucket
        assert bucket["full_path"] is not None
        assert "external_url" in bucket
        assert bucket["external_url"] is not None
        assert "relative_path" in bucket  # This can still be None


def test_get_file_share_paths(test_client):
    """Test getting file share paths"""
    response = test_client.get("/api/file-share-paths")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert isinstance(data["paths"], list)
    # Should have at least the tempdir path we created in the fixture
    assert len(data["paths"]) > 0

    # Verify structure of returned paths
    path = data["paths"][0]
    assert "zone" in path
    assert "name" in path
    assert "mount_path" in path
    assert path["zone"] == "testzone"
    assert path["name"] == "tempdir"


def test_get_files(test_client, temp_dir):
    """Test getting files from a file share path"""
    # Create a test file in the temp directory
    test_file = os.path.join(temp_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    response = test_client.get("/api/files/tempdir")
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert isinstance(data["files"], list)

    # Find our test file in the results
    file_names = [f["name"] for f in data["files"]]
    assert "test_file.txt" in file_names


def test_create_directory(test_client, temp_dir):
    """Test creating a directory"""
    response = test_client.post(
        "/api/files/tempdir?subpath=newdir",
        json={"type": "directory"}
    )
    assert response.status_code == 201
    assert os.path.exists(os.path.join(temp_dir, "newdir"))


def test_create_file(test_client, temp_dir):
    """Test creating an empty file"""
    response = test_client.post(
        "/api/files/tempdir?subpath=newfile.txt",
        json={"type": "file"}
    )
    assert response.status_code == 201
    assert os.path.exists(os.path.join(temp_dir, "newfile.txt"))


def test_patch_file_permissions(test_client, temp_dir):
    """Test changing file permissions"""
    # Create a test file
    test_file = os.path.join(temp_dir, "test_perms.txt")
    with open(test_file, "w") as f:
        f.write("test")

    response = test_client.patch(
        "/api/files/tempdir?subpath=test_perms.txt",
        json={"permissions": "-rw-r--r--"}
    )
    assert response.status_code == 204


def test_patch_file_move(test_client, temp_dir):
    """Test moving a file"""
    # Create a test file
    test_file = os.path.join(temp_dir, "move_me.txt")
    with open(test_file, "w") as f:
        f.write("test")

    response = test_client.patch(
        "/api/files/tempdir?subpath=move_me.txt",
        json={"path": "moved.txt"}
    )
    assert response.status_code == 204
    assert not os.path.exists(test_file)
    assert os.path.exists(os.path.join(temp_dir, "moved.txt"))


def test_delete_file(test_client, temp_dir):
    """Test deleting a file"""
    # Create a test file
    test_file = os.path.join(temp_dir, "delete_me.txt")
    with open(test_file, "w") as f:
        f.write("test")

    response = test_client.delete("/api/files/tempdir?subpath=delete_me.txt")
    assert response.status_code == 204
    assert not os.path.exists(test_file)


def test_get_profile(test_client):
    """Test getting user profile"""
    response = test_client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "homeFileSharePathName" in data
    assert "homeDirectoryName" in data
    assert "groups" in data
    assert isinstance(data["username"], str)
    assert isinstance(data["groups"], list)


def test_get_notifications_no_file(test_client):
    """Test getting notifications when notifications.yaml doesn't exist"""
    response = test_client.get("/api/notifications")
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert isinstance(data["notifications"], list)
    assert len(data["notifications"]) == 0


def test_get_notifications_with_file(test_client, temp_dir):
    """Test getting notifications when notifications.yaml exists"""
    # Create a notifications.yaml file in the current working directory
    notifications_file = os.path.join(os.getcwd(), "notifications.yaml")
    notifications_content = f"""notifications:
  - id: 1
    type: info
    title: Test Notification
    message: This is a test notification
    active: true
    created_at: {datetime.now(timezone.utc).isoformat()}
    expires_at: null
  - id: 2
    type: warning
    title: Expired Notification
    message: This notification is expired
    active: true
    created_at: 2020-01-01T00:00:00Z
    expires_at: 2020-01-02T00:00:00Z
  - id: 3
    type: error
    title: Inactive Notification
    message: This notification is inactive
    active: false
    created_at: {datetime.now(timezone.utc).isoformat()}
    expires_at: null
"""

    try:
        with open(notifications_file, "w") as f:
            f.write(notifications_content)

        response = test_client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert isinstance(data["notifications"], list)
        # Should only include the active, non-expired notification
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["id"] == 1
        assert data["notifications"][0]["type"] == "info"
        assert data["notifications"][0]["title"] == "Test Notification"
    finally:
        # Clean up
        if os.path.exists(notifications_file):
            os.remove(notifications_file)


def test_head_file_content(test_client, temp_dir):
    """Test HEAD request for file content"""
    # Create a test file
    test_file = os.path.join(temp_dir, "content_test.txt")
    test_content = "Hello, World!"
    with open(test_file, "w") as f:
        f.write(test_content)

    response = test_client.head("/api/content/tempdir?subpath=content_test.txt")
    assert response.status_code == 200
    assert "Accept-Ranges" in response.headers
    assert response.headers["Accept-Ranges"] == "bytes"
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len(test_content)


def test_get_file_content(test_client, temp_dir):
    """Test GET request for file content"""
    # Create a test file
    test_file = os.path.join(temp_dir, "download_test.txt")
    test_content = "This is test content for download"
    with open(test_file, "w") as f:
        f.write(test_content)

    response = test_client.get("/api/content/tempdir?subpath=download_test.txt")
    assert response.status_code == 200
    assert response.text == test_content
    assert "Accept-Ranges" in response.headers
    assert response.headers["Accept-Ranges"] == "bytes"


def test_get_file_content_with_range(test_client, temp_dir):
    """Test GET request for file content with Range header"""
    # Create a test file
    test_file = os.path.join(temp_dir, "range_test.txt")
    test_content = "0123456789"
    with open(test_file, "w") as f:
        f.write(test_content)

    # Request bytes 2-5 (should return "2345")
    response = test_client.get(
        "/api/content/tempdir?subpath=range_test.txt",
        headers={"Range": "bytes=2-5"}
    )
    assert response.status_code == 206  # Partial content
    assert response.text == "2345"
    assert "Content-Range" in response.headers
    assert response.headers["Content-Range"] == "bytes 2-5/10"


def test_get_file_content_invalid_range(test_client, temp_dir):
    """Test GET request with invalid range returns 416"""
    # Create a test file
    test_file = os.path.join(temp_dir, "invalid_range_test.txt")
    test_content = "short"
    with open(test_file, "w") as f:
        f.write(test_content)

    # Request range beyond file size
    response = test_client.get(
        "/api/content/tempdir?subpath=invalid_range_test.txt",
        headers={"Range": "bytes=100-200"}
    )
    assert response.status_code == 416  # Range not satisfiable
    assert "Content-Range" in response.headers


def test_get_file_content_directory_error(test_client, temp_dir):
    """Test GET request for directory content returns 400"""
    # Create a directory
    test_dir = os.path.join(temp_dir, "test_directory")
    os.makedirs(test_dir)

    response = test_client.get("/api/content/tempdir?subpath=test_directory")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "directory" in data["error"].lower()


def test_get_file_content_not_found(test_client):
    """Test GET request for non-existent file returns 404"""
    response = test_client.get("/api/content/tempdir?subpath=nonexistent.txt")
    assert response.status_code == 404


# Ticket endpoint tests with mocked JIRA integration

@patch('fileglancer.app.create_jira_ticket')
@patch('fileglancer.app.get_jira_ticket_details')
def test_create_ticket(mock_get_details, mock_create, test_client, temp_dir):
    """Test creating a new ticket"""
    # Mock JIRA responses
    mock_create.return_value = {'key': 'TEST-123'}
    mock_get_details.return_value = {
        'key': 'TEST-123',
        'created': datetime.now(timezone.utc),
        'updated': datetime.now(timezone.utc),
        'status': 'Open',
        'resolution': 'Unresolved',
        'description': 'Test ticket description',
        'link': HttpUrl('https://jira.example.com/browse/TEST-123'),
        'comments': []
    }

    # Create a test directory in tempdir
    test_path = os.path.join(temp_dir, "test_ticket_path")
    os.makedirs(test_path, exist_ok=True)

    ticket_data = {
        "fsp_name": "tempdir",
        "path": "test_ticket_path",
        "project_key": "TEST",
        "issue_type": "Bug",
        "summary": "Test ticket",
        "description": "This is a test ticket"
    }

    response = test_client.post("/api/ticket", json=ticket_data)
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "TEST-123"
    assert data["username"] == TEST_USERNAME
    assert data["fsp_name"] == "tempdir"
    assert data["path"] == "test_ticket_path"
    assert data["status"] == "Open"
    assert data["resolution"] == "Unresolved"

    # Verify JIRA functions were called
    mock_create.assert_called_once_with(
        project_key="TEST",
        issue_type="Bug",
        summary="Test ticket",
        description="This is a test ticket"
    )
    mock_get_details.assert_called_once_with('TEST-123')


@patch('fileglancer.app.create_jira_ticket')
@patch('fileglancer.app.get_jira_ticket_details')
def test_create_ticket_jira_failure(mock_get_details, mock_create, test_client, temp_dir):
    """Test creating a ticket when JIRA returns invalid response"""
    # Mock JIRA to return invalid response
    mock_create.return_value = {}  # Missing 'key'

    test_path = os.path.join(temp_dir, "test_ticket_path")
    os.makedirs(test_path, exist_ok=True)

    ticket_data = {
        "fsp_name": "tempdir",
        "path": "test_ticket_path",
        "project_key": "TEST",
        "issue_type": "Bug",
        "summary": "Test ticket",
        "description": "This is a test ticket"
    }

    response = test_client.post("/api/ticket", json=ticket_data)
    assert response.status_code == 500
    data = response.json()
    assert "error" in data


@patch('fileglancer.app.create_jira_ticket')
@patch('fileglancer.app.get_jira_ticket_details')
def test_get_tickets(mock_get_details, mock_create, test_client, temp_dir):
    """Test retrieving tickets for a user"""
    # First create a ticket
    mock_create.return_value = {'key': 'TEST-456'}

    # Create a proper TicketComment object
    test_comment = TicketComment(
        author_name='testuser',
        author_display_name='Test User',
        body='Test comment',
        created=datetime.now(timezone.utc),
        updated=datetime.now(timezone.utc)
    )

    mock_get_details.return_value = {
        'key': 'TEST-456',
        'created': datetime.now(timezone.utc),
        'updated': datetime.now(timezone.utc),
        'status': 'In Progress',
        'resolution': 'Unresolved',
        'description': 'Another test ticket',
        'link': HttpUrl('https://jira.example.com/browse/TEST-456'),
        'comments': [test_comment]
    }

    test_path = os.path.join(temp_dir, "test_ticket_path2")
    os.makedirs(test_path, exist_ok=True)

    ticket_data = {
        "fsp_name": "tempdir",
        "path": "test_ticket_path2",
        "project_key": "TEST",
        "issue_type": "Task",
        "summary": "Another ticket",
        "description": "Another test ticket"
    }

    # Create the ticket
    response = test_client.post("/api/ticket", json=ticket_data)
    assert response.status_code == 200

    # Now retrieve tickets
    response = test_client.get("/api/ticket")
    assert response.status_code == 200
    data = response.json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)
    assert len(data["tickets"]) > 0

    # Check the ticket details
    ticket = data["tickets"][0]
    assert ticket["key"] == "TEST-456"
    assert ticket["status"] == "In Progress"
    assert "comments" in ticket
    assert len(ticket["comments"]) == 1


@patch('fileglancer.app.create_jira_ticket')
@patch('fileglancer.app.get_jira_ticket_details')
def test_get_tickets_with_filters(mock_get_details, mock_create, test_client, temp_dir):
    """Test retrieving tickets with fsp_name and path filters"""
    # Create a ticket
    mock_create.return_value = {'key': 'TEST-789'}
    mock_get_details.return_value = {
        'key': 'TEST-789',
        'created': datetime.now(timezone.utc),
        'updated': datetime.now(timezone.utc),
        'status': 'Resolved',
        'resolution': 'Fixed',
        'description': 'Filtered ticket',
        'link': HttpUrl('https://jira.example.com/browse/TEST-789'),
        'comments': []
    }

    test_path = os.path.join(temp_dir, "filtered_path")
    os.makedirs(test_path, exist_ok=True)

    ticket_data = {
        "fsp_name": "tempdir",
        "path": "filtered_path",
        "project_key": "TEST",
        "issue_type": "Task",
        "summary": "Filtered ticket",
        "description": "Test filtering"
    }

    response = test_client.post("/api/ticket", json=ticket_data)
    assert response.status_code == 200

    # Retrieve with filters
    response = test_client.get("/api/ticket?fsp_name=tempdir&path=filtered_path")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tickets"]) > 0
    assert data["tickets"][0]["path"] == "filtered_path"


@patch('fileglancer.app.get_jira_ticket_details')
def test_get_tickets_jira_unavailable(mock_get_details, test_client):
    """Test retrieving tickets when JIRA details are unavailable"""
    # Mock JIRA to raise an exception
    mock_get_details.side_effect = Exception("JIRA unavailable")

    # This should still return tickets, but with 'Deleted' status
    response = test_client.get("/api/ticket")
    # Should return 404 if no tickets exist, which is expected for clean test
    assert response.status_code == 404


@patch('fileglancer.app.delete_jira_ticket')
def test_delete_ticket(mock_delete, test_client):
    """Test deleting a ticket"""
    # Mock successful deletion
    mock_delete.return_value = None

    response = test_client.delete("/api/ticket/TEST-999")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "TEST-999" in data["message"]

    mock_delete.assert_called_once_with("TEST-999")


@patch('fileglancer.app.delete_jira_ticket')
def test_delete_ticket_not_found(mock_delete, test_client):
    """Test deleting a non-existent ticket"""
    # Mock JIRA to raise "Issue Does Not Exist" exception
    mock_delete.side_effect = Exception("Issue Does Not Exist")

    response = test_client.delete("/api/ticket/NONEXISTENT-123")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

