"""
Prefect Status Monitor Module

This module implements a status monitor for Prefect Cloud services. It extends the BaseStatusMonitor
to provide specific functionality for monitoring Prefect's operational status, including service
health checks and incident reporting.

Classes:
    PrefectStatusMonitor: Monitor for Prefect Cloud service status
"""

from datetime import datetime
from typing import Dict, List, Optional
import requests
from base_status_monitor import BaseStatusMonitor


class PrefectStatusMonitor(BaseStatusMonitor):
    """
    Monitor for Prefect Cloud service status.

    This class implements status monitoring specific to Prefect Cloud services.
    It fetches status information from Prefect's status API and processes it into
    a standardized format for monitoring and reporting.

    Attributes:
        status_url (str): The URL endpoint for Prefect's status API
        region (str): The region identifier for Prefect services
    """

    def __init__(self):
        """
        Initialize the PrefectStatusMonitor.

        Sets up the monitor with Prefect-specific configuration including the status API
        endpoint and region information. Since Prefect Cloud doesn't specify regions,
        it uses 'NA' as a default region identifier.
        """
        super().__init__("prefect")
        self.status_url = "https://2266113422411059.hostedstatus.com/1.0/status/5f33ff702715c204c20d6da1"
        self.region = "NA"  # Prefect doesn't specify regions, using NA as required

    def get_status_data(self) -> Dict:
        """
        Fetch status data from Prefect API.

        Retrieves the current operational status of Prefect Cloud services
        from their status API endpoint.

        Returns:
            Dict: Raw status data from Prefect's API

        Raises:
            Exception: If the API request fails or returns invalid data
        """
        try:
            response = requests.get(self.status_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Prefect status: {str(e)}")

    def get_component_status(self, components: List[Dict]) -> Dict:
        """
        Get status details for all components.

        Processes the raw component data from Prefect's API into a standardized
        format, including operational status and last update times.

        Args:
            components (List[Dict]): List of component status dictionaries from Prefect API

        Returns:
            Dict: Processed status information with the following structure:
                {
                    "status": str,          # Overall status (operational/degraded)
                    "last_updated": str,    # ISO format timestamp
                    "services": Dict        # Individual service statuses
                }
        """
        status_info = {"status": "unknown", "last_updated": None, "services": {}}

        for component in components:
            service_name = component.get("name", "Unknown Service")
            component_status = component.get("status", "unknown").lower()
            last_updated = component.get("updated")

            status_info["services"][service_name] = {
                "status": component_status,
                "last_updated": last_updated,
            }

            # Update the last_updated time if it's more recent
            if last_updated and (
                not status_info["last_updated"]
                or last_updated > status_info["last_updated"]
            ):
                status_info["last_updated"] = last_updated

        # Determine overall status
        status_info["status"] = (
            "operational"
            if all(
                svc["status"].lower() == "operational"
                for svc in status_info["services"].values()
            )
            else "degraded"
        )

        return status_info

    def get_incidents(self, raw_data: Dict) -> List[Dict]:
        """
        Get all active incidents.

        Extracts and processes incident information from the raw API data.

        Args:
            raw_data (Dict): Raw status data from Prefect's API

        Returns:
            List[Dict]: List of processed incidents with the following structure:
                [{
                    "id": str,
                    "name": str,
                    "status": str,
                    "impact": str,
                    "created_at": str,
                    "updated_at": str,
                    "resolved_at": str
                }]
        """
        incidents = []

        # Process active incidents
        for incident in raw_data.get("result", {}).get("incidents", []):
            incidents.append(
                {
                    "id": incident.get("id"),
                    "name": incident.get("name"),
                    "status": incident.get("status"),
                    "impact": incident.get("impact", "none"),
                    "created_at": incident.get("created", ""),
                    "updated_at": incident.get("updated", ""),
                    "resolved_at": incident.get("resolved", ""),
                }
            )

        return incidents

    def generate_status_report(self) -> Dict:
        """
        Generate a comprehensive status report.

        Implements the abstract method from BaseStatusMonitor to create a complete
        status report for Prefect Cloud services. This includes overall status,
        component-level details, and any active incidents.

        Returns:
            Dict: Complete status report with the following structure:
                {
                    "timestamp": str,          # ISO format timestamp
                    "overall_status": str,     # Overall Prefect Cloud status
                    "regions": Dict,           # Status data by region
                    "incidents": Dict          # Active incidents by region
                }

        Raises:
            Exception: If status data cannot be fetched or processed
        """
        raw_data = self.get_status_data()
        result = raw_data.get("result", {})

        status_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": result.get("status_overall", {}).get("status", "Unknown"),
            "regions": {
                self.region: self.get_component_status(result.get("status", []))
            },
            "incidents": {},
        }

        # Add incidents if any exist
        incidents = self.get_incidents(raw_data)
        if incidents:
            status_report["incidents"][self.region] = incidents

        return status_report


def main():
    """
    Main entry point for the Prefect status monitor.

    Creates a PrefectStatusMonitor instance and processes all regions,
    handling any errors that occur during execution.
    """
    monitor = PrefectStatusMonitor()
    try:
        monitor.process_all_regions()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
