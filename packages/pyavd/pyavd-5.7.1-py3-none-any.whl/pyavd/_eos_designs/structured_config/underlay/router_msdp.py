# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdInvalidInputsError
from pyavd.j2filters import natural_sort

if TYPE_CHECKING:
    from . import AvdStructuredConfigUnderlayProtocol


class RouterMsdpMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def router_msdp(self: AvdStructuredConfigUnderlayProtocol) -> None:
        """
        Set the structured config for router_msdp.

        Used for to configure multicast anycast RPs for the underlay
        """
        if not self.shared_utils.underlay_multicast_pim_sm_enabled or not self.inputs.underlay_multicast_rps:
            return

        if self.inputs.underlay_multicast_anycast_rp.mode != "msdp":
            return

        peers = set()
        for rp_entry in self.inputs.underlay_multicast_rps:
            if len(rp_entry.nodes) < 2 or self.shared_utils.hostname not in rp_entry.nodes:
                continue

            # Anycast-RP using MSDP
            peers.update(node.name for node in rp_entry.nodes if node.name != self.shared_utils.hostname)

        if not peers:
            return

        self.structured_config.router_msdp.originator_id_local_interface = "Loopback0"
        for peer in natural_sort(peers):
            peer_facts = self.shared_utils.get_peer_facts(peer)
            # TODO: router_id is always set by method router_id in python-avd/pyavd/api/ip_addressing/__init__.py.
            if not peer_facts.router_id:
                msg = f"'router_id' is required but was not found for {peer}."
                raise AristaAvdInvalidInputsError(msg)
            self.structured_config.router_msdp.peers.append_new(
                ipv4_address=peer_facts.router_id,
                local_interface="Loopback0",
                description=peer,
                mesh_groups=EosCliConfigGen.RouterMsdp.PeersItem.MeshGroups([EosCliConfigGen.RouterMsdp.PeersItem.MeshGroupsItem(name="ANYCAST-RP")]),
            )
