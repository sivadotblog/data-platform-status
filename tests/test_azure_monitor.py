"""
Unit tests for AzureHealthMonitor class.

Tests the Azure-specific monitoring functionality including:
- Authentication handling
- Service health data processing
- Event categorization
- Region-specific event filtering
- Resource impact assessment
"""

import os
from datetime import datetime
import pytest
import requests
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from azure_health import AzureHealthMonitor


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up environment variables for testing"""
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "test-subscription")
    monkeypatch.setenv("AZURE_CLIENT_ID", "test-client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant")


@pytest.fixture
def mock_azure_response(requests_mock):
    """Fixture to mock Azure API responses"""
    return requests_mock.get(
        "https://management.azure.com/subscriptions/test-subscription/providers/Microsoft.ResourceHealth/events",
        json={
            "value": [
                {
                    "id": "/subscriptions/test-subscription/events/incident1",
                    "properties": {
                        "eventType": "Incident",
                        "title": "VM Service Issues",
                        "status": "Active",
                        "severity": "Warning",
                        "stage": "Active",
                        "communicationId": "COM1",
                        "impactedServices": [
                            {
                                "serviceName": "Virtual Machines",
                                "resourceId": "/subscriptions/test-subscription/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
                            }
                        ],
                        "impactedRegions": [
                            {"location": "eastus2", "status": "Active"}
                        ],
                        "lastModifiedTime": "2024-02-07T21:00:00Z",
                        "origin": "Platform",
                        "description": "VM service experiencing issues",
                        "statusHistory": ["Investigating", "Active"],
                        "estimatedResolutionTime": "2024-02-08T00:00:00Z",
                        "userImpact": "Some VMs may be unreachable",
                        "rootCause": "Network connectivity issues",
                    },
                },
                {
                    "id": "/subscriptions/test-subscription/events/maintenance1",
                    "properties": {
                        "eventType": "Maintenance",
                        "title": "Planned Network Maintenance",
                        "status": "Scheduled",
                        "severity": "Information",
                        "impactedServices": [{"serviceName": "Virtual Network"}],
                        "impactedRegions": [
                            {"location": "centralus", "status": "Scheduled"}
                        ],
                        "lastModifiedTime": "2024-02-07T20:00:00Z",
                    },
                },
            ]
        },
    )


def test_azure_monitor_initialization(mock_env_vars):
    """Test basic initialization of Azure monitor"""
    monitor = AzureHealthMonitor()
    assert monitor.technology == "azure"
    assert monitor.base_url == "https://management.azure.com"
    assert monitor.api_version == "2022-05-01"
    assert monitor.subscription_id == "test-subscription"
    assert "eastus2" in monitor.regions_of_interest
    assert "centralus" in monitor.regions_of_interest


def test_get_subscription_id_missing():
    """Test handling of missing subscription ID"""
    with pytest.raises(Exception) as exc_info:
        monitor = AzureHealthMonitor()
    assert "AZURE_SUBSCRIPTION_ID environment variable is not set" in str(
        exc_info.value
    )


def test_get_azure_credentials_service_principal(mock_env_vars, mocker):
    """Test Service Principal authentication"""
    mock_credential = mocker.patch("azure.identity.ClientSecretCredential")
    mock_credential.return_value.get_token.return_value.token = "test-token"

    monitor = AzureHealthMonitor()
    token, headers = monitor.get_azure_credentials()

    assert token == "test-token"
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Content-Type"] == "application/json"


def test_get_azure_credentials_fallback(monkeypatch):
    """Test fallback to AZ_TOKEN authentication"""
    monkeypatch.setenv("AZ_TOKEN", "fallback-token")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "test-subscription")

    monitor = AzureHealthMonitor()
    token, headers = monitor.get_azure_credentials()

    assert token == "fallback-token"
    assert headers["Authorization"] == "Bearer fallback-token"


def test_get_azure_credentials_no_auth(mock_env_base):
    """Test handling of missing authentication credentials"""
    os.environ["AZURE_SUBSCRIPTION_ID"] = "test-subscription"

    with pytest.raises(Exception) as exc_info:
        monitor = AzureHealthMonitor()
        monitor.get_azure_credentials()
    assert (
        "Neither Service Principal credentials nor AZ_TOKEN are properly configured"
        in str(exc_info.value)
    )


def test_get_service_health(mock_env_vars, mock_azure_response, mocker):
    """Test fetching and processing service health data"""
    mock_cred = mocker.patch("azure.identity.ClientSecretCredential")
    mock_cred.return_value.get_token.return_value.token = "test-token"
    monitor = AzureHealthMonitor()
    health_data = monitor.get_service_health()

    assert len(health_data["issues"]) == 1
    assert len(health_data["maintenance"]) == 1
    assert len(health_data["advisories"]) == 0
    assert len(health_data["security"]) == 0
    assert "impacted_resources" in health_data


def test_is_event_in_regions(mock_env_vars):
    """Test region filtering for events"""
    monitor = AzureHealthMonitor()
    event = {
        "properties": {
            "impactedRegions": [
                {"location": "eastus2"},
                {"location": "westus"},
            ]
        }
    }

    assert monitor._is_event_in_regions(event) is True

    event["properties"]["impactedRegions"] = [{"location": "westus"}]
    assert monitor._is_event_in_regions(event) is False


def test_process_event(mock_env_vars):
    """Test event data processing"""
    monitor = AzureHealthMonitor()
    event = {
        "id": "test-event",
        "properties": {
            "eventType": "Incident",
            "title": "Test Event",
            "status": "Active",
            "severity": "Warning",
            "impactedRegions": [{"location": "eastus2"}],
            "lastModifiedTime": "2024-02-07T21:00:00Z",
        },
    }

    processed = monitor._process_event(event)
    assert processed["id"] == "test-event"
    assert processed["event_type"] == "Incident"
    assert processed["title"] == "Test Event"
    assert len(processed["impacted_regions"]) == 1


def test_process_impacted_resources(mock_env_vars):
    """Test processing of impacted resources"""
    monitor = AzureHealthMonitor()
    event = {
        "properties": {
            "eventType": "Incident",
            "impactedServices": [
                {
                    "serviceName": "Test Service",
                    "resourceId": "test-resource",
                }
            ],
            "impactedRegions": [{"location": "eastus2"}],
        },
    }

    impacted_resources = {}
    monitor._process_impacted_resources(event, impacted_resources)

    assert "test-resource" in impacted_resources
    assert impacted_resources["test-resource"]["service_name"] == "Test Service"
    assert "eastus2" in impacted_resources["test-resource"]["regions_affected"]


def test_generate_status_report(mock_env_vars, mock_azure_response, mocker):
    """Test generation of complete status report"""
    mock_cred = mocker.patch("azure.identity.ClientSecretCredential")
    mock_cred.return_value.get_token.return_value.token = "test-token"
    monitor = AzureHealthMonitor()
    report = monitor.generate_status_report()

    assert isinstance(report["timestamp"], str)
    assert "technology" in report
    assert report["technology"]["name"] == "azure"
    assert len(report["regions"]) == 2

    # Check eastus2 region (has incident)
    eastus2 = report["regions"]["eastus2"]
    assert eastus2["status"] == "degraded"
    assert eastus2["services"]["service_issues"]["status"] == "degraded"

    # Check centralus region (has maintenance)
    centralus = report["regions"]["centralus"]
    assert centralus["status"] == "maintenance"
    assert centralus["services"]["planned_maintenance"]["status"] == "maintenance"


def test_get_region_status(mock_env_vars):
    """Test region status determination"""
    monitor = AzureHealthMonitor()
    health_data = {
        "issues": [
            {
                "impacted_regions": [{"location": "eastus2"}],
            }
        ],
        "maintenance": [],
        "advisories": [],
        "security": [],
    }

    status = monitor._get_region_status("eastus2", health_data)
    assert status["status"] == "degraded"

    status = monitor._get_region_status("centralus", health_data)
    assert status["status"] == "operational"


def test_main_function_success(mock_env_vars, mock_azure_response, mocker, capsys):
    """Test successful execution of main function"""
    mock_cred = mocker.patch("azure.identity.ClientSecretCredential")
    mock_cred.return_value.get_token.return_value.token = "test-token"
    mock_cred.return_value.get_token.return_value.expires_on = None

    from azure_health import main

    main()

    captured = capsys.readouterr()
    assert "Error" not in captured.out


def test_main_function_error(mock_env_vars, requests_mock, mocker, capsys):
    """Test error handling in main function"""
    mocker.patch("azure.identity.ClientSecretCredential")
    from azure_health import main

    requests_mock.get(
        "https://management.azure.com/subscriptions/test-subscription/providers/Microsoft.ResourceHealth/events",
        status_code=500,
    )

    main()
    captured = capsys.readouterr()
    assert "Error" in captured.out
