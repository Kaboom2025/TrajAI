# Configuration Reference

UnitAI is configured through TOML files and/or environment variables. No configuration is required to get started — all settings have sensible defaults.

---

## Configuration Sources

Settings are loaded in this order (highest priority first):

1. **Environment variables** (`UNITAI_*`)
2. **`unitai.toml`** (project root)
3. **`pyproject.toml`** `[tool.unitai]` section
4. **Built-in defaults**

---

## TOML Configuration

### In `pyproject.toml`

```toml
[tool.unitai]
default_n = 10
default_threshold = 0.95
max_workers = 5
cost_budget_per_test = 1.00
cost_budget_per_suite = 10.00
strict_mocks = true
cache_enabled = false
cache_directory = ".unitai/cache"
cache_ttl_hours = 168.0
junit_xml = "test-results/unitai.xml"
verbose = false
```

### In `unitai.toml`

Same keys, but at the top level (no `[tool.unitai]` wrapper):

```toml
default_n = 10
default_threshold = 0.95
strict_mocks = true
```

---

## Environment Variables

Every setting can be overridden via environment variables. These take the highest priority.

```bash
export UNITAI_DEFAULT_N=10
export UNITAI_DEFAULT_THRESHOLD=0.95
export UNITAI_MAX_WORKERS=5
export UNITAI_COST_BUDGET_PER_TEST=1.00
export UNITAI_COST_BUDGET_PER_SUITE=10.00
export UNITAI_MODEL_OVERRIDE=gpt-4o-mini
export UNITAI_STRICT_MOCKS=true
export UNITAI_CACHE_ENABLED=true
export UNITAI_CACHE_DIRECTORY=.unitai/cache
export UNITAI_CACHE_TTL_HOURS=168.0
export UNITAI_JUNIT_XML=test-results/unitai.xml
export UNITAI_VERBOSE=true
export UNITAI_ADAPTER=langgraph
```

Boolean values accept: `true`, `1`, `yes` (case-insensitive).

---

## Full Settings Reference

### Statistical Runner

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `default_n` | `int` | `10` | `UNITAI_DEFAULT_N` | Number of runs per statistical test |
| `default_threshold` | `float` | `0.95` | `UNITAI_DEFAULT_THRESHOLD` | Required pass rate (0.0 to 1.0) |
| `max_workers` | `int` | `5` | `UNITAI_MAX_WORKERS` | Max parallel threads for statistical runs |

### Cost Controls

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `cost_budget_per_test` | `float` | `1.00` | `UNITAI_COST_BUDGET_PER_TEST` | Max cost (USD) per individual test |
| `cost_budget_per_suite` | `float` | `10.00` | `UNITAI_COST_BUDGET_PER_SUITE` | Max cost (USD) per test suite |
| `model_override` | `str` | `""` | `UNITAI_MODEL_OVERRIDE` or `UNITAI_MODEL` | Force a specific LLM model for all tests |

### Mock Behavior

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `strict_mocks` | `bool` | `true` | `UNITAI_STRICT_MOCKS` | Raise `UnmockedToolError` when agent calls an unmocked tool |

When `strict_mocks` is `true` (the default), calling a tool that hasn't been mocked raises an error immediately. Set to `false` to allow unmocked tool calls to raise a standard `KeyError` instead.

### Cache / Replay

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `cache_enabled` | `bool` | `false` | `UNITAI_CACHE_ENABLED` | Enable LLM response caching |
| `cache_directory` | `str` | `".unitai/cache"` | `UNITAI_CACHE_DIRECTORY` | Directory for cached LLM responses |
| `cache_ttl_hours` | `float` | `168.0` | `UNITAI_CACHE_TTL_HOURS` | Cache entry time-to-live (hours). Default is 7 days. |

### Output

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `junit_xml` | `str` | `"test-results/unitai.xml"` | `UNITAI_JUNIT_XML` | Path for JUnit XML output |
| `verbose` | `bool` | `false` | `UNITAI_VERBOSE` | Enable verbose output |

### Adapter

| Setting | Type | Default | Env Var | Description |
|---------|------|---------|---------|-------------|
| `adapter` | `str` | `""` | `UNITAI_ADAPTER` | Force a specific adapter (e.g., `langgraph`, `crewai`) |

---

## Programmatic Access

Load the configuration in Python:

```python
from unitai.config import get_config, reload_config

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
export UNITAI_DEFAULT_N=5
export UNITAI_DEFAULT_THRESHOLD=0.9
export UNITAI_COST_BUDGET_PER_TEST=2.00
export UNITAI_CACHE_ENABLED=true
export UNITAI_CACHE_MODE=replay

unitai test --xml test-results/unitai.xml
```

Or in `pyproject.toml`:

```toml
[tool.unitai]
default_n = 5
default_threshold = 0.9
cost_budget_per_test = 2.00
cache_enabled = true
```
