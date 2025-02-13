import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from databricks_status import DatabricksStatusMonitor, get_env_var

# Mock data for different event types
MOCK_WAREHOUSE_EVENT = [
    (
        "acc1",
        "ws1",
        "wh1",
        "START",
        2,
        datetime(2024, 1, 1),
        [["env", "prod"], ["team", "data"]],
    )
]

MOCK_JOB_EVENT = [
    (
        "acc1",
        "ws1",
        "job1",
        "run1",
        "MANUAL",
        "JOB_RUN",
        "test_run",
        "compute1",
        "SUCCESS",
        None,
        {"param": "value"},
        datetime(2024, 1, 1),
        datetime(2024, 1, 2),
        [["env", "prod"]],
        "Test Job",
        "Test Description",
    )
]

MOCK_QUERY_EVENT = [
    (
        "acc1",
        "ws1",
        "stmt1",
        "sess1",
        "SUCCESS",
        "wh1",
        "user1",
        "test@test.com",
        "SELECT 1",
        "SELECT",
        None,
        "app1",
        "driver1",
        1000,
        100,
        50,
        800,
        50,
        900,
        100,
        datetime(2024, 1, 1),
        datetime(2024, 1, 2),
        datetime(2024, 1, 2),
        10,
        5,
        3,
        1000,
        500,
        1024,
        80,
        True,
        0,
        512,
        256,
        "UI",
        "test",
        "user_id1",
    )
]

MOCK_AUDIT_EVENT = [
    (
        "v1",
        datetime(2024, 1, 1),
        datetime(2024, 1, 1),
        "ws1",
        "1.1.1.1",
        "Mozilla",
        "sess1",
        "user1",
        "service1",
        "action1",
        "req1",
        {"param": "value"},
        {"status": "success"},
        "INFO",
        "acc1",
        "event1",
        {"key": "value"},
    )
]

MOCK_CLUSTER_EVENT = [
    (
        "acc1",
        "ws1",
        "cluster1",
        "test-cluster",
        "owner1",
        datetime(2024, 1, 1),
        None,
        "Standard_D4s_v3",
        "Standard_D4s_v3",
        2,
        1,
        4,
        120,
        True,
        [["env", "prod"]],
        "UI",
        None,
        None,
        None,
        None,
        "10.4",
        datetime(2024, 1, 1),
    )
]

MOCK_JOB_TASK_EVENT = [
    (
        "acc1",
        "ws1",
        "job1",
        "run1",
        "job_run1",
        "parent1",
        "task1",
        "compute1",
        "SUCCESS",
        None,
        datetime(2024, 1, 1),
        datetime(2024, 1, 2),
        [["env", "prod"]],
        "Test Job",
        "Test Description",
        ["task2", "task3"],
    )
]


class MockCursorContextManager:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_cursor():
    """Create a mock cursor with execute and fetchall methods."""
    cursor = Mock()
    cursor.fetchall = Mock()
    cursor.fetchone = Mock(return_value=None)
    cursor.execute = Mock()
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    """Create a mock connection that returns our mock cursor."""
    connection = Mock()
    cursor_context = MockCursorContextManager(mock_cursor)
    connection.cursor.return_value = cursor_context
    return connection


@pytest.fixture
def mock_monitor(mock_connection):
    """Create a DatabricksStatusMonitor instance with mocked connection."""
    with patch("databricks.sql.connect", return_value=mock_connection):
        monitor = DatabricksStatusMonitor(
            server_hostname="test-host",
            http_path="test-path",
            access_token="test-token",
        )
        # Mock the send_to_splunk method from parent class
        monitor.send_to_splunk = Mock(return_value=True)
        return monitor


def test_init(mock_monitor):
    """Test monitor initialization."""
    assert mock_monitor.server_hostname == "test-host"
    assert mock_monitor.http_path == "test-path"
    assert mock_monitor.access_token == "test-token"
    assert mock_monitor.checkpoint_table == "main.default.batch_job_checkpoint"


def test_ensure_checkpoint_table(mock_monitor, mock_cursor):
    """Test checkpoint table creation."""
    mock_monitor.ensure_checkpoint_table()
    mock_cursor.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS" in mock_cursor.execute.call_args[0][0]


def test_get_last_checkpoint_existing(mock_monitor, mock_cursor):
    """Test getting existing checkpoint."""
    expected_time = datetime(2024, 1, 1)
    mock_cursor.fetchone.return_value = [expected_time]

    result = mock_monitor.get_last_checkpoint("test_type", "test_table")
    assert result == expected_time


def test_get_last_checkpoint_new(mock_monitor, mock_cursor):
    """Test getting checkpoint when none exists."""
    mock_cursor.fetchone.return_value = None

    result = mock_monitor.get_last_checkpoint("test_type", "test_table")
    assert isinstance(result, datetime)
    assert result < datetime.utcnow()


