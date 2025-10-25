# Benchmarking Pipelines

Benchmarking lets you monitor the latency cost of every step in a pipeline so you can detect regressions before shipping to production. Leksara provides first-class support for benchmarking through both the functional API and the `ReviewChain` class.

---

## Enabling benchmarks

Benchmarks are disabled by default. Toggle them when invoking `leksara(...)` or any `ReviewChain` entrypoint by passing `benchmark=True`.

```python
from leksara import leksara

texts = [
    "Barangnya bagus tapi email saya user@example.com",
    "Rating 5/5, kurir ramah banget!",
]

cleaned, metrics = leksara(texts, preset="ecommerce_review", benchmark=True)

print(cleaned)
print(metrics)
```

The `metrics` dictionary contains:

- `n_steps`: total number of functions and pattern detectors executed.
- `total_time_sec`: end-to-end duration.
- `per_step`: ordered list of `(step_name, seconds)` pairs.

---

## Using `ReviewChain` with benchmarks

```python
from leksara import ReviewChain
from leksara.function import case_normal
from leksara.pattern import replace_phone, replace_email

chain = ReviewChain.from_steps(
    patterns=[(replace_phone, {"mode": "replace"}), (replace_email, {"mode": "replace"})],
    functions=[case_normal],
)

results, metrics = chain.transform([
    "Hubungi +62 812-3333-4444, email sales@shop.id",
], benchmark=True)

print(results[0])
print(metrics["per_step"])
```

`ReviewChain.process_text` and `ReviewChain.run_on_series` expose the same `benchmark` flag. Use the variant that best matches your workload.

---

## Persisting benchmark results

Benchmarks return plain Python types, making it easy to store them alongside other diagnostics:

```python
import json
from pathlib import Path

output, metrics = leksara(texts, preset="ecommerce_review", benchmark=True)

Path("benchmark.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

You can also emit the data to observability systems (Grafana, Datadog, Prometheus) by converting each `per_step` entry into a custom metric. Combine this with the logging helpers described in `features.md`.

---

## Best practices

- **Run benchmarks in CI** – Add a smoke test that asserts maximum acceptable `total_time_sec`. This guards against accidental slowdowns when dictionaries grow or regex patterns change.
- **Compare presets and custom pipelines** – Inspect `per_step` to decide whether a custom pipeline offers enough benefit over a preset.
- **Diagnose slow resources** – If a specific step suddenly spikes, verify whether optional dependencies (for example `regex` or `emoji`) are installed with compatible versions.
- **Tune chunk sizes** – When running on streaming data, benchmark representative batches (10–100 reviews) to understand warm-up effects and cache behaviour.

---

## Related documentation

- `features.md` – “ReviewChain & leksara orchestrators” section describes how benchmarking interacts with whitelists.
- `examples.md` – Recipe 4 demonstrates returning benchmark payloads from a streaming job.
- `usage.md` – Shows how to integrate benchmarks with Pandas workflows.
