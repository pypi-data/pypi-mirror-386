# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING

from pyavd._eos_designs.eos_designs_facts import EosDesignsFactsGenerator
from pyavd._eos_designs.shared_utils import SharedUtils
from pyavd._errors import AristaAvdError, AristaAvdMissingVariableError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ansible.template import Templar

    from pyavd._eos_designs.schema import EosDesigns
    from pyavd.api.pool_manager import PoolManager

    from .schema import EosDesignsFacts


def get_facts(
    all_inputs: dict[str, EosDesigns],
    all_hostvars: Mapping[str, Mapping],
    templar: Templar | None = None,
    pool_manager: PoolManager | None = None,
    digital_twin: bool = False,
) -> dict[str, EosDesignsFacts]:
    """
    Generate facts for all devices.

    Args:
        all_inputs: EosDesigns instances for each device.
        all_hostvars: Dictionaries with validated input vars.
        templar: Templater used to render custom jinja templates.
        pool_manager: instance of pool-manager used for dynamic assignments like node ids.
        digital_twin: Optional flag to enable avd_digital_twin_mode.

    Returns:
        EosDesignsFacts instances for each device.
    """
    peer_facts_generators: dict[str, EosDesignsFactsGenerator] = {}
    """Placeholder for generators. Referenced in the generators themselves as well as in shared_utils to be able to resolve facts for peers."""

    all_facts: dict[str, EosDesignsFacts] = {}
    """Placeholder for the final facts data to be returned."""

    for hostname, inputs in all_inputs.items():
        hostvars = all_hostvars.get(hostname, {})
        peer_facts_generators[hostname] = _create_generator_instance(hostname, inputs, hostvars, templar, pool_manager, digital_twin, peer_facts_generators)

    for generator in peer_facts_generators.values():
        generator.cross_pollinate()

    for hostname, generator in peer_facts_generators.items():
        try:
            all_facts[hostname] = generator.render()
        except AristaAvdMissingVariableError as e:  # noqa: PERF203
            raise AristaAvdMissingVariableError(variable=e.variable, host=e.host or hostname) from e
        except AristaAvdError as e:
            host = e.host if hasattr(e, "host") and e.host else hostname
            msg = f"{str(e).removesuffix('.')} for host '{host}'."
            raise type(e)(msg, host=host) from e

    return all_facts


def _create_generator_instance(
    hostname: str,
    inputs: EosDesigns,
    hostvars: Mapping,
    templar: Templar | None,
    pool_manager: PoolManager | None,
    digital_twin: bool,
    peer_facts_generators: dict[str, EosDesignsFactsGenerator],
) -> EosDesignsFactsGenerator:
    """Initialize SharedUtils and EosDesignsFactsGenerator and return the instance of the generator."""
    shared_utils = SharedUtils(
        hostname=hostname,
        hostvars=hostvars,
        inputs=inputs,
        templar=templar,
        peer_facts=peer_facts_generators,
        pool_manager=pool_manager,
        digital_twin=digital_twin,
    )
    return EosDesignsFactsGenerator(hostvars=hostvars, inputs=inputs, peer_generators=peer_facts_generators, shared_utils=shared_utils)
