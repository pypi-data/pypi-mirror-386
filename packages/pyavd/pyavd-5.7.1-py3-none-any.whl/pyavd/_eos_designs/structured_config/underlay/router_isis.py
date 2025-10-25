# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Protocol, cast

from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdInvalidInputsError
from pyavd._utils import default

if TYPE_CHECKING:
    from . import AvdStructuredConfigUnderlayProtocol


class RouterIsisMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def router_isis(self: AvdStructuredConfigUnderlayProtocol) -> None:
        """Set the structured config for router_isis."""
        if self.shared_utils.underlay_isis is not True:
            return

        self.structured_config.router_isis._update(
            instance=cast("str", self.shared_utils.isis_instance_name),
            log_adjacency_changes=True,
            net=self._isis_net,
            router_id=self.shared_utils.router_id if not self.inputs.use_router_general_for_router_id else None,
            is_type=default(self.shared_utils.node_config.is_type, self.inputs.isis_default_is_type),
        )
        self.structured_config.router_isis.address_family_ipv4._update(enabled=True, maximum_paths=self.inputs.isis_maximum_paths)

        if self.shared_utils.underlay_ldp is True:
            self.structured_config.router_isis.mpls_ldp_sync_default = True

        # TI-LFA
        if self.inputs.isis_ti_lfa.enabled:
            self.structured_config.router_isis.timers.local_convergence._update(delay=self.inputs.isis_ti_lfa.local_convergence_delay, protected_prefixes=True)

        match self.inputs.isis_ti_lfa.protection:
            case "link":
                ti_lfa_mode = "link-protection"
            case "node":
                ti_lfa_mode = "node-protection"
            case _:
                ti_lfa_mode = None

        if ti_lfa_mode:
            self.structured_config.router_isis.address_family_ipv4.fast_reroute_ti_lfa.mode = ti_lfa_mode

        # Overlay protocol
        if self.shared_utils.overlay_routing_protocol == "none":
            self.structured_config.router_isis.redistribute_routes.append_new(source_protocol="connected")

        if self.shared_utils.underlay_sr is True:
            self.structured_config.router_isis.advertise.passive_only = self.inputs.isis_advertise_passive_only
            # TODO: - enabling IPv6 only in SR cases as per existing behavior
            # but this could probably be taken out
            if self.shared_utils.underlay_ipv6 is True:
                self.structured_config.router_isis.address_family_ipv6._update(enabled=True, maximum_paths=self.inputs.isis_maximum_paths)
                if ti_lfa_mode:
                    self.structured_config.router_isis.address_family_ipv6.fast_reroute_ti_lfa.mode = ti_lfa_mode
            self.structured_config.router_isis.segment_routing_mpls._update(router_id=self.shared_utils.router_id, enabled=True)

    @cached_property
    def _isis_net(self: AvdStructuredConfigUnderlayProtocol) -> str | None:
        if self.inputs.isis_system_id_format == "node_id":
            isis_system_id_prefix = self.shared_utils.node_config.isis_system_id_prefix
            if self.shared_utils.underlay_isis is True and isis_system_id_prefix is None:
                msg = (
                    f"'isis_system_id_prefix' is required when 'isis_system_id_format' is set to 'node_id'."
                    f" 'isis_system_id_prefix' was not set for '{self.shared_utils.hostname}'"
                )
                raise AristaAvdInvalidInputsError(msg)

            # This condition is not covered by current tests but is retained for potential unexpected behavior.
            if self.shared_utils.id is None:
                msg = f"'id' is not set on '{self.shared_utils.hostname}' and is required to set ISIS NET address using the node ID"
                raise AristaAvdInvalidInputsError(msg)
            system_id = f"{isis_system_id_prefix}.{self.shared_utils.id:04d}"
        else:
            system_id = self.ipv4_to_isis_system_id(cast("str", self.shared_utils.router_id))

        isis_area_id = self.inputs.isis_area_id
        return f"{isis_area_id}.{system_id}.00"

    @staticmethod
    def ipv4_to_isis_system_id(ipv4_address: str) -> str:
        """
        Converts an IPv4 address into an IS-IS system-id.

        Examples:
        192.168.0.1 -> 1921.6800.0001
        10.0.0.3 -> 0100.0000.0003
        """
        octets = str(ipv4_address).split(".")
        padded_addr = octets[0].zfill(3) + octets[1].zfill(3) + octets[2].zfill(3) + octets[3].zfill(3)
        return ".".join(padded_addr[i : i + 4] for i in range(0, len(padded_addr), 4))
