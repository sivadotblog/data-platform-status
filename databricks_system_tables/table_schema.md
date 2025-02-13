## Cluster table schema

The cluster table is a slow-changing dimension table that contains the full history of compute configurations over time for all-purpose and jobs compute.

**Table path**: `system.compute.clusters`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this cluster was created. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the workspace where this cluster was created. | `1234567890123456` |
| `cluster_id` | string | ID of the cluster for which this record is associated. | `0000-123456-crmpt124` |
| `cluster_name` | string | User defined name for the cluster. | `My cluster` |
| `owned_by` | string | Username of the cluster owner. Defaults to the cluster creator, but can be changed through the [Clusters API](https://docs.databricks.com/api/azure/workspace/clusters/changeowner). | `sample_user@email.com` |
| `create_time` | timestamp | Timestamp of the change to this compute definition. | `2023-01-09 11:00:00.000` |
| `delete_time` | timestamp | Timestamp of when the cluster was deleted. The value is `null` if the cluster is not deleted. | `2023-01-09 11:00:00.000` |
| `driver_node_type` | string | Driver node type name. This matches the instance type name from the cloud provider. | `Standard_D16s_v3` |
| `worker_node_type` | string | Worker node type name. This matches the instance type name from the cloud provider. | `Standard_D16s_v3` |
| `worker_count` | bigint | Number of workers. Defined for fixed-size clusters only. | `4` |
| `min_autoscale_workers` | bigint | The set minimum number of workers. This field is valid only for autoscaling clusters. | `1` |
| `max_autoscale_workers` | bigint | The set maximum number of workers. This field is valid only for autoscaling clusters. | `1` |
| `auto_termination_minutes` | bigint | The configured autotermination duration. | `120` |
| `enable_elastic_disk` | boolean | Autoscaling disk enablement status. | `true` |
| `tags` | map | User-defined tags for the cluster (does not include default tags). | `{"ResourceClass":"SingleNode"}` |
| `cluster_source` | string | Indicates the creator for the cluster: `UI`, `API`, `JOB`, etc. | `UI` |
| `init_scripts` | array | Set of paths for init scripts. | `"/Users/example@email.com`  <br>`/files/scripts/install-python-pacakges.sh"` |
| `aws_attributes` | struct | AWS specific settings. | `null` |
| `azure_attributes` | struct | Azure specific settings. | `{`  <br>`"first_on_demand": "0",`  <br>`"availability": "ON_DEMAND_AZURE",`  <br>`"spot_bid_max_price": "—1"`  <br>`}` |
| `gcp_attributes` | struct | GCP specific settings. This field will be empty. | `null` |
| `driver_instance_pool_id` | string | Instance pool ID if the driver is configured on top of an instance pool. | `1107-555555-crhod16-pool-DIdnjazB` |
| `worker_instance_pool_id` | string | Instance Pool ID if the worker is configured on top of an instance pool. | `1107-555555-crhod16-pool-DIdnjazB` |
| `dbr_version` | string | The Databricks Runtime of the cluster. | `14.x-snapshot-scala2.12` |
| `change_time` | timestamp | Timestamp of change to the compute definition. | `2023-01-09 11:00:00.000` |
| `change_date` | date | Change date. Used for retention. | `2023-01-09` |

## Node types table schema

The node type table captures the currently available node types with their basic hardware information.

**Table path**: `system.compute.node_types`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this cluster was created. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `node_type` | string | Unique identifier for node type. | `Standard_D16s_v3` |
| `core_count` | double | Number of vCPUs for the instance. | `48.0` |
| `memory_mb` | long | Total memory for the instance. | `393216` |
| `gpu_count` | long | Number of GPUs for the instance. | `0` |

## Node timeline table schema

The node timeline table captures node-level resource utilization data at minute granularity. Each record contains data for a given minute of time per instance.

**Table path**: `system.compute.node_timeline`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this compute resource is running. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the workspace where this compute resource is running. | `1234567890123456` |
| `cluster_id` | string | ID of the compute resource. | `0000-123456-crmpt124` |
| `instance_id` | string | ID for the specific instance. | `i-1234a6c12a2681234` |
| `start_time` | timestamp | Start time for the record in UTC. | `2024-07-16T12:00:00Z` |
| `end_time` | timestamp | End time for the record in UTC. | `2024-07-16T13:00:00Z` |
| `driver` | boolean | Whether the instance is a driver or worker node. | `true` |
| `cpu_user_percent` | double | Percentage of time the CPU spent in userland. | `34.76163817234407` |
| `cpu_system_percent` | double | Percentage of time the CPU spent in the kernel. | `1.0895310279488264` |
| `cpu_wait_percent` | double | Percentage of time the CPU spent waiting for I/O. | `0.03445157400629276` |
| `mem_used_percent` | double | Percentage of the compute’s memory that was used during the time period (including memory used by background processes running on the compute). | `45.34858216779041` |
| `mem_swap_percent` | double | Percentage of memory usage attributed to memory swap. | `0.014648443087939` |
| `network_sent_bytes` | bigint | The number of bytes sent out in network traffic. | `517376` |
| `network_received_bytes` | bigint | The number of received bytes from network traffic. | `179234` |
| `disk_free_bytes_per_mount_point` | map | The disk utilization grouped by mount point. This is ephemeral storage provisioned only while the compute is running. | `{"/var/lib/lxc":123455551234,"/":123456789123,"/local_disk0":123412341234}` |
| `node_type` | string | The name of the node type. This will match the instance type name from the cloud provider. | `Standard_D16s_v3` |

## Audit log system table schema

The audit log system table uses the following schema:

**Table path**: `system.access.audit`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `version` | string | Audit log schema version | `2.0` |
| `event_time` | timestamp | Timestamp of the event. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-01T01:01:01.123+00:00` |
| `event_date` | date | Calendar date the action took place | `2023-01-01` |
| `workspace_id` | long | ID of the workspace | `1234567890123456` |
| `source_ip_address` | string | IP address where the request originated | `10.30.0.242` |
| `user_agent` | string | Origination of request | `Apache-HttpClient/4.5.13 (Java/1.8.0_345)` |
| `session_id` | string | ID of the session where the request came from | `123456789` |
| `user_identity` | string | Identity of user initiating request | `{"email": "user@domain.com", "subjectName": null}` |
| `service_name` | string | Service name initiating request | `unityCatalog` |
| `action_name` | string | Category of the event captured in audit log | `getTable` |
| `request_id` | string | ID of request | `ServiceMain-4529754264` |
| `request_params` | map | Map of key values containing all the request parameters. Depends on request type | `[["full_name_arg", "user.chat.messages"], ["workspace_id", "123456789"], ["metastore_id", "123456789"]]` |
| `response` | struct | Struct of response return values | `{"statusCode": 200, "errorMessage": null, "result": null}` |
| `audit_level` | string | Workspace or account level event | `ACCOUNT_LEVEL` |
| `account_id` | string | ID of the account | `23e22ba4-87b9-4cc2-9770-d10b894bxx` |
| `event_id` | string | ID of the event | `34ac703c772f3549dcc8671f654950f0` |
| `identity_metadata` | struct | Identities involved in the action, including `run_by` and `run_as`. See [Auditing group dedicated compute activty](../../compute/group-access#audit-group). | `{run_by: example@email.com; run_as: example@email.com;` |

## Billable usage table schema

The billable usage system table uses the following schema:

**Table path**: `system.billing.usage`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `record_id` | string | Unique ID for this usage record | `11e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `account_id` | string | ID of the account this report was generated for | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the Workspace this usage was associated with | `1234567890123456` |
| `sku_name` | string | Name of the SKU | `STANDARD_ALL_PURPOSE_COMPUTE` |
| `cloud` | string | Cloud this usage is relevant for. Possible values are `AWS`, `AZURE`, and `GCP`. | `AWS`, `AZURE`, or `GCP` |
| `usage_start_time` | timestamp | The start time relevant to this usage record. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-09 10:00:00.000+00:00` |
| `usage_end_time` | timestamp | The end time relevant to this usage record. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-09 11:00:00.000+00:00` |
| `usage_date` | date | Date of the usage record, this field can be used for faster aggregation by date | `2023-01-01` |
| `custom_tags` | map | Tags applied to this usage. Includes compute resource tags, jobs tags, workspace custom tags, and budget policy tags. | `{ “env”: “production” }` |
| `usage_unit` | string | Unit this usage is measured in. Possible values include DBUs. | `DBU` |
| `usage_quantity` | decimal | Number of units consumed for this record. | `259.2958` |
| `usage_metadata` | struct | System-provided metadata about the usage, including IDs for compute resources and jobs (if applicable). See [Usage metadata reference](#usage-metadata). | `{cluster_id: null; instance_pool_id: null; notebook_id: null; job_id: null; node_type: null}` |
| `identity_metadata` | struct | System-provided metadata about the identities involved in the usage. See [Identity metadata reference](#identity-metadata). | `{"run_as": example@email.com,"created_by":null}` |
| `record_type` | string | Whether the record is original, a retraction, or a restatement. The value is `ORIGINAL` unless the record is related to a correction. See [Record type reference](#record-type). | `ORIGINAL` |
| `ingestion_date` | date | Date the record was ingested into the `usage` table. | `2024-01-01` |
| `billing_origin_product` | string | The product that originated the usage. Some products can be billed as different SKUs. For possible values, see [Billing origin product reference](#product). | `JOBS` |
| `product_features` | struct | Details about the specific product features used. | For possible values, see [Product features](#features). |
| `usage_type` | string | The type of usage attributed to the product or workload for billing purposes. Possible values are `COMPUTE_TIME`, `STORAGE_SPACE`, `NETWORK_BYTES`, `API_OPERATION`, `TOKEN`, or `GPU_TIME`. | `STORAGE_SPACE` |

## Pricing table schema

The pricing system table uses the following schema:

**Table path**: `system.billing.list_prices`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `price_start_time` | timestamp | The time this price became effective in UTC | `2023-01-01T09:59:59.999Z` |
| `price_end_time` | timestamp | The time this price stopped being effective in UTC | `2023-01-01T09:59:59.999Z` |
| `account_id` | string | ID of the account this report was generated for | `1234567890123456` |
| `sku_name` | string | Name of the SKU | `STANDARD_ALL_PURPOSE_COMPUTE` |
| `cloud` | string | Name of the Cloud this price is applicable to. Possible values are `AWS`, `AZURE`, and `GCP`. | `AWS`, `AZURE`, or `GCP` |
| `currency_code` | string | The currency this price is expressed in | `USD` |
| `usage_unit` | string | The unit of measurement that is monetized. | `DBU` |
| `pricing` | struct | A structured data field that includes pricing info at the published list price rate. The key `default` will always return a single price that can be used for simple long-term estimates. The key `promotional` represents a temporary promotional price that all customers get which could be used for cost estimation during the temporary period. The key `effective_list` resolves list and promotional price, and contains the effective list price used for calculating the cost. Some pricing models might also include additional keys that provide more detail. | `{ "default": "0.10", "promotional": {"default": "0.07"}, "effective_list": {"default": "0.07"}` |

## Warehouses table schema

**Table path**: `system.compute.warehouses`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `warehouse_id` | string | The ID of the SQL warehouse. | `123456789012345` |
| `workspace_id` | string | The ID of the workspace where the warehouse is deployed. | `123456789012345` |
| `account_id` | string | The ID of the Azure Databricks account. | `7af234db-66d7-4db3-bbf0-956098224879` |
| `warehouse_name` | string | The name of the SQL warehouse. | `My Serverless Warehouse` |
| `warehouse_type` | string | The type of SQL warehouse. Possible values are `CLASSIC`, `PRO`, and `SERVERLESS`. | `SERVERLESS` |
| `warehouse_channel` | string | The channel of the SQL warehouse. Possible values are `CURRENT` and `PREVIEW`. | `CURRENT` |
| `warehouse_size` | string | The cluster size of the SQL warehouse. Possible values are `2X_SMALL`, `X_SMALL`, `SMALL`, `MEDIUM`, `LARGE`, `X_LARGE`, `2X_LARGE`, `3X_LARGE`, and `4X_LARGE`. | `MEDIUM` |
| `min_clusters` | int | The minimum number of clusters permitted. | `1` |
| `max_clusters` | int | The maximum number of clusters permitted. | `5` |
| `auto_stop_minutes` | int | The number of minutes before the SQL warehouse auto-stops due to inactivity. | `35` |
| `tags` | map | Tags for the SQL warehouse. | `{"budget":"research"}` |
| `change_time` | timestamp | Timestamp of change to the SQL warehouse definition. | `2023-07-20T19:13:09.504Z` |
| `delete_time` | timestamp | Timestamp of when the SQL warehouse was deleted. The value is `null` if the SQL warehouse is not deleted. | `2023-07-20T19:13:09.504Z` |

## Warehouse events schema

**Table path**: `system.compute.warehouse_events`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the Azure Databricks account. | `7af234db-66d7-4db3-bbf0-956098224879` |
| `workspace_id` | string | The ID of the workspace where the warehouse is deployed. | `123456789012345` |
| `warehouse_id` |## Cluster table schema

The cluster table is a slow-changing dimension table that contains the full history of compute configurations over time for all-purpose and jobs compute.

**Table path**: `system.compute.clusters`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this cluster was created. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the workspace where this cluster was created. | `1234567890123456` |
| `cluster_id` | string | ID of the cluster for which this record is associated. | `0000-123456-crmpt124` |
| `cluster_name` | string | User defined name for the cluster. | `My cluster` |
| `owned_by` | string | Username of the cluster owner. Defaults to the cluster creator, but can be changed through the [Clusters API](https://docs.databricks.com/api/azure/workspace/clusters/changeowner). | `sample_user@email.com` |
| `create_time` | timestamp | Timestamp of the change to this compute definition. | `2023-01-09 11:00:00.000` |
| `delete_time` | timestamp | Timestamp of when the cluster was deleted. The value is `null` if the cluster is not deleted. | `2023-01-09 11:00:00.000` |
| `driver_node_type` | string | Driver node type name. This matches the instance type name from the cloud provider. | `Standard_D16s_v3` |
| `worker_node_type` | string | Worker node type name. This matches the instance type name from the cloud provider. | `Standard_D16s_v3` |
| `worker_count` | bigint | Number of workers. Defined for fixed-size clusters only. | `4` |
| `min_autoscale_workers` | bigint | The set minimum number of workers. This field is valid only for autoscaling clusters. | `1` |
| `max_autoscale_workers` | bigint | The set maximum number of workers. This field is valid only for autoscaling clusters. | `1` |
| `auto_termination_minutes` | bigint | The configured autotermination duration. | `120` |
| `enable_elastic_disk` | boolean | Autoscaling disk enablement status. | `true` |
| `tags` | map | User-defined tags for the cluster (does not include default tags). | `{"ResourceClass":"SingleNode"}` |
| `cluster_source` | string | Indicates the creator for the cluster: `UI`, `API`, `JOB`, etc. | `UI` |
| `init_scripts` | array | Set of paths for init scripts. | `"/Users/example@email.com`  <br>`/files/scripts/install-python-pacakges.sh"` |
| `aws_attributes` | struct | AWS specific settings. | `null` |
| `azure_attributes` | struct | Azure specific settings. | `{`  <br>`"first_on_demand": "0",`  <br>`"availability": "ON_DEMAND_AZURE",`  <br>`"spot_bid_max_price": "—1"`  <br>`}` |
| `gcp_attributes` | struct | GCP specific settings. This field will be empty. | `null` |
| `driver_instance_pool_id` | string | Instance pool ID if the driver is configured on top of an instance pool. | `1107-555555-crhod16-pool-DIdnjazB` |
| `worker_instance_pool_id` | string | Instance Pool ID if the worker is configured on top of an instance pool. | `1107-555555-crhod16-pool-DIdnjazB` |
| `dbr_version` | string | The Databricks Runtime of the cluster. | `14.x-snapshot-scala2.12` |
| `change_time` | timestamp | Timestamp of change to the compute definition. | `2023-01-09 11:00:00.000` |
| `change_date` | date | Change date. Used for retention. | `2023-01-09` |

## Node types table schema

The node type table captures the currently available node types with their basic hardware information.

**Table path**: `system.compute.node_types`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this cluster was created. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `node_type` | string | Unique identifier for node type. | `Standard_D16s_v3` |
| `core_count` | double | Number of vCPUs for the instance. | `48.0` |
| `memory_mb` | long | Total memory for the instance. | `393216` |
| `gpu_count` | long | Number of GPUs for the instance. | `0` |

## Node timeline table schema

The node timeline table captures node-level resource utilization data at minute granularity. Each record contains data for a given minute of time per instance.

**Table path**: `system.compute.node_timeline`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account where this compute resource is running. | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the workspace where this compute resource is running. | `1234567890123456` |
| `cluster_id` | string | ID of the compute resource. | `0000-123456-crmpt124` |
| `instance_id` | string | ID for the specific instance. | `i-1234a6c12a2681234` |
| `start_time` | timestamp | Start time for the record in UTC. | `2024-07-16T12:00:00Z` |
| `end_time` | timestamp | End time for the record in UTC. | `2024-07-16T13:00:00Z` |
| `driver` | boolean | Whether the instance is a driver or worker node. | `true` |
| `cpu_user_percent` | double | Percentage of time the CPU spent in userland. | `34.76163817234407` |
| `cpu_system_percent` | double | Percentage of time the CPU spent in the kernel. | `1.0895310279488264` |
| `cpu_wait_percent` | double | Percentage of time the CPU spent waiting for I/O. | `0.03445157400629276` |
| `mem_used_percent` | double | Percentage of the compute’s memory that was used during the time period (including memory used by background processes running on the compute). | `45.34858216779041` |
| `mem_swap_percent` | double | Percentage of memory usage attributed to memory swap. | `0.014648443087939` |
| `network_sent_bytes` | bigint | The number of bytes sent out in network traffic. | `517376` |
| `network_received_bytes` | bigint | The number of received bytes from network traffic. | `179234` |
| `disk_free_bytes_per_mount_point` | map | The disk utilization grouped by mount point. This is ephemeral storage provisioned only while the compute is running. | `{"/var/lib/lxc":123455551234,"/":123456789123,"/local_disk0":123412341234}` |
| `node_type` | string | The name of the node type. This will match the instance type name from the cloud provider. | `Standard_D16s_v3` |

## Audit log system table schema

The audit log system table uses the following schema:

**Table path**: `system.access.audit`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `version` | string | Audit log schema version | `2.0` |
| `event_time` | timestamp | Timestamp of the event. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-01T01:01:01.123+00:00` |
| `event_date` | date | Calendar date the action took place | `2023-01-01` |
| `workspace_id` | long | ID of the workspace | `1234567890123456` |
| `source_ip_address` | string | IP address where the request originated | `10.30.0.242` |
| `user_agent` | string | Origination of request | `Apache-HttpClient/4.5.13 (Java/1.8.0_345)` |
| `session_id` | string | ID of the session where the request came from | `123456789` |
| `user_identity` | string | Identity of user initiating request | `{"email": "user@domain.com", "subjectName": null}` |
| `service_name` | string | Service name initiating request | `unityCatalog` |
| `action_name` | string | Category of the event captured in audit log | `getTable` |
| `request_id` | string | ID of request | `ServiceMain-4529754264` |
| `request_params` | map | Map of key values containing all the request parameters. Depends on request type | `[["full_name_arg", "user.chat.messages"], ["workspace_id", "123456789"], ["metastore_id", "123456789"]]` |
| `response` | struct | Struct of response return values | `{"statusCode": 200, "errorMessage": null, "result": null}` |
| `audit_level` | string | Workspace or account level event | `ACCOUNT_LEVEL` |
| `account_id` | string | ID of the account | `23e22ba4-87b9-4cc2-9770-d10b894bxx` |
| `event_id` | string | ID of the event | `34ac703c772f3549dcc8671f654950f0` |
| `identity_metadata` | struct | Identities involved in the action, including `run_by` and `run_as`. See [Auditing group dedicated compute activty](../../compute/group-access#audit-group). | `{run_by: example@email.com; run_as: example@email.com;` |

## Billable usage table schema

The billable usage system table uses the following schema:

**Table path**: `system.billing.usage`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `record_id` | string | Unique ID for this usage record | `11e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `account_id` | string | ID of the account this report was generated for | `23e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | ID of the Workspace this usage was associated with | `1234567890123456` |
| `sku_name` | string | Name of the SKU | `STANDARD_ALL_PURPOSE_COMPUTE` |
| `cloud` | string | Cloud this usage is relevant for. Possible values are `AWS`, `AZURE`, and `GCP`. | `AWS`, `AZURE`, or `GCP` |
| `usage_start_time` | timestamp | The start time relevant to this usage record. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-09 10:00:00.000+00:00` |
| `usage_end_time` | timestamp | The end time relevant to this usage record. Timezone information is recorded at the end of the value with `+00:00` representing UTC timezone. | `2023-01-09 11:00:00.000+00:00` |
| `usage_date` | date | Date of the usage record, this field can be used for faster aggregation by date | `2023-01-01` |
| `custom_tags` | map | Tags applied to this usage. Includes compute resource tags, jobs tags, workspace custom tags, and budget policy tags. | `{ “env”: “production” }` |
| `usage_unit` | string | Unit this usage is measured in. Possible values include DBUs. | `DBU` |
| `usage_quantity` | decimal | Number of units consumed for this record. | `259.2958` |
| `usage_metadata` | struct | System-provided metadata about the usage, including IDs for compute resources and jobs (if applicable). See [Usage metadata reference](#usage-metadata). | `{cluster_id: null; instance_pool_id: null; notebook_id: null; job_id: null; node_type: null}` |
| `identity_metadata` | struct | System-provided metadata about the identities involved in the usage. See [Identity metadata reference](#identity-metadata). | `{"run_as": example@email.com,"created_by":null}` |
| `record_type` | string | Whether the record is original, a retraction, or a restatement. The value is `ORIGINAL` unless the record is related to a correction. See [Record type reference](#record-type). | `ORIGINAL` |
| `ingestion_date` | date | Date the record was ingested into the `usage` table. | `2024-01-01` |
| `billing_origin_product` | string | The product that originated the usage. Some products can be billed as different SKUs. For possible values, see [Billing origin product reference](#product). | `JOBS` |
| `product_features` | struct | Details about the specific product features used. | For possible values, see [Product features](#features). |
| `usage_type` | string | The type of usage attributed to the product or workload for billing purposes. Possible values are `COMPUTE_TIME`, `STORAGE_SPACE`, `NETWORK_BYTES`, `API_OPERATION`, `TOKEN`, or `GPU_TIME`. | `STORAGE_SPACE` |

## Pricing table schema

The pricing system table uses the following schema:

**Table path**: `system.billing.list_prices`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `price_start_time` | timestamp | The time this price became effective in UTC | `2023-01-01T09:59:59.999Z` |
| `price_end_time` | timestamp | The time this price stopped being effective in UTC | `2023-01-01T09:59:59.999Z` |
| `account_id` | string | ID of the account this report was generated for | `1234567890123456` |
| `sku_name` | string | Name of the SKU | `STANDARD_ALL_PURPOSE_COMPUTE` |
| `cloud` | string | Name of the Cloud this price is applicable to. Possible values are `AWS`, `AZURE`, and `GCP`. | `AWS`, `AZURE`, or `GCP` |
| `currency_code` | string | The currency this price is expressed in | `USD` |
| `usage_unit` | string | The unit of measurement that is monetized. | `DBU` |
| `pricing` | struct | A structured data field that includes pricing info at the published list price rate. The key `default` will always return a single price that can be used for simple long-term estimates. The key `promotional` represents a temporary promotional price that all customers get which could be used for cost estimation during the temporary period. The key `effective_list` resolves list and promotional price, and contains the effective list price used for calculating the cost. Some pricing models might also include additional keys that provide more detail. | `{ "default": "0.10", "promotional": {"default": "0.07"}, "effective_list": {"default": "0.07"}` |

## Warehouses table schema

**Table path**: `system.compute.warehouses`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `warehouse_id` | string | The ID of the SQL warehouse. | `123456789012345` |
| `workspace_id` | string | The ID of the workspace where the warehouse is deployed. | `123456789012345` |
| `account_id` | string | The ID of the Azure Databricks account. | `7af234db-66d7-4db3-bbf0-956098224879` |
| `warehouse_name` | string | The name of the SQL warehouse. | `My Serverless Warehouse` |
| `warehouse_type` | string | The type of SQL warehouse. Possible values are `CLASSIC`, `PRO`, and `SERVERLESS`. | `SERVERLESS` |
| `warehouse_channel` | string | The channel of the SQL warehouse. Possible values are `CURRENT` and `PREVIEW`. | `CURRENT` |
| `warehouse_size` | string | The cluster size of the SQL warehouse. Possible values are `2X_SMALL`, `X_SMALL`, `SMALL`, `MEDIUM`, `LARGE`, `X_LARGE`, `2X_LARGE`, `3X_LARGE`, and `4X_LARGE`. | `MEDIUM` |
| `min_clusters` | int | The minimum number of clusters permitted. | `1` |
| `max_clusters` | int | The maximum number of clusters permitted. | `5` |
| `auto_stop_minutes` | int | The number of minutes before the SQL warehouse auto-stops due to inactivity. | `35` |
| `tags` | map | Tags for the SQL warehouse. | `{"budget":"research"}` |
| `change_time` | timestamp | Timestamp of change to the SQL warehouse definition. | `2023-07-20T19:13:09.504Z` |
| `delete_time` | timestamp | Timestamp of when the SQL warehouse was deleted. The value is `null` if the SQL warehouse is not deleted. | `2023-07-20T19:13:09.504Z` |

## Warehouses table schema

**Table path**: `system.compute.warehouses`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `warehouse_id` | string | The ID of the SQL warehouse. | `123456789012345` |
| `workspace_id` | string | The ID of the workspace where the warehouse is deployed. | `123456789012345` |
| `account_id` | string | The ID of the Azure Databricks account. | `7af234db-66d7-4db3-bbf0-956098224879` |
| `warehouse_name` | string | The name of the SQL warehouse. | `My Serverless Warehouse` |
| `warehouse_type` | string | The type of SQL warehouse. Possible values are `CLASSIC`, `PRO`, and `SERVERLESS`. | `SERVERLESS` |
| `warehouse_channel` | string | The channel of the SQL warehouse. Possible values are `CURRENT` and `PREVIEW`. | `CURRENT` |
| `warehouse_size` | string | The cluster size of the SQL warehouse. Possible values are `2X_SMALL`, `X_SMALL`, `SMALL`, `MEDIUM`, `LARGE`, `X_LARGE`, `2X_LARGE`, `3X_LARGE`, and `4X_LARGE`. | `MEDIUM` |
| `min_clusters` | int | The minimum number of clusters permitted. | `1` |
| `max_clusters` | int | The maximum number of clusters permitted. | `5` |
| `auto_stop_minutes` | int | The number of minutes before the SQL warehouse auto-stops due to inactivity. | `35` |
| `tags` | map | Tags for the SQL warehouse. | `{"budget":"research"}` |
| `change_time` | timestamp | Timestamp of change to the SQL warehouse definition. | `2023-07-20T19:13:09.504Z` |
| `delete_time` | timestamp | Timestamp of when the SQL warehouse was deleted. The value is `null` if the SQL warehouse is not deleted. | `2023-07-20T19:13:09.504Z` |

## Warehouse events schema

**Table path**: `system.compute.warehouse_events`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the Azure Databricks account. | `7af234db-66d7-4db3-bbf0-956098224879` |
| `workspace_id` | string | The ID of the workspace where the warehouse is deployed. | `123456789012345` |
| `warehouse_id` | string | The ID of SQL warehouse the event is related to. | `123456789012345` |
| `event_type` | string | The type of warehouse event. Possible values are `SCALED_UP`, `SCALED_DOWN`, `STOPPING`, `RUNNING`, `STARTING`, and `STOPPED`. | `SCALED_UP` |
| `cluster_count` | integer | The number of clusters that are actively running. | `2` |
| `event_time` | timestamp | Timestamp of when the event took place in UTC. | `2023-07-20T19:13:09.504Z` |

## Jobs table schema

**Table path**: `system.lakeflow.jobs`

| Column name | Data type | Description | Notes |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the account this job belongs to |     |
| `workspace_id` | string | The ID of the workspace this job belongs to |     |
| `job_id` | string | The ID of the job | Only unique within a single workspace |
| `name` | string | The user-supplied name of the job |     |
| `description` | string | The user-supplied description of the job | This field is empty if you have [customer-managed keys](https://docs.databricks.com/en/security/keys/customer-managed-keys.html) configured.  <br>  <br>Not populated for rows emitted before late August 2024 |
| `creator_id` | string | The ID of the principal who created the job |     |
| `tags` | string | The user-supplied custom tags associated with this job |     |
| `change_time` | timestamp | The time when the job was last modified | Timezone recorded as +00:00 (UTC) |
| `delete_time` | timestamp | The time when the job was deleted by the user | Timezone recorded as +00:00 (UTC) |
| `run_as` | string | The ID of the user or service principal whose permissions are used for the job run |     |

## Job task table schema

**Table path**: `system.lakeflow.job_tasks`

| Column name | Data type | Description | Notes |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the account this job belongs to |     |
| `workspace_id` | string | The ID of the workspace this job belongs to |     |
| `job_id` | string | The ID of the job | Only unique within a single workspace |
| `task_key` | string | The reference key for a task in a job | Only unique within a single job |
| `depends_on_keys` | array | The task keys of all upstream dependencies of this task |     |
| `change_time` | timestamp | The time when the task was last modified | Timezone recorded as +00:00 (UTC) |
| `delete_time` | timestamp | The time when a task was deleted by the user | Timezone recorded as +00:00 (UTC) |

## Job run timeline schema

**Table path**: `system.lakeflow.job_run_timeline`

| Column name | Data type | Description | Notes |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the account this job belongs to |     |
| `workspace_id` | string | The ID of the workspace this job belongs to |     |
| `job_id` | string | The ID of the job | This key is only unique within a single workspace |
| `run_id` | string | The ID of the job run |     |
| `period_start_time` | timestamp | The start time for the run or for the time period | Timezone information is recorded at the end of the value with `+00:00` representing UTC |
| `period_end_time` | timestamp | The end time for the run or for the time period | Timezone information is recorded at the end of the value with `+00:00` representing UTC |
| `trigger_type` | string | The type of trigger that can fire a run | For possible values, see [Trigger type values](#trigger) |
| `run_type` | string | The type of job run | For possible values, see [Run type values](#run-type) |
| `run_name` | string | The user-supplied run name associated with this job run |     |
| `compute_ids` | array | Array containing the job compute IDs for the parent job run | Use for identifying job cluster used by `WORKFLOW_RUN` run types. For other compute information, refer to the `job_task_run_timeline` table.  <br>  <br>Not populated for rows emitted before late August 2024 |
| `result_state` | string | The outcome of the job run | For possible values, see [Result state values](#result) |
| `termination_code` | string | The termination code of the job run | For possible values, see [Termination code values](#termination).  <br>  <br>Not populated for rows emitted before late August 2024 |
| `job_parameters` | map | The job-level parameters used in the job run | The deprecated [notebook\_params](https://docs.databricks.com/api/azure/workspace/jobs/runnow) settings are not included in this field.  <br>  <br>Not populated for rows emitted before late August 2024 |

## Job task run timeline schema

**Table path**: `system.lakeflow.job_task_run_timeline`

| Column name | Data type | Description | Notes |
| --- | --- | --- | --- |
| `account_id` | string | The ID of the account this job belongs to |     |
| `workspace_id` | string | The ID of the workspace this job belongs to |     |
| `job_id` | string | The ID of the job | Only unique within a single workspace |
| `run_id` | string | The ID of the task run |     |
| `job_run_id` | string | The ID of the job run | Not populated for rows emitted before late August 2024 |
| `parent_run_id` | string | The ID of the parent run | Not populated for rows emitted before late August 2024 |
| `period_start_time` | timestamp | The start time for the task or for the time period | Timezone information is recorded at the end of the value with `+00:00` representing UTC |
| `period_end_time` | timestamp | The end time for the task or for the time period | Timezone information is recorded at the end of the value with `+00:00` representing UTC |
| `task_key` | string | The reference key for a task in a job | This key is only unique within a single job |
| `compute_ids` | array | The compute\_ids array contains IDs of job clusters, interactive clusters, and SQL warehouses used by the job task |     |
| `result_state` | string | The outcome of the job task run | For possible values, see [Result state values](#result) |
| `termination_code` | string | The termination code of the task run | For possible values, see [Termination code values](#termination).  <br>  <br>Not populated for rows emitted before late August 2024 |

## Query history schema

**Table path**: `system.query.history`

| Column name | Data type | Description | Example |
| --- | --- | --- | --- |
| `account_id` | string | ID of the account. | `11e22ba4-87b9-4cc2-9770-d10b894b7118` |
| `workspace_id` | string | The ID of the workspace where the query was run. | `1234567890123456` |
| `statement_id` | string | The ID that uniquely identifies the execution of the statement. You can use this ID to find the statement execution in the **Query History** UI. | `7a99b43c-b46c-432b-b0a7-814217701909` |
| `session_id` | string | The Spark session ID. | `01234567-cr06-a2mp-t0nd-a14ecfb5a9c2` |
| `execution_status` | string | The statement termination state. Possible values are: `FINISHED`, `FAILED`, `CANCELED` | `FINISHED` |
| `compute` | struct | A struct that represents the type of compute resource used to run the statement and the ID of the resource where applicable. The `type` value will be either `WAREHOUSE` or `SERVERLESS_COMPUTE`. | `{ type: WAREHOUSE, cluster_id: NULL, warehouse_id: ec58ee3772e8d305 }` |
| `executed_by_user_id` | string | The ID of the user who ran the statement. | `2967555311742259` |
| `executed_by` | string | The email address or username of the user who ran the statement. | `example@databricks.com` |
| `statement_text` | string | Text of the SQL statement. If you have configured customer-managed keys, `statement_text` is empty. Due to storage limitations, longer statement text values are compressed. Even with compression, you may reach a character limit. | `SELECT 1` |
| `statement_type` | string | The statement type. For example: `ALTER`, `COPY`, `INSERT`. | `SELECT` |
| `error_message` | string | Message describing the error condition. If you have configured customer-managed keys, `error_message` is empty. | `[INSUFFICIENT_PERMISSIONS] Insufficient privileges: User does not have permission SELECT on table 'default.nyctaxi_trips'.` |
| `client_application` | string | Client application that ran the statement. For example: Databricks SQL Editor, Tableau, Power BI. This field is derived from information provided by client applications. While values are expected to remain static over time, this cannot be guaranteed. | `Databricks SQL Editor` |
| `client_driver` | string | The connector used to connect to Azure Databricks to run the statement. For example: Databricks SQL Driver for Go, Databricks ODBC Driver, Databricks JDBC Driver. | `Databricks JDBC Driver` |
| `total_duration_ms` | bigint | Total execution time of the statement in milliseconds (excluding result fetch time). | `1` |
| `waiting_for_compute_duration_ms` | bigint | Time spent waiting for compute resources to be provisioned in milliseconds. | `1` |
| `waiting_at_capacity_duration_ms` | bigint | Time spent waiting in queue for available compute capacity in milliseconds. | `1` |
| `execution_duration_ms` | bigint | Time spent executing the statement in milliseconds. | `1` |
| `compilation_duration_ms` | bigint | Time spent loading metadata and optimizing the statement in milliseconds. | `1` |
| `total_task_duration_ms` | bigint | The sum of all task durations in milliseconds. This time represents the combined time it took to run the query across all cores of all nodes. It can be significantly longer than the wall-clock duration if multiple tasks are executed in parallel. It can be shorter than the wall-clock duration if tasks wait for available nodes. | `1` |
| `result_fetch_duration_ms` | bigint | Time spent, in milliseconds, fetching the statement results after the execution finished. | `1` |
| `start_time` | timestamp | The time when Databricks received the request. Timezone information is recorded at the end of the value with `+00:00` representing UTC. | `2022-12-05T00:00:00.000+0000` |
| `end_time` | timestamp | The time the statement execution ended, excluding result fetch time. Timezone information is recorded at the end of the value with `+00:00` representing UTC. | `2022-12-05T00:00:00.000+00:00` |
| `update_time` | timestamp | The time the statement last received a progress update. Timezone information is recorded at the end of the value with `+00:00` representing UTC. | `2022-12-05T00:00:00.000+00:00` |
| `read_partitions` | bigint | The number of partitions read after pruning. | `1` |
| `pruned_files` | bigint | The number of pruned files. | `1` |
| `read_files` | bigint | The number of files read after pruning. | `1` |
| `read_rows` | bigint | Total number of rows read by the statement. | `1` |
| `produced_rows` | bigint | Total number of rows returned by the statement. | `1` |
| `read_bytes` | bigint | Total size of data read by the statement in bytes. | `1` |
| `read_io_cache_percent` | int | The percentage of bytes of persistent data read from the IO cache. | `50` |
| `from_result_cache` | boolean | `TRUE` indicates that the statement result was fetched from the cache. | `TRUE` |
| `spilled_local_bytes` | bigint | Size of data, in bytes, temporarily written to disk while executing the statement. | `1` |
| `written_bytes` | bigint | The size in bytes of persistent data written to cloud object storage. | `1` |
| `shuffle_read_bytes` | bigint | The total amount of data in bytes sent over the network. | `1` |
| `query_source` | struct | A struct that contains key-value pairs representing one or more Databricks entities that were involved in the execution of this statement, such as jobs, notebooks, or dashboards. This field only records Databricks entities. | `{ job_info: { job_id: 64361233243479, job_run_id: 887406461287882, job_task_key: “job_task_1”, job_task_run_id: 110378410199121 } }` |
| `executed_as` | string | The name of the user or service principal whose privilege was used to run the statement. | `example@databricks.com` |
| `executed_as_user_id` | string | The ID of the user or service principal whose privilege was used to run the statement. | `2967555311742259` |