# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdInvalidInputsError, AristaAvdMissingVariableError
from pyavd._utils import Undefined, get_ip_from_ip_prefix

if TYPE_CHECKING:
    from . import AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol


class RouterBgpMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def router_bgp(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol) -> None:
        """Set the structured config for router_bgp."""
        if not self.shared_utils.underlay_bgp:
            return
        for p2p_link, p2p_link_data in self._filtered_p2p_links:
            if not p2p_link.include_in_underlay_protocol and p2p_link.routing_protocol != "ebgp":
                continue

            if p2p_link_data["bgp_as"] is None or p2p_link_data["peer_bgp_as"] is None:
                msg = f"{self.data_model}.p2p_links.[].as or {self.data_model}.p2p_links_profiles.[].as"
                raise AristaAvdInvalidInputsError(msg)

            # RFC5549
            # When routing protocol is not set, we just add the neighbor_interface and continue.
            if self.inputs.underlay_rfc5549 and p2p_link.include_in_underlay_protocol and p2p_link.routing_protocol != "ebgp":
                self.structured_config.router_bgp.neighbor_interfaces.append_new(
                    name=p2p_link_data["interface"],
                    remote_as=p2p_link_data["peer_bgp_as"],
                    peer=p2p_link_data["peer"],
                    description=p2p_link_data["peer"],
                    peer_group=self.inputs.bgp_peer_groups.ipv4_underlay_peers.name,
                )
                continue

            # Regular BGP Neighbors
            if p2p_link_data["ip"] is None or p2p_link_data["peer_ip"] is None:
                msg = f"{self.data_model}.p2p_links.[].ip, .subnet or .ip_pool"
                raise AristaAvdMissingVariableError(msg)

            self.structured_config.router_bgp.neighbors.append_new(
                ip_address=get_ip_from_ip_prefix(p2p_link_data["peer_ip"]),
                remote_as=p2p_link_data["peer_bgp_as"],
                peer=p2p_link_data["peer"],
                description=p2p_link_data["peer"],
                peer_group=self.inputs.bgp_peer_groups.ipv4_underlay_peers.name if p2p_link.include_in_underlay_protocol else Undefined,
                bfd=p2p_link.bfd,
                local_as=p2p_link_data["bgp_as"] if p2p_link_data["bgp_as"] != self.shared_utils.bgp_as else None,
            )

            # For the combination of underlay-routing, rfc5549 and ebgp we will add the neighbor using the regular logic above,
            # but since it is also included in the underlay peer group which is configured for rfc5549,
            # we need to override the nexthop behavior for this neighbor.
            if self.inputs.underlay_rfc5549 and p2p_link.include_in_underlay_protocol and p2p_link.routing_protocol == "ebgp":
                address_family_ipv4_neighbor = EosCliConfigGen.RouterBgp.AddressFamilyIpv4.NeighborsItem(
                    ip_address=get_ip_from_ip_prefix(p2p_link_data["peer_ip"])
                )
                address_family_ipv4_neighbor.next_hop.address_family_ipv6.enabled = False
                self.structured_config.router_bgp.address_family_ipv4.neighbors.append(address_family_ipv4_neighbor)
