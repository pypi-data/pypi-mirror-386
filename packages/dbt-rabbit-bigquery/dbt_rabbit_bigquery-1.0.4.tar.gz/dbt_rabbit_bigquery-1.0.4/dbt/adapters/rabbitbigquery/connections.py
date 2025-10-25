import json
from dataclasses import asdict
from dbt.adapters.events.logging import AdapterLogger

from dbt.adapters.bigquery.connections import BigQueryConnectionManager
from dbt.adapters.rabbitbigquery.credentials import RabbitBigQueryCredentials
from rabbit_bq_job_optimizer import RabbitBQJobOptimizer, OptimizationConfig

# Configure logger for dbt integration
_logger = AdapterLogger("RabbitBigQuery")


class RabbitBigQueryConnectionManager(BigQueryConnectionManager):
    """
    Extended BigQuery connection manager that intercepts and optimizes
    all BigQuery job configurations via monkey-patching.
    """
    
    TYPE = "rabbitbigquery"
    RABBIT_PATCHED_MARKER = "_rabbit_patched"
    
    @classmethod
    def open(cls, connection):
        """Open connection and patch BigQuery client if not already patched."""
        connection = super().open(connection)
        
        creds = connection.credentials
        if not isinstance(creds, RabbitBigQueryCredentials):
            return connection
        
        if not creds.rabbit_enabled or not creds.rabbit_api_key or not creds.rabbit_reservation_ids:
            return connection
        
        # Get the BigQuery client from the connection
        bq_client = connection.handle
        
        # Check if already patched to avoid double-patching
        if hasattr(bq_client, cls.RABBIT_PATCHED_MARKER):
            return connection
        
        # Mark as patched
        setattr(bq_client, cls.RABBIT_PATCHED_MARKER, True)
        
        # Initialize Rabbit optimizer
        rabbit_optimizer = RabbitBQJobOptimizer(
            api_key=creds.rabbit_api_key,
            base_url=creds.rabbit_base_url
        )
        
        rabbit_config = {
            "defaultPricingMode": creds.rabbit_default_pricing_mode,
            "reservationIds": creds.rabbit_reservation_ids
        }
        
        _logger.info(
            f"Rabbit optimization enabled | Default pricing mode: {creds.rabbit_default_pricing_mode} | "
            f"Reservations: {creds.rabbit_reservation_ids}"
        )
        
        # Store original query method
        original_query = bq_client.query
        
        # Create patched query method
        def patched_query(query, *args, job_config=None, **kwargs):
            """Intercept and optimize job configuration before submission."""
            try:
                if job_config:
                    _logger.debug("Optimizing BigQuery job configuration")
                    # Convert job_config to dict for optimization
                    config_dict = job_config.to_api_repr()
                    
                    # Add the SQL query string to the configuration
                    # BigQuery expects the query in config_dict["query"]["query"]
                    if "query" not in config_dict:
                        config_dict["query"] = {}
                    config_dict["query"]["query"] = query
                    
                    # Optimize via Rabbit API
                    optimization_config = OptimizationConfig(
                        type="reservation_assignment",
                        config=rabbit_config
                    )
                    
                    _logger.debug(f"Original job configuration: {json.dumps(config_dict, indent=2)}")
                    _logger.debug(f"Optimization config: {json.dumps(asdict(optimization_config), indent=2)}")

                    result = rabbit_optimizer.optimize_job(
                        configuration={"configuration": config_dict},
                        enabledOptimizations=[optimization_config]
                    )
                    
                    # Log the entire result in JSON format (convert dataclass to dict)
                    result_dict = asdict(result)
                    _logger.debug(f"Rabbit API optimization result: {json.dumps(result_dict, indent=2)}")
                    
                    # Get optimized configuration
                    optimized_config = result.optimizedJob["configuration"]
                    
                    # Convert back to QueryJobConfig
                    from google.cloud.bigquery import QueryJobConfig
                    job_config = QueryJobConfig.from_api_repr(optimized_config)
                    
                    _logger.info("Optimized Job executed successfully")
                    
            except Exception as e:
                import traceback
                _logger.warning(f"Rabbit optimization failed: {str(e)}\nStacktrace: {traceback.format_exc()}")
                # Continue with original config
            
            return original_query(query, *args, job_config=job_config, **kwargs)
        
        # Apply the patch
        bq_client.query = patched_query
        
        return connection

