# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from functools import cached_property
from ipaddress import ip_network
from itertools import islice
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar, cast

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError, AristaAvdMissingVariableError
from pyavd._utils import default, get_ip_from_pool
from pyavd._utils.password_utils.password import isis_encrypt

if TYPE_CHECKING:
    from . import AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol

T_P2pLinksItem = TypeVar("T_P2pLinksItem", EosDesigns.CoreInterfaces.P2pLinksItem, EosDesigns.L3Edge.P2pLinksItem)
T_P2pLinksProfiles = TypeVar("T_P2pLinksProfiles", EosDesigns.CoreInterfaces.P2pLinksProfiles, EosDesigns.L3Edge.P2pLinksProfiles)
T_Ptp = TypeVar("T_Ptp", EosCliConfigGen.EthernetInterfacesItem.Ptp, EosCliConfigGen.PortChannelInterfacesItem.Ptp)


class UtilsMixin(Protocol):
    """
    Mixin Class with internal functions.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @cached_property
    def _filtered_p2p_links(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol) -> list[tuple[T_P2pLinksItem, dict]]:
        """
        Returns a filtered list of p2p_links, which only contains links with our hostname.

        For each links any referenced profiles are applied and IP addresses are resolved
        from pools or subnets.
        """
        if not self.inputs_data.p2p_links:
            return []

        # Apply p2p_profiles if set. Silently ignoring missing profile.
        p2p_links: list[T_P2pLinksItem] = [self._apply_p2p_links_profile(p2p_link) for p2p_link in cast("list[T_P2pLinksItem]", self.inputs_data.p2p_links)]

        # Filter to only include p2p_links with our hostname under "nodes"
        p2p_links = [p2p_link for p2p_link in p2p_links if self.shared_utils.hostname in p2p_link.nodes]
        if not p2p_links:
            return []

        # Resolve IPs from subnet or p2p_pools.
        p2p_links = [self._resolve_p2p_ips(p2p_link) for p2p_link in p2p_links]

        # Parse P2P data model and create simplified data
        return [(p2p_link, self._get_p2p_data(p2p_link)) for p2p_link in p2p_links]

    def _apply_p2p_links_profile(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link: T_P2pLinksItem) -> T_P2pLinksItem:
        """Apply a profile to a p2p_link. Always returns a new instance. TODO: Raise if profile is missing."""
        if not p2p_link.profile or p2p_link.profile not in self.inputs_data.p2p_links_profiles:
            # Nothing to do
            return p2p_link._deepcopy()

        profile_as_p2p_link_item = self.inputs_data.p2p_links_profiles[p2p_link.profile]._cast_as(type(p2p_link), ignore_extra_keys=True)
        return p2p_link._deepinherited(profile_as_p2p_link_item)

    def _resolve_p2p_ips(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link: T_P2pLinksItem) -> T_P2pLinksItem:
        if p2p_link.ip:
            # ip already set, so nothing to do
            return p2p_link

        if p2p_link.subnet:
            # Resolve IPs from subnet
            network = ip_network(p2p_link.subnet, strict=False)
            p2p_link.ip.extend([f"{ip}/{network.prefixlen}" for ip in islice(network.hosts(), 2)])

        elif p2p_link.ip_pool and p2p_link.id and p2p_link.ip_pool in self.inputs_data.p2p_links_ip_pools:
            # Subnet not set but we have what we need to resolve IPs from pool.
            ip_pool = self.inputs_data.p2p_links_ip_pools[p2p_link.ip_pool]
            if not ip_pool.ipv4_pool:
                # The pool was missing ipv4_pool so we give up.
                return p2p_link

            p2p_link.ip.extend(
                [f"{get_ip_from_pool(ip_pool.ipv4_pool, ip_pool.prefix_size, p2p_link.id - 1, host_offset)}/{ip_pool.prefix_size}" for host_offset in [0, 1]]
            )

        return p2p_link

    def _get_p2p_data(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link: T_P2pLinksItem) -> dict:
        """
        Parses p2p_link data model and extracts information which is easier to parse.

        Returns:
        {
            peer: <peer name>
            peer_type: <type of peer>
            interface: <interface on this node>
            peer_interface: <interface on peer>
            port_channel_id: <id on this node | None>
            port_channel_members:
              - interface: <interface on this node>
                peer_interface: <interface on peer>
            ip: <ip if set | None>
            peer_ip: <peer ip if set | None>
            bgp_as: <as if set | None>
            peer_bgp_as: <peer as if set | None>
        }
        """
        index = p2p_link.nodes.index(self.shared_utils.hostname)
        peer_index = (index + 1) % 2
        peer = p2p_link.nodes[peer_index]
        peer_facts = self.shared_utils.get_peer_facts(peer, required=False)
        peer_type = "other" if peer_facts is None else peer_facts.type

        # Set ip or fallback to list with None values
        ips = p2p_link.ip or [None, None]
        # Set bgp_as or fallback to list with None values
        bgp_as = p2p_link.field_as or [None, None]
        # Set descriptions or fallback to list with None values
        descriptions = p2p_link.descriptions or [None, None]

        try:
            ip = ips[index]
            peer_ip = ips[peer_index]
            description = descriptions[index]
        except IndexError as exc:
            msg = "p2p_links model is intended to work for only two devices per entry."
            raise AristaAvdError(msg) from exc

        data = {
            "peer": peer,
            "peer_type": peer_type,
            "ip": ip,
            "peer_ip": peer_ip,
            "bgp_as": str(bgp_as[index]) if index < len(bgp_as) and bgp_as[index] else None,
            "peer_bgp_as": str(bgp_as[peer_index]) if peer_index < len(bgp_as) and bgp_as[peer_index] else None,
            "description": description,
        }

        if (
            self.shared_utils.hostname in p2p_link.port_channel.nodes_child_interfaces
            and p2p_link.port_channel.nodes_child_interfaces[self.shared_utils.hostname].interfaces
        ):
            node_data = p2p_link.port_channel.nodes_child_interfaces[self.shared_utils.hostname]
            # Port-channel
            portchannel_id = self._get_channel_id(p2p_link, node_data)

            if peer not in p2p_link.port_channel.nodes_child_interfaces:
                msg = f"{peer} under {self.data_model}.p2p_links.[].port_channel.nodes_child_interfaces"
                raise AristaAvdMissingVariableError(msg)

            peer_data = p2p_link.port_channel.nodes_child_interfaces[peer]
            default_peer_channel_id = int("".join(re.findall(r"\d", peer_data.interfaces[0])))
            peer_id = peer_data.channel_id or default_peer_channel_id

            data.update(
                {
                    "interface": f"Port-Channel{portchannel_id}",
                    "peer_interface": f"Port-Channel{peer_id}",
                    "port_channel_id": portchannel_id,
                    "peer_port_channel_id": peer_id,
                    "port_channel_description": p2p_link.port_channel.description,
                    "port_channel_members": [
                        {
                            "interface": interface,
                            "peer_interface": peer_data.interfaces[index],
                        }
                        for index, interface in enumerate(node_data.interfaces)
                    ],
                },
            )
            return data

        if p2p_link.interfaces:
            # Ethernet
            data.update(
                {
                    "interface": p2p_link.interfaces[index],
                    "peer_interface": p2p_link.interfaces[peer_index],
                    "port_channel_id": None,
                    "peer_port_channel_id": None,
                    "port_channel_description": None,
                    "port_channel_members": [],
                },
            )
            return data

        msg = f"{self.data_model}.p2p_links must have either 'interfaces' or 'port_channel' with correct members set."
        raise AristaAvdInvalidInputsError(msg)

    def _get_ptp_config_interface(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link: T_P2pLinksItem, output_type: type[T_Ptp]) -> T_Ptp:
        """
        Return ptp config for one p2p_link.

        Covers common config that is applicable to both port-channels and ethernet interfaces.
        This config will only be used on the main interface - so not port-channel members.
        """
        ptp_config = output_type()

        # Early return if PTP is not enabled
        if not (p2p_link.ptp.enabled and self.shared_utils.platform_settings.feature_support.ptp):
            return ptp_config

        if self.shared_utils.ptp_enabled:
            # Apply PTP profile config from node settings when profile is not defined on p2p_link
            if not p2p_link.ptp.profile:
                ptp_config = self.shared_utils.ptp_profile._cast_as(output_type, ignore_extra_keys=True)

            # Apply PTP profile defined for the p2p_link
            elif p2p_link.ptp.profile not in self.inputs.ptp_profiles:
                msg = f"PTP Profile '{p2p_link.ptp.profile}' referenced under {self.data_model}.p2p_links does not exist in `ptp_profiles`."
                raise AristaAvdInvalidInputsError(msg)

            else:
                ptp_profile_config = self.inputs.ptp_profiles[p2p_link.ptp.profile]._deepcopy()
                if ptp_profile_config.profile:
                    delattr(ptp_profile_config, "profile")
                ptp_config = ptp_profile_config._cast_as(output_type, ignore_extra_keys=True)

        node_index = p2p_link.nodes._as_list().index(self.shared_utils.hostname)  # TODO: Implement .index() method on AvdList and AvdIndexedList class.
        if len(p2p_link.ptp.roles) > node_index and p2p_link.ptp.roles[node_index] == "master":
            ptp_config.role = "master"

        ptp_config.enable = True

        return ptp_config

    def _update_common_interface_cfg(
        self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol,
        p2p_link: T_P2pLinksItem,
        p2p_link_data: dict,
        interface: EosCliConfigGen.EthernetInterfacesItem | EosCliConfigGen.PortChannelInterfacesItem,
    ) -> None:
        """
        Update the partial structured_config for one p2p_link under ethernet or port-channel interface.

        Covers common config that is applicable to both port-channels and ethernet interfaces.
        This config will only be used on the main interface - so not port-channel members.
        """
        interface._update(
            name=p2p_link_data["interface"],
            peer=p2p_link_data["peer"],
            peer_interface=p2p_link_data["peer_interface"],
            peer_type=p2p_link_data["peer_type"],
            shutdown=False,
            mtu=self.shared_utils.get_interface_mtu(p2p_link_data["interface"], p2p_link._get("mtu", self.shared_utils.p2p_uplinks_mtu)),
            service_profile=p2p_link._get("qos_profile", self.inputs.p2p_uplinks_qos_profile),
            eos_cli=p2p_link.raw_eos_cli,
        )
        interface.switchport.enabled = False
        # Remove this block after removing p2p_links[].structured_config from schema.
        if not (p2p_link.ethernet_structured_config or p2p_link.port_channel_structured_config) and p2p_link.structured_config:
            if isinstance(interface, EosCliConfigGen.PortChannelInterfacesItem):
                # Port-channel
                self.custom_structured_configs.nested.port_channel_interfaces.obtain(interface.name)._deepmerge(
                    EosCliConfigGen.PortChannelInterfacesItem._from_dict(p2p_link.structured_config),
                    list_merge=self.custom_structured_configs.list_merge_strategy,
                )
            else:
                # Ethernet
                self.custom_structured_configs.nested.ethernet_interfaces.obtain(interface.name)._deepmerge(
                    EosCliConfigGen.EthernetInterfacesItem._from_dict(p2p_link.structured_config),
                    list_merge=self.custom_structured_configs.list_merge_strategy,
                )

        if p2p_link_data["ip"]:
            interface.ip_address = p2p_link_data["ip"]

        self._update_interface_multicast_config(p2p_link, interface)

        if p2p_link.include_in_underlay_protocol:
            if (self.inputs.underlay_rfc5549 and p2p_link.routing_protocol != "ebgp") or p2p_link.ipv6_enable is True:
                interface.ipv6_enable = True

            if self.shared_utils.underlay_ospf:
                interface._update(ospf_network_point_to_point=True, ospf_area=self.inputs.underlay_ospf_area)

            if self.shared_utils.underlay_isis:
                interface._update(
                    isis_enable=self.shared_utils.isis_instance_name,
                    isis_bfd=self.inputs.underlay_isis_bfd or None,
                    isis_metric=default(p2p_link.isis_metric, self.inputs.isis_default_metric),
                    isis_network_point_to_point=p2p_link.isis_network_type == "point-to-point",
                    isis_hello_padding=p2p_link.isis_hello_padding,
                )
                isis_circuit_type: Literal["level-1", "level-2", "level-1-2"] = default(p2p_link.isis_circuit_type, self.inputs.isis_default_circuit_type)
                interface.isis_circuit_type = isis_circuit_type

                mode: Literal["md5", "text"] | None = default(p2p_link.isis_authentication_mode, self.inputs.underlay_isis_authentication_mode)
                interface.isis_authentication.both.mode = mode

                if p2p_link.isis_authentication_key is not None:
                    interface.isis_authentication.both._update(key=p2p_link.isis_authentication_key, key_type="7")
                elif p2p_link.isis_authentication_cleartext_key is not None:
                    interface.isis_authentication.both._update(
                        key=isis_encrypt(
                            password=p2p_link.isis_authentication_cleartext_key,
                            key=cast("str", self.shared_utils.isis_instance_name),
                            mode=mode or "none",
                        ),
                        key_type="7",
                    )
                elif (isis_authentication_key := self.shared_utils.underlay_isis_authentication_key) is not None:
                    interface.isis_authentication.both._update(key=isis_authentication_key, key_type="7")

        if p2p_link.macsec_profile:
            interface.mac_security.profile = p2p_link.macsec_profile

        interface.sflow.enable = self.shared_utils.get_interface_sflow(
            interface.name,
            default(p2p_link.sflow, self.inputs.fabric_sflow.core_interfaces if self.data_model == "core_interfaces" else self.inputs.fabric_sflow.l3_edge),
        )

        # Adding type check to avoid confusing the type checker.
        if isinstance(interface, EosCliConfigGen.PortChannelInterfacesItem):  # NOSONAR(S3923)
            interface._update(flow_tracker=self.shared_utils.get_flow_tracker(p2p_link.flow_tracking, output_type=interface.FlowTracker))
        else:
            interface._update(flow_tracker=self.shared_utils.get_flow_tracker(p2p_link.flow_tracking, output_type=interface.FlowTracker))

        if self.shared_utils.mpls_lsr and default(p2p_link.mpls_ip, True):  # noqa: FBT003
            interface.mpls.ip = True
            if p2p_link.include_in_underlay_protocol is True and self.shared_utils.underlay_ldp and default(p2p_link.mpls_ldp, True):  # noqa: FBT003
                interface.mpls.ldp.interface = True
                interface.mpls.ldp.igp_sync = True

    def _get_channel_id(
        self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol,
        p2p_link: T_P2pLinksItem,
        node_data: EosDesigns.CoreInterfaces.P2pLinksItem.PortChannel.NodesChildInterfacesItem
        | EosDesigns.L3Edge.P2pLinksItem.PortChannel.NodesChildInterfacesItem,
    ) -> int:
        """Returns a channel ID for one p2p_link."""
        if node_data.channel_id:
            return node_data.channel_id
        if p2p_link.port_channel.channel_id_algorithm == "p2p_link_id":
            if not p2p_link.id:
                msg = f"'id' is not set for p2p link on {self.shared_utils.hostname} but the selected 'channel_id_algorithm' is 'p2p_link_id'."
                raise AristaAvdInvalidInputsError(msg)
            return p2p_link.id + p2p_link.port_channel._get("channel_id_offset", 0)

        # channel_id_algorithm "first_port"
        return int("".join(re.findall(r"\d", node_data.interfaces[0])))

    def _update_interface_multicast_config(
        self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol,
        p2p_link: T_P2pLinksItem,
        interface: EosCliConfigGen.EthernetInterfacesItem | EosCliConfigGen.PortChannelInterfacesItem,
    ) -> None:
        if p2p_link.include_in_underlay_protocol:
            # TODO: AVD 6.0 remove underlay_mutlicast
            # Legacy - to be non breaking, when using the legacy `underlay_multicast`, we cannot enable PIM SM if p2p_link.multicast_pim_sm is not set
            # otherwise it is breaking, as underlay_multicast used to be default False
            # The porting guide must describe the change in default between underlay_multicast and underlay_multicast_pim_sm_enabled
            if self.inputs.underlay_multicast is True and self.shared_utils.node_config.underlay_multicast.pim_sm.enabled is not False:
                if p2p_link.underlay_multicast is True or p2p_link.multicast_pim_sm is True:
                    interface.pim.ipv4.sparse_mode = True
            elif self.shared_utils.underlay_multicast_pim_sm_enabled and (p2p_link.underlay_multicast is True or p2p_link.multicast_pim_sm is not False):
                interface.pim.ipv4.sparse_mode = True

            # static multicast
            if self.shared_utils.underlay_multicast_static_enabled and p2p_link.multicast_static is not False:
                interface.multicast.ipv4.static = True
        else:
            # not included in underlay protocol
            if self.shared_utils.underlay_multicast_pim_sm_enabled and p2p_link.multicast_pim_sm:
                interface.pim.ipv4.sparse_mode = True
            if self.shared_utils.underlay_multicast_static_enabled and p2p_link.multicast_static:
                interface.multicast.ipv4.static = True
