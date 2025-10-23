# Depths Python Client SDK

A small, opinionated Python client that sends **OTLP JSON** over HTTP to the Depths telemetry server. It gives you simple tracing, logging, and metrics with a friendly Python API and automatic context linking.

This library is the **client** for the Depths Python telemetry server. It speaks the same OTLP JSON that the server ingests at `/v1/traces`, `/v1/logs`, and `/v1/metrics` with the `x-depths-project-id` header.

> Public entry point: `DepthsClient`. CamelCase aliases are provided so folks moving between TypeScript and Python feel at home. 

---

## Features

* Traces with nested spans using `with` and `async with`
* Logs that automatically carry `traceId` and `spanId` when a span is active
* Metrics: counter, gauge, and client-side histogram binning with explicit bounds and LRU capping
* Background flushing on a timer, plus synchronous `flush()` and `close()`
* Context propagation helpers: adopt or inject W3C `traceparent` header
* OTLP JSON envelopes on the wire and gzip for large payloads

---

## Installation

Can be installed as a standalone package

```bash
pip install depths-client
```

and also along with the main package:

```bash
pip install "depths[client]"
```

If you want proto extras as well, then do:
```bash
pip install "depths[all]"
```

---

## Quick start (sync)

```python
from depths_client import DepthsClient
import time

depths = DepthsClient(
    base_url="http://127.0.0.1:4318",
    project_id="proj_local",
    service_name="demo-sync",
    flush_interval_s=1.0,
    gzip=True,
)

orders = depths.metrics.counter("demo.orders")
queue  = depths.metrics.gauge("demo.queue_length")
latency = depths.metrics.histogram("demo.latency_ms")  # default 2-based bounds

with depths.with_trace("sync_flow") as trace:
    with trace.span("work_unit"):
        depths.log(level="INFO", body="starting work", attrs={"phase": "init"})
        orders.add(1, {"region": "in"})
        queue.record(3, {"shard": "a"})
        latency.record(37, {"route": "/health"})
        time.sleep(0.05)
        depths.log(level="INFO", body={"status": "ok"}, attrs={"phase": "done"})

depths.flush()
depths.close()
```

* `DepthsClient` requires `base_url`, `project_id`, and `service_name`. It builds OTLP resource attributes with `service.name`, `service.version`, `telemetry.sdk.name` and `telemetry.sdk.version`. 
* Logs inside a span are auto linked to the active context. 
* Metrics recorded inside a span carry `trace_id` and `span_id` in their attributes. 
* `flush()` is synchronous and drains queues immediately. 

---

## Quick start (async)

```python
import asyncio
from depths_client import DepthsClient

async def main():
    depths = DepthsClient(
        base_url="http://127.0.0.1:4318",
        project_id="proj_local",
        service_name="demo-async",
        flush_interval_s=1.0,
        gzip=True,
    )

    c = depths.metrics.counter("demo.orders")
    g = depths.metrics.gauge("demo.queue_length")
    h = depths.metrics.histogram("demo.latency_ms")

    async with depths.trace("async_flow") as trace:
        async with trace.span("awaited_work"):
            depths.log(level="INFO", body="async start", attrs={"phase": "init"})
            c.add(1, {"region": "in"})
            g.record(2, {"shard": "b"})
            h.record(12, {"route": "/ping"})
            await asyncio.sleep(0.05)
            depths.log(level="INFO", body={"status": "ok"}, attrs={"phase": "done"})

    await depths.aflush()
    await depths.aclose()

asyncio.run(main())
```

* Both sync and async context managers are supported for traces and spans. 
* `aflush()` and `aclose()` wrap synchronous operations so they can be awaited. 

---

## API overview

### `DepthsClient(...)`

```python
DepthsClient(
  base_url: str,
  project_id: str,
  service_name: str,
  service_version: str | None = None,
  resource: dict | None = None,
  flush_interval_s: float = 2.0,
  max_queue: int = 200,
  gzip: bool = True,
  auto_instrument_httpx: bool = False
)
```

* Builds an OTLP Resource with service info plus any extra `resource` attributes you pass. 
* Starts a background flusher thread that wakes on `flush_interval_s`. You can always call `flush()` to send data immediately. 
* Registers `atexit` to call `close()` as a safety net. 

