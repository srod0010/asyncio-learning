# AsyncIO Code Examples

## Setup (Python virtual environment)

Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Verify you are using the virtual environment

```bash
which python
python --version
python -m pip --version
```

`which python` should point to:

`/Users/saviorodrigues/Documents/AsyncIO-Code-Examples/.venv/bin/python`

## Run examples

```bash
python real_world_example_sync_v1.py
python real_world_example_async_v1.py
python real_world_example_async_v2.py
python real_world_example_async_v3.py
```

## Deactivate virtual environment

```bash
deactivate
```

## Common command mistake

Do not run:

```bash
./.venv/bin/python -m python3 -m pip install -r requirements.txt
```

Use either:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

or (after activation):

```bash
python -m pip install -r requirements.txt
```