def test_get_last_checkpoint_error(mock_monitor, mock_cursor):
    """Test getting checkpoint with database error."""
    mock_cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.get_last_checkpoint("test_type", "test_table")
    assert "Database error" in str(exc_info.value)


def test_ensure_checkpoint_table_error(mock_monitor, mock_cursor):
    """Test checkpoint table creation with error."""
    mock_cursor.execute.side_effect = Exception("Table creation failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.ensure_checkpoint_table()
    assert "Table creation failed" in str(exc_info.value)


def test_update_checkpoint_error(mock_monitor, mock_cursor):
    """Test updating checkpoint with error."""
    test_time = datetime(2024, 1, 1)
    mock_cursor.execute.side_effect = Exception("Update failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.update_checkpoint("test_type", "test_table", test_time)
    assert "Update failed" in str(exc_info.value)


def test_process_warehouse_events_no_events(mock_monitor, mock_cursor):
    """Test warehouse event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_warehouse_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_warehouse_events_send_failure(mock_monitor, mock_cursor):
    """Test warehouse event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_WAREHOUSE_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_warehouse_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_warehouse_events_error(mock_monitor, mock_cursor):
    """Test warehouse event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_warehouse_events()
    assert "Query failed" in str(exc_info.value)


def test_process_warehouse_events_with_reset(mock_monitor, mock_cursor):
    """Test warehouse event processing with reset flag."""
    mock_cursor.fetchall.return_value = MOCK_WAREHOUSE_EVENT

    mock_monitor.process_warehouse_events(reset_checkpoint=True)

    # Should have called update_checkpoint twice:
    # 1. For resetting to 24 hours ago
    # 2. For updating after processing events
    assert mock_cursor.execute.call_count >= 2


def test_update_checkpoint(mock_monitor, mock_cursor):
    """Test updating checkpoint."""
    test_time = datetime(2024, 1, 1)
    mock_monitor.update_checkpoint("test_type", "test_table", test_time)
    mock_cursor.execute.assert_called_once()
    assert test_time.isoformat() in mock_cursor.execute.call_args[0][0]


@pytest.mark.parametrize(
    "tags,expected",
    [
        (None, {}),
        ({}, {}),
        (
            [["key1", "value1"], ["key2", "value2"]],
            {"key1": "value1", "key2": "value2"},
        ),
        ({"key1": "value1"}, {"key1": "value1"}),
    ],
)
def test_convert_tags_to_dict(mock_monitor, tags, expected):
    """Test tag conversion with different input formats."""
    result = mock_monitor._convert_tags_to_dict(tags)
    assert result == expected


def test_process_warehouse_events(mock_monitor, mock_cursor):
    """Test warehouse event processing."""
    mock_cursor.fetchall.return_value = MOCK_WAREHOUSE_EVENT

    mock_monitor.process_warehouse_events()

    # Verify events were processed
    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "warehouse_events"
    assert event_data["event"]["warehouse_id"] == "wh1"


def test_process_job_events(mock_monitor, mock_cursor):
    """Test job event processing."""
    mock_cursor.fetchall.return_value = MOCK_JOB_EVENT

    mock_monitor.process_job_events()

    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "job_events"
    assert event_data["event"]["job_id"] == "job1"


def test_process_job_events_no_events(mock_monitor, mock_cursor):
    """Test job event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_job_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_job_events_send_failure(mock_monitor, mock_cursor):
    """Test job event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_JOB_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_job_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_job_events_error(mock_monitor, mock_cursor):
    """Test job event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_job_events()
    assert "Query failed" in str(exc_info.value)


def test_connection_close():
    """Test connection close in main function."""
    mock_connection = Mock()
    mock_monitor = Mock()
    mock_monitor.connection = mock_connection

    with patch("databricks.sql.connect", return_value=mock_connection), patch.dict(
        "os.environ",
        {
            "DATABRICKS_HOST": "test-host",
            "DATABRICKS_HTTP_PATH": "test-path",
            "DATABRICKS_TOKEN": "test-token",
        },
    ), patch("databricks_status.DatabricksStatusMonitor", return_value=mock_monitor):

        from databricks_status import main

        main()
        mock_connection.close.assert_called_once()


def test_process_query_events(mock_monitor, mock_cursor):
    """Test query event processing."""
    mock_cursor.fetchall.return_value = MOCK_QUERY_EVENT

    mock_monitor.process_query_events()

    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "query_events"
    assert event_data["event"]["statement_id"] == "stmt1"


def test_process_query_events_no_events(mock_monitor, mock_cursor):
    """Test query event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_query_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_query_events_send_failure(mock_monitor, mock_cursor):
    """Test query event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_QUERY_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_query_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_query_events_error(mock_monitor, mock_cursor):
    """Test query event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_query_events()
    assert "Query failed" in str(exc_info.value)


def test_process_audit_events(mock_monitor, mock_cursor):
    """Test audit event processing."""
    mock_cursor.fetchall.return_value = MOCK_AUDIT_EVENT

    mock_monitor.process_audit_events()

    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "audit_events"
    assert event_data["event"]["event_id"] == "event1"


def test_process_audit_events_no_events(mock_monitor, mock_cursor):
    """Test audit event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_audit_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_audit_events_send_failure(mock_monitor, mock_cursor):
    """Test audit event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_AUDIT_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_audit_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_audit_events_error(mock_monitor, mock_cursor):
    """Test audit event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_audit_events()
    assert "Query failed" in str(exc_info.value)


def test_process_cluster_events(mock_monitor, mock_cursor):
    """Test cluster event processing."""
    mock_cursor.fetchall.return_value = MOCK_CLUSTER_EVENT

    mock_monitor.process_cluster_events()

    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "cluster_events"
    assert event_data["event"]["cluster_id"] == "cluster1"


def test_process_cluster_events_no_events(mock_monitor, mock_cursor):
    """Test cluster event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_cluster_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_cluster_events_send_failure(mock_monitor, mock_cursor):
    """Test cluster event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_CLUSTER_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_cluster_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_cluster_events_error(mock_monitor, mock_cursor):
    """Test cluster event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_cluster_events()
    assert "Query failed" in str(exc_info.value)


def test_process_job_task_events(mock_monitor, mock_cursor):
    """Test job task event processing."""
    mock_cursor.fetchall.return_value = MOCK_JOB_TASK_EVENT

    mock_monitor.process_job_task_events()

    mock_monitor.send_to_splunk.assert_called_once()
    event_data = mock_monitor.send_to_splunk.call_args[0][1]  # Second positional arg
    assert event_data["platform"] == "databricks"
    assert event_data["event_type"] == "job_task_events"
    assert event_data["event"]["task_key"] == "task1"


def test_process_job_task_events_no_events(mock_monitor, mock_cursor):
    """Test job task event processing with no events."""
    mock_cursor.fetchall.return_value = []
    mock_monitor.process_job_task_events()
    mock_monitor.send_to_splunk.assert_not_called()


def test_process_job_task_events_send_failure(mock_monitor, mock_cursor):
    """Test job task event processing with send failure."""
    mock_cursor.fetchall.return_value = MOCK_JOB_TASK_EVENT
    mock_monitor.send_to_splunk.return_value = False

    mock_monitor.process_job_task_events()
    mock_monitor.send_to_splunk.assert_called_once()


def test_process_job_task_events_error(mock_monitor, mock_cursor):
    """Test job task event processing with database error."""
    mock_cursor.execute.side_effect = Exception("Query failed")

    with pytest.raises(Exception) as exc_info:
        mock_monitor.process_job_task_events()
    assert "Query failed" in str(exc_info.value)


def test_get_env_var_exists():
    """Test getting existing environment variable."""
    with patch("os.getenv", return_value="test-value"):
        assert get_env_var("TEST_VAR") == "test-value"


def test_get_env_var_missing():
    """Test getting missing environment variable."""
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError):
            get_env_var("MISSING_VAR")


@patch("databricks_status.DatabricksStatusMonitor")
def test_main_success(mock_monitor_class):
    """Test main function success path."""
    mock_monitor = Mock()
    mock_monitor_class.return_value = mock_monitor

    with patch.dict(
        "os.environ",
        {
            "DATABRICKS_HOST": "test-host",
            "DATABRICKS_HTTP_PATH": "test-path",
            "DATABRICKS_TOKEN": "test-token",
        },
    ):
        from databricks_status import main

        main()

        # Verify monitor was initialized and methods were called
        mock_monitor_class.assert_called_once()
        mock_monitor.ensure_checkpoint_table.assert_called_once()
        mock_monitor.process_warehouse_events.assert_called_once()
        mock_monitor.process_job_events.assert_called_once()
        mock_monitor.process_job_task_events.assert_called_once()
        mock_monitor.process_query_events.assert_called_once()
        mock_monitor.process_cluster_events.assert_called_once()
        mock_monitor.process_audit_events.assert_called_once()


@patch("databricks_status.DatabricksStatusMonitor")
def test_main_error(mock_monitor_class):
    """Test main function error handling."""
    mock_monitor = Mock()
    mock_monitor.ensure_checkpoint_table.side_effect = Exception("Test error")
    mock_monitor_class.return_value = mock_monitor

    with patch.dict(
        "os.environ",
        {
            "DATABRICKS_HOST": "test-host",
            "DATABRICKS_HTTP_PATH": "test-path",
            "DATABRICKS_TOKEN": "test-token",
        },
    ):
        from databricks_status import main

        main()  # Should handle exception without raising
