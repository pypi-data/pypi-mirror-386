# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Literal, Protocol, cast, overload

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.schema import EosDesigns
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError, AristaAvdMissingVariableError
from pyavd._utils import default, unique
from pyavd._utils.password_utils.password import ospf_message_digest_encrypt, ospf_simple_encrypt
from pyavd.j2filters import natural_sort, range_expand

if TYPE_CHECKING:
    from typing import Any

    from . import SharedUtilsProtocol


class FilteredTenantsMixin(Protocol):
    """
    Mixin Class providing a subset of SharedUtils.

    Class should only be used as Mixin to the SharedUtils class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    resolved_l2vlan_profiles_cache: dict[str, EosDesigns.L2vlanProfilesItem] | None = None

    @cached_property
    def filtered_tenants(self: SharedUtilsProtocol) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServices:
        """
        Return sorted tenants list from all network_services_keys and filtered based on filter_tenants.

        Keys of Tenant data model will be converted to lists.
        All sub data models like vrfs and l2vlans are also converted and filtered.
        """
        if not self.any_network_services:
            return EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServices()

        filtered_tenants = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServices()
        filter_tenants = self.node_config.filter.tenants
        for network_services_key in self.inputs._dynamic_keys.network_services:
            for original_tenant in network_services_key.value:
                if original_tenant.name not in filter_tenants and "all" not in filter_tenants:
                    continue
                tenant = original_tenant._deepcopy()
                tenant._internal_data.context = f"{network_services_key.key}"
                tenant.l2vlans = self.filtered_l2vlans(tenant)
                tenant.vrfs = self.filtered_vrfs(tenant)
                filtered_tenants.append(tenant)

        no_vrf_default = all("default" not in tenant.vrfs for tenant in filtered_tenants)
        if self.is_wan_router and no_vrf_default:
            filtered_tenants.append(
                EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem(
                    name="WAN_DEFAULT",
                    vrfs=EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.Vrfs(
                        [
                            EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem(
                                name="default",
                                vrf_id=1,
                            )
                        ]
                    ),
                )
            )
        elif self.is_wan_router:
            # It is enough to check only the first occurrence of default VRF as some other piece of code
            # checks that if the VRF is in multiple tenants, the configuration is consistent.
            for tenant in filtered_tenants:
                if "default" not in tenant.vrfs:
                    continue
                if self.inputs.underlay_filter_peer_as:
                    msg = "WAN configuration is not compatible with 'underlay_filter_peer_as'"
                    raise AristaAvdError(msg)
                break

        return filtered_tenants._natural_sorted()

    def filtered_l2vlans(
        self: SharedUtilsProtocol, tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlans:
        """
        Return sorted and filtered l2vlan list from given tenant.

        Filtering based on l2vlan tags.
        """
        if not self.network_services_l2 or not tenant.l2vlans:
            return EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlans()

        filtered_l2vlans = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlans()
        for l2vlan in tenant.l2vlans:
            if not self.is_accepted_vlan(l2vlan):
                continue

            # Perform filtering on tags before merge of profiles, to avoid spending cycles on merging something that will be filtered away.
            if not ("all" in self.filter_tags or bool(set(l2vlan.tags).intersection(self.filter_tags))):
                continue

            merged_l2vlan = self.get_merged_l2vlan_config(l2vlan)
            if tenant.evpn_vlan_bundle:
                merged_l2vlan.evpn_vlan_bundle = merged_l2vlan.evpn_vlan_bundle or tenant.evpn_vlan_bundle

            filtered_l2vlans.append(merged_l2vlan)

        return filtered_l2vlans._natural_sorted(sort_key="id")

    def get_merged_l2vlan_config(
        self: SharedUtilsProtocol, vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem:
        """
        Return structured config for one l2vlan after inheritance.

        Handle inheritance of l2vlan_profiles in two levels:
        l2vlan > l2vlan_profile > l2vlan_parent_profile --> l2vlan_cfg
        """
        if vlan.profile:
            l2vlan_profile = self.get_merged_l2vlan_profile(vlan.profile, f"{vlan.name}")

            # Inherit from the profile
            merged_vlan = vlan._deepinherited(
                l2vlan_profile._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem, ignore_extra_keys=True)
            )
        else:
            merged_vlan = vlan
        return merged_vlan

    def get_merged_l2vlan_profile(self: SharedUtilsProtocol, profile_name: str, context: str) -> EosDesigns.L2vlanProfilesItem:
        """
        Returns a merged "l2vlan_profile" where "parent_profile" has been applied.

        Leverages a dict of resolved profiles as a cache.
        """
        if self.resolved_l2vlan_profiles_cache and profile_name in self.resolved_l2vlan_profiles_cache:
            return self.resolved_l2vlan_profiles_cache[profile_name]

        resolved_profile = self.resolve_l2vlan_profile(profile_name, context)

        # Update the cache so we don't resolve again next time.
        if self.resolved_l2vlan_profiles_cache is None:
            self.resolved_l2vlan_profiles_cache = {}
        self.resolved_l2vlan_profiles_cache[profile_name] = resolved_profile

        return resolved_profile

    def resolve_l2vlan_profile(self: SharedUtilsProtocol, profile_name: str, context: str) -> EosDesigns.L2vlanProfilesItem:
        """Resolve one l2vlan profile and return it."""
        if profile_name not in self.inputs.l2vlan_profiles:
            msg = f"Profile '{profile_name}' applied under l2vlan '{context}' does not exist in 'l2vlan_profiles'."
            raise AristaAvdInvalidInputsError(msg)

        l2vlan_profile = self.inputs.l2vlan_profiles[profile_name]
        if l2vlan_profile.parent_profile:
            if l2vlan_profile.parent_profile not in self.inputs.l2vlan_profiles:
                msg = f"Profile '{l2vlan_profile.parent_profile}' applied under L2VLAN Profile '{profile_name}' does not exist in 'l2vlan_profiles'."
                raise AristaAvdInvalidInputsError(msg)

            parent_profile = self.inputs.l2vlan_profiles[l2vlan_profile.parent_profile]

            # Notice reuse of the same variable with the merged content.
            l2vlan_profile = l2vlan_profile._deepinherited(parent_profile)

        delattr(l2vlan_profile, "parent_profile")

        return l2vlan_profile

    def is_accepted_vlan(
        self: SharedUtilsProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem,
    ) -> bool:
        """
        Check if vlan is in accepted_vlans list.

        If filter.only_vlans_in_use is True also check if vlan id or trunk group is assigned to connected endpoint.
        """
        if vlan.id not in self.accepted_vlans:
            return False

        if not self.node_config.filter.only_vlans_in_use:
            # No further filtering
            return True

        if vlan.id in self.endpoint_vlans:
            return True

        # Picking this up from facts so this would fail if accessed when shared_utils is run before facts
        # TODO: see if this can be optimized
        endpoint_trunk_groups = set(self.switch_facts.endpoint_trunk_groups)
        return bool(self.inputs.enable_trunk_groups and vlan.trunk_groups and endpoint_trunk_groups.intersection(vlan.trunk_groups))

    @cached_property
    def accepted_vlans(self: SharedUtilsProtocol) -> list[int]:
        """
        The 'vlans' switch fact is a string representing a vlan range (ex. "1-200").

        For l2 switches return intersection of vlans from this switch and vlans from uplink switches.
        For anything else return the expanded vlans from this switch.
        """
        switch_vlans = self.switch_facts.vlans
        if not switch_vlans:
            return []
        switch_vlans_list = range_expand(switch_vlans)
        accepted_vlans = [int(vlan) for vlan in switch_vlans_list]
        if self.uplink_type != "port-channel":
            return accepted_vlans

        uplink_switches = unique(self.uplink_switches)
        uplink_switches = [uplink_switch for uplink_switch in uplink_switches if uplink_switch in self.all_fabric_devices]
        for uplink_switch in uplink_switches:
            uplink_switch_facts = self.get_peer_facts(uplink_switch, required=True)
            uplink_switch_vlans = uplink_switch_facts.vlans
            uplink_switch_vlans_list = range_expand(uplink_switch_vlans)
            uplink_switch_vlans_list = [int(vlan) for vlan in uplink_switch_vlans_list]
            accepted_vlans = [vlan for vlan in accepted_vlans if vlan in uplink_switch_vlans_list]

        return accepted_vlans

    def is_accepted_vrf(self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem) -> bool:
        """
        Returns True if.

        - filter.allow_vrfs == ["all"] OR VRF is included in filter.allow_vrfs.

        AND

        - filter.not_vrfs == [] OR VRF is NOT in filter.deny_vrfs
        """
        return ("all" in self.node_config.filter.allow_vrfs or vrf.name in self.node_config.filter.allow_vrfs) and (
            not self.node_config.filter.deny_vrfs or vrf.name not in self.node_config.filter.deny_vrfs
        )

    def is_forced_vrf(
        self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem, tenant_name: str
    ) -> bool:
        """
        Returns True if the given VRF name should be configured even without any loopbacks or SVIs etc.

        There can be various causes for this:
        - The VRF is part of a tenant set under 'always_include_vrfs_in_tenants'
        - 'always_include_vrfs_in_tenants' is set to ['all']
        - This device is using 'p2p-vrfs' as uplink type and the VRF present on the uplink switch.
        """
        if "all" in self.node_config.filter.always_include_vrfs_in_tenants or tenant_name in self.node_config.filter.always_include_vrfs_in_tenants:
            return True

        return vrf.name in self.switch_facts.uplink_switch_vrfs

    def filtered_vrfs(
        self: SharedUtilsProtocol, tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.Vrfs:
        """
        Return sorted and filtered vrf list from given tenant.

        Filtering based on svi tags, l3interfaces, loopbacks or self.is_forced_vrf() check.
        Keys of VRF data model will be converted to lists.
        """
        filtered_vrfs = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.Vrfs()

        for vrf in tenant.vrfs._natural_sorted():
            if not self.is_accepted_vrf(vrf):
                continue

            vrf.bgp_peers = vrf.bgp_peers._filtered(lambda bgp_peer: self.hostname in bgp_peer.nodes)._natural_sorted(sort_key="ip_address")
            vrf.static_routes = vrf.static_routes._filtered(lambda route: not route.nodes or self.hostname in route.nodes)
            vrf.ipv6_static_routes = vrf.ipv6_static_routes._filtered(lambda route: not route.nodes or self.hostname in route.nodes)
            vrf.svis = self.filtered_svis(vrf)
            vrf.l3_interfaces = self.filtered_l3_interfaces(vrf)
            vrf.l3_port_channels = self.filtered_l3_port_channels(vrf)
            vrf.loopbacks = vrf.loopbacks._filtered(lambda loopback: loopback.node == self.hostname)
            vrf.aggregate_addresses = vrf.aggregate_addresses._filtered(lambda aggregate_address: self.match_nodes(aggregate_address.nodes))._natural_sorted(
                sort_key="prefix"
            )

            if self.vtep is True:
                evpn_l3_multicast_enabled = default(vrf.evpn_l3_multicast.enabled, tenant.evpn_l3_multicast.enabled)
                # TODO: Consider if all this should be moved out of filtered_vrfs.
                if self.evpn_multicast:
                    vrf._internal_data.evpn_l3_multicast_enabled = evpn_l3_multicast_enabled
                    vrf._internal_data.evpn_l3_multicast_group_ip = vrf.evpn_l3_multicast.evpn_underlay_l3_multicast_group

                    rps = []
                    for rp_entry in vrf.pim_rp_addresses or tenant.pim_rp_addresses:
                        if not rp_entry.nodes or self.hostname in rp_entry.nodes:
                            if not rp_entry.rps:
                                # TODO: Evaluate if schema should just have required for this key.
                                msg = f"'pim_rp_addresses.rps' under VRF '{vrf.name}' in Tenant '{tenant.name}' is required."
                                raise AristaAvdInvalidInputsError(msg)
                            for rp_ip in rp_entry.rps:
                                rp_address: dict[str, Any] = {"address": rp_ip}
                                if rp_entry.groups:
                                    if rp_entry.access_list_name:
                                        rp_address["access_lists"] = [rp_entry.access_list_name]
                                    else:
                                        rp_address["groups"] = rp_entry.groups._as_list()

                                rps.append(rp_address)

                    if rps:
                        vrf._internal_data.pim_rp_addresses = rps

                        for evpn_peg in vrf.evpn_l3_multicast.evpn_peg or tenant.evpn_l3_multicast.evpn_peg:
                            if not evpn_peg.nodes or self.hostname in evpn_peg.nodes:
                                vrf._internal_data.evpn_l3_multicast_evpn_peg_transit = evpn_peg.transit
                                break

            vrf.additional_route_targets = vrf.additional_route_targets._filtered(
                lambda rt: bool((not rt.nodes or self.hostname in rt.nodes) and rt.address_family and rt.route_target and rt.type in ["import", "export"])
            )

            if vrf.svis or vrf.l3_interfaces or vrf.loopbacks or vrf.l3_port_channels or self.is_forced_vrf(vrf, tenant.name):
                filtered_vrfs.append(vrf)

            if tenant_evpn_vlan_bundle := tenant.evpn_vlan_bundle:
                for svi in vrf.svis:
                    svi.evpn_vlan_bundle = svi.evpn_vlan_bundle or tenant_evpn_vlan_bundle

        return filtered_vrfs

    def get_merged_svi_config(
        self: SharedUtilsProtocol, svi: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem:
        """
        Return structured config for one svi after inheritance.

        Handle inheritance of node config as svi_profiles in two levels:

        First variables will be merged
        svi > svi_profile > svi_parent_profile --> svi_cfg
        &
        svi.nodes.<hostname> > svi_profile.nodes.<hostname> > svi_parent_profile.nodes.<hostname> --> svi_node_cfg

        Then svi is updated with the result of merging svi_node_cfg over svi_cfg
        svi_node_cfg > svi_cfg --> svi
        """
        if svi.profile:
            if svi.profile not in self.inputs.svi_profiles:
                msg = f"Profile '{svi.profile}' applied under SVI '{svi.name}' does not exist in `svi_profiles`."
                raise AristaAvdInvalidInputsError(msg)
            svi_profile = self.inputs.svi_profiles[svi.profile]._deepcopy()

            if svi_profile.parent_profile:
                if svi_profile.parent_profile not in self.inputs.svi_profiles:
                    msg = f"Profile '{svi_profile.parent_profile}' applied under SVI Profile '{svi_profile.profile}' does not exist in `svi_profiles`."
                    raise AristaAvdInvalidInputsError(msg)

                # Inherit from the parent profile
                svi_profile._deepinherit(self.inputs.svi_profiles[svi_profile.parent_profile])

            # Inherit from the profile
            merged_svi = svi._deepinherited(
                svi_profile._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem, ignore_extra_keys=True)
            )
        else:
            merged_svi = svi

        # Merge node specific SVI over the general SVI data.
        if self.hostname in merged_svi.nodes:
            node_specific_svi = merged_svi.nodes[self.hostname]._cast_as(
                EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem, ignore_extra_keys=True
            )
            merged_svi._deepmerge(node_specific_svi, list_merge="replace")

        return merged_svi

    def filtered_svis(
        self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Svis:
        """
        Return sorted and filtered svi list from given tenant vrf.

        Filtering based on accepted vlans since eos_designs_facts already
        filtered that on tags and trunk_groups.
        Extracts static_routes and ipv6_static_routes set under SVIs and appends them to vrf.static_routes and vrf.ipv6_static_routes.
        """
        if not (self.network_services_l2 or self.network_services_l2_as_subint):
            return EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Svis()

        filtered_svis = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Svis()
        for svi in vrf.svis:
            if not self.is_accepted_vlan(svi):
                continue
            # TODO: Tags exist only on the SVI itself, not in svi_profiles. Avoid duplicating this logic here—check tags before merging.
            # Handle svi_profile inheritance
            merged_svi = self.get_merged_svi_config(svi)
            # Perform filtering on tags after merge of profiles, to support tags being set inside profiles.
            if not ("all" in self.filter_tags or bool(set(svi.tags).intersection(self.filter_tags))):
                continue

            filtered_svis.append(merged_svi)

            if merged_svi.static_routes:
                vrf.static_routes.extend(
                    merged_svi.static_routes._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.StaticRoutes)
                )
            if merged_svi.ipv6_static_routes:
                vrf.ipv6_static_routes.extend(
                    merged_svi.ipv6_static_routes._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Ipv6StaticRoutes)
                )

        return filtered_svis._natural_sorted(sort_key="id")

    def filtered_l3_interfaces(
        self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3Interfaces:
        """
        Returns filtered l3_interfaces for the VRFs.

        Extracts static_routes and ipv6_static_routes defined under l3_interfaces and appends them to vrf.static_routes and vrf.ipv6_static_routes.
        """
        filtered_l3_interfaces = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3Interfaces()
        for l3_interface in vrf.l3_interfaces:
            if not (self.hostname in l3_interface.nodes and l3_interface.ip_addresses and l3_interface.interfaces):
                continue
            if l3_interface.static_routes:
                vrf.static_routes.extend(
                    l3_interface.static_routes._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.StaticRoutes)
                )
            if l3_interface.ipv6_static_routes:
                vrf.ipv6_static_routes.extend(
                    l3_interface.ipv6_static_routes._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Ipv6StaticRoutes)
                )
            filtered_l3_interfaces.append(l3_interface)

        return filtered_l3_interfaces

    def filtered_l3_port_channels(
        self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem
    ) -> EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3PortChannels:
        """
        Returns filtered l3_port_channels for the VRFs.

        Extracts static_routes and ipv6_static_routes defined under l3_port_channels and appends them to vrf.static_routes and vrf.ipv6_static_routes.
        """
        filtered_l3_port_channels = EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3PortChannels()
        for l3_port_channel in vrf.l3_port_channels:
            if self.hostname != l3_port_channel.node:
                continue
            if l3_port_channel.static_routes:
                vrf.static_routes.extend(
                    l3_port_channel.static_routes._cast_as(EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.StaticRoutes)
                )
            if l3_port_channel.ipv6_static_routes:
                vrf.ipv6_static_routes.extend(
                    l3_port_channel.ipv6_static_routes._cast_as(
                        EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Ipv6StaticRoutes
                    )
                )
            filtered_l3_port_channels.append(l3_port_channel)

        return filtered_l3_port_channels

    @cached_property
    def endpoint_vlans(self: SharedUtilsProtocol) -> list:
        endpoint_vlans = self.switch_facts.endpoint_vlans
        if not endpoint_vlans:
            return []
        return [int(vlan_id) for vlan_id in range_expand(endpoint_vlans)]

    @overload
    @staticmethod
    def get_vrf_id(vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem, required: Literal[True] = True) -> int: ...

    @overload
    @staticmethod
    def get_vrf_id(vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem, required: Literal[False]) -> int | None: ...

    @staticmethod
    def get_vrf_id(vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem, required: bool = True) -> int | None:
        vrf_id = default(vrf.vrf_id, vrf.vrf_vni)
        if vrf_id is None and required:
            msg = f"'vrf_id' or 'vrf_vni' for VRF '{vrf.name}' must be set."
            raise AristaAvdInvalidInputsError(msg)
        return vrf_id

    @staticmethod
    def get_vrf_vni(vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem) -> int:
        vrf_vni = default(vrf.vrf_vni, vrf.vrf_id)
        if vrf_vni is None:
            msg = f"'vrf_vni' or 'vrf_id' for VRF '{vrf.name}' must be set."
            raise AristaAvdInvalidInputsError(msg)
        return vrf_vni

    @cached_property
    def vrfs(self: SharedUtilsProtocol) -> list[str]:
        """
        Return the list of vrfs to be defined on this switch.

        Ex. ["default", "prod"]
        """
        if not self.network_services_l3:
            return []

        return natural_sort({vrf.name for tenant in self.filtered_tenants for vrf in tenant.vrfs})

    def get_additional_svi_config(
        self: SharedUtilsProtocol,
        config: EosCliConfigGen.VlanInterfacesItem | EosCliConfigGen.EthernetInterfacesItem,
        svi: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> None:
        """
        Adding IP helpers and OSPF for SVIs via a common function.

        Used for SVIs and for subinterfaces when uplink_type: lan.

        The given config is updated in-place.
        """
        ip_helpers = svi.ip_helpers or vrf.ip_helpers
        if ip_helpers:
            for svi_ip_helper in ip_helpers:
                config.ip_helpers.append_new(
                    ip_helper=svi_ip_helper.ip_helper,
                    source_interface=svi_ip_helper.source_interface,
                    vrf=svi_ip_helper.source_vrf,
                )

        if svi.ospf.enabled and vrf.ospf.enabled:
            config._update(
                ospf_area=svi.ospf.area,
                ospf_network_point_to_point=svi.ospf.point_to_point,
                ospf_cost=svi.ospf.cost,
            )
            self.update_ospf_authentication(config, svi, vrf, tenant)

    def update_ospf_authentication(
        self: SharedUtilsProtocol,
        interface: EosCliConfigGen.EthernetInterfacesItem | EosCliConfigGen.PortChannelInterfacesItem | EosCliConfigGen.VlanInterfacesItem,
        network_services_interface: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3InterfacesItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3PortChannelsItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> None:
        """
        Handle OSPF authentication for l3_interfaces, l3_port_channels and SVIs.

        Work for both simple and message_digest authentication method.
        If encryption by AVD is required via `encrypt_passwords` or because it must always be encrypted (password at VRF level), handle this as well.

        Interface level configuration always takes precedence over VRF level configuration.

        Args:
            interface: The EosCliConfigGen interface to update with authentication.
            network_services_interface: The l3_interface, l3_port_channel_interface or SVI input.
            vrf: The VRF object containing OSPF/BGP and vtep_diagnostic details.
            tenant: The tenant object containing the VRF.

        Raises:
            AristaAvdMissingVariableError: If key is missing.
        """
        # Handle OSPF authentication
        ospf_authentication = network_services_interface.ospf.authentication or vrf.ospf.authentication
        if not ospf_authentication:
            return

        match ospf_authentication:
            case "simple":
                if network_services_interface.ospf.simple_auth_key is not None:
                    ospf_simple_auth_key = network_services_interface.ospf.simple_auth_key
                elif network_services_interface.ospf.cleartext_simple_auth_key is not None:
                    ospf_simple_auth_key = ospf_simple_encrypt(network_services_interface.ospf.cleartext_simple_auth_key, interface.name)
                elif vrf.ospf.cleartext_simple_auth_key is not None:
                    # Always encrypt if defined at VRF level.
                    ospf_simple_auth_key = ospf_simple_encrypt(vrf.ospf.cleartext_simple_auth_key, interface.name)
                else:
                    match interface:
                        case EosCliConfigGen.EthernetInterfacesItem():
                            interface_ospf_path = f"tenants[name={tenant.name}].vrfs[name={vrf.name}].l3_interfaces[name={interface.name}].ospf"
                        case EosCliConfigGen.PortChannelInterfacesItem():
                            interface_ospf_path = f"tenants[name={tenant.name}].vrfs[name={vrf.name}].l3_port_channels[name={interface.name}].ospf"
                        case _:
                            # This is EosCliConfigGen.VlanInterfacesItem
                            interface_ospf_path = f"tenants[name={tenant.name}].vrfs[name={vrf.name}].svis[id={network_services_interface.id}].ospf"
                    msg = (
                        f"`tenants[name={tenant.name}].vrfs[name={vrf.name}].ospf.cleartext_simple_auth_key` or `{interface_ospf_path}.simple_auth_key` "
                        f"or `{interface_ospf_path}.cleartext_simple_auth_key`"
                    )

                    raise AristaAvdMissingVariableError(msg)

                interface._update(ospf_authentication=ospf_authentication, ospf_authentication_key=ospf_simple_auth_key)

            case _:
                # This is "message-digest"
                # The full list of keys is EITHER taken from the network_services_interface or from the VRF
                # TODO: AVD 6.0.0 Make 'id' a primary key and 'key' required - it means the two lists will should be merged instead of replacing.
                if network_services_interface.ospf.message_digest_keys:
                    for ospf_key in network_services_interface.ospf.message_digest_keys:
                        self.update_message_digest_key(ospf_key, interface, vrf, tenant)

                elif vrf.ospf.message_digest_keys:
                    for ospf_key in vrf.ospf.message_digest_keys:
                        self.update_message_digest_key(ospf_key, interface, vrf, tenant)

                # TODO: AVD 6.0: raise if we end up with no keys
                if interface.ospf_message_digest_keys:
                    interface.ospf_authentication = ospf_authentication

    def update_message_digest_key(
        self: SharedUtilsProtocol,
        ospf_key: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3InterfacesItem.Ospf.MessageDigestKeysItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3PortChannelsItem.Ospf.MessageDigestKeysItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem.Ospf.MessageDigestKeysItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.Ospf.MessageDigestKeysItem,
        interface: EosCliConfigGen.EthernetInterfacesItem | EosCliConfigGen.PortChannelInterfacesItem | EosCliConfigGen.VlanInterfacesItem,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> None:
        """Handle OSPF authentication for one message digest key."""
        if not ospf_key.id:
            return
        # VRF level does not have a 'key' attribute.
        if hasattr(ospf_key, "key") and ospf_key.key is not None:
            key = ospf_key.key
        elif ospf_key.cleartext_key is not None:
            # ospf_key.cleartext_key is not None
            key = ospf_message_digest_encrypt(
                password=cast("str", ospf_key.cleartext_key),
                key=interface.name,
                hash_algorithm=ospf_key.hash_algorithm,
                key_id=str(ospf_key.id),
            )
        else:
            # This cannot happen for Vrf level as cleartext_key is required.
            match ospf_key:
                case EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3InterfacesItem.Ospf.MessageDigestKeysItem():
                    interface_ospf_path = (
                        f"tenants[name={tenant.name}].vrfs[name={vrf.name}].l3_interfaces[name={interface.name}].ospf.message_digest_keys[key={ospf_key.id}]"
                    )
                    msg = f"`{interface_ospf_path}.key` or `{interface_ospf_path}.cleartext_key`"
                case EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.L3PortChannelsItem.Ospf.MessageDigestKeysItem():
                    interface_ospf_path = (
                        f"tenants[name={tenant.name}].vrfs[name={vrf.name}].l3_port_channels[name={interface.name}].ospf.message_digest_keys[key={ospf_key.id}]"
                    )
                    msg = f"`{interface_ospf_path}.key` or `{interface_ospf_path}.cleartext_key`"
                case EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem.Ospf.MessageDigestKeysItem():
                    interface_ospf_path = (
                        f"tenants[name={tenant.name}].vrfs[name={vrf.name}].svis[id={interface.name[4:]}].ospf.message_digest_keys[key={ospf_key.id}]"
                    )
                    msg = f"`{interface_ospf_path}.key` or `{interface_ospf_path}.cleartext_key`"

            raise AristaAvdMissingVariableError(msg)

        interface.ospf_message_digest_keys.append_new(
            id=ospf_key.id,
            hash_algorithm=ospf_key.hash_algorithm,
            key=key,
        )

    @cached_property
    def bgp_in_network_services(self: SharedUtilsProtocol) -> bool:
        """
        True if BGP is needed or forcefully enabled for any VRF under network services.

        Used to enable router_bgp even if there is no overlay or underlay routing protocol.
        """
        if not self.network_services_l3:
            return False

        return any(self.bgp_enabled_for_vrf(vrf) for tenant in self.filtered_tenants for vrf in tenant.vrfs)

    def bgp_enabled_for_vrf(self: SharedUtilsProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem) -> bool:
        """
        True if the given VRF should be included under Router BGP.

        - If bgp.enabled is set to True, we will always configure the VRF.
        - If bgp.enabled is set to False, we will never configure the VRF.

        Otherwise we will autodetect:
        - If the VRF is part of an overlay we will configure BGP for it.
        - If the VRF is on a WAN router, we will configure BGP for it.
        - If any BGP peers are configured we will configure BGP for it.
        - If uplink type is p2p_vrfs and the vrf is included in uplink VRFs.
        """
        if vrf.bgp.enabled is not None:
            return vrf.bgp.enabled

        vrf_address_families = [af for af in vrf.address_families if af in self.overlay_address_families]
        return any(
            [
                vrf_address_families,
                vrf.bgp_peers,
                (self.uplink_type == "p2p-vrfs" and vrf.name in self.switch_facts.uplink_switch_vrfs),
                self.is_wan_vrf(vrf),
            ]
        )
