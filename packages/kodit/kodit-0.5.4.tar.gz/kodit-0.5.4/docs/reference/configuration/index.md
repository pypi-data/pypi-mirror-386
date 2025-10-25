---
title: Configuration Reference
description: Kodit Configuration Reference
weight: 29
---

This document contains the complete configuration reference for Kodit. All configuration is done through environment variables.

## AppContext

Global context for the kodit project. Provides a shared state for the app.

| Environment Variable | Type | Default | Description |
|---------------------|------|---------|-------------|
| `DATA_DIR` | Path | `~/.kodit` |  |
| `DB_URL` | str | `<lambda>()` |  |
| `LOG_LEVEL` | str | `INFO` |  |
| `LOG_FORMAT` | LogFormat | `LogFormat.PRETTY` |  |
| `DISABLE_TELEMETRY` | bool | `False` |  |
| `EMBEDDING_ENDPOINT` | `Endpoint | None` | `None` | Endpoint to use for embedding. |
| `EMBEDDING_ENDPOINT_BASE_URL` | `str | None` | `None` |  |
| `EMBEDDING_ENDPOINT_MODEL` | `str | None` | `None` | Model to use for the endpoint in litellm format (e.g. 'openai/text-embedding-3-small') |
| `EMBEDDING_ENDPOINT_API_KEY` | `str | None` | `None` |  |
| `EMBEDDING_ENDPOINT_NUM_PARALLEL_TASKS` | int | `10` | Number of parallel tasks to use for the endpoint |
| `EMBEDDING_ENDPOINT_SOCKET_PATH` | `str | None` | `None` | Unix socket path for local communication (e.g., /tmp/openai.sock) |
| `EMBEDDING_ENDPOINT_TIMEOUT` | float | `60` | Request timeout in seconds |
| `EMBEDDING_ENDPOINT_MAX_RETRIES` | int | `5` | Maximum number of retries for the endpoint |
| `EMBEDDING_ENDPOINT_INITIAL_DELAY` | float | `2.0` | Initial delay in seconds for the endpoint |
| `EMBEDDING_ENDPOINT_BACKOFF_FACTOR` | float | `2.0` | Backoff factor for the endpoint |
| `EMBEDDING_ENDPOINT_EXTRA_PARAMS` | `dict | None` | `None` | Extra provider-specific non-secret parameters for LiteLLM |
| `EMBEDDING_ENDPOINT_MAX_TOKENS` | int | `8000` | Conservative token limit for the embedding model |
| `ENRICHMENT_ENDPOINT` | `Endpoint | None` | `None` | Endpoint to use for enrichment. |
| `ENRICHMENT_ENDPOINT_BASE_URL` | `str | None` | `None` |  |
| `ENRICHMENT_ENDPOINT_MODEL` | `str | None` | `None` | Model to use for the endpoint in litellm format (e.g. 'openai/text-embedding-3-small') |
| `ENRICHMENT_ENDPOINT_API_KEY` | `str | None` | `None` |  |
| `ENRICHMENT_ENDPOINT_NUM_PARALLEL_TASKS` | int | `10` | Number of parallel tasks to use for the endpoint |
| `ENRICHMENT_ENDPOINT_SOCKET_PATH` | `str | None` | `None` | Unix socket path for local communication (e.g., /tmp/openai.sock) |
| `ENRICHMENT_ENDPOINT_TIMEOUT` | float | `60` | Request timeout in seconds |
| `ENRICHMENT_ENDPOINT_MAX_RETRIES` | int | `5` | Maximum number of retries for the endpoint |
| `ENRICHMENT_ENDPOINT_INITIAL_DELAY` | float | `2.0` | Initial delay in seconds for the endpoint |
| `ENRICHMENT_ENDPOINT_BACKOFF_FACTOR` | float | `2.0` | Backoff factor for the endpoint |
| `ENRICHMENT_ENDPOINT_EXTRA_PARAMS` | `dict | None` | `None` | Extra provider-specific non-secret parameters for LiteLLM |
| `ENRICHMENT_ENDPOINT_MAX_TOKENS` | int | `8000` | Conservative token limit for the embedding model |
| `DEFAULT_SEARCH` | Search | `provider='sqlite'` |  |
| `DEFAULT_SEARCH_PROVIDER` | Literal | `sqlite` |  |
| `PERIODIC_SYNC` | PeriodicSyncConfig | `enabled=True interval_seconds=1800 retry_attempts=3` | Periodic sync configuration |
| `PERIODIC_SYNC_ENABLED` | bool | `True` | Enable periodic sync |
| `PERIODIC_SYNC_INTERVAL_SECONDS` | float | `1800` | Interval between periodic syncs in seconds |
| `PERIODIC_SYNC_RETRY_ATTEMPTS` | int | `3` | Number of retry attempts for failed syncs |
| `API_KEYS` | list | `[]` | Comma-separated list of valid API keys (e.g. 'key1,key2') |
| `REMOTE` | RemoteConfig | `server_url=None api_key=None timeout=30.0 max_retries=3 verify_ssl=True` | Remote server configuration |
| `REMOTE_SERVER_URL` | `str | None` | `None` | Remote Kodit server URL |
| `REMOTE_API_KEY` | `str | None` | `None` | API key for authentication |
| `REMOTE_TIMEOUT` | float | `30.0` | Request timeout in seconds |
| `REMOTE_MAX_RETRIES` | int | `3` | Maximum retry attempts |
| `REMOTE_VERIFY_SSL` | bool | `True` | Verify SSL certificates |
| `REPORTING` | ReportingConfig | `log_time_interval=datetime.timedelta(seconds=5)` | Reporting configuration |
| `REPORTING_LOG_TIME_INTERVAL` | timedelta | `0:00:05` | Time interval to log progress in seconds |

## Applying Configuration

There are two ways to apply configuration to Kodit:

1. A local `.env` file (e.g. `kodit --env-file .env serve`)
2. Environment variables (e.g. `DATA_DIR=/path/to/kodit/data kodit serve`)

How you specify environment variables is dependent on your deployment mechanism.

### Docker Compose

For example, in docker compose you can use the `environment` key:

```yaml
services:
  kodit:
    environment:
      - DATA_DIR=/path/to/kodit/data
```

### Kubernetes

For example, in Kubernetes you can use the `env` key:

```yaml
env:
  - name: DATA_DIR
    value: /path/to/kodit/data
```
