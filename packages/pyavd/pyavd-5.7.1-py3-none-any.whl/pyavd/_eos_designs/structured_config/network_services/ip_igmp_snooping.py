# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._utils import default

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import AvdStructuredConfigNetworkServicesProtocol


class IpIgmpSnoopingMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def ip_igmp_snooping(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """Set structured config for ip_igmp_snooping."""
        if not self.shared_utils.network_services_l2:
            return

        igmp_snooping_enabled = self.shared_utils.igmp_snooping_enabled
        self.structured_config.ip_igmp_snooping.globally_enabled = igmp_snooping_enabled
        if not igmp_snooping_enabled:
            return

        for tenant in self.shared_utils.filtered_tenants:
            for vrf in tenant.vrfs:
                for svi in vrf.svis:
                    self._set_ip_igmp_snooping_vlan(svi, tenant)
            for l2vlan in tenant.l2vlans:
                self._set_ip_igmp_snooping_vlan(l2vlan, tenant)

    def _set_ip_igmp_snooping_vlan(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> None:
        """
        Set ip_igmp_snooping structured_config for one vlan.

        Can be used for both svis and l2vlans
        """
        igmp_snooping_enabled = None
        igmp_snooping_querier_enabled = None
        evpn_l2_multicast_enabled = bool(default(vlan.evpn_l2_multicast.enabled, tenant.evpn_l2_multicast.enabled)) and self.shared_utils.evpn_multicast
        if self.shared_utils.overlay_vtep and evpn_l2_multicast_enabled:
            # Leaving igmp_snooping_enabled unset, to avoid extra line of config as we already check
            # that global igmp snooping is enabled and igmp snooping is required for evpn_l2_multicast.

            # Forcing querier to True since evpn_l2_multicast requires
            # querier on all vteps
            igmp_snooping_querier_enabled = True

        else:
            igmp_snooping_enabled = vlan.igmp_snooping_enabled
            if self.shared_utils.network_services_l3 and self.shared_utils.uplink_type in ["p2p", "p2p-vrfs"]:
                igmp_snooping_querier_enabled = default(vlan.igmp_snooping_querier.enabled, tenant.igmp_snooping_querier.enabled)

        vlan_item = EosCliConfigGen.IpIgmpSnooping.VlansItem()
        if igmp_snooping_enabled is not None:
            vlan_item.enabled = igmp_snooping_enabled

        if igmp_snooping_querier_enabled is not None:
            vlan_item.querier.enabled = igmp_snooping_querier_enabled
            if igmp_snooping_querier_enabled:
                vlan_item.querier.address = default(
                    vlan.igmp_snooping_querier.source_address, tenant.igmp_snooping_querier.source_address, self.shared_utils.router_id
                )
                vlan_item.querier.version = default(vlan.igmp_snooping_querier.version, tenant.igmp_snooping_querier.version)

        if evpn_l2_multicast_enabled:
            vlan_item.fast_leave = default(vlan.igmp_snooping_querier.fast_leave, tenant.evpn_l2_multicast.fast_leave)

        if vlan_item:
            vlan_item.id = vlan.id
            self.structured_config.ip_igmp_snooping.vlans.append(vlan_item)
