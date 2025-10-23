from typing import Dict, List, Any


class EnumOptions(object):
    """Base class for enum-like classes using class-attributes with string values to represent enum key/value pairs"""

    __cache = None

    @classmethod
    def values(cls) -> List[str]:
        """Extract list of enum-like options based on the derived classes' attributes.
        Any class attribute who's key doesn't start with an underscore and who's value is not a class method
         or callable is considered an option.
        Returns a list of attribute names representing the options.
        """
        if cls.__cache is None:
            cls.__cache = [
                v
                for k, v in vars(cls).items()
                if not k.startswith("_") and not callable(v) and not isinstance(v, classmethod)
            ]
        return cls.__cache


class Options(object):
    """Base class for an Options class which allow getting all class properties as a key/value mapping"""

    @classmethod
    def _all(cls) -> Dict[str, Any]:
        return {k: v for k, v in vars(cls) if not k.startswith("_")}
