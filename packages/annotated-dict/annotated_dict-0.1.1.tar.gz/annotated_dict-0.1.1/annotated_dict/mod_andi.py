from typing import Any
from flatten_dict import flatten


class Andi(dict):
    def __init__(self, **kwargs):
        for anno in self.__annotations__:
            # Check if the annotation has a default value in the class definition
            default_value = getattr(self.__class__, anno, None)
            self.__setattr__(anno, default_value)

        super().__init__()
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs.get(kwarg))

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __getattribute__(self, item):
        try:
            annotations = object.__getattribute__(self, '__class__').__annotations__
            for anno in annotations:
                if anno in self:
                    object.__setattr__(self, anno, self[anno])
        except (AttributeError, KeyError):
            pass
        return object.__getattribute__(self, item)

    def flatten(self,
                reducer: Any = "tuple",
                inverse: bool = False,
                max_flatten_depth: Any = None,
                enumerate_types: Any = (),
                keep_empty_types: Any = ()
                ) -> dict:
        return flatten(
            self,
            reducer,
            inverse,
            max_flatten_depth,
            enumerate_types,
            keep_empty_types
        )