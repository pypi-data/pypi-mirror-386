# burla_io

Tiny utilities you can import for working with `burla`.

## Install (local)

From this folder, run:

```
pip install .
```

Or for development/editable mode:

```
pip install -e .
```

## Usage

```
from burla_io import cd, prepare_inputs

with cd("/tmp"):
    ...  # do work in /tmp

combos = prepare_inputs({
    "lr": [1e-3, 1e-4],
    "batch": [16, 32],
})
# combos -> [
#   {"lr": 0.001, "batch": 16},
#   {"lr": 0.001, "batch": 32},
#   {"lr": 0.0001, "batch": 16},
#   {"lr": 0.0001, "batch": 32},
# ]
```

## License

MIT
