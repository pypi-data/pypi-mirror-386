from dbt.adapters.bigquery import BigQueryAdapter
from dbt.adapters.rabbitbigquery.connections import RabbitBigQueryConnectionManager


class RabbitBigQueryAdapter(BigQueryAdapter):
    """
    Extended BigQuery adapter that optimizes job configurations
    using the Rabbit API before submitting to BigQuery.
    
    The actual optimization logic is implemented in RabbitBigQueryConnectionManager.
    """
    
    ConnectionManager = RabbitBigQueryConnectionManager
