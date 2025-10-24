from typing import Iterable
import warnings
try:
    from tqdm import tqdm
except ImportError:
    warnings.warn("Cannot import tqdm for verbose output", ImportWarning)
    pass


def wrap_verbose_loop(iter: Iterable, name: str = None, verbose: bool = False, **kwargs) -> Iterable:
    return tqdm(iter, desc=name, **kwargs) if verbose else iter
