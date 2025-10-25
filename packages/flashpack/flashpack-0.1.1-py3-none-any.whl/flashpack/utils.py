import importlib.util
import logging
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager

import numpy as np
import torch
import torch.distributed as dist

logger = logging.getLogger("flashpack")


def maybe_init_distributed(
    rank: int | None = None,
    local_rank: int | None = None,
    world_size: int | None = None,
) -> None:
    """
    Initialize a distributed process group if it is not already initialized.
    """
    rank = rank or int(os.environ.get("RANK", 0))
    local_rank = local_rank or int(os.environ.get("LOCAL_RANK", rank))
    world_size = world_size or int(os.environ.get("WORLD_SIZE", 1))

    if not dist.is_initialized() and world_size > 1:
        dist.init_process_group(
            backend="nccl",
            init_method="env://",
            rank=rank,
            world_size=world_size,
            device_id=torch.device(f"cuda:{local_rank}"),
        )
        torch.cuda.set_device(torch.device(f"cuda:{local_rank}"))


def get_module_and_attribute(
    model: torch.nn.Module,
    name: str,
) -> tuple[torch.nn.Module, str]:
    """
    Get the module and attribute name from a full name.
    """
    module_path, _, name = name.rpartition(".")
    module = model.get_submodule(module_path)

    if module is None:
        raise ValueError(f"Module not found: {module_path}")

    return module, name


def string_to_dtype(string: str) -> torch.dtype:
    """
    Convert a string to a torch.dtype.
    """
    dtype = getattr(torch, string, None)
    if not isinstance(dtype, torch.dtype):
        raise ValueError(f"Unsupported dtype string in metadata: {string}")
    return dtype


def dtype_to_string(dtype: torch.dtype) -> str:
    """
    Convert a torch.dtype to a string.
    """
    if not isinstance(dtype, torch.dtype):
        raise ValueError(f"Unsupported dtype in metadata: {dtype}")
    return str(dtype).split(".")[1]


def torch_dtype_to_numpy_dtype(dtype: torch.dtype) -> np.dtype:
    """
    Convert a torch.dtype to a numpy.dtype.
    """
    mapping = {
        torch.float32: np.float32,
        torch.float64: np.float64,
        torch.float16: np.float16,
        torch.bfloat16: np.uint16,  # store raw bf16 bits as uint16 payload
        torch.int8: np.int8,
        torch.uint8: np.uint8,
        torch.int16: np.int16,
        torch.int32: np.int32,
        torch.int64: np.int64,
        torch.bool: np.bool_,
    }
    if dtype not in mapping:
        raise ValueError(f"Unsupported dtype for packing: {dtype}")
    return mapping[dtype]


def human_duration(seconds: float) -> str:
    """
    Convert a number of seconds to a human-readable duration.
    """
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f}ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f}µs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        return f"{seconds // 60:.0f}m{seconds % 60:.0f}s"
    else:
        return f"{seconds // 3600:.0f}h{seconds % 3600 // 60:.0f}m{seconds % 60:.0f}s"


def human_num_elements(elements: int) -> str:
    """
    Convert a number of elements to a human-readable number of elements.
    """
    if elements > 1e9:
        return f"{elements / 1e9:.2f}B"
    elif elements > 1e6:
        return f"{elements / 1e6:.2f}M"
    elif elements > 1e3:
        return f"{elements / 1e3:.2f}K"
    else:
        return f"{elements}"


@contextmanager
def timer(name: str, silent: bool = False) -> Iterator[None]:
    """
    Context manager to time a block of code.
    """
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    if not silent:
        print(f"{name}: {human_duration(end_time - start_time)}")


def is_ignored_tensor_name(
    name: str,
    ignore_names: list[str] | None = None,
    ignore_prefixes: list[str] | None = None,
    ignore_suffixes: list[str] | None = None,
) -> bool:
    """
    Check if a tensor name is ignored.
    """
    if ignore_names is not None and name in ignore_names:
        return True
    if ignore_prefixes is not None:
        for prefix in ignore_prefixes:
            if name.startswith(prefix):
                return True
    if ignore_suffixes is not None:
        for suffix in ignore_suffixes:
            if name.endswith(suffix):
                return True
    return False


def filter_state_dict(
    state_dict: dict[str, torch.Tensor],
    ignore_names: list[str] | None = None,
    ignore_prefixes: list[str] | None = None,
    ignore_suffixes: list[str] | None = None,
) -> dict[str, torch.Tensor]:
    """
    Filter a state dictionary to only include tensors that are not ignored.
    """
    return {
        name: tensor
        for name, tensor in state_dict.items()
        if not is_ignored_tensor_name(
            name, ignore_names, ignore_prefixes, ignore_suffixes
        )
    }


def diffusers_is_available() -> bool:
    """
    Check if diffusers is available.
    """
    return importlib.util.find_spec("diffusers") is not None


def transformers_is_available() -> bool:
    """
    Check if transformers is available.
    """
    return importlib.util.find_spec("transformers") is not None
