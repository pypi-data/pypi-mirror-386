from dataclasses import dataclass, field
from typing import Optional, List

from dbt.adapters.bigquery.credentials import BigQueryCredentials


@dataclass
class RabbitBigQueryCredentials(BigQueryCredentials):
    """
    Extended BigQuery credentials that include Rabbit API configuration
    for job optimization.
    """
    
    # Rabbit API configuration
    rabbit_api_key: Optional[str] = None
    rabbit_base_url: Optional[str] = None
    rabbit_default_pricing_mode: Optional[str] = "on_demand"
    rabbit_reservation_ids: List[str] = field(default_factory=list)
    rabbit_enabled: bool = True  # Allow disabling optimization if needed
    
    @property
    def type(self):
        return "rabbit-bigquery"
    
    @property
    def unique_field(self):
        return self.database
    
    def _connection_keys(self):
        # Get parent connection keys
        keys = super()._connection_keys()
        
        # Add Rabbit-specific keys
        return keys + (
            "rabbit_api_key",
            "rabbit_base_url",
            "rabbit_default_pricing_mode",
            "rabbit_reservation_ids",
            "rabbit_enabled",
        )

