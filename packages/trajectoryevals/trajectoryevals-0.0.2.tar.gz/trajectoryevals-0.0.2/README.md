# Trajectory SDK

A powerful Python SDK for tracing and monitoring AI applications with support for local and remote tracing, comprehensive logging, and seamless integration with popular AI frameworks.

## 🚀 Quick Start

### Installation

```bash
pip install trajectoryevals
```

### Basic Usage

```python
from trajectory import Tracer

# Initialize the tracer
tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    project_name="my-project"
)

# Trace your functions
@tracer.observe
def my_ai_function(input_data):
    # Your AI logic here
    result = process_data(input_data)
    return result

# Or use context manager
with tracer.trace("my_operation") as trace:
    trace.log_metric("accuracy", value=0.95)
    result = my_ai_function(data)
```

## 🔧 Configuration

### Environment Variables

The Trajectory SDK can be configured using environment variables for seamless integration:

#### Core Configuration
```bash
# Required for remote tracing
export TRAJECTORY_API_KEY="your-api-key"
export TRAJECTORY_ORG_ID="your-organization-id"
```

#### Monitoring and Evaluations
```bash
# Enable/disable monitoring (default: true)
export TRAJECTORY_MONITORING="true"

# Enable/disable evaluations (default: true)
export TRAJECTORY_EVALUATIONS="true"
```

#### Logging Configuration
```bash
# Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export TRAJECTORY_LOGGING_LEVEL="INFO"

# Disable colored output
export NO_COLOR="1"
```

#### Local Tracing
```bash
# Enable local tracing (saves traces locally instead of remote server)
export TRAJECTORY_TRACING_LOCAL="true"

# Custom directory for local traces (default: ./trajectory_traces)
export TRAJECTORY_TRACING_LOCAL_DIR="/path/to/your/traces"

# Only local tracing (completely bypasses remote server calls)
export TRAJECTORY_ONLY_LOCAL_TRACING="true"
```

#### Development Mode
```bash
# Enable development mode
export TRAJECTORY_DEV="true"
```

### Programmatic Configuration

```python
from trajectory import Tracer
from trajectory.common.logger import configure_trajectory_logger

# Configure logging
configure_trajectory_logger(
    level="DEBUG",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    use_color=True
)

# Configure tracer
tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    project_name="my-project",
    enable_monitoring=True,
    enable_evaluations=True,
    enable_local_tracing=False,  # Set to True for local tracing
    local_tracing_dir="./my_traces"  # Custom local directory
)
```

## 🔗 Framework Integrations

### LangGraph Integration

```python
from trajectory import Tracer
from trajectory.integrations.langgraph import TrajectoryCallbackHandler

# Initialize tracer
tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    project_name="langgraph-project"
)

# Create callback handler
callback_handler = TrajectoryCallbackHandler(tracer)

# Use with LangGraph
from langgraph.graph import StateGraph

graph = StateGraph(YourState)
# Add your nodes and edges
compiled_graph = graph.compile()

# Run with tracing
result = compiled_graph.invoke(
    {"input": "your data"},
    config={"callbacks": [callback_handler]}
)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from trajectory import Tracer

app = FastAPI()

# Initialize tracer
tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    project_name="fastapi-app"
)

@app.post("/predict")
@tracer.observe
async def predict(data: dict):
    # Your prediction logic
    result = await process_prediction(data)
    return result
```

### Custom Integration

```python
from trajectory import Tracer

tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    project_name="custom-app"
)

# Trace any function
@tracer.observe(name="custom_function")
def my_function(x, y):
    return x + y

# Trace with context manager
with tracer.trace("batch_processing") as trace:
    trace.log_metric("batch_size", value=100)
    results = []
    for item in data:
        result = process_item(item)
        results.append(result)
        trace.log_metric("processed_items", value=len(results))
```

## 📊 Local Tracing

For development, testing, or privacy-sensitive applications, you can save traces locally instead of sending them to the remote server:

```python
# Enable local tracing
tracer = Tracer(
    api_key="your-api-key",
    organization_id="your-org-id",
    enable_local_tracing=True,
    local_tracing_dir="./my_local_traces"
)

# Or use environment variables
# export TRAJECTORY_TRACING_LOCAL=true
# export TRAJECTORY_TRACING_LOCAL_DIR=/path/to/traces
```

### Local Trace Management

```python
from trajectory.common.local_trace_storage import LocalTraceStorage

# Initialize storage
storage = LocalTraceStorage("./my_traces")

# List all traces
traces = storage.list_traces()
for trace in traces:
    print(f"Trace: {trace['trace_id']} - {trace['timestamp']}")

# Get specific trace
trace_data = storage.get_trace("your-trace-id")

# Clean up old traces (older than 30 days)
storage.cleanup_old_traces(days_to_keep=30)
```

