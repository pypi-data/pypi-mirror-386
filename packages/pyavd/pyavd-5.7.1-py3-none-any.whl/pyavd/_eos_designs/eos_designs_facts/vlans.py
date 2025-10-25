# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFactsProtocol
from pyavd._utils import remove_cached_property_type
from pyavd.j2filters import list_compress, natural_sort, range_expand

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import EosDesignsFactsGeneratorProtocol


class VlansMixin(EosDesignsFactsProtocol, Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @remove_cached_property_type
    @cached_property
    def vlans(self: EosDesignsFactsGeneratorProtocol) -> str:
        """
        Exposed in avd_switch_facts.

        Return the compressed list of vlans to be defined on this switch

        Ex. "1-100, 201-202"

        This excludes the optional "uplink_native_vlan" if that vlan is not used for anything else.
        This is to ensure that native vlan is not necessarily permitted on the uplink trunk.
        """
        return list_compress(self._vlans)

    def _parse_adapter_settings(
        self: EosDesignsFactsGeneratorProtocol,
        adapter_settings: EosDesigns._DynamicKeys.DynamicConnectedEndpointsItem.ConnectedEndpointsItem.AdaptersItem | EosDesigns.NetworkPortsItem,
    ) -> tuple[set, set]:
        """Parse the given adapter_settings and return relevant vlans and trunk_groups."""
        vlans = set()
        trunk_groups = set(adapter_settings.trunk_groups)
        if adapter_settings.vlans and adapter_settings.vlans != "all":
            vlans.update(map(int, range_expand(adapter_settings.vlans)))
        elif adapter_settings.mode == "trunk" and not trunk_groups:
            # No vlans or trunk_groups defined, but this is a trunk, so default is all vlans allowed
            # No need to check further, since the list is now containing all vlans.
            return set(range(1, 4094)), trunk_groups
        elif adapter_settings.mode == "trunk phone":
            # # EOS default native VLAN is VLAN 1
            if not adapter_settings.native_vlan:
                vlans.add(1)
        else:
            # No vlans or mode defined so this is an access port with only vlan 1 allowed
            vlans.add(1)

        if adapter_settings.native_vlan:
            vlans.add(adapter_settings.native_vlan)
        if adapter_settings.phone_vlan:
            vlans.add(adapter_settings.phone_vlan)

        for subinterface in adapter_settings.port_channel.subinterfaces:
            if subinterface.vlan_id:
                vlans.add(subinterface.vlan_id)
            elif subinterface.number:
                vlans.add(subinterface.number)

        return vlans, trunk_groups

    @cached_property
    def _local_endpoint_vlans_and_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> tuple[set, set]:
        """
        Return list of vlans and list of trunk groups used by connected_endpoints on this switch.

        Also includes the inband_mgmt_vlan.
        """
        if not (self.shared_utils.any_network_services and self.shared_utils.connected_endpoints):
            return set(), set()

        vlans = set()
        trunk_groups = set()

        if self.shared_utils.configure_inband_mgmt:
            vlans.add(self.shared_utils.node_config.inband_mgmt_vlan)
        connected_endpoints = self.shared_utils.all_connected_endpoints
        for connected_endpoints_key in connected_endpoints:
            for connected_endpoint in connected_endpoints_key.value:
                for index, adapter in enumerate(connected_endpoint.adapters):
                    adapter._internal_data.context = f"{connected_endpoints_key.key}[name={connected_endpoint.name}].adapters[{index}]"
                    adapter_settings = self.shared_utils.get_merged_adapter_settings(adapter)
                    if self.shared_utils.hostname not in adapter_settings.switches:
                        # This switch is not connected to this endpoint. Skipping.
                        continue

                    adapter_vlans, adapter_trunk_groups = self._parse_adapter_settings(adapter_settings)
                    vlans.update(adapter_vlans)
                    trunk_groups.update(adapter_trunk_groups)
                    if individual_adapter_settings := self.shared_utils.get_merged_individual_adapter_settings(adapter_settings):
                        individual_vlans, individual_trunk_groups = self._parse_adapter_settings(individual_adapter_settings)
                        vlans.update(individual_vlans)
                        trunk_groups.update(individual_trunk_groups)

                    if len(vlans) >= 4094:
                        # No need to check further, since the set is now containing all vlans.
                        # The trunk group list may not be complete, but it will not matter, since we will
                        # configure all vlans anyway.
                        return vlans, trunk_groups

        for index, network_port_item in enumerate(self.inputs.network_ports):
            for switch_regex in network_port_item.switches:
                # The match test is built on Python re.match which tests from the beginning of the string #}
                # Since the user would not expect "DC1-LEAF1" to also match "DC-LEAF11" we will force ^ and $ around the regex
                raw_switch_regex = rf"^{switch_regex}$"
                if not re.match(raw_switch_regex, self.shared_utils.hostname):
                    # Skip entry if no match
                    continue

                network_port_item._internal_data.context = f"network_ports[{index}]"
                adapter_settings = self.shared_utils.get_merged_adapter_settings(network_port_item)
                adapter_vlans, adapter_trunk_groups = self._parse_adapter_settings(adapter_settings)
                vlans.update(adapter_vlans)
                trunk_groups.update(adapter_trunk_groups)
                if individual_adapter_settings := self.shared_utils.get_merged_individual_adapter_settings(adapter_settings):
                    individual_vlans, individual_trunk_groups = self._parse_adapter_settings(individual_adapter_settings)
                    vlans.update(individual_vlans)
                    trunk_groups.update(individual_trunk_groups)

                if len(vlans) >= 4094:
                    # No need to check further, since the list is now containing all vlans.
                    # The trunk group list may not be complete, but it will not matter, since we will
                    # configure all vlans anyway.
                    return vlans, trunk_groups

        return vlans, trunk_groups

    @cached_property
    def _downstream_switch_endpoint_vlans_and_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> tuple[set, set]:
        """
        Return set of vlans and set of trunk groups used by downstream switches.

        Traverse any downstream L2 switches so ensure we can provide connectivity to any vlans / trunk groups used by them.
        """
        if not self.shared_utils.any_network_services:
            return set(), set()

        vlans = set()
        trunk_groups = set()
        for fabric_switch in self.shared_utils.all_fabric_devices:
            fabric_switch_facts = self.get_peer_facts_generator(fabric_switch)
            if fabric_switch_facts.shared_utils.uplink_type == "port-channel" and self.shared_utils.hostname in fabric_switch_facts.uplink_peers:
                fabric_switch_endpoint_vlans, fabric_switch_endpoint_trunk_groups = fabric_switch_facts._endpoint_vlans_and_trunk_groups
                vlans.update(fabric_switch_endpoint_vlans)
                trunk_groups.update(fabric_switch_endpoint_trunk_groups)

        return vlans, trunk_groups

    @cached_property
    def _endpoint_vlans_and_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> tuple[set, set]:
        """
        Return set of vlans and set of trunk groups.

        The trunk groups are those used by connected_endpoints on this switch,
        downstream switches but NOT mlag peer (since we would have circular references then).
        """
        local_endpoint_vlans, local_endpoint_trunk_groups = self._local_endpoint_vlans_and_trunk_groups
        downstream_switch_endpoint_vlans, downstream_switch_endpoint_trunk_groups = self._downstream_switch_endpoint_vlans_and_trunk_groups
        return local_endpoint_vlans.union(downstream_switch_endpoint_vlans), local_endpoint_trunk_groups.union(downstream_switch_endpoint_trunk_groups)

    @cached_property
    def _endpoint_vlans(self: EosDesignsFactsGeneratorProtocol) -> set[int]:
        """
        Return set of vlans in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Ex: {1, 20, 21, 22, 23} or set().
        """
        endpoint_vlans, _ = self._endpoint_vlans_and_trunk_groups
        if not self.shared_utils.mlag:
            return endpoint_vlans

        # Get the set of vlans and set of trunk groups used by connected_endpoints on the MLAG peer.
        # This could differ from local vlans and trunk groups if a connected endpoint is only connected to one leaf.
        mlag_endpoint_vlans, _ = self._mlag_peer_facts_generator._endpoint_vlans_and_trunk_groups

        return endpoint_vlans.union(mlag_endpoint_vlans)

    @remove_cached_property_type
    @cached_property
    def endpoint_vlans(self: EosDesignsFactsGeneratorProtocol) -> str | None:
        """
        Return compressed list of vlans in use by endpoints connected to this switch or MLAG peer.

        Ex: "1,20-30" or "".
        """
        if self.shared_utils.node_config.filter.only_vlans_in_use:
            return list_compress(list(self._endpoint_vlans))

        return None

    @cached_property
    def _endpoint_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> set[str]:
        """Return set of trunk_groups in use by endpoints connected to this switch, downstream switches or MLAG peer."""
        if not self.shared_utils.node_config.filter.only_vlans_in_use:
            return set()

        _, endpoint_trunk_groups = self._endpoint_vlans_and_trunk_groups
        if not self.shared_utils.mlag:
            return endpoint_trunk_groups

        # Get the set of vlans and set of trunk groups used by connected_endpoints on the MLAG peer.
        # This could differ from local vlans and trunk groups if a connected endpoint is only connected to one leaf.
        _, mlag_endpoint_trunk_groups = self._mlag_peer_facts_generator._endpoint_vlans_and_trunk_groups
        return endpoint_trunk_groups.union(mlag_endpoint_trunk_groups)

    @remove_cached_property_type
    @cached_property
    def local_endpoint_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.LocalEndpointTrunkGroups:
        """
        Return list of trunk_groups in use by endpoints connected to this switch only.

        Used for only applying the trunk groups in config that are relevant on this device
        This is a subset of endpoint_trunk_groups which is used for filtering.
        """
        if self.shared_utils.only_local_vlan_trunk_groups:
            _, local_endpoint_trunk_groups = self._local_endpoint_vlans_and_trunk_groups
            return EosDesignsFactsProtocol.LocalEndpointTrunkGroups(natural_sort(local_endpoint_trunk_groups))

        return EosDesignsFactsProtocol.LocalEndpointTrunkGroups()

    @remove_cached_property_type
    @cached_property
    def endpoint_trunk_groups(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.EndpointTrunkGroups:
        """
        Return list of trunk_groups in use by endpoints connected to this switch, downstream switches or MLAG peer.

        Used for filtering which vlans we configure on the device. This is a superset of local_endpoint_trunk_groups.
        """
        return EosDesignsFactsProtocol.EndpointTrunkGroups(natural_sort(self._endpoint_trunk_groups))

    @cached_property
    def _vlans(self: EosDesignsFactsGeneratorProtocol) -> list[int]:
        """
        Return list of vlans after filtering network services.

        The filter is based on filter.tenants, filter.tags and filter.only_vlans_in_use.

        Ex. [1, 2, 3 ,4 ,201, 3021]
        """
        if not self.shared_utils.any_network_services:
            return []

        vlans = []
        for network_services_key in self.inputs._dynamic_keys.network_services:
            tenants = network_services_key.value
            for tenant in tenants:
                if not set(self.shared_utils.node_config.filter.tenants).intersection([tenant.name, "all"]):
                    # Not matching tenant filters. Skipping this tenant.
                    continue

                vlans.extend(svi.id for vrf in tenant.vrfs for svi in vrf.svis if self._is_accepted_vlan(svi))
                vlans.extend(l2vlan.id for l2vlan in tenant.l2vlans if self._is_accepted_vlan(l2vlan))

        return vlans

    def _is_accepted_vlan(
        self: EosDesignsFactsGeneratorProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
    ) -> bool:
        if "all" not in self.shared_utils.filter_tags and not set(vlan.tags).intersection(self.shared_utils.filter_tags):
            return False

        if not self.shared_utils.node_config.filter.only_vlans_in_use:
            # Nothing else to filter
            return True

        # Check if vlan is in use
        if vlan.id in self._endpoint_vlans:
            return True

        # Check if vlan has a trunk group defined which is in use
        return bool(self.inputs.enable_trunk_groups and vlan.trunk_groups and self._endpoint_trunk_groups.intersection(vlan.trunk_groups))
