"""SubclassDict: A TypeDict that allows subclasses of type keys to be used as keys."""

__version__ = "0.1.1"

from subclassdict.subclassdict import SubclassDict
from subclassdict.subclasses import subclasses

__all__ = ["SubclassDict", "subclasses"]