## 📝 Logging

The SDK includes comprehensive logging that can be configured for different environments:

```python
from trajectory.common.logger import configure_trajectory_logger

# Configure logging level
configure_trajectory_logger(level="DEBUG")

# Custom format
configure_trajectory_logger(
    level="INFO",
    format_string="[%(levelname)s] %(name)s: %(message)s",
    date_format="%Y-%m-%d %H:%M:%S",
    use_color=False
)
```

### Logging Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages

## 🎯 Advanced Features

### Metrics and Metadata

```python
with tracer.trace("data_processing") as trace:
    # Log metrics
    trace.log_metric("accuracy", value=0.95)
    trace.log_metric("latency_ms", value=150)
    
    # Add metadata
    trace.update_metadata({
        "model_version": "v2.1",
        "dataset": "training_data_v3",
        "environment": "production"
    })
    
    # Add tags
    trace.update_metadata({
        "tags": ["ml", "nlp", "production"]
    })
```

### Conversation Context

```python
from trajectory.common.tracer.core import conversation_id_var, user_id_var

# Set conversation context
conversation_id_var.set("conv_123")
user_id_var.set("user_456")

# All traces in this context will include conversation and user IDs
with tracer.trace("user_query") as trace:
    # This trace will be associated with the conversation and user
    pass
```

### Custom Spans

```python
# Create custom spans
with tracer.trace("custom_operation", span_type="custom") as trace:
    # Your custom logic
    pass

# Nested spans
with tracer.trace("parent_operation") as parent:
    with tracer.trace("child_operation") as child:
        # Nested operations
        pass
```

## 🔍 Monitoring and Debugging

### Trace Visualization

When using remote tracing, you can view your traces in the Trajectory AI dashboard. The SDK provides URLs to access your traces:

```python
trace_id, response = trace.save()
print(f"View your trace: {response.get('ui_results_url')}")
```

### Local Trace Inspection

For local traces, you can inspect the JSON files directly or use the storage utilities:

```python
import json

# Load and inspect a trace file
with open("trajectory_traces/trace_20241201_143022_a1b2c3d4.json", "r") as f:
    trace_data = json.load(f)
    print(f"Trace: {trace_data['data']['name']}")
    print(f"Duration: {trace_data['data']['duration']}s")
    print(f"Spans: {len(trace_data['data']['trace_spans'])}")
```

## 🛠️ Development

### Editable Installation

For development, install the package in editable mode:

```bash
# Using pip
pip install -e .

# Using uv
uv add --editable .
```

### Testing

```python
# Test basic functionality
from trajectory import Tracer

tracer = Tracer(
    api_key="test-key",
    organization_id="test-org",
    enable_local_tracing=True  # Use local tracing for testing
)

with tracer.trace("test") as trace:
    trace.log_metric("test_metric", value=42)
```

## 📚 API Reference

### Tracer Class

```python
Tracer(
    api_key: str = None,
    organization_id: str = None,
    project_name: str = None,
    enable_monitoring: bool = True,
    enable_evaluations: bool = True,
    enable_local_tracing: bool = None,
    local_tracing_dir: str = None,
    deep_tracing: bool = False,
    trace_across_async_contexts: bool = False
)
```

### TraceClient Methods

```python
# Context manager
with tracer.trace("operation_name") as trace:
    pass

# Decorator
@tracer.observe(name="function_name")
def my_function():
    pass

# Metrics and metadata
trace.log_metric(name, value, unit=None, tags=None)
trace.update_metadata(metadata_dict)
```

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed correctly
   ```bash
   pip list | grep trajectoryevals
   ```

2. **API Key Issues**: Verify your API key and organization ID
   ```bash
   echo $TRAJECTORY_API_KEY
   echo $TRAJECTORY_ORG_ID
   ```

3. **Local Tracing Not Working**: Check directory permissions
   ```bash
   ls -la ./trajectory_traces/
   ```

4. **Logging Not Showing**: Check logging level configuration
   ```bash
   export TRAJECTORY_LOGGING_LEVEL=DEBUG
   ```

### Getting Help

- Check the [development guide](README_DEV.md) for detailed setup instructions
- Review the [feature documentation](feature_docs/) for specific features
- Ensure all environment variables are set correctly
- Use local tracing for debugging without affecting production data

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Package Name**: `trajectoryevals`  
**Import Name**: `trajectory`  
**Version**: 0.0.2