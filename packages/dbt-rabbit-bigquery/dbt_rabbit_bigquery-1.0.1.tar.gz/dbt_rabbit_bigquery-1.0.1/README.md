# dbt-rabbit-bigquery

A dbt adapter plugin that automatically optimizes BigQuery job configurations using the Rabbit API. This adapter extends the standard `dbt-bigquery` adapter to intercept and optimize all BigQuery jobs before execution.

## Features

- **Automatic Optimization**: Transparently optimizes all BigQuery queries executed by dbt
- **Reservation Assignment**: Intelligently assigns queries to the most cost-effective BigQuery reservations
- **Seamless Integration**: Works with existing dbt projects with minimal configuration changes
- **Graceful Fallback**: Falls back to original configuration if optimization fails
- **Comprehensive Logging**: Detailed logs for debugging and monitoring optimization

## Installation

Install the adapter using pip:

```bash
pip install dbt-rabbit-bigquery
```

Or add it to your `requirements.txt`:

```
dbt-rabbit-bigquery>=1.0.0
```

## Configuration

### 1. Update your `profiles.yml`

Change your profile type from `bigquery` to `rabbit-bigquery` and add Rabbit configuration:

```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: rabbit-bigquery  # Changed from 'bigquery'
      method: service-account
      project: my-gcp-project
      dataset: my_dataset
      threads: 4
      keyfile: /path/to/service-account.json
      location: US
      
      # Rabbit-specific configuration
      rabbit_api_key: "{{ env_var('RABBIT_API_KEY') }}"
      rabbit_default_pricing_mode: on_demand
      rabbit_reservation_ids:
        - "project:us-central1.reservation-name1"
        - "project:us-east1.reservation-name2"
      rabbit_enabled: true  # Optional: set to false to disable optimization
```

### 2. Configuration Fields

