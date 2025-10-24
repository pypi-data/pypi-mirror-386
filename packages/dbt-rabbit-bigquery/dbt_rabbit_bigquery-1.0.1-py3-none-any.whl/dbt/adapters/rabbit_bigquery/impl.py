import logging
from typing import Optional, Dict, Any

from dbt.adapters.bigquery import BigQueryAdapter
from dbt.adapters.rabbit_bigquery.connections import RabbitBigQueryConnectionManager
from dbt.adapters.rabbit_bigquery.credentials import RabbitBigQueryCredentials
from rabbit_bq_job_optimizer import RabbitBQJobOptimizer, OptimizationConfig

logger = logging.getLogger(__name__)


class RabbitBigQueryAdapter(BigQueryAdapter):
    """
    Extended BigQuery adapter that optimizes job configurations
    using the Rabbit API before submitting to BigQuery.
    """
    
    ConnectionManager = RabbitBigQueryConnectionManager
    
    def __init__(self, config):
        super().__init__(config)
        self._rabbit_optimizer: Optional[RabbitBQJobOptimizer] = None
        self._rabbit_config: Optional[Dict[str, Any]] = None
        self._initialize_rabbit_optimizer()
    
    def _initialize_rabbit_optimizer(self):
        """
        Initialize the Rabbit optimizer client if credentials are provided.
        """
        try:
            creds = self.connections.profile.credentials
            
            if not isinstance(creds, RabbitBigQueryCredentials):
                logger.warning("Rabbit BigQuery Optimizer: Credentials not of type RabbitBigQueryCredentials")
                return
            
            if not creds.rabbit_enabled:
                logger.info("Rabbit BigQuery Optimizer: Disabled by configuration")
                return
            
            if not creds.rabbit_api_key:
                logger.warning("Rabbit BigQuery Optimizer: API key not provided, optimization disabled")
                return
            
            # Validate required configuration
            if not creds.rabbit_reservation_ids:
                logger.warning("Rabbit BigQuery Optimizer: No reservation IDs configured, optimization disabled")
                return
            
            valid_pricing_modes = ["on_demand", "slot_based"]
            if creds.rabbit_default_pricing_mode not in valid_pricing_modes:
                logger.warning(
                    f"Rabbit BigQuery Optimizer: Invalid pricing mode '{creds.rabbit_default_pricing_mode}'. "
                    f"Must be one of: {', '.join(valid_pricing_modes)}. Optimization disabled."
                )
                return
            
            # Initialize the optimizer client
            self._rabbit_optimizer = RabbitBQJobOptimizer(
                api_key=creds.rabbit_api_key,
                base_url=creds.rabbit_base_url
            )
            
            # Store configuration for optimization
            self._rabbit_config = {
                "defaultPricingMode": creds.rabbit_default_pricing_mode,
                "reservationIds": creds.rabbit_reservation_ids
            }
            
            logger.info(
                f"Rabbit BigQuery Optimizer: Initialized successfully with "
                f"pricing mode '{creds.rabbit_default_pricing_mode}' and "
                f"{len(creds.rabbit_reservation_ids)} reservation(s)"
            )
            
        except Exception as e:
            logger.warning(f"Rabbit BigQuery Optimizer: Failed to initialize: {str(e)}")
            self._rabbit_optimizer = None
            self._rabbit_config = None
    
    def _optimize_job_configuration(self, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize a BigQuery job configuration using the Rabbit API.
        
        Args:
            configuration: The original BigQuery job configuration
            
        Returns:
            The optimized job configuration, or the original if optimization fails
        """
        # If optimizer is not initialized, return original configuration
        if not self._rabbit_optimizer or not self._rabbit_config:
            return configuration
        
        try:
            logger.debug(f"Rabbit BigQuery Optimizer: Original configuration: {configuration}")
            
            # Create optimization config
            optimization_config = OptimizationConfig(
                type="reservation_assignment",
                config=self._rabbit_config
            )
            
            # Call the optimizer API
            result = self._rabbit_optimizer.optimize_job(
                configuration={"configuration": configuration},
                enabledOptimizations=[optimization_config]
            )
            
            logger.info("Rabbit BigQuery Optimizer: Job configuration optimized successfully")
            logger.debug(f"Rabbit BigQuery Optimizer: Optimization result: {result}")
            
            # Extract and return the optimized configuration
            optimized_config = result.optimizedJob["configuration"]
            logger.debug(f"Rabbit BigQuery Optimizer: Optimized configuration: {optimized_config}")
            
            return optimized_config
            
        except Exception as e:
            logger.warning(
                f"Rabbit BigQuery Optimizer: Optimization failed: {str(e)}. "
                "Proceeding with original job configuration."
            )
            return configuration
    
    def _create_job_request(self, sql: str, **kwargs) -> Dict[str, Any]:
        """
        Override to intercept and optimize job configurations.
        """
        # Get the original job configuration from parent
        job_config = super()._create_job_request(sql, **kwargs)
        
        # Optimize the configuration using Rabbit API
        optimized_config = self._optimize_job_configuration(job_config)
        
        return optimized_config
    
    @classmethod
    def date_function(cls):
        """Inherit from BigQueryAdapter"""
        return "CURRENT_DATE()"
    
    @classmethod
    def timestamp_function(cls):
        """Inherit from BigQueryAdapter"""
        return "CURRENT_TIMESTAMP()"

