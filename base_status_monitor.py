"""
Base Status Monitor Module

This module provides a base class for monitoring the operational status of various technology services.
It implements core functionality for collecting status data and sending reports to a monitoring system.
The class is designed to be extended by specific service monitors that implement their own status
checking logic while inheriting common reporting capabilities.

Classes:
    BaseStatusMonitor: Abstract base class for service status monitoring
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
import requests


class BaseStatusMonitor:
    """
    Abstract base class for service status monitoring.

    This class provides the foundation for monitoring various technology services.
    It implements common functionality for processing and reporting service status
    while defining an interface that specific service monitors must implement.

    Attributes:
        technology (str): The name of the technology being monitored
        status_report (Optional[Dict]): The latest generated status report
    """

    def __init__(self, technology: str):
        """
        Initialize the BaseStatusMonitor.

        Args:
            technology (str): The name of the technology service being monitored
        """
        self.technology = technology
        self.status_report = None

    def send_to_splunk(self, region_name: str, region_data: Dict) -> bool:
        """
        Send status report for a specific region to Splunk API.

        This method handles the transmission of status data to a Splunk instance
        for monitoring and analysis purposes.

        Args:
            region_name (str): The name of the region being reported
            region_data (Dict): Status data for the specified region

        Returns:
            bool: True if the data was successfully sent, False otherwise
        """
        api_url = "api.example.com"

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "technology": self.technology,
            "region": region_name,
            "status": region_data.get("status"),
            "services": region_data.get("services", {}),
            "incidents": self.status_report.get("incidents", {}).get(region_name, []),
        }

        # Commented out for testing
        """
        try:
            response = requests.post(
                f"https://{api_url}/region-status",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Region": region_name
                }
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to send status for region {region_name}: {str(e)}")
            return False
        """
        print(
            f"\nWould send to API for region {region_name}:",
            json.dumps(payload, indent=2),
        )
        return True

    def process_all_regions(self) -> None:
        """
        Process and send status for each region separately.

        This method orchestrates the collection and transmission of status data
        for all monitored regions. It handles any errors that occur during
        processing and ensures each region is processed independently.

        Raises:
            Exception: If there are errors processing specific regions
        """
        self.status_report = self.generate_status_report()

        print("Processing regions individually:")
        for region_name, region_data in self.status_report["regions"].items():
            try:
                success = self.send_to_splunk(region_name, region_data)
                if not success:
                    print(f"Failed to process region: {region_name}")
            except Exception as e:
                print(f"Error processing region {region_name}: {str(e)}")

    def generate_status_report(self) -> Dict:
        """
        Generate a comprehensive status report.

        This is an abstract method that must be implemented by subclasses to generate
        a complete status report for their specific technology service.

        Returns:
            Dict: A dictionary containing the complete status report with the following structure:
                {
                    "timestamp": str,          # ISO format timestamp
                    "overall_status": str,     # Overall service status
                    "regions": Dict,           # Status data for each region
                    "incidents": Dict          # Any active incidents by region
                }

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate_status_report")
