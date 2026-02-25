# Configuration Reference

TrajAI is configured through TOML files and/or environment variables. No configuration is required to get started — all settings have sensible defaults.

---

## Configuration Sources

Settings are loaded in this order (highest priority first):

1. **Environment variables** (`TRAJAI_*`)
2. **`trajai.toml`** (project root)
3. **`pyproject.toml`** `[tool.trajai]` section
4. **Built-in defaults**

---

## TOML Configuration

### In `pyproject.toml`

```toml
[tool.trajai]
default_n = 10
default_threshold = 0.95
max_workers = 5
cost_budget_per_test = 1.00
cost_budget_per_suite = 10.00
strict_mocks = true
cache_enabled = false
cache_directory = ".trajai/cache"
cache_ttl_hours = 168.0
junit_xml = "test-results/trajai.xml"
verbose = false
```

### In `trajai.toml`

Same keys, but at the top level (no `[tool.trajai]` wrapper):

```toml
default_n = 10
default_threshold = 0.95
strict_mocks = true
```

---

## Environment Variables

Every setting can be overridden via environment variables. These take the highest priority.

```bash
export TRAJAI_DEFAULT_N=10
export TRAJAI_DEFAULT_THRESHOLD=0.95
export TRAJAI_MAX_WORKERS=5
export TRAJAI_COST_BUDGET_PER_TEST=1.00
export TRAJAI_COST_BUDGET_PER_SUITE=10.00
export TRAJAI_MODEL_OVERRIDE=gpt-4o-mini
export TRAJAI_STRICT_MOCKS=true
export TRAJAI_CACHE_ENABLED=true
export TRAJAI_CACHE_DIRECTORY=.trajai/cache
export TRAJAI_CACHE_TTL_HOURS=168.0
export TRAJAI_JUNIT_XML=test-results/trajai.xml
export TRAJAI_VERBOSE=true
export TRAJAI_ADAPTER=langgraph
```

Boolean values accept: `true`, `1`, `yes` (case-insensitive).

---

## Full Settings Reference

### Statistical Runner

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `default_n` | `int` | `10` | `TRAJAI_DEFAULT_N` | Number of runs per statistical test |
| `default_threshold` | `float` | `0.95` | `TRAJAI_DEFAULT_THRESHOLD` | Required pass rate (0.0 to 1.0) |
| `max_workers` | `int` | `5` | `TRAJAI_MAX_WORKERS` | Max parallel threads for statistical runs |

### Cost Controls

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `cost_budget_per_test` | `float` | `1.00` | `TRAJAI_COST_BUDGET_PER_TEST` | Max cost (USD) per individual test |
| `cost_budget_per_suite` | `float` | `10.00` | `TRAJAI_COST_BUDGET_PER_SUITE` | Max cost (USD) per test suite |
| `model_override` | `str` | `""` | `TRAJAI_MODEL_OVERRIDE` or `TRAJAI_MODEL` | Force a specific LLM model for all tests |

### Mock Behavior

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `strict_mocks` | `bool` | `true` | `TRAJAI_STRICT_MOCKS` | Raise `UnmockedToolError` when agent calls an unmocked tool |

When `strict_mocks` is `true` (the default), calling a tool that hasn't been mocked raises an error immediately. Set to `false` to allow unmocked tool calls to raise a standard `KeyError` instead.

### Cache / Replay

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `cache_enabled` | `bool` | `false` | `TRAJAI_CACHE_ENABLED` | Enable LLM response caching |
| `cache_directory` | `str` | `".trajai/cache"` | `TRAJAI_CACHE_DIRECTORY` | Directory for cached LLM responses |
| `cache_ttl_hours` | `float` | `168.0` | `TRAJAI_CACHE_TTL_HOURS` | Cache entry time-to-live (hours). Default is 7 days. |

### Output

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `junit_xml` | `str` | `"test-results/trajai.xml"` | `TRAJAI_JUNIT_XML` | Path for JUnit XML output |
| `verbose` | `bool` | `false` | `TRAJAI_VERBOSE` | Enable verbose output |

### Adapter

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `adapter` | `str` | `""` | `TRAJAI_ADAPTER` | Force a specific adapter (e.g., `langgraph`, `crewai`) |

---

## Programmatic Access

Load the configuration in Python:

```python
from trajai.config import get_config, reload_config

config = get_config()
print(config.default_n)         # 10
print(config.strict_mocks)      # True
print(config.cost_budget_per_test)  # 1.0

# Reload after changing env vars or files
config = reload_config()
```

---

## Example: CI Configuration

A typical CI setup using environment variables:

```bash
# In your CI environment
export TRAJAI_DEFAULT_N=5
export TRAJAI_DEFAULT_THRESHOLD=0.9
export TRAJAI_COST_BUDGET_PER_TEST=2.00
export TRAJAI_CACHE_ENABLED=true
export TRAJAI_CACHE_MODE=replay

trajai test --xml test-results/trajai.xml
```

Or in `pyproject.toml`:

```toml
[tool.trajai]
default_n = 5
default_threshold = 0.9
cost_budget_per_test = 2.00
cache_enabled = true
```
