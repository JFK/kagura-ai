# CLI Performance

Kagura CLI uses lazy loading to ensure fast startup times.

## Startup Performance

**Before optimization**: `kagura --help` took **8.8 seconds**

**After optimization**: `kagura --help` takes **0.1 seconds** (98.9% faster!)

## How It Works

### Lazy Loading

Subcommands are imported only when invoked:

```python
# Before (slow)
from .mcp import mcp          # Always imported - 393ms!
from .monitor import monitor  # Always imported

# After (fast)
@click.group(cls=LazyGroup, lazy_subcommands={
    "mcp": ("kagura.cli.mcp", "mcp", "MCP commands"),     # Import on demand
    "monitor": ("kagura.cli.monitor", "monitor", "Monitor telemetry"),
})
```

**Benefits**:
- `kagura --help`: No heavy modules loaded
- `kagura chat`: Only chat module loaded
- `kagura mcp start`: Only MCP module loaded

### Module-level Lazy Imports

The main `kagura` package also uses lazy imports via `__getattr__`:

```python
# kagura/__init__.py

def __getattr__(name: str):
    """Lazy import attributes on demand"""
    if name == "agent":
        from .core.decorators import agent
        return agent
    # ...
```

**Benefits**:
- CLI startup doesn't load decorators, memory, etc.
- User code loads only what it needs

## Performance Metrics

| Command | Before | After | Improvement |
|---------|--------|-------|-------------|
| `kagura --help` | 8.8s | 0.1s | 98.9% faster |
| `kagura version` | 8.8s | 0.1s | 98.9% faster |
| `kagura chat` | 8.8s | 0.5s | 94.3% faster |
| `kagura mcp start` | 8.8s | 1.0s | 88.6% faster |

## Adding New Commands

When adding a new CLI command, use lazy loading to maintain performance:

```python
# src/kagura/cli/main.py

@click.group(cls=LazyGroup, lazy_subcommands={
    # Add your command here
    "mycommand": ("kagura.cli.mycommand", "mycommand", "My command description"),
})
def cli():
    pass
```

**Guidelines**:
1. Always add new commands to `lazy_subcommands`
2. Provide a short description (third tuple element)
3. Avoid top-level imports in `main.py`

## Benchmarking

### Measure Startup Time

```bash
# Overall time
time kagura --help

# Import time only
python -c "
import time
start = time.time()
from kagura.cli.main import cli
print(f'Import: {(time.time()-start)*1000:.0f}ms')
"
```

### Profile Imports

```bash
# Detailed import profiling
python -X importtime -c "from kagura.cli.main import cli" 2>&1 | tail -50
```

### Expected Results

- CLI import: **< 50ms**
- `kagura --help`: **< 200ms**
- No heavy modules (mcp, observability) loaded on `--help`

## Troubleshooting

### Q: My command is slow to start

A: Check if you're importing heavy modules at the top level:

```python
# Bad - imports immediately
from heavy_module import something

@click.command()
def mycommand():
    pass

# Good - imports on execution
@click.command()
def mycommand():
    from heavy_module import something  # Import here
    pass
```

### Q: How do I know if a module is heavy?

A: Use `python -X importtime`:

```bash
python -X importtime -c "import my_module" 2>&1 | tail -20
```

Look for cumulative times > 100ms.

### Q: Can I disable lazy loading?

A: Not recommended, but you can import modules explicitly in `main.py`:

```python
# Not recommended - slow startup
from .mcp import mcp
from .monitor import monitor
# ...

cli.add_command(mcp)
cli.add_command(monitor)
```

## Best Practices

1. **Always use lazy loading** for CLI commands
2. **Import heavy modules inside functions**, not at module level
3. **Test startup time** in CI (see `tests/cli/test_lazy_loading.py`)
4. **Profile regularly** to catch regressions

## Future Improvements

- Pre-compiled bytecode (`.pyc`) optimization
- Startup profiling in CI
- Dynamic help text loading
