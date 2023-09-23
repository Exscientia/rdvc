import warnings
from typing import Union


def get_stamped_version() -> Union[str, None]:
    try:
        # pylint: disable=import-outside-toplevel
        from ._version import version as stamped_version

        return stamped_version
    except ImportError:
        warnings.warn(f"could not determine {__name__} package version - have you run `pip install -e.` ?")
        return None


__version__ = get_stamped_version()
