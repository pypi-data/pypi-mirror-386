from pydantic import BaseModel, Field


class ConnectorPaginationOptions(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=500)

    @property
    def page_params(self) -> tuple[int, int]:
        if self.page is not None:
            return (self.page, self.page_size)
        else:
            raise ValueError(
                "Pagination options must be set to return a page and page size",
            )


# connector constants
S3_CONNECTOR_ENDPOINT_FIELD = "endpoint"
AWS_CONNECTOR_REGION_FIELD = "region"
AWS_CONNECTOR_ACCESS_KEY_ID_FIELD = "access_key_id"
AWS_CONNECTOR_SECRET_ACCESS_KEY_FIELD = "secret_access_key"
AWS_CONNECTOR_ROLE_ARN_FIELD = "role_arn"
AWS_CONNECTOR_EXTERNAL_ID_FIELD = "external_id"
AWS_CONNECTOR_ROLE_DURATION_SECONDS_FIELD = "role_duration_seconds"
BUCKET_BASED_CONNECTOR_BUCKET_FIELD = "bucket"
GOOGLE_CONNECTOR_CREDENTIALS_FIELD = "credentials"
GOOGLE_CONNECTOR_PROJECT_ID_FIELD = "project_id"
GOOGLE_CONNECTOR_LOCATION_FIELD = "location"
SHIELD_CONNECTOR_API_KEY_FIELD = "api_key"
SHIELD_CONNECTOR_ENDPOINT_FIELD = "endpoint"
ODBC_CONNECTOR_HOST_FIELD = "host"
ODBC_CONNECTOR_PORT_FIELD = "port"
ODBC_CONNECTOR_DATABASE_FIELD = "database"
ODBC_CONNECTOR_USERNAME_FIELD = "username"
ODBC_CONNECTOR_PASSWORD_FIELD = "password"
ODBC_CONNECTOR_DRIVER_FIELD = "driver"
ODBC_CONNECTOR_TABLE_NAME_FIELD = "table_name"
ODBC_CONNECTOR_DIALECT_FIELD = "dialect"

# Snowflake connector constants
SNOWFLAKE_CONNECTOR_ACCOUNT_FIELD = "account"
SNOWFLAKE_CONNECTOR_SCHEMA_FIELD = "schema"
SNOWFLAKE_CONNECTOR_WAREHOUSE_FIELD = "warehouse"
SNOWFLAKE_CONNECTOR_ROLE_FIELD = "role"
SNOWFLAKE_CONNECTOR_AUTHENTICATOR_FIELD = "authenticator"
SNOWFLAKE_CONNECTOR_PRIVATE_KEY_FIELD = "private_key"
SNOWFLAKE_CONNECTOR_PRIVATE_KEY_PASSPHRASE_FIELD = "private_key_passphrase"

# dataset (connector type dependent) constants
SHIELD_DATASET_TASK_ID_FIELD = "task_id"
BUCKET_BASED_DATASET_FILE_PREFIX_FIELD = "file_prefix"
BUCKET_BASED_DATASET_FILE_SUFFIX_FIELD = "file_suffix"
BUCKET_BASED_DATASET_FILE_TYPE_FIELD = "data_file_type"
BUCKET_BASED_DATASET_TIMESTAMP_TIME_ZONE_FIELD = "timestamp_time_zone"
BIG_QUERY_DATASET_TABLE_NAME_FIELD = "table_name"
BIG_QUERY_DATASET_DATASET_ID_FIELD = "dataset_id"
