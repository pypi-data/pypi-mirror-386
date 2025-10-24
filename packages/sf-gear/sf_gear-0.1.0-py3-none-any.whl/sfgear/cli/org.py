from typing import Any, Dict
from ..utils import sf_run


def display(alias: str) -> Dict[str, Any]:
    """Run `sf org display` for the given alias and return the result as a dict.

    This helper is universal and does not print; it raises RuntimeError on failure.
    """
    return sf_run('org display', {'target-org': alias})
