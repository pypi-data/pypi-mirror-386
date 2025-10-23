# IFS ECS Logger

**IFS ECS Logger** is a lightweight Python library providing **IFS-compliant structured logging** based on the **Elastic Common Schema (ECS)**. It standardizes how logs are emitted across IFS CI/CD pipelines and automation scripts, ensuring consistent observability and easy ingestion into Elasticsearch, Kibana, or any ECS-aware platform.

---

## Features It standardizes and how logs are emitted across IFS CI/CD pipelines and automation scripts

ensuring consistent observability and easy ingestion into Elasticsearch, Kibana, or any ECS-aware platform.

- **IFS ECS compliance** — follows company formatting rules (e.g., `_timestamp`, `host.name`, structured `http` objects)

- **ECS 1.6.0 compatible** — automatically includes ECS fields (`log.level`, `process.pid`, etc.)

- **Tekton & Kubernetes context** — automatically detects and includes pipeline context when running in Tekton/K8s environments

- **Structured JSON output** — perfect for Elastic, Loki, Azure Monitor, and Fluent Bit ingestion## ✨ Features

- **Log levels supported:** `debug`, `info`, `warning`, `error`, `critical`

- **Zero configuration** — simple import and use- ✅ **IFS ECS compliance** — follows company formatting rules (e.g., `_timestamp`, `host.name`, structured `http` objects)


---

## 📦 Installation

```bash

pip install ifs-ecs-logger

```

## Usage

### Standard Python Logging with IFS ECS Formatting

```python
import logging
import sys
from ifs_ecs_logger import IFSECSFormatter

# Configure logger with IFS ECS formatting
logger = logging.getLogger("fetchConfig")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(IFSECSFormatter())

logger.handlers.clear()
logger.addHandler(handler)

# Set logging level (DEBUG shows all messages, info/debug/warning/error/critical)
logger.setLevel(logging.DEBUG)

# Info - general progress updates
logger.info("Starting configuration fetch", extra={
    "hostName": "build-agent-01",
    "timestamp": "2025-10-21T12:34:56Z",
    "http": "200"
})

# Debug - detailed internal state, visible only if level=DEBUG
logger.debug("Preparing to fetch configuration file", extra={
    "timestamp": "2025-10-21T12:34:00Z"
})

# Warning - non-critical anomalies
logger.warning("Response took longer than expected", extra={
    "timestamp": "2025-10-21T12:35:10Z",
    "http": {"status_code": 200}
})

# Error - operational failures
logger.error("API call failed", extra={
    "http": {"status_code": 500},
    "timestamp": "2025-10-21T12:35:30Z"
})

# Critical - system-level or unrecoverable errors
logger.critical("Fetch pipeline aborted", extra={
    "timestamp": "2025-10-21T12:36:00Z",
    "hostName": "build-agent-01"
})
```

### Alternative Handler Types (File Handler)

```python
import logging
from ifs_ecs_logger import IFSECSFormatter

# File logging with IFS ECS formatting
logger = logging.getLogger("myapp")
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(IFSECSFormatter())
logger.addHandler(file_handler)

# Multiple handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(IFSECSFormatter())
logger.addHandler(console_handler)

logger.setLevel(logging.INFO)
logger.info("Application started", extra={"version": "1.0.0"})
```

## Expected Output (IFS ECS-Compliant JSON)

Each log entry will be emitted as a single-line structured JSON like:

```json
{"_timestamp":"2025-10-21T12:34:56Z","log.level":"info","message":"Starting configuration fetch","ecs.version":"1.6.0","service.name":"fetchConfig","host":{"name":"build-agent-01"},"http":{"response":{"status_code":200}}}
```

This flat format is optimized for log processing systems and ensures compatibility with log aggregators like ElasticSearch, Fluent Bit, Logstash, and cloud logging services.

---

## IFS Compliance

This logger is designed to comply with IFS logging policies:

### Forbidden Fields
The following fields are automatically filtered out to avoid compliance issues:
- `kubernetes` (contains sensitive cluster information)
- `_id`, `_index`, `_score` (Elasticsearch internal fields)
- `stream` (duplicate information)

### Normalized Fields
- `timestamp` → `_timestamp` (IFS standard)
- `hostName` → `host.name` (nested structure)
- HTTP fields are structured as nested objects

---

## Requirements

- Python 3.8+
- `ecs-logging>=2.1.0`
- `python-json-logger>=2.0.7`

---

## License

MIT License © IFS Golden CI Team