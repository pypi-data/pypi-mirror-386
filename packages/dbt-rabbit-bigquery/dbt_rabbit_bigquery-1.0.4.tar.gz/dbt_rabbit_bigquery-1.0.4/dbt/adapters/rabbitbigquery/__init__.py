from dbt.adapters.rabbitbigquery.connections import RabbitBigQueryConnectionManager
from dbt.adapters.rabbitbigquery.credentials import RabbitBigQueryCredentials
from dbt.adapters.rabbitbigquery.impl import RabbitBigQueryAdapter
from dbt.adapters.rabbitbigquery.__version__ import version

from dbt.adapters.base import AdapterPlugin
from dbt.include import rabbitbigquery

Plugin = AdapterPlugin(
    adapter=RabbitBigQueryAdapter,
    credentials=RabbitBigQueryCredentials,
    include_path=rabbitbigquery.PACKAGE_PATH,
)

__version__ = version

__all__ = [
    "RabbitBigQueryAdapter",
    "RabbitBigQueryConnectionManager",
    "RabbitBigQueryCredentials",
    "Plugin",
    "__version__",
]
