"""
Databricks Status Monitor Module

This module implements a status monitor for Databricks services. It extends the BaseStatusMonitor
to provide specific functionality for monitoring Databricks operational status, including
job runs, warehouse usage, and system events.

Classes:
    DatabricksStatusMonitor: Monitor for Databricks service status
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import databricks.sql
import json
from base_status_monitor import BaseStatusMonitor


class DatabricksStatusMonitor(BaseStatusMonitor):
    """
    Monitor for Databricks service status.

    This class implements status monitoring specific to Databricks services.
    It connects to Databricks SQL warehouse to fetch system events and job statuses,
    processes them into a standardized format for monitoring and reporting.

    Attributes:
        server_hostname (str): The Databricks SQL warehouse hostname
        http_path (str): The HTTP path for the SQL warehouse
        access_token (str): Databricks access token
        checkpoint_table (str): Fully qualified name of the checkpoint table
    """

    def __init__(
        self,
        server_hostname: str,
        http_path: str,
        access_token: str,
        checkpoint_table: str = "main.default.batch_job_checkpoint",
    ):
        """
        Initialize the DatabricksStatusMonitor.

        Args:
            server_hostname (str): The Databricks SQL warehouse hostname
            http_path (str): The HTTP path for the SQL warehouse
            access_token (str): Databricks access token
            checkpoint_table (str): Fully qualified name of the checkpoint table
        """
        super().__init__("databricks")
        self.server_hostname = server_hostname
        self.http_path = http_path
        self.access_token = access_token
        self.checkpoint_table = checkpoint_table
        print("Initializing database connection...")
        self.connection = databricks.sql.connect(
            server_hostname=self.server_hostname,
            http_path=self.http_path,
            access_token=self.access_token,
        )
        print("Successfully connected to Databricks SQL warehouse")

    def ensure_checkpoint_table(self) -> None:
        """
        Ensure the checkpoint table exists, create if it doesn't.

        The checkpoint table stores the last processed timestamp for incremental extraction.
        """
        print(f"Ensuring checkpoint table exists: {self.checkpoint_table}")
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.checkpoint_table} (
            monitor_type STRING,
            table_name STRING,
            last_processed_time TIMESTAMP,
            PRIMARY KEY (monitor_type, table_name)
        )
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                print("Checkpoint table created/verified successfully")
        except Exception as e:
            print(f"Error creating checkpoint table: {str(e)}")
            raise

    def get_last_checkpoint(self, monitor_type: str, table_name: str) -> datetime:
        """
        Get the last processed timestamp for a specific monitor type and table.

        Args:
            monitor_type (str): Type of monitoring (e.g., 'jobs', 'tasks')
            table_name (str): Name of the audit table being monitored

        Returns:
            datetime: The last processed timestamp or 24 hours ago if no checkpoint exists
        """
        print(
            f"Getting last checkpoint for monitor type: {monitor_type}, table: {table_name}"
        )
        query = f"""
        SELECT last_processed_time
        FROM {self.checkpoint_table}
        WHERE monitor_type = '{monitor_type}'
        AND table_name = '{table_name}'
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()

                if result:
                    print(f"Found existing checkpoint: {result[0]}")
                    return result[0]

                # Default to 24 hours ago if no checkpoint exists
                default_time = datetime.utcnow() - timedelta(days=1)
                print(f"No checkpoint found, inserting default time: {default_time}")
                cursor.execute(
                    f"""
                    INSERT INTO {self.checkpoint_table} (monitor_type, table_name, last_processed_time)
                    VALUES ('{monitor_type}', '{table_name}', '{default_time.isoformat()}')
                    """
                )
                return default_time
        except Exception as e:
            print(f"Error getting/setting checkpoint: {str(e)}")
            raise

    def update_checkpoint(
        self, monitor_type: str, table_name: str, new_timestamp: datetime
    ) -> None:
        """
        Update the checkpoint timestamp for a specific monitor type and table.

        Args:
            monitor_type (str): Type of monitoring (e.g., 'jobs', 'tasks')
            table_name (str): Name of the audit table being monitored
            new_timestamp (datetime): The new checkpoint timestamp
        """
        print(
            f"Updating checkpoint for {monitor_type}, table: {table_name} to {new_timestamp}"
        )
        update_sql = f"""
        UPDATE {self.checkpoint_table}
        SET last_processed_time = '{new_timestamp.isoformat()}'
        WHERE monitor_type = '{monitor_type}'
        AND table_name = '{table_name}'
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(update_sql)
                print("Checkpoint updated successfully")
        except Exception as e:
            print(f"Error updating checkpoint: {str(e)}")
            raise

    def _convert_tags_to_dict(self, tags: Union[List, Dict, None]) -> Dict:
        """
        Convert tags from list format to dictionary format.

        Args:
            tags: Tags in either list format [[key1, value1], [key2, value2]]
                 or dict format {key1: value1, key2: value2} or None

        Returns:
            Dict format {key1: value1, key2: value2}
        """
        if not tags:
            return {}

        # If already a dict, return as is
        if isinstance(tags, dict):
            return tags

        # Convert list format to dict
        if isinstance(tags, list):
            return {tag[0]: tag[1] for tag in tags if len(tag) == 2}

        return {}

    def process_warehouse_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process warehouse events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "warehouse_events"
        table_name = "system.compute.warehouse_events"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                w.account_id,
                w.workspace_id,
                w.warehouse_id,
                w.event_type,
                w.cluster_count,
                w.event_time,
                wh.tags
            FROM {table_name} w
            LEFT JOIN system.compute.warehouses wh 
                ON w.warehouse_id = wh.warehouse_id 
                AND w.workspace_id = wh.workspace_id
                AND w.account_id = wh.account_id
            WHERE w.event_time > '{last_checkpoint.isoformat()}'
            AND w.event_time <= '{current_time.isoformat()}'
            ORDER BY w.event_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new warehouse events found")
                    return

                # Process each event
                for event in events:
                    event_data = {
                        "platform": "databricks",
                        "event_type": "warehouse_events",
                        "event": {
                            "account_id": event[0],
                            "workspace_id": event[1],
                            "warehouse_id": event[2],
                            "event_type": event[3],
                            "cluster_count": event[4],
                            "event_time": event[5].isoformat(),
                            "tags": self._convert_tags_to_dict(event[6]),
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("warehouse", event_data)
                    if not success:
                        print(f"Failed to send warehouse event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[5] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} warehouse events")

        except Exception as e:
            print(f"Error processing warehouse events: {str(e)}")
            raise

    def process_job_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process job events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "job_events"
        table_name = "system.lakeflow.job_run_timeline"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                r.account_id,
                r.workspace_id,
                r.job_id,
                r.run_id,
                r.trigger_type,
                r.run_type,
                r.run_name,
                r.compute_ids,
                r.result_state,
                r.termination_code,
                r.job_parameters,
                r.period_start_time,
                r.period_end_time,
                j.tags,
                j.name as job_name,
                j.description as job_description
            FROM {table_name} r
            LEFT JOIN system.lakeflow.jobs j
                ON r.job_id = j.job_id
                AND r.workspace_id = j.workspace_id
                AND r.account_id = j.account_id
            WHERE r.period_start_time > '{last_checkpoint.isoformat()}'
            AND r.period_start_time <= '{current_time.isoformat()}'
            ORDER BY r.period_start_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new job events found")
                    return

                # Process each event
                for event in events:
                    event_data = {
                        "platform": "databricks",
                        "event_type": "job_events",
                        "event": {
                            "account_id": event[0],
                            "workspace_id": event[1],
                            "job_id": event[2],
                            "run_id": event[3],
                            "trigger_type": event[4],
                            "run_type": event[5],
                            "run_name": event[6],
                            "compute_ids": str(event[7]) if event[7] else "",
                            "result_state": event[8],
                            "termination_code": event[9],
                            "job_parameters": event[10] if event[10] else {},
                            "period_start_time": event[11].isoformat(),
                            "period_end_time": (
                                event[12].isoformat() if event[12] else None
                            ),
                            "tags": self._convert_tags_to_dict(event[13]),
                            "job_name": event[14],
                            "job_description": event[15],
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("jobs", event_data)
                    if not success:
                        print(f"Failed to send job event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[11] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} job events")

        except Exception as e:
            print(f"Error processing job events: {str(e)}")
            raise

    def process_query_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process query execution events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "query_events"
        table_name = "system.query.history"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                account_id,
                workspace_id,
                statement_id,
                session_id,
                execution_status,
                compute,
                executed_by_user_id,
                executed_by,
                statement_text,
                statement_type,
                error_message,
                client_application,
                client_driver,
                total_duration_ms,
                waiting_for_compute_duration_ms,
                waiting_at_capacity_duration_ms,
                execution_duration_ms,
                compilation_duration_ms,
                total_task_duration_ms,
                result_fetch_duration_ms,
                start_time,
                end_time,
                update_time,
                read_partitions,
                pruned_files,
                read_files,
                read_rows,
                produced_rows,
                read_bytes,
                read_io_cache_percent,
                from_result_cache,
                spilled_local_bytes,
                written_bytes,
                shuffle_read_bytes,
                query_source,
                executed_as,
                executed_as_user_id
            FROM {table_name}
            WHERE start_time > '{last_checkpoint.isoformat()}'
            AND start_time <= '{current_time.isoformat()}'
            ORDER BY start_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new query events found")
                    return

                # Process each event
                for event in events:
                    event_data = {
                        "platform": "databricks",
                        "event_type": "query_events",
                        "event": {
                            "account_id": event[0],
                            "workspace_id": event[1],
                            "statement_id": event[2],
                            "session_id": event[3],
                            "execution_status": event[4],
                            "compute": event[5],
                            "executed_by_user_id": event[6],
                            "executed_by": event[7],
                            "statement_text": event[8],
                            "statement_type": event[9],
                            "error_message": event[10],
                            "client_application": event[11],
                            "client_driver": event[12],
                            "total_duration_ms": event[13],
                            "waiting_for_compute_duration_ms": event[14],
                            "waiting_at_capacity_duration_ms": event[15],
                            "execution_duration_ms": event[16],
                            "compilation_duration_ms": event[17],
                            "total_task_duration_ms": event[18],
                            "result_fetch_duration_ms": event[19],
                            "start_time": event[20].isoformat() if event[20] else None,
                            "end_time": event[21].isoformat() if event[21] else None,
                            "update_time": event[22].isoformat() if event[22] else None,
                            "read_partitions": event[23],
                            "pruned_files": event[24],
                            "read_files": event[25],
                            "read_rows": event[26],
                            "produced_rows": event[27],
                            "read_bytes": event[28],
                            "read_io_cache_percent": event[29],
                            "from_result_cache": event[30],
                            "spilled_local_bytes": event[31],
                            "written_bytes": event[32],
                            "shuffle_read_bytes": event[33],
                            "query_source": event[34],
                            "executed_as": event[35],
                            "executed_as_user_id": event[36],
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("queries", event_data)
                    if not success:
                        print(f"Failed to send query event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[20] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} query events")

        except Exception as e:
            print(f"Error processing query events: {str(e)}")
            raise

    def process_audit_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process audit log events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "audit_events"
        table_name = "system.access.audit"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                version,
                event_time,
                event_date,
                workspace_id,
                source_ip_address,
                user_agent,
                session_id,
                user_identity,
                service_name,
                action_name,
                request_id,
                request_params,
                response,
                audit_level,
                account_id,
                event_id,
                identity_metadata
            FROM {table_name}
            WHERE event_time > '{last_checkpoint.isoformat()}'
            AND event_time <= '{current_time.isoformat()}'
            ORDER BY event_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new audit events found")
                    return

                # Process each event
                for event in events:
                    event_data = {
                        "platform": "databricks",
                        "event_type": "audit_events",
                        "event": {
                            "version": event[0],
                            "event_time": event[1].isoformat(),
                            "event_date": event[2].isoformat() if event[2] else None,
                            "workspace_id": event[3],
                            "source_ip_address": event[4],
                            "user_agent": event[5],
                            "session_id": event[6],
                            "user_identity": event[7],
                            "service_name": event[8],
                            "action_name": event[9],
                            "request_id": event[10],
                            "request_params": event[11] if event[11] else {},
                            "response": event[12] if event[12] else {},
                            "audit_level": event[13],
                            "account_id": event[14],
                            "event_id": event[15],
                            "identity_metadata": event[16] if event[16] else {},
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("audit", event_data)
                    if not success:
                        print(f"Failed to send audit event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[1] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} audit events")

        except Exception as e:
            print(f"Error processing audit events: {str(e)}")
            raise

    def process_cluster_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process cluster creation and deletion events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "cluster_events"
        table_name = "system.compute.clusters"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                account_id,
                workspace_id,
                cluster_id,
                cluster_name,
                owned_by,
                create_time,
                delete_time,
                driver_node_type,
                worker_node_type,
                worker_count,
                min_autoscale_workers,
                max_autoscale_workers,
                auto_termination_minutes,
                enable_elastic_disk,
                tags,
                cluster_source,
                init_scripts,
                azure_attributes,
                driver_instance_pool_id,
                worker_instance_pool_id,
                dbr_version,
                change_time
            FROM {table_name}
            WHERE change_time > '{last_checkpoint.isoformat()}'
            AND change_time <= '{current_time.isoformat()}'
            ORDER BY change_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new cluster events found")
                    return

                # Process each event
                for event in events:
                    # Determine event type based on create/delete times
                    event_type = (
                        "CLUSTER_CREATED"
                        if event[5] == event[21]
                        else "CLUSTER_DELETED"
                    )

                    event_data = {
                        "platform": "databricks",
                        "event_type": "cluster_events",
                        "event": {
                            "account_id": event[0],
                            "workspace_id": event[1],
                            "cluster_id": event[2],
                            "cluster_name": event[3],
                            "owned_by": event[4],
                            "create_time": event[5].isoformat() if event[5] else None,
                            "delete_time": event[6].isoformat() if event[6] else None,
                            "driver_node_type": event[7],
                            "worker_node_type": event[8],
                            "worker_count": event[9],
                            "min_autoscale_workers": event[10],
                            "max_autoscale_workers": event[11],
                            "auto_termination_minutes": event[12],
                            "enable_elastic_disk": event[13],
                            "tags": self._convert_tags_to_dict(event[14]),
                            "cluster_source": event[15],
                            "init_scripts": event[16] if event[16] else [],
                            "azure_attributes": event[17] if event[17] else {},
                            "driver_instance_pool_id": event[18],
                            "worker_instance_pool_id": event[19],
                            "dbr_version": event[20],
                            "change_time": event[21].isoformat(),
                            "event_type": event_type,
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("clusters", event_data)
                    if not success:
                        print(f"Failed to send cluster event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[21] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} cluster events")

        except Exception as e:
            print(f"Error processing cluster events: {str(e)}")
            raise

    def process_job_task_events(self, reset_checkpoint: bool = False) -> None:
        """
        Process job task events from the system table.

        Gets events between the last checkpoint and current time, formats them,
        and sends them to monitoring system. Updates checkpoint if successful.

        Args:
            reset_checkpoint (bool): If True, resets the checkpoint to 24 hours ago
                                   before processing events. Useful for testing.
        """
        monitor_type = "job_task_events"
        table_name = "system.lakeflow.job_task_run_timeline"

        try:
            current_time = datetime.utcnow()

            if reset_checkpoint:
                # Force checkpoint to 24 hours ago
                last_checkpoint = current_time - timedelta(days=1)
                print(f"Resetting checkpoint to: {last_checkpoint}")
                self.update_checkpoint(monitor_type, table_name, last_checkpoint)
            else:
                # Get last checkpoint normally
                last_checkpoint = self.get_last_checkpoint(monitor_type, table_name)

            # Query for new events
            query = f"""
            SELECT 
                t.account_id,
                t.workspace_id,
                t.job_id,
                t.run_id,
                t.job_run_id,
                t.parent_run_id,
                t.task_key,
                t.compute_ids,
                t.result_state,
                t.termination_code,
                t.period_start_time,
                t.period_end_time,
                j.tags,
                j.name as job_name,
                j.description as job_description,
                jt.depends_on_keys as task_dependencies
            FROM {table_name} t
            LEFT JOIN system.lakeflow.jobs j
                ON t.job_id = j.job_id
                AND t.workspace_id = j.workspace_id
                AND t.account_id = j.account_id
            LEFT JOIN system.lakeflow.job_tasks jt
                ON t.job_id = jt.job_id
                AND t.workspace_id = jt.workspace_id
                AND t.account_id = jt.account_id
                AND t.task_key = jt.task_key
            WHERE t.period_start_time > '{last_checkpoint.isoformat()}'
            AND t.period_start_time <= '{current_time.isoformat()}'
            ORDER BY t.period_start_time ASC
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                events = cursor.fetchall()

                if not events:
                    print("No new job task events found")
                    return

                # Process each event
                for event in events:
                    event_data = {
                        "platform": "databricks",
                        "event_type": "job_task_events",
                        "event": {
                            "account_id": event[0],
                            "workspace_id": event[1],
                            "job_id": event[2],
                            "run_id": event[3],
                            "job_run_id": event[4],
                            "parent_run_id": event[5],
                            "task_key": event[6],
                            "compute_ids": str(event[7]) if event[7] else "",
                            "result_state": event[8],
                            "termination_code": event[9],
                            "period_start_time": event[10].isoformat(),
                            "period_end_time": (
                                event[11].isoformat() if event[11] else None
                            ),
                            "tags": self._convert_tags_to_dict(event[12]),
                            "job_name": event[13],
                            "job_description": event[14],
                            "task_dependencies": event[15] if event[15] else [],
                        },
                    }

                    # Send to monitoring system
                    success = self.send_to_splunk("job_tasks", event_data)
                    if not success:
                        print(f"Failed to send job task event: {event_data}")
                        return

                # Update checkpoint after successful processing
                max_event_time = max(event[10] for event in events)
                self.update_checkpoint(monitor_type, table_name, max_event_time)
                print(f"Successfully processed {len(events)} job task events")

        except Exception as e:
            print(f"Error processing job task events: {str(e)}")
            raise


import os


def get_env_var(var_name: str, default: Optional[str] = None) -> str:
    """Get environment variable with error handling."""
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set")
    return value


def main():
    """
    Main entry point for the Databricks status monitor.

    Creates a DatabricksStatusMonitor instance and processes all regions,
    handling any errors that occur during execution.
    """
    # Get connection details from environment variables
    server_hostname = get_env_var("DATABRICKS_HOST")
    http_path = get_env_var("DATABRICKS_HTTP_PATH")
    access_token = get_env_var("DATABRICKS_TOKEN")

    try:
        monitor = DatabricksStatusMonitor(server_hostname, http_path, access_token)

        # Initialize checkpoint table
        monitor.ensure_checkpoint_table()

        # Get reset flag from command line
        import sys

        reset_checkpoint = "--reset" in sys.argv

        # Process all event types
        monitor.process_warehouse_events(True)
        monitor.process_job_events(reset_checkpoint)
        monitor.process_job_task_events(reset_checkpoint)
        monitor.process_query_events(reset_checkpoint)
        monitor.process_cluster_events(reset_checkpoint)
        monitor.process_audit_events(reset_checkpoint)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if monitor and monitor.connection:
            monitor.connection.close()


if __name__ == "__main__":
    main()
