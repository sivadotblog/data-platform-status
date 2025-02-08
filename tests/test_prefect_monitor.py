"""
Unit tests for PrefectStatusMonitor class.

Tests the Prefect-specific monitoring functionality including:
- API interaction
- Status data processing
- Incident handling
"""

from datetime import datetime
import pytest
import requests
import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prefect_status import PrefectStatusMonitor


@pytest.fixture
def mock_prefect_response(requests_mock):
    """Fixture to mock Prefect API responses"""
    return requests_mock.get(
        "https://2266113422411059.hostedstatus.com/1.0/status/5f33ff702715c204c20d6da1",
        json={
            "result": {
                "status_overall": {"status": "All Systems Operational"},
                "status": [
                    {
                        "name": "Prefect Cloud",
                        "status": "operational",
                        "updated": "2024-02-07T20:00:00Z",
                    },
                    {
                        "name": "Prefect API",
                        "status": "degraded",
                        "updated": "2024-02-07T21:00:00Z",
                    },
                ],
                "incidents": [
                    {
                        "id": "test-incident-1",
                        "name": "API Performance Issues",
                        "status": "investigating",
                        "impact": "minor",
                        "created": "2024-02-07T21:00:00Z",
                        "updated": "2024-02-07T21:30:00Z",
                    }
                ],
            }
        },
    )


def test_prefect_monitor_initialization():
    """Test basic initialization of Prefect monitor"""
    monitor = PrefectStatusMonitor()
    assert monitor.technology == "prefect"
    assert (
        monitor.status_url
        == "https://2266113422411059.hostedstatus.com/1.0/status/5f33ff702715c204c20d6da1"
    )
    assert monitor.region == "NA"


def test_get_status_data(mock_prefect_response):
    """Test fetching status data from Prefect API"""
    monitor = PrefectStatusMonitor()
    data = monitor.get_status_data()

    assert "result" in data
    assert "status_overall" in data["result"]
    assert data["result"]["status_overall"]["status"] == "All Systems Operational"


def test_get_status_data_api_error(requests_mock):
    """Test handling of API errors when fetching status data"""
    requests_mock.get(
        "https://2266113422411059.hostedstatus.com/1.0/status/5f33ff702715c204c20d6da1",
        status_code=500,
    )

    monitor = PrefectStatusMonitor()
    with pytest.raises(Exception) as exc_info:
        monitor.get_status_data()
    assert "Failed to fetch Prefect status" in str(exc_info.value)


def test_get_component_status(mock_prefect_response):
    """Test processing of component status data"""
    monitor = PrefectStatusMonitor()
    components = [
        {
            "name": "Prefect Cloud",
            "status": "operational",
            "updated": "2024-02-07T20:00:00Z",
        },
        {
            "name": "Prefect API",
            "status": "degraded",
            "updated": "2024-02-07T21:00:00Z",
        },
    ]

    status_info = monitor.get_component_status(components)

    assert status_info["status"] == "degraded"  # Because one service is degraded
    assert status_info["last_updated"] == "2024-02-07T21:00:00Z"  # Most recent update
    assert len(status_info["services"]) == 2
    assert status_info["services"]["Prefect Cloud"]["status"] == "operational"
    assert status_info["services"]["Prefect API"]["status"] == "degraded"


def test_get_incidents(mock_prefect_response):
    """Test processing of incident data"""
    monitor = PrefectStatusMonitor()
    raw_data = monitor.get_status_data()

    incidents = monitor.get_incidents(raw_data)

    assert len(incidents) == 1
    incident = incidents[0]
    assert incident["id"] == "test-incident-1"
    assert incident["name"] == "API Performance Issues"
    assert incident["status"] == "investigating"
    assert incident["impact"] == "minor"
    assert incident["created_at"] == "2024-02-07T21:00:00Z"
    assert incident["updated_at"] == "2024-02-07T21:30:00Z"


def test_generate_status_report(mock_prefect_response):
    """Test generation of complete status report"""
    monitor = PrefectStatusMonitor()
    report = monitor.generate_status_report()

    assert isinstance(report["timestamp"], str)
    assert report["overall_status"] == "All Systems Operational"
    assert "NA" in report["regions"]
    assert report["regions"]["NA"]["status"] == "degraded"
    assert len(report["regions"]["NA"]["services"]) == 2
    assert "incidents" in report
    assert len(report["incidents"]["NA"]) == 1


def test_empty_component_status():
    """Test handling of empty component data"""
    monitor = PrefectStatusMonitor()
    status_info = monitor.get_component_status([])

    assert (
        status_info["status"] == "unknown"
    )  # Status should be unknown when no components
    assert status_info["last_updated"] is None
    assert status_info["services"] == {}

    # Test with mixed status components
    status_info = monitor.get_component_status(
        [
            {
                "name": "Service 1",
                "status": "operational",
                "updated": "2024-02-07T20:00:00Z",
            },
            {
                "name": "Service 2",
                "status": "degraded",
                "updated": "2024-02-07T21:00:00Z",
            },
        ]
    )
    assert status_info["status"] == "degraded"


def test_empty_incidents():
    """Test handling of empty incident data"""
    monitor = PrefectStatusMonitor()
    incidents = monitor.get_incidents({"result": {}})

    assert incidents == []


def test_main_function_success(mock_prefect_response, capsys):
    """Test successful execution of main function"""
    from prefect_status import main

    main()
    captured = capsys.readouterr()
    assert "Error" not in captured.out


def test_main_function_error(requests_mock, capsys):
    """Test error handling in main function"""
    from prefect_status import main

    requests_mock.get(
        "https://2266113422411059.hostedstatus.com/1.0/status/5f33ff702715c204c20d6da1",
        status_code=500,
    )

    main()
    captured = capsys.readouterr()
    assert "Error" in captured.out
