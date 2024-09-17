from typing import Any


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances: dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        else:
            instance = cls._instances[cls]
            instance.__init__(
                *args, **kwargs
            )  # Reinitialize the instance with new arguments
        return instance
