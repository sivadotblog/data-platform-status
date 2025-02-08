"""
Unit tests for SnowflakeStatusMonitor class.

Tests the Snowflake-specific monitoring functionality including:
- Region-specific status monitoring
- Component group handling
- Incident filtering by region
"""

from datetime import datetime
import pytest
import requests
import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from snowflake_status import SnowflakeStatusMonitor


@pytest.fixture
def mock_snowflake_response(requests_mock):
    """Fixture to mock Snowflake API responses"""
    return requests_mock.get(
        "https://status.snowflake.com/api/v2/summary.json",
        json={
            "status": {"description": "All Systems Operational"},
            "components": [
                {
                    "name": "Query Processing",
                    "status": "operational",
                    "updated_at": "2024-02-07T20:00:00Z",
                    "group_id": "4pbr6y23kkht",  # East US 2
                },
                {
                    "name": "Data Loading",
                    "status": "degraded",
                    "updated_at": "2024-02-07T21:00:00Z",
                    "group_id": "4pbr6y23kkht",  # East US 2
                },
                {
                    "name": "Query Processing",
                    "status": "operational",
                    "updated_at": "2024-02-07T20:00:00Z",
                    "group_id": "y7xv3hzhhc80",  # Central US
                },
            ],
            "incidents": [
                {
                    "id": "test-incident-1",
                    "name": "Data Loading Performance Issues",
                    "status": "investigating",
                    "impact": "minor",
                    "created_at": "2024-02-07T21:00:00Z",
                    "updated_at": "2024-02-07T21:30:00Z",
                    "resolved_at": None,
                    "components": [
                        {"name": "Data Loading", "group_id": "4pbr6y23kkht"}
                    ],
                }
            ],
        },
    )


def test_snowflake_monitor_initialization():
    """Test basic initialization of Snowflake monitor"""
    monitor = SnowflakeStatusMonitor()
    assert monitor.technology == "snowflake"
    assert monitor.status_url == "https://status.snowflake.com/api/v2/summary.json"
    assert len(monitor.regions_of_interest) == 2
    assert "Azure - East US 2 (Virginia)" in monitor.regions_of_interest
    assert "Azure - Central US (Iowa)" in monitor.regions_of_interest


def test_get_status_data(mock_snowflake_response):
    """Test fetching status data from Snowflake API"""
    monitor = SnowflakeStatusMonitor()
    data = monitor.get_status_data()

    assert "status" in data
    assert "components" in data
    assert "incidents" in data
    assert data["status"]["description"] == "All Systems Operational"


def test_get_status_data_api_error(requests_mock):
    """Test handling of API errors when fetching status data"""
    requests_mock.get(
        "https://status.snowflake.com/api/v2/summary.json",
        status_code=500,
    )

    monitor = SnowflakeStatusMonitor()
    with pytest.raises(Exception) as exc_info:
        monitor.get_status_data()
    assert "Failed to fetch Snowflake status" in str(exc_info.value)


def test_get_component_status(mock_snowflake_response):
    """Test processing of component status data for a specific region"""
    monitor = SnowflakeStatusMonitor()
    raw_data = monitor.get_status_data()

    # Test East US 2 region components
    status_info = monitor.get_component_status(raw_data["components"], "4pbr6y23kkht")

    assert status_info["status"] == "degraded"  # Because Data Loading is degraded
    assert status_info["last_updated"] == "2024-02-07T21:00:00Z"  # Most recent update
    assert len(status_info["services"]) == 2
    assert status_info["services"]["Query Processing"]["status"] == "operational"
    assert status_info["services"]["Data Loading"]["status"] == "degraded"


def test_get_region_incidents(mock_snowflake_response):
    """Test filtering of incidents by region"""
    monitor = SnowflakeStatusMonitor()
    raw_data = monitor.get_status_data()

    # Test East US 2 region incidents
    incidents = monitor.get_region_incidents(raw_data["incidents"], "4pbr6y23kkht")

    assert len(incidents) == 1
    incident = incidents[0]
    assert incident["id"] == "test-incident-1"
    assert incident["name"] == "Data Loading Performance Issues"
    assert incident["status"] == "investigating"

    # Test Central US region incidents (should be empty)
    central_incidents = monitor.get_region_incidents(
        raw_data["incidents"], "y7xv3hzhhc80"
    )
    assert len(central_incidents) == 0


def test_generate_status_report(mock_snowflake_response):
    """Test generation of complete status report"""
    monitor = SnowflakeStatusMonitor()
    report = monitor.generate_status_report()

    assert isinstance(report["timestamp"], str)
    assert report["overall_status"] == "All Systems Operational"
    assert len(report["regions"]) == 2

    # Check East US 2 region
    east_us = report["regions"]["Azure - East US 2 (Virginia)"]
    assert east_us["status"] == "degraded"
    assert len(east_us["services"]) == 2
    assert "incidents" in report
    assert len(report["incidents"]["Azure - East US 2 (Virginia)"]) == 1

    # Check Central US region
    central_us = report["regions"]["Azure - Central US (Iowa)"]
    assert central_us["status"] == "operational"
    assert len(central_us["services"]) == 1


def test_empty_component_status():
    """Test handling of empty component data"""
    monitor = SnowflakeStatusMonitor()
    status_info = monitor.get_component_status([], "4pbr6y23kkht")

    assert status_info["status"] == "unknown"
    assert status_info["last_updated"] is None
    assert status_info["services"] == {}


def test_empty_incidents():
    """Test handling of empty incident data"""
    monitor = SnowflakeStatusMonitor()
    incidents = monitor.get_region_incidents([], "4pbr6y23kkht")

    assert incidents == []


def test_main_function_success(mock_snowflake_response, capsys):
    """Test successful execution of main function"""
    from snowflake_status import main

    main()
    captured = capsys.readouterr()
    assert "Error" not in captured.out


def test_main_function_error(requests_mock, capsys):
    """Test error handling in main function"""
    from snowflake_status import main

    requests_mock.get(
        "https://status.snowflake.com/api/v2/summary.json",
        status_code=500,
    )

    main()
    captured = capsys.readouterr()
    assert "Error" in captured.out


def test_component_status_no_matching_group():
    """Test component status when no components match the group ID"""
    monitor = SnowflakeStatusMonitor()
    status_info = monitor.get_component_status(
        [
            {
                "name": "Service",
                "status": "operational",
                "group_id": "different-group",
            }
        ],
        "4pbr6y23kkht",
    )

    assert status_info["status"] == "unknown"
    assert status_info["services"] == {}


def test_incidents_with_no_components():
    """Test handling of incidents with no component information"""
    monitor = SnowflakeStatusMonitor()
    incidents = monitor.get_region_incidents(
        [
            {
                "id": "test-incident",
                "name": "Test Incident",
                "components": [],  # Empty components list
            }
        ],
        "4pbr6y23kkht",
    )

    assert incidents == []
