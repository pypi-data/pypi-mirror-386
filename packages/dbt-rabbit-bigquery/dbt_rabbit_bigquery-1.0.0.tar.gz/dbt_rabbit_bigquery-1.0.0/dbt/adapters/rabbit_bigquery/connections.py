import logging
from contextlib import contextmanager
from typing import Optional

from dbt.adapters.bigquery.connections import BigQueryConnectionManager
from dbt.adapters.rabbit_bigquery.credentials import RabbitBigQueryCredentials
from dbt.contracts.connection import AdapterResponse

logger = logging.getLogger(__name__)


class RabbitBigQueryConnectionManager(BigQueryConnectionManager):
    """
    Extended BigQuery connection manager that handles Rabbit-optimized
    job configurations.
    """
    
    TYPE = "rabbit-bigquery"
    
    @contextmanager
    def exception_handler(self, sql: str):
        """
        Handle exceptions during query execution, providing context
        about whether optimization was attempted.
        """
        try:
            yield
        except Exception as e:
            logger.debug(f"Error executing query: {sql}")
            logger.debug(f"Exception: {str(e)}")
            raise
    
    @classmethod
    def open(cls, connection):
        """
        Open a BigQuery connection with Rabbit optimization enabled.
        Validates Rabbit configuration if provided.
        """
        connection = super().open(connection)
        
        # Validate Rabbit configuration
        creds = connection.credentials
        if isinstance(creds, RabbitBigQueryCredentials) and creds.rabbit_enabled:
            if creds.rabbit_api_key:
                logger.info("Rabbit BigQuery Optimizer: Enabled")
                logger.debug(
                    f"Rabbit BigQuery Optimizer: Using pricing mode '{creds.rabbit_default_pricing_mode}' "
                    f"with {len(creds.rabbit_reservation_ids)} reservation(s)"
                )
            else:
                logger.warning(
                    "Rabbit BigQuery Optimizer: API key not provided. "
                    "Optimization will be skipped. Set 'rabbit_api_key' in your profiles.yml"
                )
        
        return connection

