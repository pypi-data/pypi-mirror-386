from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode, Trait


@dataclass(eq=False)
class MinMax(Trait):
    min: Any = 10
    max: Any = 30
    element_id: str = field(default_factory=lambda: "MinMaxTrait")

    _allowed_modes: set = field(default_factory=lambda: {ParameterMode.PROPERTY})

    def __init__(self, min_val: float, max_val: float) -> None:
        super().__init__()
        self.min = min_val
        self.max = max_val

    @classmethod
    def get_trait_keys(cls) -> list[str]:
        return ["min", "max", "minmax", "min_max"]

    def ui_options_for_trait(self) -> dict:
        return {"multiline": True}

    def display_options_for_trait(self) -> dict:
        return {}

    def converters_for_trait(self) -> list[Callable]:
        return []

    def validators_for_trait(self) -> list[Callable[..., Any]]:
        def validate(param: Parameter, value: Any) -> None:  # noqa: ARG001
            if value > self.max or value < self.min:
                msg = "Value out of range"
                raise ValueError(msg)

        return [validate]


# These Traits get added to a list on the parameter. When they are added they apply their functions to the parameter.
