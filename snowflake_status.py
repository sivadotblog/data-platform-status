"""
Snowflake Status Monitor Module

This module implements a status monitor for Snowflake services. It extends the BaseStatusMonitor
to provide specific functionality for monitoring Snowflake's operational status across different
Azure regions, including service health checks and incident reporting.

Classes:
    SnowflakeStatusMonitor: Monitor for Snowflake service status
"""

from datetime import datetime
from typing import Dict, List, Optional
import requests
from base_status_monitor import BaseStatusMonitor


class SnowflakeStatusMonitor(BaseStatusMonitor):
    """
    Monitor for Snowflake service status.

    This class implements status monitoring specific to Snowflake services.
    It fetches status information from Snowflake's status API and processes it into
    a standardized format for monitoring and reporting, with a focus on specific
    Azure regions.

    Attributes:
        status_url (str): The URL endpoint for Snowflake's status API
        regions_of_interest (Dict[str, str]): Mapping of region names to their IDs
    """

    def __init__(self):
        """
        Initialize the SnowflakeStatusMonitor.

        Sets up the monitor with Snowflake-specific configuration including the status API
        endpoint and region mappings for Azure regions of interest.
        """
        super().__init__("snowflake")
        self.status_url = "https://status.snowflake.com/api/v2/summary.json"
        self.regions_of_interest = {
            "Azure - East US 2 (Virginia)": "4pbr6y23kkht",
            "Azure - Central US (Iowa)": "y7xv3hzhhc80",
        }

    def get_status_data(self) -> Dict:
        """
        Fetch status data from Snowflake API.

        Retrieves the current operational status of Snowflake services
        from their status API endpoint.

        Returns:
            Dict: Raw status data from Snowflake's API

        Raises:
            Exception: If the API request fails or returns invalid data
        """
        try:
            response = requests.get(self.status_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Snowflake status: {str(e)}")

    def get_component_status(self, components: List[Dict], group_id: str) -> Dict:
        """
        Get status details for a specific component group.

        Processes the raw component data from Snowflake's API for a specific region
        into a standardized format, including operational status and last update times.

        Args:
            components (List[Dict]): List of component status dictionaries from Snowflake API
            group_id (str): The ID of the region group to process

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
            if component.get("group_id") == group_id:
                service_name = component.get("name", "Unknown Service")
                status_info["services"][service_name] = {
                    "status": component.get("status", "unknown"),
                    "last_updated": component.get("updated_at"),
                }
                status_info["status"] = (
                    "operational"
                    if all(
                        svc["status"] == "operational"
                        for svc in status_info["services"].values()
                    )
                    else "degraded"
                )

                # Update the last_updated time if it's more recent
                component_time = component.get("updated_at")
                if component_time and (
                    not status_info["last_updated"]
                    or component_time > status_info["last_updated"]
                ):
                    status_info["last_updated"] = component_time

        return status_info

    def get_region_incidents(self, incidents: List[Dict], group_id: str) -> List[Dict]:
        """
        Get incidents affecting a specific region.

        Filters and processes incident information from the raw API data
        for a specific region.

        Args:
            incidents (List[Dict]): List of all incidents from Snowflake API
            group_id (str): The ID of the region group to filter incidents for

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
        region_incidents = []

        for incident in incidents:
            # Check if incident affects our region
            affects_region = False
            for component in incident.get("components", []):
                if component.get("group_id") == group_id:
                    affects_region = True
                    break

            if affects_region:
                region_incidents.append(
                    {
                        "id": incident.get("id"),
                        "name": incident.get("name"),
                        "status": incident.get("status"),
                        "impact": incident.get("impact"),
                        "created_at": incident.get("created_at"),
                        "updated_at": incident.get("updated_at"),
                        "resolved_at": incident.get("resolved_at"),
                    }
                )

        return region_incidents

    def generate_status_report(self) -> Dict:
        """
        Generate a comprehensive status report.

        Implements the abstract method from BaseStatusMonitor to create a complete
        status report for Snowflake services. This includes overall status,
        component-level details for each monitored region, and any active incidents.

        Returns:
            Dict: Complete status report with the following structure:
                {
                    "timestamp": str,          # ISO format timestamp
                    "overall_status": str,     # Overall Snowflake status
                    "regions": Dict,           # Status data by region
                    "incidents": Dict          # Active incidents by region
                }

        Raises:
            Exception: If status data cannot be fetched or processed
        """
        raw_data = self.get_status_data()

        status_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": raw_data.get("status", {}).get("description", "Unknown"),
            "regions": {},
            "incidents": {},
        }

        # Process each region
        for region_name, group_id in self.regions_of_interest.items():
            status_report["regions"][region_name] = self.get_component_status(
                raw_data.get("components", []), group_id
            )

            # Get incidents for this region
            incidents = self.get_region_incidents(
                raw_data.get("incidents", []), group_id
            )
            if incidents:
                status_report["incidents"][region_name] = incidents

        return status_report


def main():
    """
    Main entry point for the Snowflake status monitor.

    Creates a SnowflakeStatusMonitor instance and processes all regions,
    handling any errors that occur during execution.
    """
    monitor = SnowflakeStatusMonitor()
    try:
        monitor.process_all_regions()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
