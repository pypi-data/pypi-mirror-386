# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import ipaddress
from functools import cached_property
from re import fullmatch as re_fullmatch
from typing import TYPE_CHECKING, Protocol, cast

from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError
from pyavd._utils import default, get_ip_from_ip_prefix
from pyavd.j2filters import natural_sort

if TYPE_CHECKING:
    from pyavd._eos_designs.schema import EosDesigns

    from . import AvdStructuredConfigNetworkServicesProtocol


class UtilsMixin(Protocol):
    """
    Mixin Class with internal functions.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @cached_property
    def _local_endpoint_trunk_groups(self: AvdStructuredConfigNetworkServicesProtocol) -> set:
        return set(self.facts.local_endpoint_trunk_groups)

    @cached_property
    def _vrf_default_evpn(self: AvdStructuredConfigNetworkServicesProtocol) -> bool:
        """Return boolean telling if VRF "default" is running EVPN or not."""
        if not (
            self.shared_utils.network_services_l3 and ((self.shared_utils.overlay_vtep and self.shared_utils.overlay_evpn) or self.shared_utils.is_wan_router)
        ):
            return False

        for tenant in self.shared_utils.filtered_tenants:
            if "default" not in tenant.vrfs:
                continue

            if "evpn" in tenant.vrfs["default"].address_families:
                if self.inputs.underlay_filter_peer_as:
                    msg = "'underlay_filter_peer_as' cannot be used while there are EVPN services in the default VRF."
                    raise AristaAvdError(msg)
                return True

        return False

    @cached_property
    def _vrf_default_ipv4_subnets(self: AvdStructuredConfigNetworkServicesProtocol) -> list[str]:
        """Return list of ipv4 subnets in VRF "default"."""
        subnets = []
        for tenant in self.shared_utils.filtered_tenants:
            if "default" not in tenant.vrfs:
                continue

            for svi in tenant.vrfs["default"].svis:
                ip_address = default(svi.ip_address, svi.ip_address_virtual)
                if ip_address is None:
                    continue

                subnet = str(ipaddress.ip_network(ip_address, strict=False))
                if subnet not in subnets:
                    subnets.append(subnet)

        return subnets

    @cached_property
    def _vrf_default_ipv4_static_routes(self: AvdStructuredConfigNetworkServicesProtocol) -> dict:
        """
        Finds static routes defined under VRF "default" and find out if they should be redistributed in underlay and/or overlay.

        Returns:
        -------
        dict
            static_routes: []
                List of ipv4 static routes in VRF "default"
            redistribute_in_underlay: bool
                Whether to redistribute static into the underlay protocol.
                True when there are any static routes this device is not an EVPN VTEP.
                Can be overridden with "vrf.redistribute_static: False".
            redistribute_in_overlay: bool
                Whether to redistribute static into overlay protocol for vrf default.
                True there are any static routes and this device is an EVPN VTEP.
                Can be overridden with "vrf.redistribute_static: False".
        """
        vrf_default_ipv4_static_routes = set()
        vrf_default_redistribute_static = True
        for tenant in self.shared_utils.filtered_tenants:
            if "default" not in tenant.vrfs:
                continue

            if not (static_routes := tenant.vrfs["default"].static_routes):
                continue

            for static_route in static_routes:
                vrf_default_ipv4_static_routes.add(static_route.prefix or static_route.destination_address_prefix)

            vrf_default_redistribute_static = default(tenant.vrfs["default"].redistribute_static, vrf_default_redistribute_static)

        if (self.shared_utils.overlay_evpn and self.shared_utils.overlay_vtep) or self.shared_utils.is_wan_router:
            # This is an EVPN VTEP
            redistribute_in_underlay = False
            redistribute_in_overlay = vrf_default_redistribute_static and vrf_default_ipv4_static_routes
        else:
            # This is a not an EVPN VTEP
            redistribute_in_underlay = vrf_default_redistribute_static and vrf_default_ipv4_static_routes
            redistribute_in_overlay = False

        return {
            "static_routes": natural_sort(vrf_default_ipv4_static_routes),
            "redistribute_in_underlay": redistribute_in_underlay,
            "redistribute_in_overlay": redistribute_in_overlay,
        }

    def _mlag_ibgp_peering_enabled(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> bool:
        """
        Returns True if mlag ibgp_peering is enabled.

        For VRF default we return False unless there is no underlay routing protocol.

        False otherwise.
        """
        if not self.shared_utils.mlag_l3 or not self.shared_utils.network_services_l3:
            return False

        mlag_ibgp_peering = default(vrf.enable_mlag_ibgp_peering_vrfs, tenant.enable_mlag_ibgp_peering_vrfs)
        return bool((vrf.name != "default" or self.shared_utils.underlay_routing_protocol == "none") and mlag_ibgp_peering)

    def _mlag_ibgp_peering_vlan_vrf(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> int | None:
        """
        MLAG IBGP Peering VLANs per VRF.

        Performs all relevant checks if MLAG IBGP Peering is enabled
        Returns None if peering is not enabled
        """
        if not self._mlag_ibgp_peering_enabled(vrf, tenant):
            return None

        if (mlag_ibgp_peering_vlan := vrf.mlag_ibgp_peering_vlan) is not None:
            vlan_id = mlag_ibgp_peering_vlan
        else:
            base_vlan = self.inputs.mlag_ibgp_peering_vrfs.base_vlan
            vrf_id = default(vrf.vrf_id, vrf.vrf_vni)
            if vrf_id is None:
                msg = f"Unable to assign MLAG VRF Peering VLAN for vrf {vrf.name}.Set either 'mlag_ibgp_peering_vlan' or 'vrf_id' or 'vrf_vni' on the VRF"
                raise AristaAvdInvalidInputsError(msg)
            vlan_id = base_vlan + vrf_id - 1

        return vlan_id

    def _exclude_mlag_ibgp_peering_from_redistribute(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> bool:
        """
        Returns True if redistribute_connected is True and MLAG IBGP Peering subnet should be _excluded_ from redistribution for the given vrf/tenant.

        Does _not_ include checks if the peering is enabled at all, so that should be checked first.
        """
        if vrf.redistribute_connected:
            return default(vrf.redistribute_mlag_ibgp_peering_vrfs, tenant.redistribute_mlag_ibgp_peering_vrfs) is False

        return False

    @cached_property
    def _rt_admin_subfield(self: AvdStructuredConfigNetworkServicesProtocol) -> str | None:
        """
        Return a string with the route-target admin subfield unless set to "vrf_id" or "vrf_vni" or "id".

        Returns None if not set, since the calling functions will use
        per-vlan numbers by default.
        """
        admin_subfield = self.inputs.overlay_rt_type.admin_subfield
        if admin_subfield is None:
            return None

        if admin_subfield == "bgp_as":
            return self.shared_utils.bgp_as

        if re_fullmatch(r"\d+", str(admin_subfield)):
            return admin_subfield

        return None

    def get_vlan_mac_vrf_id(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> int:
        mac_vrf_id_base = default(tenant.mac_vrf_id_base, tenant.mac_vrf_vni_base)
        if mac_vrf_id_base is None:
            msg = (
                "'rt_override' or 'vni_override' or 'mac_vrf_id_base' or 'mac_vrf_vni_base' must be set. "
                f"Unable to set EVPN RD/RT for vlan {vlan.id} in Tenant '{tenant.name}'"
            )
            raise AristaAvdInvalidInputsError(msg)
        return mac_vrf_id_base + vlan.id

    def get_vlan_mac_vrf_vni(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> int:
        mac_vrf_vni_base = default(tenant.mac_vrf_vni_base, tenant.mac_vrf_id_base)
        if mac_vrf_vni_base is None:
            msg = (
                "'rt_override' or 'vni_override' or 'mac_vrf_id_base' or 'mac_vrf_vni_base' must be set. "
                f"Unable to set EVPN RD/RT for vlan {vlan.id} in Tenant '{tenant.name}'"
            )
            raise AristaAvdInvalidInputsError(msg)
        return mac_vrf_vni_base + vlan.id

    def get_vlan_rd(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> str:
        """Return a string with the route-destinguisher for one VLAN."""
        rd_override = default(vlan.rd_override, vlan.rt_override, vlan.vni_override)

        if isinstance(rd_override, str) and (":" in rd_override or rd_override == "auto"):
            return rd_override

        if rd_override is not None:
            assigned_number_subfield = rd_override
        elif self.inputs.overlay_rd_type.vlan_assigned_number_subfield == "mac_vrf_vni":
            assigned_number_subfield = self.get_vlan_mac_vrf_vni(vlan, tenant)
        elif self.inputs.overlay_rd_type.vlan_assigned_number_subfield == "vlan_id":
            assigned_number_subfield = vlan.id
        else:
            assigned_number_subfield = self.get_vlan_mac_vrf_id(vlan, tenant)

        return f"{self.shared_utils.overlay_rd_type_admin_subfield}:{assigned_number_subfield}"

    def get_vlan_rt(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vlan: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem.SvisItem
        | EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.L2vlansItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> str:
        """Return a string with the route-target for one VLAN."""
        rt_override = default(vlan.rt_override, vlan.vni_override)

        if isinstance(rt_override, str) and ":" in rt_override:
            return rt_override

        if self._rt_admin_subfield is not None:
            admin_subfield = self._rt_admin_subfield
        elif rt_override is not None:
            admin_subfield = rt_override
        elif self.inputs.overlay_rt_type.admin_subfield == "vrf_vni":
            admin_subfield = self.get_vlan_mac_vrf_vni(vlan, tenant)
        elif self.inputs.overlay_rt_type.admin_subfield == "id":
            admin_subfield = vlan.id
        else:
            admin_subfield = self.get_vlan_mac_vrf_id(vlan, tenant)

        if rt_override is not None:
            assigned_number_subfield = rt_override
        elif self.inputs.overlay_rt_type.vlan_assigned_number_subfield == "mac_vrf_vni":
            assigned_number_subfield = self.get_vlan_mac_vrf_vni(vlan, tenant)
        elif self.inputs.overlay_rt_type.vlan_assigned_number_subfield == "vlan_id":
            assigned_number_subfield = vlan.id
        else:
            assigned_number_subfield = self.get_vlan_mac_vrf_id(vlan, tenant)

        return f"{admin_subfield}:{assigned_number_subfield}"

    @cached_property
    def _vrf_rt_admin_subfield(self: AvdStructuredConfigNetworkServicesProtocol) -> str | None:
        """
        Return a string with the VRF route-target admin subfield unless set to "vrf_id" or "vrf_vni" or "id".

        Returns None if not set, since the calling functions will use
        per-vrf numbers by default.
        """
        admin_subfield: str = default(self.inputs.overlay_rt_type.vrf_admin_subfield, self.inputs.overlay_rt_type.admin_subfield)
        if admin_subfield == "bgp_as":
            return self.shared_utils.bgp_as

        if re_fullmatch(r"\d+", admin_subfield):
            return admin_subfield

        return None

    def get_vrf_rd_admin_subfield(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> str:
        """Return a string with the route-destinguisher admin subfield for one VRF. Only called for routers where we know we have a router_id."""
        if (vrf_rd_admin_subfield := self.shared_utils.overlay_rd_type_vrf_admin_subfield) == "vrf_router_id":
            return cast("str", self.get_vrf_router_id(vrf, tenant, vrf.bgp.router_id) or self.shared_utils.router_id)

        return vrf_rd_admin_subfield

    def get_vrf_rd(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
    ) -> str:
        """Return a string with the route-destinguisher for one VRF."""
        rd_override = vrf.rd_override
        admin_subfield = self.get_vrf_rd_admin_subfield(vrf, tenant)

        if rd_override is not None:
            if ":" in rd_override:
                return rd_override

            return f"{admin_subfield}:{rd_override}"

        return f"{admin_subfield}:{self.shared_utils.get_vrf_id(vrf)}"

    def get_vrf_rt(
        self: AvdStructuredConfigNetworkServicesProtocol, vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem
    ) -> str:
        """Return a string with the route-target for one VRF."""
        rt_override = vrf.rt_override

        if rt_override is not None and ":" in rt_override:
            return rt_override

        if self._vrf_rt_admin_subfield is not None:
            admin_subfield = self._vrf_rt_admin_subfield
        elif default(self.inputs.overlay_rt_type.vrf_admin_subfield, self.inputs.overlay_rt_type.admin_subfield) == "vrf_vni":
            admin_subfield = self.shared_utils.get_vrf_vni(vrf)
        else:
            # Both for 'id' and 'vrf_id' options.
            admin_subfield = self.shared_utils.get_vrf_id(vrf)

        if rt_override is not None:
            return f"{admin_subfield}:{rt_override}"

        return f"{admin_subfield}:{self.shared_utils.get_vrf_id(vrf)}"

    def get_vlan_aware_bundle_rd(
        self: AvdStructuredConfigNetworkServicesProtocol,
        id: int,  # noqa: A002
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem | None,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
        rd_override: str | None = None,
    ) -> str:
        """Return a string with the route-destinguisher for one VLAN Aware Bundle."""
        admin_subfield = self.get_vrf_rd_admin_subfield(vrf, tenant) if vrf is not None else self.shared_utils.overlay_rd_type_admin_subfield

        if rd_override is not None:
            if ":" in rd_override or rd_override == "auto":
                return rd_override

            return f"{admin_subfield}:{rd_override}"

        bundle_number = id + tenant.vlan_aware_bundle_number_base
        return f"{admin_subfield}:{bundle_number}"

    def get_vlan_aware_bundle_rt(
        self: AvdStructuredConfigNetworkServicesProtocol,
        id: int,  # noqa: A002
        vni: int,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
        is_vrf: bool,
        rt_override: str | None = None,
    ) -> str:
        """Return a string with the route-target for one VLAN Aware Bundle."""
        if rt_override is not None and ":" in str(rt_override):
            return rt_override

        bundle_number = id + tenant.vlan_aware_bundle_number_base

        if is_vrf and self._vrf_rt_admin_subfield is not None:
            admin_subfield = self._vrf_rt_admin_subfield
        elif is_vrf and default(self.inputs.overlay_rt_type.vrf_admin_subfield, self.inputs.overlay_rt_type.admin_subfield) == "vrf_vni":
            admin_subfield = vni
        else:
            # Both for 'id' and 'vrf_id' options.
            admin_subfield = bundle_number

        if rt_override is not None:
            return f"{admin_subfield}:{rt_override}"

        return f"{admin_subfield}:{bundle_number}"

    def get_vrf_router_id(
        self: AvdStructuredConfigNetworkServicesProtocol,
        vrf: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem.VrfsItem,
        tenant: EosDesigns._DynamicKeys.DynamicNetworkServicesItem.NetworkServicesItem,
        router_id: str,
    ) -> str | None:
        """
        Determine the router ID for a given VRF based on its configuration.

        Args:
            vrf: The VRF object containing OSPF/BGP and vtep_diagnostic details.
            tenant: The Tenant to which the VRF belongs.
            router_id: The router ID type specified for the VRF (e.g., "vtep_diagnostic", "main_router_id", "none", or an IPv4 address).

        Returns:
            The resolved router ID as a string, or None if the router ID is not applicable.

        Raises:
            AristaAvdInvalidInputsError: If required configuration for "vtep_diagnostic" router ID is missing.
        """
        # Handle "vtep_diagnostic" router ID case
        if router_id == "diagnostic_loopback":
            # Validate required configuration
            if (interface_data := self._get_vtep_diagnostic_loopback_for_vrf(vrf, tenant)) is None or not interface_data.ip_address:
                msg = (
                    f"Invalid configuration on VRF '{vrf.name}' in Tenant '{tenant.name}'. "
                    "'vtep_diagnostic.loopback' along with either 'vtep_diagnostic.loopback_ip_pools' or 'vtep_diagnostic.loopback_ip_range' must be defined "
                    "when 'router_id' is set to 'diagnostic_loopback' on the VRF."
                )
                raise AristaAvdInvalidInputsError(msg)
            # Resolve router ID from loopback interface
            return get_ip_from_ip_prefix(interface_data.ip_address)
        if router_id == "main_router_id":
            return self.shared_utils.router_id if not self.inputs.use_router_general_for_router_id else None
        # Handle "none" router ID
        if router_id == "none":
            return None

        # Default to the specified router ID
        return router_id
