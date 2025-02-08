"""
Azure Health Monitor Module

This module implements a status monitor for Azure cloud services. It extends the BaseStatusMonitor
to provide comprehensive monitoring of Azure service health, including service advisories,
maintenance events, incidents, and security alerts across specified regions.

The monitor supports both Service Principal and token-based authentication methods for
accessing Azure's Management API.

Classes:
    AzureHealthMonitor: Monitor for Azure service health status
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from base_status_monitor import BaseStatusMonitor


class AzureHealthMonitor(BaseStatusMonitor):
    """
    Monitor for Azure service health status.

    This class implements comprehensive health monitoring for Azure services.
    It connects to Azure's Management API to fetch service health data,
    process various types of health events, and track the status of
    resources across specified regions.

    Attributes:
        regions_of_interest (List[str]): List of Azure regions to monitor
        base_url (str): Base URL for Azure Management API
        api_version (str): Version of the Azure Management API to use
        subscription_id (str): Azure subscription ID for API access
    """

    def __init__(self):
        """
        Initialize the AzureHealthMonitor.

        Sets up the monitor with Azure-specific configuration including regions
        to monitor, API endpoints, and authentication details. Validates the
        presence of required environment variables.

        Raises:
            Exception: If required environment variables are not set
        """
        super().__init__("azure")
        self.regions_of_interest = ["eastus2", "centralus"]
        self.base_url = "https://management.azure.com"
        self.api_version = "2022-05-01"
        self.subscription_id = self._get_subscription_id()

    def _get_subscription_id(self) -> str:
        """
        Get Azure subscription ID from environment variable.

        Retrieves and validates the Azure subscription ID from the
        AZURE_SUBSCRIPTION_ID environment variable.

        Returns:
            str: The Azure subscription ID

        Raises:
            Exception: If AZURE_SUBSCRIPTION_ID environment variable is not set
        """
        subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            raise Exception(
                "AZURE_SUBSCRIPTION_ID environment variable is not set. Please set it with your Azure subscription ID."
            )
        return subscription_id

    def get_azure_credentials(self) -> Tuple[str, Dict[str, str]]:
        """
        Get Azure credentials from environment variables.

        Attempts to authenticate using Service Principal credentials first,
        falling back to direct token authentication if necessary.

        Returns:
            Tuple[str, Dict[str, str]]: A tuple containing:
                - The authentication token
                - Headers dictionary with the token and content type

        Raises:
            Exception: If neither authentication method is properly configured
        """
        # Check for Service Principal credentials
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")

        if all([client_id, client_secret, tenant_id]):
            try:
                # Use Service Principal authentication
                credential = ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                # Get token for Azure Management API
                token = credential.get_token(
                    "https://management.azure.com/.default"
                ).token
                return token, {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
            except Exception as e:
                print(f"Failed to authenticate with Service Principal: {str(e)}")
                print("Falling back to AZ_TOKEN...")

        # Fallback to AZ_TOKEN
        token = os.getenv("AZ_TOKEN")
        if not token:
            raise Exception(
                "Neither Service Principal credentials nor AZ_TOKEN are properly configured. "
                "Please set either AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID "
                "for Service Principal authentication, or AZ_TOKEN for direct token authentication."
            )

        return token, {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_service_health(self) -> Dict:
        """
        Query Azure Service Health through Management API.

        Fetches comprehensive health data including advisories, maintenance events,
        service issues, and security alerts for the monitored regions.

        Returns:
            Dict: Processed health data with the following structure:
                {
                    "advisories": List[Dict],
                    "maintenance": List[Dict],
                    "issues": List[Dict],
                    "security": List[Dict],
                    "impacted_resources": Dict
                }

        Raises:
            Exception: If the API request fails or returns invalid data
        """
        _, headers = self.get_azure_credentials()  # Get fresh token and headers

        health_data = {
            "advisories": [],
            "maintenance": [],
            "issues": [],
            "security": [],
            "impacted_resources": {},
        }

        try:
            # Get service health alerts
            url = f"{self.base_url}/subscriptions/{self.subscription_id}/providers/Microsoft.ResourceHealth/events?api-version={self.api_version}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            events = response.json().get("value", [])
            for event in events:
                if self._is_event_in_regions(event):
                    event_type = (
                        event.get("properties", {}).get("eventType", "").lower()
                    )
                    if "advisory" in event_type:
                        health_data["advisories"].append(self._process_event(event))
                    elif "maintenance" in event_type:
                        health_data["maintenance"].append(self._process_event(event))
                    elif "incident" in event_type:
                        health_data["issues"].append(self._process_event(event))
                    elif "security" in event_type:
                        health_data["security"].append(self._process_event(event))

                    self._process_impacted_resources(
                        event, health_data["impacted_resources"]
                    )

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Azure health data: {str(e)}")

        return health_data

    def _is_event_in_regions(self, event: Dict) -> bool:
        """
        Check if event affects our regions of interest.

        Args:
            event (Dict): Health event data from Azure API

        Returns:
            bool: True if the event affects any monitored region, False otherwise
        """
        impacted_regions = event.get("properties", {}).get("impactedRegions", [])
        return any(
            region.get("location", "").lower() in self.regions_of_interest
            for region in impacted_regions
        )

    def _process_event(self, event: Dict) -> Dict:
        """
        Process and structure a health event.

        Transforms raw event data from Azure API into a standardized format
        with detailed status information and impact assessment.

        Args:
            event (Dict): Raw event data from Azure API

        Returns:
            Dict: Processed event data with standardized structure including:
                - Basic event information (ID, type, title)
                - Status and severity details
                - Impacted services and regions
                - Detailed status information and timeline
        """
        props = event.get("properties", {})
        return {
            "id": event.get("id"),
            "event_type": props.get("eventType"),
            "title": props.get("title"),
            "status": props.get("status"),
            "severity": props.get("severity"),
            "stage": props.get("stage"),
            "communication_id": props.get("communicationId"),
            "impacted_services": props.get("impactedServices", []),
            "impacted_regions": [
                {"location": region.get("location"), "status": region.get("status")}
                for region in props.get("impactedRegions", [])
                if region.get("location", "").lower() in self.regions_of_interest
            ],
            "last_updated": props.get("lastModifiedTime"),
            "origin": props.get("origin"),
            "description": props.get("description"),
            "detailed_status": {
                "current_status": props.get("status"),
                "status_history": props.get("statusHistory", []),
                "resolution_eta": props.get("estimatedResolutionTime"),
                "user_impact": props.get("userImpact"),
                "root_cause": props.get("rootCause"),
            },
        }

    def _process_impacted_resources(
        self, event: Dict, impacted_resources: Dict
    ) -> None:
        """
        Process and add impacted resources information.

        Updates the impacted_resources dictionary with information about
        resources affected by a health event.

        Args:
            event (Dict): Health event data from Azure API
            impacted_resources (Dict): Dictionary to update with impacted resource information

        Note:
            This method modifies the impacted_resources dictionary in place.
        """
        props = event.get("properties", {})
        for resource in props.get("impactedServices", []):
            resource_id = resource.get("resourceId")
            if resource_id:
                if resource_id not in impacted_resources:
                    impacted_resources[resource_id] = {
                        "service_name": resource.get("serviceName"),
                        "regions_affected": [],
                        "events": [],
                    }

                # Add affected regions
                for region in props.get("impactedRegions", []):
                    region_name = region.get("location", "").lower()
                    if (
                        region_name in self.regions_of_interest
                        and region_name
                        not in impacted_resources[resource_id]["regions_affected"]
                    ):
                        impacted_resources[resource_id]["regions_affected"].append(
                            region_name
                        )

                # Add event reference
                impacted_resources[resource_id]["events"].append(
                    {
                        "event_id": event.get("id"),
                        "type": props.get("eventType"),
                        "severity": props.get("severity"),
                        "status": props.get("status"),
                    }
                )

    def generate_status_report(self) -> Dict:
        """
        Generate a comprehensive status report.

        Implements the abstract method from BaseStatusMonitor to create a complete
        status report for Azure services. This includes detailed health information
        for each monitored region, active incidents, and resource impact assessments.

        Returns:
            Dict: Complete status report with the following structure:
                {
                    "timestamp": str,
                    "technology": Dict,        # Azure service information
                    "regions": Dict            # Status data by region including:
                                             # - Health advisories
                                             # - Planned maintenance
                                             # - Service issues
                                             # - Security advisories
                                             # - Impacted resources
                }

        Raises:
            Exception: If status data cannot be fetched or processed
        """
        health_data = self.get_service_health()

        status_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "technology": {
                "name": "azure",
                "type": "cloud_platform",
                "provider": "microsoft",
                "regions_monitored": self.regions_of_interest,
            },
            "regions": {},
        }

        # Process each region
        for region in self.regions_of_interest:
            region_status = self._get_region_status(region, health_data)
            status_report["regions"][region] = {
                "status": region_status["status"],
                "last_updated": datetime.utcnow().isoformat(),
                "services": {
                    "health_advisory": {
                        "status": (
                            "degraded" if health_data["advisories"] else "operational"
                        ),
                        "events": [
                            e
                            for e in health_data["advisories"]
                            if region
                            in [r["location"].lower() for r in e["impacted_regions"]]
                        ],
                    },
                    "planned_maintenance": {
                        "status": (
                            "maintenance"
                            if health_data["maintenance"]
                            else "operational"
                        ),
                        "events": [
                            e
                            for e in health_data["maintenance"]
                            if region
                            in [r["location"].lower() for r in e["impacted_regions"]]
                        ],
                    },
                    "service_issues": {
                        "status": (
                            "degraded" if health_data["issues"] else "operational"
                        ),
                        "events": [
                            e
                            for e in health_data["issues"]
                            if region
                            in [r["location"].lower() for r in e["impacted_regions"]]
                        ],
                    },
                    "security_advisory": {
                        "status": (
                            "degraded" if health_data["security"] else "operational"
                        ),
                        "events": [
                            e
                            for e in health_data["security"]
                            if region
                            in [r["location"].lower() for r in e["impacted_regions"]]
                        ],
                    },
                },
                "impacted_resources": {
                    resource_id: resource_data
                    for resource_id, resource_data in health_data[
                        "impacted_resources"
                    ].items()
                    if region in resource_data["regions_affected"]
                },
            }

        return status_report

    def _get_region_status(self, region: str, health_data: Dict) -> Dict:
        """
        Determine overall status for a region.

        Analyzes various health events to determine the overall operational
        status of a specific region.

        Args:
            region (str): The region to evaluate
            health_data (Dict): Collected health data for all regions

        Returns:
            Dict: Status information with structure:
                {
                    "status": str    # One of: "operational", "degraded", "maintenance"
                }
        """
        has_issues = any(
            region in [r["location"].lower() for r in event["impacted_regions"]]
            for event_list in [
                health_data["issues"],
                health_data["advisories"],
                health_data["security"],
            ]
            for event in event_list
        )
        has_maintenance = any(
            region in [r["location"].lower() for r in event["impacted_regions"]]
            for event in health_data["maintenance"]
        )

        if has_issues:
            return {"status": "degraded"}
        elif has_maintenance:
            return {"status": "maintenance"}
        return {"status": "operational"}


def main():
    """
    Main entry point for the Azure health monitor.

    Creates an AzureHealthMonitor instance and processes all regions,
    handling any errors that occur during execution.
    """
    monitor = AzureHealthMonitor()
    try:
        monitor.process_all_regions()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