#### Standard BigQuery Fields
All standard `dbt-bigquery` configuration options are supported. See [dbt-bigquery documentation](https://docs.getdbt.com/reference/warehouse-setups/bigquery-setup) for details.

#### Rabbit-Specific Fields

| Field | Required | Description |
|-------|----------|-------------|
| `rabbit_api_key` | Yes | Your Rabbit API key. Use `env_var()` to load from environment |
| `rabbit_default_pricing_mode` | Yes | Default pricing mode: `"on_demand"` or `"slot_based"` |
| `rabbit_reservation_ids` | Yes | List of reservation IDs in format `"project:region.reservation-name"` |
| `rabbit_base_url` | No | Custom Rabbit API base URL (defaults to production) |
| `rabbit_enabled` | No | Enable/disable optimization (default: `true`) |

### 3. Set Environment Variables

For security, store your API key as an environment variable:

```bash
export RABBIT_API_KEY="your-rabbit-api-key"
```

Or add it to your `.env` file:

```bash
RABBIT_API_KEY=your-rabbit-api-key
```

## Usage

Once configured, the adapter works automatically with all dbt commands:

```bash
# Run models - all queries will be optimized
dbt run

# Run specific models
dbt run --select my_model

# Test models
dbt test

# Snapshot
dbt snapshot

# All dbt commands work as expected
```

The adapter will:
1. Intercept every BigQuery job configuration
2. Send it to the Rabbit API for optimization
3. Apply the optimized configuration
4. Submit the job to BigQuery

## How It Works

```
┌─────────────┐
│  dbt Core   │
└──────┬──────┘
       │
       ├─ SQL Query
       │
       ▼
┌──────────────────────────┐
│ Rabbit BigQuery Adapter  │
│  1. Create job config    │
│  2. Call Rabbit API      │
│  3. Get optimized config │
└──────┬───────────────────┘
       │
       ├─ Optimized Job Config
       │
       ▼
┌──────────────┐
│  BigQuery    │
└──────────────┘
```

## Example Optimization Flow

**Original Configuration:**
```json
{
  "query": {
    "query": "SELECT * FROM my_table WHERE date = CURRENT_DATE()",
    "useLegacySql": false
  }
}
```

**After Rabbit Optimization:**
```json
{
  "query": {
    "query": "SELECT * FROM my_table WHERE date = CURRENT_DATE()",
    "useLegacySql": false,
    "connectionProperties": [
      {
        "key": "reservation_id",
        "value": "project:us-central1.reservation-name1"
      }
    ]
  }
}
```

## Disabling Optimization

You can disable optimization in several ways:

### 1. In profiles.yml
```yaml
dev:
  type: rabbit-bigquery
  # ... other config ...
  rabbit_enabled: false
```

### 2. Via Environment Variable
```bash
export DBT_RABBIT_ENABLED=false
dbt run
```

### 3. For Specific Models
Use the standard BigQuery adapter for specific models:
```yaml
# In dbt_project.yml or model config
models:
  my_project:
    legacy_models:
      +materialized: table
      +adapter: bigquery  # Use standard adapter
```

## Logging and Debugging

The adapter provides detailed logging at different levels:

### Info Level (Default)
```
Rabbit BigQuery Optimizer: Enabled
Rabbit BigQuery Optimizer: Job configuration optimized successfully
```

### Debug Level
Set environment variable for detailed logs:
```bash
export DBT_LOG_LEVEL=debug
dbt run
```

You'll see:
- Original job configurations
- Optimization requests/responses
- Optimized configurations
- API call details

## Error Handling

The adapter includes comprehensive error handling:

| Scenario | Behavior |
|----------|----------|
| Missing API key | Warning logged, optimization disabled |
| Invalid reservation IDs | Warning logged, optimization disabled |
| API request fails | Warning logged, uses original configuration |
| Network error | Warning logged, uses original configuration |
| Invalid response | Warning logged, uses original configuration |

In all error cases:
- A warning is logged with details
- The original (unoptimized) configuration is used
- dbt execution continues normally

## Troubleshooting

### Issue: `No module named 'dbt.adapters.rabbit_bigquery'`

**Solution:** Ensure the package is installed in your dbt environment:
```bash
pip install dbt-rabbit-bigquery
```

### Issue: `Credentials not of type RabbitBigQueryCredentials`

**Solution:** Verify your `profiles.yml` has `type: rabbit-bigquery` (not `bigquery`)

### Issue: `API key not provided, optimization disabled`

**Solution:** Ensure `rabbit_api_key` is set in `profiles.yml`:
```yaml
rabbit_api_key: "{{ env_var('RABBIT_API_KEY') }}"
```

And the environment variable is set:
```bash
export RABBIT_API_KEY="your-api-key"
```

### Issue: `No reservation IDs configured, optimization disabled`

**Solution:** Add reservation IDs to your `profiles.yml`:
```yaml
rabbit_reservation_ids:
  - "project:us-central1.reservation-name1"
```

### Issue: Jobs not being optimized

**Steps to debug:**

1. Enable debug logging:
   ```bash
   export DBT_LOG_LEVEL=debug
   dbt run
   ```

2. Check for Rabbit-related log messages

3. Verify configuration:
   ```bash
   dbt debug
   ```

4. Test API connectivity manually with the Python package:
   ```python
   from rabbit_bq_job_optimizer import RabbitBQJobOptimizer
   client = RabbitBQJobOptimizer(api_key="your-key")
   # Test optimization...
   ```

## Performance Impact

The adapter adds minimal overhead:
- **API call latency**: ~100-500ms per query
- **Parallel execution**: dbt's multi-threading still works normally
- **Network optimizations**: The Rabbit API is highly available and low-latency

For long-running queries, the optimization overhead is negligible compared to query execution time.

## Compatibility

| Component | Version |
|-----------|---------|
| dbt-core | ≥1.5.0 |
| dbt-bigquery | ≥1.5.0, <2.0.0 |
| Python | ≥3.8 |
| rabbit-bq-job-optimizer | ≥1.0.0 |

## Migration from Standard dbt-bigquery

1. Install `dbt-rabbit-bigquery`:
   ```bash
   pip install dbt-rabbit-bigquery
   ```

2. Update `profiles.yml`:
   ```yaml
   # Change this:
   type: bigquery
   
   # To this:
   type: rabbit-bigquery
   
   # Add Rabbit config:
   rabbit_api_key: "{{ env_var('RABBIT_API_KEY') }}"
   rabbit_default_pricing_mode: on_demand
   rabbit_reservation_ids:
     - "project:region.reservation-name"
   ```

3. Set environment variable:
   ```bash
   export RABBIT_API_KEY="your-api-key"
   ```

4. Test:
   ```bash
   dbt debug
   dbt run --select my_model
   ```

That's it! No changes needed to your models or project structure.

## Examples

See the [examples](./examples) directory for:
- Sample `profiles.yml` configurations
- Example dbt projects
- Integration patterns
- Advanced use cases

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Publishing to PyPI

For maintainers publishing new versions.

### Prerequisites

1. **PyPI Account**: https://pypi.org/account/register/

2. **API Token**: 
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Save the token (starts with `pypi-`)

3. **Configure Credentials**

   Create `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-YourActualTokenHere
   ```
   
   Set secure permissions:
   ```bash
   chmod 600 ~/.pypirc
   ```

### Pre-Release Checklist

Before publishing, ensure:
- [ ] CHANGELOG.md updated with new version
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Git repo is clean (no uncommitted changes)

### Publish

Run the publish script:

```bash
./publish.sh
```

The script automatically:
- Creates/uses virtual environment
- Installs required tools (twine, setuptools, wheel)
- Gets version from setup.py
- Cleans previous builds
- Builds the package
- Creates git tag (v{version})
- Pushes git tag to origin
- Uploads to PyPI
- Auto-increments version for next release

Verify on PyPI: https://pypi.org/project/dbt-rabbit-bigquery/

### Version Numbering

Follow Semantic Versioning:
- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Edit `setup.py` to update version:
```python
package_version = "1.0.1"  # Update this
```

### Troubleshooting

**Error: "File already exists"**
- Version already published. Increment version in `setup.py` and republish.

**Error: "Invalid username/password"**
- Verify `~/.pypirc` is configured correctly
- Ensure using `__token__` as username
- Check API token is valid

## Support

For questions, issues, or API access:
- Email: success@followrabbit.ai
- Issues: https://github.com/your-repo/dbt-rabbit-bigquery/issues

## License

Apache License 2.0 - see [LICENSE](./LICENSE) for details.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and updates.

