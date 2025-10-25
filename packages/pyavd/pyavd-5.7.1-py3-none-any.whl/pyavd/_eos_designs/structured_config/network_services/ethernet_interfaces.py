# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError
from pyavd._utils import get_ip_from_ip_prefix
from pyavd.j2filters import natural_sort

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import AvdStructuredConfigNetworkServicesProtocol


class EthernetInterfacesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def ethernet_interfaces(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """
        Set structured config for ethernet_interfaces.

        Only used with L3 or L1 network services
        """
        if not (self.shared_utils.network_services_l3 or self.shared_utils.network_services_l1):
            return

        subif_parent_interface_names: set[str] = set()
        """Set to collect all the parent interface names of all the subinterfaces defined under l3_interfaces or point_to_point_services in network_services."""

        if self.shared_utils.network_services_l3:
            for tenant in self.shared_utils.filtered_tenants:
                for vrf in tenant.vrfs:
                    # The l3_interfaces has already been filtered in filtered_tenants
                    # to only contain entries with our hostname
                    self._set_l3_interfaces(vrf, tenant, subif_parent_interface_names)

                    # Member ethernet ports for Port-Channel interface
                    self._set_l3_port_channel_members(vrf)

        if self.shared_utils.network_services_l1:
            for tenant in self.shared_utils.filtered_tenants:
                if not tenant.point_to_point_services:
                    continue
                self._set_point_to_point_interfaces(tenant, subif_parent_interface_names)

        # Add missing parent interface names if any
        if missing_parent_interface_names := subif_parent_interface_names.difference(eth_int.name for eth_int in self.structured_config.ethernet_interfaces):
            self._set_subif_parent_interfaces(missing_parent_interface_names)

    def _set_l3_port_channel_members(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
    ) -> None:
        """Set the structured_config for ethernet_interfaces which are members of l3_port_channels."""
        for l3_port_channel in vrf.l3_port_channels:
            # sub-interface for l3_port_channel cannot have member eth ports
            # skip any logic to generate member port config for such sub-interfaces
            if "." in l3_port_channel.name:
                continue

            channel_group_id = l3_port_channel.name.removeprefix("Port-Channel")
            for member_intf in l3_port_channel.member_interfaces:
                interface_description = member_intf.description
                # derive values for peer from parent L3 port-channel
                # if not defined explicitly for member interface
                peer = member_intf.peer if member_intf.peer else l3_port_channel.peer
                if not interface_description:
                    elems = [peer, member_intf.peer_interface]
                    if elems:
                        interface_description = "_".join([elem for elem in elems if elem])

                ethernet_interface = EosCliConfigGen.EthernetInterfacesItem(
                    name=member_intf.name,
                    description=interface_description or None,
                    peer_type="l3_port_channel_member",
                    peer=peer or None,
                    peer_interface=member_intf.peer_interface or None,
                    shutdown=not l3_port_channel.enabled,
                    speed=member_intf.speed if member_intf.speed else None,
                )
                ethernet_interface.channel_group.id = int(channel_group_id)
                ethernet_interface.channel_group.mode = l3_port_channel.mode

                if member_intf.structured_config:
                    self.custom_structured_configs.nested.ethernet_interfaces.obtain(member_intf.name)._deepmerge(
                        member_intf.structured_config, list_merge=self.custom_structured_configs.list_merge_strategy
                    )
                self.structured_config.ethernet_interfaces.append(ethernet_interface)

    def _set_l3_interfaces(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
        subif_parent_interface_names: set[str],
    ) -> None:
        """Set the structured_config for ethernet_interfaces with the l3interfaces."""
        for l3_interface in vrf.l3_interfaces:
            nodes_length = len(l3_interface.nodes)
            if (
                len(l3_interface.interfaces) != nodes_length
                or len(l3_interface.ip_addresses) != nodes_length
                or (l3_interface.descriptions and len(l3_interface.descriptions) != nodes_length)
            ):
                msg = (
                    "Length of lists 'interfaces', 'nodes', 'ip_addresses' and 'descriptions' (if used) must match for l3_interfaces for"
                    f" {vrf.name} in {tenant.name}"
                )
                raise AristaAvdError(msg)

            for node_index, node_name in enumerate(l3_interface.nodes):
                if node_name != self.shared_utils.hostname:
                    continue

                interface_name = l3_interface.interfaces[node_index]
                interface_ip = l3_interface.ip_addresses[node_index]
                if "/" in interface_ip:
                    interface_ip = get_ip_from_ip_prefix(interface_ip)
                # if 'descriptions' is set, it is preferred
                interface_description = l3_interface.descriptions[node_index] if l3_interface.descriptions else l3_interface.description
                interface = EosCliConfigGen.EthernetInterfacesItem(
                    name=interface_name,
                    peer_type="l3_interface",
                    ip_address=l3_interface.ip_addresses[node_index],
                    mtu=self.shared_utils.get_interface_mtu(interface_name, l3_interface.mtu),
                    shutdown=not l3_interface.enabled,
                    arp_gratuitous_accept=l3_interface.arp_gratuitous_accept,
                    description=interface_description,
                    eos_cli=l3_interface.raw_eos_cli,
                    flow_tracker=self.shared_utils.get_flow_tracker(l3_interface.flow_tracking, output_type=EosCliConfigGen.EthernetInterfacesItem.FlowTracker),
                )

                if l3_interface.structured_config:
                    self.custom_structured_configs.nested.ethernet_interfaces.obtain(interface_name)._deepmerge(
                        l3_interface.structured_config, list_merge=self.custom_structured_configs.list_merge_strategy
                    )

                interface.sflow.enable = self.shared_utils.get_interface_sflow(interface.name, self.inputs.fabric_sflow.l3_interfaces)

                if l3_interface.ipv4_acl_in:
                    acl = self.shared_utils.get_ipv4_acl(
                        name=l3_interface.ipv4_acl_in,
                        interface_name=interface_name,
                        interface_ip=interface_ip,
                    )
                    interface.access_group_in = acl.name
                    self._set_ipv4_acl(acl)

                if l3_interface.ipv4_acl_out:
                    acl = self.shared_utils.get_ipv4_acl(
                        name=l3_interface.ipv4_acl_out,
                        interface_name=interface_name,
                        interface_ip=interface_ip,
                    )
                    interface.access_group_out = acl.name
                    self._set_ipv4_acl(acl)

                if "." in interface_name:
                    # This is a subinterface so we need to ensure that the parent is created
                    parent_interface_name, subif_id = interface_name.split(".", maxsplit=1)
                    subif_parent_interface_names.add(parent_interface_name)

                    encapsulation_dot1q_vlans = l3_interface.encapsulation_dot1q_vlan
                    if len(encapsulation_dot1q_vlans) > node_index:
                        interface.encapsulation_dot1q.vlan = encapsulation_dot1q_vlans[node_index]
                    else:
                        interface.encapsulation_dot1q.vlan = int(subif_id)
                else:
                    interface.switchport.enabled = False

                if vrf.name != "default":
                    interface.vrf = vrf.name

                if l3_interface.ospf.enabled and vrf.ospf.enabled:
                    interface._update(
                        ospf_area=l3_interface.ospf.area,
                        ospf_network_point_to_point=l3_interface.ospf.point_to_point,
                        ospf_cost=l3_interface.ospf.cost,
                    )

                    self.shared_utils.update_ospf_authentication(interface, l3_interface, vrf, tenant)

                if l3_interface.pim.enabled:
                    if not getattr(vrf._internal_data, "evpn_l3_multicast_enabled", False):
                        # Possibly the key was not set because `evpn_multicast` is not set to `true`.
                        if not self.shared_utils.evpn_multicast:
                            msg = (
                                f"'pim: enabled' set on l3_interface '{interface_name}' on '{self.shared_utils.hostname}' requires "
                                "'evpn_multicast: true' at the fabric level"
                            )
                        else:
                            msg = (
                                f"'pim: enabled' set on l3_interface '{interface_name}' on '{self.shared_utils.hostname}' requires "
                                f"'evpn_l3_multicast.enabled: true' under VRF '{vrf.name}' or Tenant '{tenant.name}'"
                            )
                        raise AristaAvdError(msg)

                    if not getattr(vrf._internal_data, "pim_rp_addresses", None):
                        msg = (
                            f"'pim: enabled' set on l3_interface '{interface_name}' on '{self.shared_utils.hostname}' requires at least one RP"
                            f" defined in pim_rp_addresses under VRF '{vrf.name}' or Tenant '{tenant.name}'"
                        )
                        raise AristaAvdError(msg)

                    interface.pim.ipv4.sparse_mode = True

                # Propagate campus_link_type for campus devices
                if self.shared_utils.is_campus_device and l3_interface.campus_link_type:
                    interface._internal_data.campus_link_type = list(l3_interface.campus_link_type)
                self.structured_config.ethernet_interfaces.append(interface)

    def _set_point_to_point_interfaces(
        self: AvdStructuredConfigNetworkServicesProtocol,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
        subif_parent_interface_names: set[str],
    ) -> None:
        """
        Set the structured_config for ethernet_interfaces with the point-to-point interfaces defined under network_services.

        This makes sure that any added interface is not conflicting with an already existing interface.
        """
        for point_to_point_service in tenant.point_to_point_services._natural_sorted():
            for endpoint_index, endpoint in enumerate(point_to_point_service.endpoints):
                # TODO: Filter port-to-point services in filtered_tenants
                if self.shared_utils.hostname not in endpoint.nodes:
                    continue

                for node_index, interface_name in enumerate(endpoint.interfaces):
                    if endpoint.nodes[node_index] != self.shared_utils.hostname:
                        continue

                    if interface_name in self.structured_config.ethernet_interfaces:
                        context = f"tenants[{tenant.name}].point_to_point_services[{point_to_point_service.name}].endpoints[{endpoint_index}]"
                        msg = (
                            "Found duplicate objects with conflicting data while generating configuration for Network Services "
                            f"point-to-point EthernetInterfaces. Interface {interface_name} defined under {context} "
                            f"conflicts with {self.structured_config.ethernet_interfaces[interface_name]._as_dict()}."
                        )
                        raise AristaAvdInvalidInputsError(msg)

                    if (port_channel_mode := endpoint.port_channel.mode) in ["active", "on"]:
                        first_interface_index = endpoint.nodes.index(self.shared_utils.hostname)
                        first_interface_name = endpoint.interfaces[first_interface_index]
                        channel_group_id = int("".join(re.findall(r"\d", first_interface_name)))
                        self.structured_config.ethernet_interfaces.append_new(
                            name=interface_name,
                            peer_type="point_to_point_service",
                            shutdown=False,
                            channel_group=EosCliConfigGen.EthernetInterfacesItem.ChannelGroup(id=channel_group_id, mode=port_channel_mode),
                        )

                        continue

                    if point_to_point_service.subinterfaces:
                        # This is a subinterface so we need to ensure that the parent is created
                        subif_parent_interface_names.add(interface_name)
                        for subif in point_to_point_service.subinterfaces:
                            subif_name = f"{interface_name}.{subif.number}"
                            if subif_name in self.structured_config.ethernet_interfaces:
                                context = f"tenants[{tenant.name}].point_to_point_services[{point_to_point_service.name}].endpoints[{endpoint_index}]"
                                msg = (
                                    "Found duplicate objects with conflicting data while generating configuration for Network Services "
                                    f"point-to-point EthernetInterfaces. Interface {subif_name} defined under {context} "
                                    f"conflicts with {self.structured_config.ethernet_interfaces[subif_name]._as_dict()}."
                                )
                                raise AristaAvdInvalidInputsError(msg)

                            interface = EosCliConfigGen.EthernetInterfacesItem(
                                name=subif_name,
                                peer_type="point_to_point_service",
                                shutdown=False,
                            )
                            if subif.raw_eos_cli:
                                interface.eos_cli = subif.raw_eos_cli
                            interface.encapsulation_vlan.client.encapsulation = "dot1q"
                            interface.encapsulation_vlan.client.vlan = subif.number
                            interface.encapsulation_vlan.network.encapsulation = "client"

                            if subif.structured_config:
                                self.custom_structured_configs.nested.ethernet_interfaces.obtain(subif_name)._deepmerge(
                                    subif.structured_config, list_merge=self.custom_structured_configs.list_merge_strategy
                                )
                            self.structured_config.ethernet_interfaces.append(interface)

                    else:
                        interface = EosCliConfigGen.EthernetInterfacesItem(
                            name=interface_name,
                            peer_type="point_to_point_service",
                            shutdown=False,
                        )
                        interface.switchport.enabled = False
                        if point_to_point_service.lldp_disable:
                            interface.lldp._update(transmit=False, receive=False)

                        self.structured_config.ethernet_interfaces.append(interface)

    def _set_subif_parent_interfaces(self: AvdStructuredConfigNetworkServicesProtocol, missing_parent_interface_names: set[str]) -> None:
        """Set the ethernet_interfaces with the missing parent interfaces of l3_subinterfaces."""
        for interface_name in natural_sort(missing_parent_interface_names):
            interface = EosCliConfigGen.EthernetInterfacesItem(
                name=interface_name,
                peer_type="l3_interface",
                shutdown=False,
            )
            interface.switchport.enabled = False
            self.structured_config.ethernet_interfaces.append(interface)

    def set_direct_ie_connection_ethernet_interfaces(self: AvdStructuredConfigNetworkServicesProtocol, source_interface: str) -> None:
        # TODO: This should be moved to the place where we configure the same interface in underlay as this will clash between modules..
        interface = EosCliConfigGen.EthernetInterfacesItem(name=source_interface)
        interface.ip_nat.service_profile = self.INTERNET_EXIT_DIRECT_NAT_PROFILE_NAME
        self.structured_config.ethernet_interfaces.append(interface)
