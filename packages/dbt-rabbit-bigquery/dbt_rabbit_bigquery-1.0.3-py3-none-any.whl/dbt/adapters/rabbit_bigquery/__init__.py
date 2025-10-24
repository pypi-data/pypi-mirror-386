from dbt.adapters.rabbit_bigquery.connections import RabbitBigQueryConnectionManager
from dbt.adapters.rabbit_bigquery.credentials import RabbitBigQueryCredentials
from dbt.adapters.rabbit_bigquery.impl import RabbitBigQueryAdapter

from dbt.adapters.base import AdapterPlugin
from dbt.include import rabbit_bigquery

Plugin = AdapterPlugin(
    adapter=RabbitBigQueryAdapter,
    credentials=RabbitBigQueryCredentials,
    include_path=rabbit_bigquery.PACKAGE_PATH,
)

__all__ = [
    "RabbitBigQueryAdapter",
    "RabbitBigQueryConnectionManager",
    "RabbitBigQueryCredentials",
    "Plugin",
]

