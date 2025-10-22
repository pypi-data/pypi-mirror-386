"""burla_io - small utility helpers."""

from __future__ import annotations

import os
import itertools
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Mapping

__all__ = ["cd", "prepare_inputs", "__version__"]
__version__ = "0.3.0"


@contextmanager
def cd(path: str):
    """Temporarily change the working directory within a context.

    Example:
        with cd('/tmp'):
            ...
    """
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def prepare_inputs(params_to_test: Mapping[str, Iterable[Any]]) -> List[Dict[str, Any]]:
    """Create a list of param dictionaries from a cartesian product.

    Given a mapping of parameter names to iterables of values, returns a list
    of dictionaries representing the cartesian product of all combinations.
    """
    data: List[Dict[str, Any]] = []
    keys = list(params_to_test.keys())
    values = list(params_to_test.values())

    for combination in itertools.product(*values):
        param_dict = dict(zip(keys, combination))
        data.append(param_dict)
    return data

def chunk_inputs(inputs, chunk_size=None, num_workers=None):
    """
    Split a list into chunks and return a list of tuples containing each chunk.

    Args:
        inputs: List to be chunked
        chunk_size: Size of each chunk (optional)
        num_workers: Number of chunks to split into (optional)

    Returns:
        List of tuples, where each tuple contains one chunk (list)

    Note: Either chunk_size or num_workers must be specified, not both.
    """
    if (chunk_size is None) == (num_workers is None):
        raise ValueError("Exactly one of chunk_size or num_workers must be specified")

    if num_workers is not None:
        # Split into num_workers chunks
        chunk_size = len(inputs) // num_workers
        remainder = len(inputs) % num_workers

        data = []
        start = 0
        for i in range(num_workers):
            # Add one extra item to the first 'remainder' chunks
            end = start + chunk_size + (1 if i < remainder else 0)
            chunk = inputs[start:end]
            data.append((chunk,))
            start = end
        return data

    else:
        # Split by chunk_size
        data = []
        for i in range(0, len(inputs), chunk_size):
            chunk = inputs[i:i + chunk_size]
            data.append((chunk,))
        return data

def uv_pip_install(*packages, system=True, upgrade=False, extra_options: str):
    import subprocess
    import shlex

    cmd = ["uv", "pip", "install"]
    if system:
        cmd.append("--system")
    if upgrade:
        cmd.append("--upgrade")
    if extra_options:
        cmd.extend(shlex.split(extra_options))

    cmd.extend(packages)
    subprocess.run(cmd)