**CamelCase aliases** for familiarity with the TypeScript SDK: `withTrace`, `withSpan`, `createTrace`, `adoptFromTraceparent`, `instrumentHttpx`, `flushAsync`, `closeAsync`. 

---

### Tracing

Create a root trace and nested spans:

```python
with depths.with_trace("checkout") as trace:
    with trace.span("load-cart"):
        ...
    with trace.span("payment") as span:
        span.add_event("payment.intent.created", {"provider": "stripe"})
```

* Root and child spans are context managed. The active `trace_id` and `span_id` are set when a span enters and cleared on exit. 
* `SpanHandle` supports `add_event`, `set_attributes`, `record_exception`, and `end`. CamelCase aliases are also available. 
* Spans are exported as OTLP spans with attributes, events and status. `OK` maps to code 1 and `ERROR` to 2. 

You can also create a handle directly:

```python
trace = depths.create_trace("sync-job", attrs={"job_id": "42"})
s1 = trace.start_span("phase-1"); ...; s1.end()
s2 = trace.start_span("phase-2"); ...; s2.end()
trace.end()
```



---

### Logs

```python
depths.log(level="INFO", body="message text", attrs={"key": "value"})
```

* If called inside an active span, the SDK includes the `traceId` and `spanId` in the log record. 
* Logs are exported as OTLP `logRecords` with a string or structured body and attributes. 

---

### Metrics

```python
# Counter (delta)
orders = depths.metrics.counter("orders.created")
orders.add(1, {"region": "eu"})

# Gauge (last value)
qlen = depths.metrics.gauge("queue.length")
qlen.record(5, {"shard": "a"})

# Histogram (client-side binning, delta)
latency = depths.metrics.histogram("http.server.latency_ms")  # explicit bounds optional
latency.record(37, {"route": "/checkout"})
```

* Counters export as OTLP `Sum` with delta temporality and monotonic true. Gauges export as OTLP `Gauge`. Histograms use explicit bounds and delta temporality. 
* Histogram bounds default to a 2-based sequence up to 65536, and you can override per instrument. Series are LRU capped per instrument by `max_series`. 
* When a span is active, the client adds `trace_id` and `span_id` as **metric attributes** automatically. 

Metrics are snapshotted and reset on each `flush` or `close`, then transported as a single batch.  

---

### Context propagation

Adopt an upstream trace:

```python
depths.adopt_from_traceparent(request.headers.get("traceparent"))
```

Inject into outgoing `httpx` calls:

```python
import httpx
client = httpx.Client()
depths.instrument_httpx(client)

resp = client.get("https://example.com/api")  # traceparent header is set if a span is active
```

* `adopt_from_traceparent` parses W3C headers and sets the active context.  
* `instrument_httpx` registers a request hook that writes `traceparent` from the current span. 

---

### Flushing and lifecycle

* The client keeps per-signal queues and a background thread that wakes on `flush_interval_s`. 
* `flush()` is synchronous and will drain and POST immediately. `aflush()` wraps this for async code.  
* `close()` does a final flush and stops the thread. `aclose()` wraps this for async code. `atexit` calls `close()` as a safety net.  

---

## How data is sent to the server

* Endpoints: `POST {base_url}/v1/traces | /v1/logs | /v1/metrics` with `content-type: application/json` and `x-depths-project-id` header from your client config. 
* JSON is compact. The client will gzip the payload when large. 
* On HTTP 413, the client splits a large batch once and retries. 

This matches the Depths Python telemetry server’s ingestion expectations. The server reads the project id from the header and accepts OTLP JSON at those routes.

---

## Defaults and limits

* Flush interval: 2.0 s, queue size: 200 per signal. 
* Histogram bounds: 2-based defaults; override per instrument. 
* Counter and gauge series LRU cap: 1024 entries per instrument (internal). Histogram LRU cap is configurable via `max_series`. 
* Strings in attributes are truncated at a safe size during sanitization. 

---

## Troubleshooting

* Only some signals appear: make sure you call `flush()` or `close()` at the end of your flow. Flush is synchronous and will send spans, logs, and metric deltas in one go. 
* Trace context not linked: ensure logs and metrics are recorded while a span is active. They auto attach `trace_id` and `span_id` when called inside `with ... span`.  
* No downstream correlation: call `instrument_httpx(client)` to inject `traceparent` on outgoing requests. 

---
