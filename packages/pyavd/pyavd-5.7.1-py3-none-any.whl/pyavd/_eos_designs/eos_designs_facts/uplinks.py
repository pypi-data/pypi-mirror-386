# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import re
from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_designs.eos_designs_facts.schema import EosDesignsFactsProtocol
from pyavd._errors import AristaAvdError, AristaAvdInvalidInputsError
from pyavd._utils import get, remove_cached_property_type
from pyavd.j2filters import list_compress, natural_sort, range_expand

if TYPE_CHECKING:
    from . import EosDesignsFactsGeneratorProtocol


class UplinksMixin(EosDesignsFactsProtocol, Protocol):
    """
    Mixin Class used to generate some of the EosDesignsFacts.

    Class should only be used as Mixin to the EosDesignsFacts class.
    Using type-hint on self to get proper type-hints on attributes across all Mixins.
    """

    @remove_cached_property_type
    @cached_property
    def max_parallel_uplinks(self: EosDesignsFactsGeneratorProtocol) -> int:
        """Exposed in avd_switch_facts."""
        return self.shared_utils.node_config.max_parallel_uplinks

    @remove_cached_property_type
    @cached_property
    def max_uplink_switches(self: EosDesignsFactsGeneratorProtocol) -> int:
        """Exposed in avd_switch_facts."""
        return self.shared_utils.max_uplink_switches

    @cached_property
    def _uplink_port_channel_id(self: EosDesignsFactsGeneratorProtocol) -> int:
        """
        For MLAG secondary get the uplink_port_channel_id from the peer's facts.

        We don't need to validate it (1-2000), since it will be validated on the peer.

        For MLAG primary or none MLAG, take the value of 'uplink_port_channel_id' if set,
        or use the numbers from the first interface in 'uplink_interfaces'.

        For MLAG primary validate that the port-channel id falls within 1-2000 since we also use this ID as MLAG ID.
        """
        uplink_port_channel_id = self.shared_utils.node_config.uplink_port_channel_id

        if self.shared_utils.mlag_role == "secondary":
            # MLAG Secondary
            peer_uplink_port_channel_id = self._mlag_peer_facts_generator._uplink_port_channel_id
            # check that port-channel IDs are the same as on primary
            if uplink_port_channel_id is not None and uplink_port_channel_id != peer_uplink_port_channel_id:
                msg = (
                    f"'uplink_port_channel_id' is set to {uplink_port_channel_id} and is not matching {peer_uplink_port_channel_id} set on MLAG peer."
                    " The 'uplink_port_channel_id' must be matching on MLAG peers."
                )
                raise AristaAvdError(msg)
            return peer_uplink_port_channel_id

        # MLAG Primary or not MLAG.
        if uplink_port_channel_id is None:
            # Overwriting uplink_port_channel_id
            uplink_port_channel_id = int("".join(re.findall(r"\d", self.shared_utils.uplink_interfaces[0])))

        # produce an error if the switch is MLAG and port-channel ID is above 2000
        if self.shared_utils.mlag and not 1 <= uplink_port_channel_id <= 2000:
            msg = f"'uplink_port_channel_id' must be between 1 and 2000 for MLAG switches. Got '{uplink_port_channel_id}'."
            raise AristaAvdError(msg)

        return uplink_port_channel_id

    @cached_property
    def _uplink_switch_port_channel_id(self: EosDesignsFactsGeneratorProtocol) -> int:
        """
        For MLAG secondary get the uplink_switch_port_channel_id from the peer's facts.

        We don't need to validate it (1-2000), since it will be validated on the peer.

        For MLAG primary or none MLAG, take the value of 'uplink_switch_port_channel_id' if set,
        or use the numbers from the first interface in 'uplink_switch_interfaces'.

        If the *uplink_switch* is in MLAG,  validate that the port-channel id falls within 1-2000
        since we also use this ID as MLAG ID on the *uplink switch*.
        """
        uplink_switch_port_channel_id = self.shared_utils.node_config.uplink_switch_port_channel_id

        if self.shared_utils.mlag_role == "secondary":
            # MLAG Secondary
            peer_uplink_switch_port_channel_id = self._mlag_peer_facts_generator._uplink_switch_port_channel_id
            # check that port-channel IDs are the same as on primary
            if uplink_switch_port_channel_id is not None and uplink_switch_port_channel_id != peer_uplink_switch_port_channel_id:
                msg = (
                    f"'uplink_switch_port_channel_id' is set to {uplink_switch_port_channel_id} and is not matching {peer_uplink_switch_port_channel_id} "
                    "set on MLAG peer. The 'uplink_switch_port_channel_id' must be matching on MLAG peers."
                )
                raise AristaAvdError(msg)
            return peer_uplink_switch_port_channel_id

        # MLAG Primary or not MLAG.
        if uplink_switch_port_channel_id is None:
            # Overwriting uplink_switch_port_channel_id
            uplink_switch_port_channel_id = int("".join(re.findall(r"\d", self.uplink_switch_interfaces[0])))

        # produce an error if the uplink switch is MLAG and port-channel ID is above 2000
        uplink_switch_facts = self.get_peer_facts_generator(self.shared_utils.uplink_switches[0])
        if uplink_switch_facts.shared_utils.mlag and not 1 <= uplink_switch_port_channel_id <= 2000:
            msg = f"'uplink_switch_port_channel_id' must be between 1 and 2000 for MLAG switches. Got '{uplink_switch_port_channel_id}'."
            raise AristaAvdError(msg)

        return uplink_switch_port_channel_id

    @remove_cached_property_type
    @cached_property
    def uplinks(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.Uplinks:
        """
        Exposed in avd_switch_facts.

        List of uplinks with all parameters

        These facts are leveraged by templates for this device when rendering uplinks
        and by templates for peer devices when rendering downlinks
        """
        if self.shared_utils.uplink_type == "port-channel":
            get_uplink = self._get_port_channel_uplink
        elif self.shared_utils.uplink_type == "p2p-vrfs":
            if self.shared_utils.network_services_l3 is False or self.shared_utils.underlay_router is False:
                msg = "'underlay_router' and 'network_services.l3' must be 'true' for the node_type_key when using 'p2p-vrfs' as 'uplink_type'."
                raise AristaAvdError(msg)
            get_uplink = self._get_p2p_vrfs_uplink
        elif self.shared_utils.uplink_type == "lan":
            if self.shared_utils.network_services_l3 is False or self.shared_utils.underlay_router is False:
                msg = "'underlay_router' and 'network_services.l3' must be 'true' for the node_type_key when using 'lan' as 'uplink_type'."
                raise AristaAvdError(msg)
            if len(self.shared_utils.uplink_interfaces) > 1:
                msg = f"'uplink_type: lan' only supports a single uplink interface. Got {self.shared_utils.uplink_interfaces}."
                raise AristaAvdError(msg)
                # TODO: Adjust error message when we add lan-port-channel support.
                # uplink_type: lan' only supports a single uplink interface.
                # Got {self._uplink_interfaces}. Consider 'uplink_type: lan-port-channel' if applicable.
            get_uplink = self._get_l2_uplink
        else:
            # Uplink type is 'p2p'.
            get_uplink = self._get_p2p_uplink

        uplinks = EosDesignsFactsProtocol.Uplinks()
        uplink_switches = self.shared_utils.uplink_switches
        uplink_switch_interfaces = self.uplink_switch_interfaces
        for uplink_index, uplink_interface in enumerate(self.shared_utils.uplink_interfaces):
            if len(uplink_switches) <= uplink_index or len(uplink_switch_interfaces) <= uplink_index:
                # Invalid length of input variables. Skipping
                continue

            uplink_switch = uplink_switches[uplink_index]
            uplink_switch_interface = uplink_switch_interfaces[uplink_index]

            uplink = get_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface)
            uplinks.append(uplink)

        return uplinks

    def _get_p2p_uplink(
        self: EosDesignsFactsGeneratorProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFactsProtocol.UplinksItem:
        """Return a single uplink dictionary for uplink_type p2p."""
        uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)
        uplink = EosDesignsFactsProtocol.UplinksItem(
            interface=uplink_interface,
            peer=uplink_switch,
            peer_interface=uplink_switch_interface,
            peer_type=uplink_switch_facts.type,
            peer_is_deployed=uplink_switch_facts.is_deployed,
            peer_bgp_as=uplink_switch_facts.bgp_as,
            type="underlay_p2p",
        )
        if self.shared_utils.uplink_interface_speed is not None:
            uplink.speed = self.shared_utils.uplink_interface_speed

        if self.shared_utils.node_config.uplink_bfd:
            uplink.bfd = True

        if self.shared_utils.uplink_switch_interface_speed is not None:
            uplink.peer_speed = self.shared_utils.uplink_switch_interface_speed

        if self.shared_utils.platform_settings.feature_support.ptp:
            if uplink_ptp := self.shared_utils.node_config.uplink_ptp:
                uplink.ptp.enable = uplink_ptp.enable
            elif self.shared_utils.ptp_enabled and (not (ptp_uplinks := self.shared_utils.node_config.ptp.uplinks) or (uplink_interface in ptp_uplinks)):
                uplink.ptp.enable = True

        if self.shared_utils.node_config.uplink_macsec.profile:
            uplink.mac_security.profile = self.shared_utils.node_config.uplink_macsec.profile

        if (
            self.shared_utils.underlay_multicast_pim_sm_enabled
            and uplink_switch_facts.shared_utils.underlay_multicast_pim_sm_enabled
            and self.shared_utils.node_config.underlay_multicast.pim_sm.uplinks
            and (
                not self.shared_utils.node_config.underlay_multicast.pim_sm.uplink_interfaces
                or uplink_interface in self.shared_utils.node_config.underlay_multicast.pim_sm.uplink_interfaces
            )
        ):
            # means all uplinks are enabled or uplinks are filtered and this uplink interface is accepted
            uplink.underlay_multicast_pim_sm = True
        if (
            self.shared_utils.underlay_multicast_static_enabled
            and uplink_switch_facts.shared_utils.underlay_multicast_static_enabled
            and self.shared_utils.node_config.underlay_multicast.static.uplinks
            and (
                not self.shared_utils.node_config.underlay_multicast.static.uplink_interfaces
                or uplink_interface in self.shared_utils.node_config.underlay_multicast.static.uplink_interfaces
            )
        ):
            # means all uplinks are enabled or uplinks are filtered and this uplink interface is accepted
            uplink.underlay_multicast_static = True

        if self.inputs.underlay_rfc5549:
            uplink.ipv6_enable = True
        elif self.shared_utils.underlay_ipv6_numbered:
            uplink.prefix_length = self.inputs.fabric_ip_addressing.p2p_uplinks.ipv6_prefix_length
            uplink.ip_address = self.shared_utils.ip_addressing.p2p_uplinks_ipv6(uplink_index)
            uplink.peer_ip_address = self.shared_utils.ip_addressing.p2p_uplinks_peer_ipv6(uplink_index)
        else:
            uplink.prefix_length = self.inputs.fabric_ip_addressing.p2p_uplinks.ipv4_prefix_length
            uplink.ip_address = self.shared_utils.ip_addressing.p2p_uplinks_ip(uplink_index)
            uplink.peer_ip_address = self.shared_utils.ip_addressing.p2p_uplinks_peer_ip(uplink_index)

        if self.shared_utils.link_tracking_groups is not None:
            uplink.link_tracking_groups.extend(
                EosDesignsFactsProtocol.UplinksItem.LinkTrackingGroupsItem(name=lt_group.name, direction="upstream")
                for lt_group in self.shared_utils.link_tracking_groups
            )
        self._update_uplink_structured_config(uplink)

        return uplink

    def _get_port_channel_uplink(
        self: EosDesignsFactsGeneratorProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFactsProtocol.UplinksItem:
        """Return a single uplink dictionary for uplink_type port-channel."""
        uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)

        # Reusing get_l2_uplink
        uplink = self._get_l2_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface)

        if uplink_switch_facts.shared_utils.mlag is True or self._short_esi is not None:
            # Override our description on port-channel to be peer's group name if they are mlag pair or A/A #}
            uplink.peer_node_group = uplink_switch_facts.shared_utils.group

        # Used to determine whether or not port-channel should have an mlag id configure on the uplink_switch
        unique_uplink_switches = set(self.shared_utils.uplink_switches)
        if self.shared_utils.mlag is True:
            # Override the peer's description on port-channel to be our group name if we are mlag pair #}
            uplink.node_group = self.shared_utils.group

            # Updating unique_uplink_switches with our mlag peer's uplink switches
            unique_uplink_switches.update(self._mlag_peer_facts_generator.shared_utils.uplink_switches)

        # Only enable mlag for this port-channel on the uplink switch if there are multiple unique uplink switches
        uplink.peer_mlag = len(unique_uplink_switches) > 1

        uplink.channel_group_id = self._uplink_port_channel_id
        uplink.peer_channel_group_id = self._uplink_switch_port_channel_id

        return uplink

    def _get_l2_uplink(
        self: EosDesignsFactsGeneratorProtocol,
        uplink_index: int,  # pylint: disable=unused-argument # noqa: ARG002
        uplink_interface: str,
        uplink_switch: str,
        uplink_switch_interface: str,
    ) -> EosDesignsFactsProtocol.UplinksItem:
        """Return a single uplink dictionary for an L2 uplink. Reused for both uplink_type port-channel, lan and TODO: lan-port-channel."""
        uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)
        uplink = EosDesignsFactsProtocol.UplinksItem(
            interface=uplink_interface,
            peer=uplink_switch,
            peer_interface=uplink_switch_interface,
            peer_type=uplink_switch_facts.type,
            peer_is_deployed=uplink_switch_facts.is_deployed,
            type="underlay_l2",
        )
        if self.shared_utils.uplink_interface_speed is not None:
            uplink.speed = self.shared_utils.uplink_interface_speed

        if self.shared_utils.uplink_switch_interface_speed is not None:
            uplink.peer_speed = self.shared_utils.uplink_switch_interface_speed

        if self.shared_utils.platform_settings.feature_support.ptp:
            if self.shared_utils.node_config.uplink_ptp:
                uplink.ptp.enable = self.shared_utils.node_config.uplink_ptp.enable
            elif self.shared_utils.ptp_enabled:
                uplink.ptp.enable = True

        # Remove vlans if upstream switch does not have them #}
        if self.inputs.enable_trunk_groups:
            uplink.trunk_groups.append_unique("UPLINK")
            if self.shared_utils.mlag is True and self.shared_utils.group:
                uplink.peer_trunk_groups.append_unique(self.shared_utils.group)
            else:
                uplink.peer_trunk_groups.append_unique(self.shared_utils.hostname)

        uplink_vlans = set(self._vlans)
        uplink_vlans = uplink_vlans.intersection(uplink_switch_facts._vlans)

        if self.shared_utils.configure_inband_mgmt or self.shared_utils.configure_inband_mgmt_ipv6:
            # Always add inband_mgmt_vlan even if the uplink switch does not have this vlan defined
            uplink_vlans.add(self.shared_utils.node_config.inband_mgmt_vlan)

        uplink.vlans = list_compress(list(uplink_vlans)) if uplink_vlans else "none"

        if uplink_native_vlan := self.shared_utils.node_config.uplink_native_vlan:
            uplink.native_vlan = uplink_native_vlan

        if self._short_esi is not None:
            uplink.peer_short_esi = self._short_esi

        if self.shared_utils.link_tracking_groups is not None:
            uplink.link_tracking_groups.extend(
                EosDesignsFactsProtocol.UplinksItem.LinkTrackingGroupsItem(name=lt_group.name, direction="upstream")
                for lt_group in self.shared_utils.link_tracking_groups
            )

        if not self.shared_utils.network_services_l2:
            # This child device does not support VLANs, so we tell the peer to enable portfast
            uplink.peer_spanning_tree_portfast = "edge"

        self._update_uplink_structured_config(uplink)
        return uplink

    def _get_p2p_vrfs_uplink(
        self: EosDesignsFactsGeneratorProtocol, uplink_index: int, uplink_interface: str, uplink_switch: str, uplink_switch_interface: str
    ) -> EosDesignsFactsProtocol.UplinksItem:
        """Return a single uplink dictionary for uplink_type p2p-vrfs."""
        uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)

        # Reusing regular p2p logic for main interface.
        uplink = self._get_p2p_uplink(uplink_index, uplink_interface, uplink_switch, uplink_switch_interface)
        for tenant in self.shared_utils.filtered_tenants:
            for vrf in tenant.vrfs:
                # Only keep VRFs present on the uplink switch as well.
                # Also skip VRF default since it is covered on the parent interface.
                # ok to use like this because this is only ever called inside EosDesignsFacts
                uplink_switch_vrfs = uplink_switch_facts.shared_utils.vrfs
                if vrf.name == "default" or vrf.name not in uplink_switch_vrfs:
                    continue

                vrf_id = self.shared_utils.get_vrf_id(vrf)
                subinterface = EosDesignsFactsProtocol.UplinksItem.SubinterfacesItem(
                    interface=f"{uplink_interface}.{vrf_id}",
                    peer_interface=f"{uplink_switch_interface}.{vrf_id}",
                    vrf=vrf.name,
                    encapsulation_dot1q_vlan=vrf_id,
                )

                if self.inputs.underlay_rfc5549:
                    subinterface.ipv6_enable = True
                elif self.shared_utils.underlay_ipv6_numbered:
                    subinterface.ipv6_prefix_length = self.inputs.fabric_ip_addressing.p2p_uplinks.ipv6_prefix_length
                    subinterface.ipv6_address = self.shared_utils.ip_addressing.p2p_vrfs_uplinks_ipv6(uplink_index, vrf.name)
                    subinterface.peer_ipv6_address = self.shared_utils.ip_addressing.p2p_vrfs_uplinks_peer_ipv6(uplink_index, vrf.name)
                else:
                    subinterface.prefix_length = self.inputs.fabric_ip_addressing.p2p_uplinks.ipv4_prefix_length
                    subinterface.ip_address = self.shared_utils.ip_addressing.p2p_vrfs_uplinks_ip(uplink_index, vrf.name)
                    subinterface.peer_ip_address = self.shared_utils.ip_addressing.p2p_vrfs_uplinks_peer_ip(uplink_index, vrf.name)

                if self.shared_utils.node_config.uplink_structured_config is not None:
                    subinterface.structured_config = self.shared_utils.node_config.uplink_structured_config

                uplink.subinterfaces.append(subinterface)

        return uplink

    def _update_uplink_structured_config(self: EosDesignsFactsGeneratorProtocol, uplink: EosDesignsFactsProtocol.UplinksItem) -> None:
        """
        Update uplink object with structured_config keys.

        Take structured config from the various input keys and apply it to uplink.
        - `uplink_ethernet_structured_config`
        - `uplink_switch_ethernet_structured_config`
        - `uplink_port_channel_structured_config`
        - `uplink_switch_port_channel_structured_config`

        OR

        - `uplink_structured_config` (deprecated) TODO: Remove in AVD 6.0.0
        """
        if ethernet_struct_config := self.shared_utils.node_config.uplink_ethernet_structured_config:
            uplink.ethernet_structured_config = ethernet_struct_config
        if peer_ethernet_struct_config := self.shared_utils.node_config.uplink_switch_ethernet_structured_config:
            uplink.peer_ethernet_structured_config = peer_ethernet_struct_config
        if port_channel_struct_config := self.shared_utils.node_config.uplink_port_channel_structured_config:
            uplink.port_channel_structured_config = port_channel_struct_config
        if peer_port_channel_struct_config := self.shared_utils.node_config.uplink_switch_port_channel_structured_config:
            uplink.peer_port_channel_structured_config = peer_port_channel_struct_config

        if (
            not any((ethernet_struct_config, peer_ethernet_struct_config, port_channel_struct_config, peer_port_channel_struct_config))
            and self.shared_utils.node_config.uplink_structured_config is not None
        ):
            uplink.structured_config = self.shared_utils.node_config.uplink_structured_config

    @remove_cached_property_type
    @cached_property
    def uplink_peers(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.UplinkPeers:
        """
        Exposed in avd_switch_facts.

        List of all **unique** uplink peers

        These are used to generate the "avd_topology_peers" fact covering downlinks for all devices.
        """
        # Since uplinks logic silently skips extra entries in uplink vars, we only need to parse shortest list.
        min_length = min(len(self.uplink_switch_interfaces), len(self.shared_utils.uplink_interfaces), len(self.shared_utils.uplink_switches))
        # Using set to only get unique uplink switches
        unique_uplink_switches = set(self.shared_utils.uplink_switches[:min_length])
        return EosDesignsFactsProtocol.UplinkPeers(natural_sort(unique_uplink_switches))

    @cached_property
    def _default_downlink_interfaces(self: EosDesignsFactsGeneratorProtocol) -> list:
        """
        Internal _default_downlink_interfaces set based on default_interfaces.

        Parsed by downstream switches during eos_designs_facts phase.
        """
        return range_expand(self.shared_utils.default_interfaces.downlink_interfaces)

    @remove_cached_property_type
    @cached_property
    def uplink_switch_vrfs(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.UplinkSwitchVrfs:
        """
        Exposed in avd_switch_facts.

        Return the list of VRF names present on uplink switches.
        """
        if self.shared_utils.uplink_type != "p2p-vrfs":
            return EosDesignsFactsProtocol.UplinkSwitchVrfs()

        vrfs = set()
        for uplink_switch in self.uplink_peers:
            uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)
            vrfs.update(uplink_switch_facts.shared_utils.vrfs)

        return EosDesignsFactsProtocol.UplinkSwitchVrfs(natural_sort(vrfs))

    @remove_cached_property_type
    @cached_property
    def uplink_switch_interfaces(self: EosDesignsFactsGeneratorProtocol) -> EosDesignsFactsProtocol.UplinkSwitchInterfaces:
        uplink_switch_interfaces = (
            self.shared_utils.node_config.uplink_switch_interfaces or get(self.shared_utils.cv_topology_config, "uplink_switch_interfaces") or []
        )
        if uplink_switch_interfaces:
            return EosDesignsFactsProtocol.UplinkSwitchInterfaces(range_expand(uplink_switch_interfaces))

        if not self.shared_utils.uplink_switches:
            return EosDesignsFactsProtocol.UplinkSwitchInterfaces()

        if self.id is None:
            msg = f"'id' is not set on '{self.shared_utils.hostname}'."
            raise AristaAvdInvalidInputsError(msg)

        uplink_switch_interfaces = EosDesignsFactsProtocol.UplinkSwitchInterfaces()
        uplink_switch_counter = {}
        for uplink_switch in self.shared_utils.uplink_switches:
            uplink_switch_facts = self.get_peer_facts_generator(uplink_switch)

            # Count the number of instances the current switch was processed
            uplink_switch_counter[uplink_switch] = uplink_switch_counter.get(uplink_switch, 0) + 1
            index_of_parallel_uplinks = uplink_switch_counter[uplink_switch] - 1

            # Add uplink_switch_interface based on this switch's ID (-1 for 0-based) * max_parallel_uplinks + index_of_parallel_uplinks.
            # For max_parallel_uplinks: 2 this would assign downlink interfaces like this:
            # spine1 downlink-interface mapping: [ leaf-id1, leaf-id1, leaf-id2, leaf-id2, leaf-id3, leaf-id3, ... ]
            downlink_index = (self.id - 1) * self.shared_utils.node_config.max_parallel_uplinks + index_of_parallel_uplinks
            uplink_switch_downlink_interfaces_length = len(uplink_switch_facts._default_downlink_interfaces)
            if uplink_switch_downlink_interfaces_length > downlink_index:
                uplink_switch_interfaces.append(uplink_switch_facts._default_downlink_interfaces[downlink_index])
            elif uplink_switch_downlink_interfaces_length == 0:
                msg = (
                    f"'uplink_switch_interfaces' is not set on '{self.shared_utils.hostname}' and 'uplink_switch' '{uplink_switch}' "
                    f"does not have any 'downlink_interfaces' set under 'default_interfaces'. At least one or the other must be defined."
                )
                raise AristaAvdError(msg)
            else:
                msg = (
                    f"'uplink_switch_interfaces' is not set on '{self.shared_utils.hostname}' and 'uplink_switch' '{uplink_switch}' "
                    f"does not have enough 'downlink_interfaces' defined under 'default_interfaces'. "
                    f"The uplink switch requires at least {downlink_index + 1} downlink_interfaces, but "
                    f"only {uplink_switch_downlink_interfaces_length} are configured."
                )
                raise AristaAvdError(msg)

        return uplink_switch_interfaces
