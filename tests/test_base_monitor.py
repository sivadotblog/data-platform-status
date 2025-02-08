"""
Unit tests for BaseStatusMonitor class.

Tests the core functionality of the base monitor including:
- Status report generation
- Region processing
- Splunk integration
"""

import json
from datetime import datetime
import pytest
import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from base_status_monitor import BaseStatusMonitor


class TestBaseMonitor(BaseStatusMonitor):
    """Test implementation of BaseStatusMonitor for testing abstract methods"""

    def generate_status_report(self):
        """Test implementation of abstract method"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "operational",
            "regions": {
                "test-region-1": {
                    "status": "operational",
                    "services": {"service1": {"status": "operational"}},
                },
                "test-region-2": {
                    "status": "degraded",
                    "services": {"service2": {"status": "degraded"}},
                },
            },
            "incidents": {
                "test-region-1": [
                    {
                        "id": "incident1",
                        "name": "Test Incident",
                        "status": "investigating",
                    }
                ]
            },
        }


def test_base_monitor_initialization():
    """Test basic initialization of monitor"""
    monitor = TestBaseMonitor("test-tech")
    assert monitor.technology == "test-tech"
    assert monitor.status_report is None


def test_process_all_regions(capsys):
    """Test processing of all regions"""
    monitor = TestBaseMonitor("test-tech")
    monitor.process_all_regions()

    # Check if regions were processed
    captured = capsys.readouterr()
    assert "Processing regions individually:" in captured.out
    assert "test-region-1" in captured.out
    assert "test-region-2" in captured.out


def test_send_to_splunk(capsys):
    """Test Splunk data transmission"""
    monitor = TestBaseMonitor("test-tech")
    region_data = {
        "status": "operational",
        "services": {"service1": {"status": "operational"}},
    }

    # Set status report for incidents
    monitor.status_report = monitor.generate_status_report()

    # Test sending data
    success = monitor.send_to_splunk("test-region", region_data)
    assert success is True

    # Verify output format
    captured = capsys.readouterr()
    output = captured.out
    assert "Would send to API for region test-region" in output

    # Parse and verify JSON payload
    # Find the JSON part between the message and any trailing content
    json_start = output.find("{")
    json_end = output.rfind("}") + 1
    json_str = output[json_start:json_end]
    payload = json.loads(json_str)

    assert payload["technology"] == "test-tech"
    assert payload["region"] == "test-region"
    assert payload["status"] == "operational"
    assert "services" in payload
    assert "timestamp" in payload


def test_generate_status_report_not_implemented():
    """Test that base class raises NotImplementedError"""

    class UnimplementedMonitor(BaseStatusMonitor):
        pass

    monitor = UnimplementedMonitor("test-tech")
    with pytest.raises(NotImplementedError):
        monitor.generate_status_report()


def test_process_all_regions_with_failed_region(capsys):
    """Test processing regions when one region fails"""

    class FailingRegionMonitor(TestBaseMonitor):
        def send_to_splunk(self, region_name, region_data):
            if region_name == "test-region-2":
                return False
            return super().send_to_splunk(region_name, region_data)

    monitor = FailingRegionMonitor("test-tech")
    monitor.process_all_regions()

    captured = capsys.readouterr()
    assert "Failed to process region: test-region-2" in captured.out


def test_process_all_regions_with_exception(capsys):
    """Test processing regions when an exception occurs"""

    class ExceptionRegionMonitor(TestBaseMonitor):
        def send_to_splunk(self, region_name, region_data):
            if region_name == "test-region-2":
                raise Exception("Test exception")
            return super().send_to_splunk(region_name, region_data)

    monitor = ExceptionRegionMonitor("test-tech")
    monitor.process_all_regions()

    captured = capsys.readouterr()
    assert "Error processing region test-region-2: Test exception" in captured.out
