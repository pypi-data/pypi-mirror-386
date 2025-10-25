# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, Literal, Protocol, cast, overload

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.avdfacts import AvdFacts, AvdFactsProtocol
from pyavd._utils.get import get_v2

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import TypeVar

    from typing_extensions import Self

    from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFacts
    from pyavd._eos_designs.schema import EosDesigns
    from pyavd._eos_designs.shared_utils import SharedUtilsProtocol

    T_StructuredConfigGeneratorSubclass = TypeVar("T_StructuredConfigGeneratorSubclass", bound="StructuredConfigGeneratorProtocol")


# Overload when assigned with args.
@overload
def structured_config_contributor(
    func: None = None, *, toggle_and_value: tuple[str, bool] | None = None
) -> Callable[[Callable[[T_StructuredConfigGeneratorSubclass], None]], Callable[[T_StructuredConfigGeneratorSubclass], None]]: ...


# Overload when assigned without args.
@overload
def structured_config_contributor(func: Callable[[T_StructuredConfigGeneratorSubclass], None]) -> Callable[[T_StructuredConfigGeneratorSubclass], None]: ...


def structured_config_contributor(
    func: Callable[[T_StructuredConfigGeneratorSubclass], None] | None = None, *, toggle_and_value: tuple[str, bool] | None = None
) -> (
    Callable[[T_StructuredConfigGeneratorSubclass], None]
    | Callable[[Callable[[T_StructuredConfigGeneratorSubclass], None]], Callable[[T_StructuredConfigGeneratorSubclass], None]]
):
    """
    Decorator to mark methods that contribute to the structured config.

    The decorator can be attached with or without args:
        ```
        @structured_config_contributor
        def ...
        ```
        or
        ```
        @structured_config_contributor(toggle_and_value=("avd_6_behaviors.snmp_settings.vrfs", True))
        def ...
        ```

    Args:
        func: The method to decorate.
        toggle_and_value: A tuple of variable path and expected value, deciding if this method should run.
            The path is a string like `avd_6_behaviors.snmp_settings_vrfs`, pointing to the feature toggle.

    TODO: Store the functions in a class variable on StructuredConfigGeneratorProtocol instead of modifying the func.
    """

    def decorator(fnc: Callable[[T_StructuredConfigGeneratorSubclass], None]) -> Callable[[T_StructuredConfigGeneratorSubclass], None]:
        """Inner actual decorator. Nested to handle assignment both with and without args."""
        fnc._is_structured_config_contributor = True  # pyright: ignore [reportFunctionMemberAccess]
        if toggle_and_value is None:
            return fnc

        toggle, toggle_value = toggle_and_value

        @wraps(fnc)
        def wrapped_func(self: T_StructuredConfigGeneratorSubclass) -> None:
            if get_v2(self.inputs, toggle, default=False) == toggle_value:
                return fnc(self)

            return None

        return wrapped_func

    if func is not None:
        # This is a @structured_config_contributor assignment without args.
        return decorator(func)

    # This is a @structured_config_contributor(...) assignment with args.
    return decorator


@dataclass
class StructCfgs:
    """
    Snips of structured config gathered during structured config generation.

    The snips comes from the `structured_config` input fields in various data models.
    """

    root: list[EosCliConfigGen] = field(default_factory=list)
    nested: EosCliConfigGen = field(default_factory=EosCliConfigGen)
    list_merge_strategy: Literal["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"] = "append_unique"

    @classmethod
    def new_from_ansible_list_merge_strategy(cls, ansible_strategy: Literal["replace", "append", "keep", "prepend", "append_rp", "prepend_rp"]) -> StructCfgs:
        merge_strategy_map = {
            "append_rp": "append_unique",
            "prepend_rp": "prepend_unique",
        }
        list_merge_strategy = merge_strategy_map.get(ansible_strategy, ansible_strategy)
        if list_merge_strategy not in ["append_unique", "append", "replace", "keep", "prepend", "prepend_unique"]:
            msg = f"Unsupported list merge strategy: {ansible_strategy}"
            raise ValueError(msg)

        list_merge_strategy = cast("Literal['append_unique', 'append', 'replace', 'keep', 'prepend', 'prepend_unique']", list_merge_strategy)
        return cls(list_merge_strategy=list_merge_strategy)


class StructuredConfigGeneratorProtocol(AvdFactsProtocol, Protocol):
    """
    Protocol for the StructuredConfigGenerator base class for structured config generators.

    This differs from AvdFacts by also taking structured_config and custom_structured_configs as argument
    and by the render function which updates the structured_config instead of
    returning a dict.
    """

    facts: EosDesignsFacts
    structured_config: EosCliConfigGen
    custom_structured_configs: StructCfgs
    _complete_structured_config: EosCliConfigGen
    """
    Temporary store of the complete structured config in case this module is still using the legacy duplication check.

    See render() for details.
    """

    def render(self) -> None:
        """
        In-place update self.structured_config.

        If 'avd_eos_designs_enforce_duplication_checks_across_all_models' is `true` (new behavior for AVD 6.0.0 (?)),
        all code is updating the same instance of self.structured_config.
        Otherwise a fresh structured_config instance is initialized for each module, and they are deepmerged on top of the final structured_config.
        """
        if not self.inputs.avd_eos_designs_enforce_duplication_checks_across_all_models and not getattr(
            self, "ignore_avd_eos_designs_enforce_duplication_checks_across_all_models", False
        ):
            self._complete_structured_config = self.structured_config
            self.structured_config = EosCliConfigGen()

        # In-place update self.structured_config by calling all methods marked with @structured_config_contributor
        self.render_structured_config()

        # If we run with the legacy behavior we now have to restore the original structured config and merge in the things we generated here.
        if not self.inputs.avd_eos_designs_enforce_duplication_checks_across_all_models and not getattr(
            self, "ignore_avd_eos_designs_enforce_duplication_checks_across_all_models", False
        ):
            module_structured_config = self.structured_config
            self.structured_config = self._complete_structured_config
            self.structured_config._deepmerge(module_structured_config, list_merge="append_unique")

    def render_structured_config(self) -> None:
        """
        Execute all class methods marked with @structured_config_contributor decorator.

        Each method will in-place update self.structured_config.
        """
        for method in self.structured_config_methods():
            method(self)

    @classmethod
    def structured_config_methods(cls) -> list[Callable[[Self], None]]:
        """Return the list of methods decorated with 'structured_config_contributor'."""
        return [method for key in cls._keys() if getattr(method := getattr(cls, key), "_is_structured_config_contributor", False)]


class StructuredConfigGenerator(AvdFacts, StructuredConfigGeneratorProtocol):
    """
    Base class for structured config generators.

    This differs from AvdFacts by also taking structured_config and custom_structured_configs as argument
    """

    def __init__(
        self,
        hostvars: Mapping,
        inputs: EosDesigns,
        facts: EosDesignsFacts,
        shared_utils: SharedUtilsProtocol,
        structured_config: EosCliConfigGen,
        custom_structured_configs: StructCfgs,
    ) -> None:
        self.facts = facts
        self.structured_config = structured_config
        self.custom_structured_configs = custom_structured_configs
        super().__init__(hostvars=hostvars, inputs=inputs, shared_utils=shared_utils)
