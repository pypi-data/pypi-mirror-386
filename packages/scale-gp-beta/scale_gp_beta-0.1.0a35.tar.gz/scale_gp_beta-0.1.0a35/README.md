# Scale GP Python API library

<!-- prettier-ignore -->
[![PyPI version](https://img.shields.io/pypi/v/scale-gp-beta.svg?label=pypi%20(stable))](https://pypi.org/project/scale-gp-beta/)

The Scale GP Python library provides convenient access to the Scale GP REST API from any Python 3.8+
application. The library includes type definitions for all request params and response fields,
and offers both synchronous and asynchronous clients powered by [httpx](https://github.com/encode/httpx).

It is generated with [Stainless](https://www.stainless.com/).

## Documentation

The REST API documentation can be found on [docs.gp.scale.com](https://docs.gp.scale.com). The full API of this library can be found in [api.md](api.md).

## Installation

```sh
# install from PyPI
pip install --pre scale-gp-beta
```

## Usage

The full API of this library can be found in [api.md](api.md).

```python
import os
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
    api_key=os.environ.get("SGP_API_KEY"),  # This is the default and can be omitted
    # defaults to "production".
    environment="development",
)

completion = client.chat.completions.create(
    messages=[{"foo": "bar"}],
    model="model",
    top_k=2,
)
```

While you can provide an `api_key` keyword argument,
we recommend using [python-dotenv](https://pypi.org/project/python-dotenv/)
to add `SGP_API_KEY="My API Key"` to your `.env` file
so that your API Key is not stored in source control.

---

## Tracing & Spans

The SGP Tracing library provides a convenient way to instrument your Python applications with tracing capabilities, allowing you to generate, manage, and send spans to the Scale GP platform. This enables detailed monitoring and debugging of your workflows.

### Quick Start Examples

For runnable examples, see the [examples/tracing](https://github.com/scaleapi/sgp-python-beta/tree/main/examples/tracing) directory in the repository.

### Using the SDK

#### Initialization

Before you can create any traces or spans, you should initialize the tracing SDK with your `SGPClient`. It's best practice to do this once at your application's entry point. You can omit this step if you have set the `SGP_API_KEY` and `SGP_ACCOUNT_ID` environment variables, as the SDK will attempt to create a default client.

```python
import scale_gp_beta.lib.tracing as tracing
from scale_gp_beta import SGPClient

client = SGPClient(api_key="YOUR_API_KEY", account_id="YOUR_ACCOUNT_ID")
tracing.init(client=client)
```

Tracing uses the `SGPClient` for all requests. You can edit the `base_url` or any other parameters via the client you pass to `init()`.

#### Disabling Tracing

You can disable tracing by setting the environment variable `DISABLE_SCALE_TRACING` or programmatically via the `disabled` parameter in `init()`.

#### Core Concepts

The SDK revolves around two primary concepts: **Traces** and **Spans**.

  * **Trace:** A trace represents a complete workflow or transaction, such as a web request or an AI agent's operation. It's a collection of related spans. Every trace has a single **root span**.
  * **Span:** A span represents a single unit of work within a trace, like a function call, a database query, or an external API request. Spans can be nested to show hierarchical relationships.

When starting a trace, we will also create a root span. Server-side, we do not record the trace resource, only spans, but rely on the root span for trace data.

#### Creating Traces and Spans

The SDK offers flexible ways to create traces and spans: using **context managers** for automatic start/end handling, or **explicit control** for manual lifecycle management.

##### 1\. Using Context Managers (Recommended)

The most straightforward way to create traces and spans is by using them as context managers (`with` statements). This ensures that spans are automatically started and ended, and errors are captured.

**Creating a Trace with a Root Span:**

Use `tracing.create_trace()` as a context manager to define a new trace. This automatically creates a root span for your trace.

```python
import scale_gp_beta.lib.tracing as tracing

def my_workflow():
    with tracing.create_trace(name="my_application_workflow", metadata={"env": "production"}):
        # All spans created within this block will belong to "my_application_workflow" trace
        print("Starting my application workflow...")
        # ... your workflow logic
        print("Application workflow completed.")
```

**Creating Spans within a Trace:**

Inside a `create_trace` block, use `tracing.create_span()` as a context manager. These spans will automatically be associated with the current trace and parent span (if one exists).

```python
import time
import scale_gp_beta.lib.tracing as tracing

def fibonacci(curr: int) -> int:
    with tracing.create_span("fibonacci_calculation", input={"curr": curr}) as span:
        time.sleep(0.1) # Simulate some work
        if curr < 2:
            span.output = {"res": curr}
            return curr
        res = fibonacci(curr - 1) + fibonacci(curr - 2)
        span.output = {"res": res}
        return res

def main_traced_example():
    with tracing.create_trace("my_fibonacci_trace"): # Creates a root span
        # This span will be a child of the "my_fibonacci_trace" root span
        with tracing.create_span("main_execution", metadata={"version": "1.0"}) as main_span:
            fib_result = fibonacci(5)
            main_span.output = {"final_fib_result": fib_result}
            print(f"Fibonacci(5) = {fib_result}")
```

##### 2\. Explicit Control

For scenarios where context managers aren't suitable, you can manually start and end spans. This approach requires more diligence to ensure all spans are properly ended and maintaining consistency.

**Manually Managing Spans (without an explicit Trace context):**

You can create spans and explicitly provide their `trace_id` and `parent_id` for fine-grained control. This is useful when integrating with existing systems that manage trace IDs.

```python
import uuid
import time
import random
from typing import Any, Dict
import scale_gp_beta.lib.tracing as tracing

class MockDatabase:
    def __init__(self) -> None:
        self._data = {
            "SELECT * FROM users WHERE id = 1;": {"id": 1, "name": "Alice"},
            "SELECT * FROM users WHERE id = 2;": {"id": 2, "name": "Bob"},
        }
    def execute_query(self, query: str, trace_id: str) -> Dict[str, Any]:
        db_span = tracing.create_span("db_query", input={"query": query}, trace_id=trace_id)
        db_span.start()
        try:
            time.sleep(random.uniform(0.1, 0.3)) # Simulate delay
            result = self._data.get(query, {})
            db_span.output = {"result": result}
            return result
        finally:
            db_span.end()

def get_user_from_db_explicit(db: MockDatabase, user_id: int, trace_id: str) -> Dict[str, Any]:
    with tracing.create_span("get_user_from_db", input={"user_id": user_id}, trace_id=trace_id):
        query = f"SELECT * FROM users WHERE id = {user_id};"
        return db.execute_query(query, trace_id)

def main_explicit_control_example():
    db = MockDatabase()
    my_trace_id = str(uuid.uuid4())
    # Manually create a root span
    main_span = tracing.create_span("main_explicit_call", metadata={"env": "local"}, trace_id=my_trace_id)
    main_span.start()
    try:
        user = get_user_from_db_explicit(db, 1, my_trace_id)
        print(f"Retrieved user: {user.get('name')}")
    finally:
        main_span.end()
```

**Exporting Existing Tracing Data (Manual Timestamps)**

You can even pre-define `start_time`, `end_time`, `span_id`, `parent_id`, and `trace_id` if you need to report historical data or reconstruct traces.

```python
import uuid
from datetime import datetime, timezone, timedelta
import scale_gp_beta.lib.tracing as tracing

parent_span_id = str(uuid.uuid4())
trace_id = str(uuid.uuid4())
child_span_id = str(uuid.uuid4())

now = datetime.now(timezone.utc)

# Parent Span
parent_span = tracing.create_span(
    "my_parent_span_name",
    input={"test": "input"},
    output={"test": "output"},
    metadata={"test": "metadata"},
    span_id=parent_span_id,
    trace_id=trace_id,
)
parent_span.start_time = (now - timedelta(minutes=10)).isoformat()
parent_span.end_time = now.isoformat()
parent_span.flush(blocking=True)

# Child Span
child_span = tracing.create_span(
    "my_child_span_name",
    input={"test": "another input"},
    output={"test": "another output"},
    metadata={"test": "another metadata"},
    span_id=child_span_id,
    trace_id=trace_id,
    parent_id=parent_span_id,
)
child_span.start_time = (now - timedelta(minutes=6)).isoformat()
child_span.end_time = (now - timedelta(minutes=2)).isoformat()
child_span.flush()
```

Note that `span.flush()` will by default block the main thread until the request has finished. Use `blocking=False` to enqueue the request which will be picked up by the background worker.

#### Helper Methods

You can retrieve the currently active span or trace in the execution context using `current_span()` and `current_trace()`:

```python
import scale_gp_beta.lib.tracing as tracing

def nested_function():
    with tracing.create_span("nested_operation"):
        current = tracing.current_span()
        if current:
            print(f"Currently active span: {current.name} (ID: {current.span_id})")
        current_t = tracing.current_trace()
        if current_t:
            print(f"Currently active trace: (ID: {current_t.trace_id})")
```

#### Flushing Tracing Data

Spans are generally batched and sent asynchronously by a background worker for efficiency. However, you might need to ensure all buffered spans are sent before an application exits or at critical points in your workflow (e.g., in a distributed worker setting).

You can force a synchronous flush of all queued spans using `flush_queue()` or on individual spans and traces (via their root span) with `span.flush()` & `trace.root_span.flush()`.

```python
import scale_gp_beta.lib.tracing as tracing

# ... (create some spans) ...

# Ensure all spans are sent before continuing
tracing.flush_queue()
print("All pending spans have been flushed.")
```

You do not need to manually flush all spans on program exit; when shutting down the background worker, we will attempt to flush all tracing data before exiting.

#### Configuration Options

| ENV Variable            | Description                                                                                                                                    |
|:------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------|
| `DISABLE_SCALE_TRACING` | If set, no tracing data will be exported. You can still observe tracing data programmatically via the No-Op variant of Trace and Span objects. |
| `SGP_API_KEY`           | SGP API Key. Used by `SGPClient`.                                                                                                              |
| `SGP_ACCOUNT_ID`        | SGP Account ID. Used by `SGPClient`.                                                                                                           |

#### Multi-Process / Multi-Worker Tracing

> **_WARNING:_** Developers should be careful when attempting tracing over multiple workers / Python processes. The SGP backend will expect well-formed trace data, and there is a strong chance of race conditions if a child span is reported before a parent span.

The easiest approach to working over multiple workers and Python processes is to only create one trace per worker. You can group traces with a `group_id`.

If you want to track an entire workflow over multiple workers, ensure you call `tracing.flush_queue()` before you enqueue a job which creates child spans of the current trace.

You will need to use the explicit controls to forward trace and parent span IDs to your workers. The automatic context detection works within the context of the original Python process only.


## Async usage

Simply import `AsyncSGPClient` instead of `SGPClient` and use `await` with each API call:

```python
import os
import asyncio
from scale_gp_beta import AsyncSGPClient

client = AsyncSGPClient(
    account_id="My Account ID",
    api_key=os.environ.get("SGP_API_KEY"),  # This is the default and can be omitted
    # defaults to "production".
    environment="development",
)


async def main() -> None:
    completion = await client.chat.completions.create(
        messages=[{"foo": "bar"}],
        model="model",
        top_k=2,
    )


asyncio.run(main())
```

Functionality between the synchronous and asynchronous clients is otherwise identical.

### With aiohttp

By default, the async client uses `httpx` for HTTP requests. However, for improved concurrency performance you may also use `aiohttp` as the HTTP backend.

You can enable this by installing `aiohttp`:

```sh
# install from PyPI
pip install --pre scale-gp-beta[aiohttp]
```

Then you can enable it by instantiating the client with `http_client=DefaultAioHttpClient()`:

```python
import asyncio
from scale_gp_beta import DefaultAioHttpClient
from scale_gp_beta import AsyncSGPClient


async def main() -> None:
    async with AsyncSGPClient(
        account_id="My Account ID",
        api_key="My API Key",
        http_client=DefaultAioHttpClient(),
    ) as client:
        completion = await client.chat.completions.create(
            messages=[{"foo": "bar"}],
            model="model",
            top_k=2,
        )


asyncio.run(main())
```

## Streaming responses

We provide support for streaming responses using Server Side Events (SSE).

```python
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)

stream = client.chat.completions.create(
    messages=[{"foo": "bar"}],
    model="model",
    stream=True,
)
for completion in stream:
    print(completion)
```

The async client uses the exact same interface.

```python
from scale_gp_beta import AsyncSGPClient

client = AsyncSGPClient(
    account_id="My Account ID",
)

stream = await client.chat.completions.create(
    messages=[{"foo": "bar"}],
    model="model",
    stream=True,
)
async for completion in stream:
    print(completion)
```

## Using types

Nested request parameters are [TypedDicts](https://docs.python.org/3/library/typing.html#typing.TypedDict). Responses are [Pydantic models](https://docs.pydantic.dev) which also provide helper methods for things like:

- Serializing back into JSON, `model.to_json()`
- Converting to a dictionary, `model.to_dict()`

Typed requests and responses provide autocomplete and documentation within your editor. If you would like to see type errors in VS Code to help catch bugs earlier, set `python.analysis.typeCheckingMode` to `basic`.

## Pagination

List methods in the Scale GP API are paginated.

This library provides auto-paginating iterators with each list response, so you do not have to request successive pages manually:

```python
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)

all_models = []
# Automatically fetches more pages as needed.
for model in client.models.list(
    limit=10,
):
    # Do something with model here
    all_models.append(model)
print(all_models)
```

Or, asynchronously:

```python
import asyncio
from scale_gp_beta import AsyncSGPClient

client = AsyncSGPClient(
    account_id="My Account ID",
)


async def main() -> None:
    all_models = []
    # Iterate through items across all pages, issuing requests as needed.
    async for model in client.models.list(
        limit=10,
    ):
        all_models.append(model)
    print(all_models)


asyncio.run(main())
```

Alternatively, you can use the `.has_next_page()`, `.next_page_info()`, or `.get_next_page()` methods for more granular control working with pages:

```python
first_page = await client.models.list(
    limit=10,
)
if first_page.has_next_page():
    print(f"will fetch next page using these details: {first_page.next_page_info()}")
    next_page = await first_page.get_next_page()
    print(f"number of items we just fetched: {len(next_page.items)}")

# Remove `await` for non-async usage.
```

Or just work directly with the returned data:

```python
first_page = await client.models.list(
    limit=10,
)

print(f"next page cursor: {first_page.starting_after}")  # => "next page cursor: ..."
for model in first_page.items:
    print(model.id)

# Remove `await` for non-async usage.
```

## Nested params

Nested parameters are dictionaries, typed using `TypedDict`, for example:

```python
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)

inference = client.inference.create(
    model="model",
    inference_configuration={},
)
print(inference.inference_configuration)
```

## File uploads

Request parameters that correspond to file uploads can be passed as `bytes`, or a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance or a tuple of `(filename, contents, media type)`.

```python
from pathlib import Path
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)

client.files.create(
    file=Path("/path/to/file"),
)
```

The async client uses the exact same interface. If you pass a [`PathLike`](https://docs.python.org/3/library/os.html#os.PathLike) instance, the file contents will be read asynchronously automatically.

## Handling errors

When the library is unable to connect to the API (for example, due to network connection problems or a timeout), a subclass of `scale_gp_beta.APIConnectionError` is raised.

When the API returns a non-success status code (that is, 4xx or 5xx
response), a subclass of `scale_gp_beta.APIStatusError` is raised, containing `status_code` and `response` properties.

All errors inherit from `scale_gp_beta.APIError`.

```python
import scale_gp_beta
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)

try:
    client.chat.completions.create(
        messages=[{"foo": "bar"}],
        model="model",
    )
except scale_gp_beta.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)  # an underlying Exception, likely raised within httpx.
except scale_gp_beta.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except scale_gp_beta.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
```

Error codes are as follows:

| Status Code | Error Type                 |
| ----------- | -------------------------- |
| 400         | `BadRequestError`          |
| 401         | `AuthenticationError`      |
| 403         | `PermissionDeniedError`    |
| 404         | `NotFoundError`            |
| 422         | `UnprocessableEntityError` |
| 429         | `RateLimitError`           |
| >=500       | `InternalServerError`      |
| N/A         | `APIConnectionError`       |

### Retries

Certain errors are automatically retried 2 times by default, with a short exponential backoff.
Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict,
429 Rate Limit, and >=500 Internal errors are all retried by default.

You can use the `max_retries` option to configure or disable retry settings:

```python
from scale_gp_beta import SGPClient

# Configure the default for all requests:
client = SGPClient(
    account_id="My Account ID",
    # default is 2
    max_retries=0,
)

# Or, configure per-request:
client.with_options(max_retries=5).chat.completions.create(
    messages=[{"foo": "bar"}],
    model="model",
)
```

### Timeouts

By default requests time out after 1 minute. You can configure this with a `timeout` option,
which accepts a float or an [`httpx.Timeout`](https://www.python-httpx.org/advanced/timeouts/#fine-tuning-the-configuration) object:

```python
from scale_gp_beta import SGPClient

# Configure the default for all requests:
client = SGPClient(
    account_id="My Account ID",
    # 20 seconds (default is 1 minute)
    timeout=20.0,
)

# More granular control:
client = SGPClient(
    account_id="My Account ID",
    timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0),
)

# Override per-request:
client.with_options(timeout=5.0).chat.completions.create(
    messages=[{"foo": "bar"}],
    model="model",
)
```

On timeout, an `APITimeoutError` is thrown.

Note that requests that time out are [retried twice by default](#retries).

## Advanced

### Logging

We use the standard library [`logging`](https://docs.python.org/3/library/logging.html) module.

You can enable logging by setting the environment variable `SGP_CLIENT_LOG` to `info`.

```shell
$ export SGP_CLIENT_LOG=info
```

Or to `debug` for more verbose logging.

### How to tell whether `None` means `null` or missing

In an API response, a field may be explicitly `null`, or missing entirely; in either case, its value is `None` in this library. You can differentiate the two cases with `.model_fields_set`:

```py
if response.my_field is None:
  if 'my_field' not in response.model_fields_set:
    print('Got json like {}, without a "my_field" key present at all.')
  else:
    print('Got json like {"my_field": null}.')
```

### Accessing raw response data (e.g. headers)

The "raw" Response object can be accessed by prefixing `.with_raw_response.` to any HTTP method call, e.g.,

```py
from scale_gp_beta import SGPClient

client = SGPClient(
    account_id="My Account ID",
)
response = client.chat.completions.with_raw_response.create(
    messages=[{
        "foo": "bar"
    }],
    model="model",
)
print(response.headers.get('X-My-Header'))

completion = response.parse()  # get the object that `chat.completions.create()` would have returned
print(completion)
```

These methods return an [`APIResponse`](https://github.com/scaleapi/sgp-python-beta/tree/main/src/scale_gp_beta/_response.py) object.

The async client returns an [`AsyncAPIResponse`](https://github.com/scaleapi/sgp-python-beta/tree/main/src/scale_gp_beta/_response.py) with the same structure, the only difference being `await`able methods for reading the response content.

#### `.with_streaming_response`

The above interface eagerly reads the full response body when you make the request, which may not always be what you want.

To stream the response body, use `.with_streaming_response` instead, which requires a context manager and only reads the response body once you call `.read()`, `.text()`, `.json()`, `.iter_bytes()`, `.iter_text()`, `.iter_lines()` or `.parse()`. In the async client, these are async methods.

```python
with client.chat.completions.with_streaming_response.create(
    messages=[{"foo": "bar"}],
    model="model",
) as response:
    print(response.headers.get("X-My-Header"))

    for line in response.iter_lines():
        print(line)
```

The context manager is required so that the response will reliably be closed.

### Making custom/undocumented requests

This library is typed for convenient access to the documented API.

If you need to access undocumented endpoints, params, or response properties, the library can still be used.

#### Undocumented endpoints

To make requests to undocumented endpoints, you can make requests using `client.get`, `client.post`, and other
http verbs. Options on the client will be respected (such as retries) when making this request.

```py
import httpx

response = client.post(
    "/foo",
    cast_to=httpx.Response,
    body={"my_param": True},
)

print(response.headers.get("x-foo"))
```

#### Undocumented request params

If you want to explicitly send an extra param, you can do so with the `extra_query`, `extra_body`, and `extra_headers` request
options.

#### Undocumented response properties

To access undocumented response properties, you can access the extra fields like `response.unknown_prop`. You
can also get all the extra fields on the Pydantic model as a dict with
[`response.model_extra`](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_extra).

### Configuring the HTTP client

You can directly override the [httpx client](https://www.python-httpx.org/api/#client) to customize it for your use case, including:

- Support for [proxies](https://www.python-httpx.org/advanced/proxies/)
- Custom [transports](https://www.python-httpx.org/advanced/transports/)
- Additional [advanced](https://www.python-httpx.org/advanced/clients/) functionality

```python
import httpx
from scale_gp_beta import SGPClient, DefaultHttpxClient

client = SGPClient(
    account_id="My Account ID",
    # Or use the `SGP_CLIENT_BASE_URL` env var
    base_url="http://my.test.server.example.com:8083",
    http_client=DefaultHttpxClient(
        proxy="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

You can also customize the client on a per-request basis by using `with_options()`:

```python
client.with_options(http_client=DefaultHttpxClient(...))
```

### Managing HTTP resources

By default the library closes underlying HTTP connections whenever the client is [garbage collected](https://docs.python.org/3/reference/datamodel.html#object.__del__). You can manually close the client using the `.close()` method if desired, or with a context manager that closes when exiting.

```py
from scale_gp_beta import SGPClient

with SGPClient(
    account_id="My Account ID",
) as client:
  # make requests here
  ...

# HTTP client is now closed
```

## Versioning

This package generally follows [SemVer](https://semver.org/spec/v2.0.0.html) conventions, though certain backwards-incompatible changes may be released as minor versions:

1. Changes that only affect static types, without breaking runtime behavior.
2. Changes to library internals which are technically public but not intended or documented for external use. _(Please open a GitHub issue to let us know if you are relying on such internals.)_
3. Changes that we do not expect to impact the vast majority of users in practice.

We take backwards-compatibility seriously and work hard to ensure you can rely on a smooth upgrade experience.

We are keen for your feedback; please open an [issue](https://www.github.com/scaleapi/sgp-python-beta/issues) with questions, bugs, or suggestions.

### Determining the installed version

If you've upgraded to the latest version but aren't seeing any new features you were expecting then your python environment is likely still using an older version.

You can determine the version that is being used at runtime with:

```py
import scale_gp_beta
print(scale_gp_beta.__version__)
```

## Requirements

Python 3.8 or higher.

## Contributing

See [the contributing documentation](./CONTRIBUTING.md).
