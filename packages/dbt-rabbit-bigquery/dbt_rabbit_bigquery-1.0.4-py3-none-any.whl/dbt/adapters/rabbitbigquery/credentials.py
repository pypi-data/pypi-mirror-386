from dataclasses import dataclass, field
from typing import Optional, List, Union

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
    rabbit_reservation_ids: Union[List[str], str] = field(default_factory=list)
    rabbit_enabled: bool = True  # Allow disabling optimization if needed
    
    def __post_init__(self):
        super().__post_init__()
        
        # Handle comma-separated string input for reservation IDs
        # This runs after mash umaro deserialization
        if isinstance(self.rabbit_reservation_ids, str):
            if self.rabbit_reservation_ids:
                self.rabbit_reservation_ids = [
                    r.strip() for r in self.rabbit_reservation_ids.split(',') if r.strip()
                ]
            else:
                self.rabbit_reservation_ids = []
        elif isinstance(self.rabbit_reservation_ids, list):
            # Check if it was incorrectly split into characters
            if len(self.rabbit_reservation_ids) > 0 and len(self.rabbit_reservation_ids[0]) == 1:
                # It was split into characters, rejoin and resplit
                joined = ''.join(self.rabbit_reservation_ids)
                self.rabbit_reservation_ids = [
                    r.strip() for r in joined.split(',') if r.strip()
                ]
    
    @property
    def type(self):
        return "rabbitbigquery"
    
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

