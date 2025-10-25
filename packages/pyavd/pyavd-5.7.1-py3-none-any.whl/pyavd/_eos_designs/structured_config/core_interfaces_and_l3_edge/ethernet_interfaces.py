# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd.api.interface_descriptions import InterfaceDescriptionData

if TYPE_CHECKING:
    from . import AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol


class EthernetInterfacesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def ethernet_interfaces(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol) -> None:
        """Set the structured config for ethernet_interfaces."""
        for p2p_link, p2p_link_data in self._filtered_p2p_links:
            if p2p_link_data["port_channel_id"] is None:
                # Ethernet interface
                ethernet_interface = EosCliConfigGen.EthernetInterfacesItem()
                self._update_common_interface_cfg(p2p_link, p2p_link_data, ethernet_interface)
                ethernet_interface.ptp = self._get_ptp_config_interface(p2p_link, output_type=EosCliConfigGen.EthernetInterfacesItem.Ptp)
                ethernet_interface.description = self._p2p_link_ethernet_description(p2p_link_data) or None
                ethernet_interface.speed = p2p_link.speed
                # Propagate campus_link_type for campus devices
                if self.shared_utils.is_campus_device and p2p_link.campus_link_type:
                    ethernet_interface._internal_data.campus_link_type = list(p2p_link.campus_link_type)

                if p2p_link.ethernet_structured_config:
                    self.custom_structured_configs.nested.ethernet_interfaces.obtain(ethernet_interface.name)._deepmerge(
                        p2p_link.ethernet_structured_config,
                        list_merge=self.custom_structured_configs.list_merge_strategy,
                    )

                self.structured_config.ethernet_interfaces.append(ethernet_interface)

            # Port-Channel members
            for member in p2p_link_data["port_channel_members"]:
                ethernet_interface = EosCliConfigGen.EthernetInterfacesItem(
                    name=member["interface"],
                    peer=p2p_link_data["peer"],
                    peer_interface=member["peer_interface"],
                    peer_type=p2p_link_data["peer_type"],
                    shutdown=False,
                    description=self._port_channel_member_description(p2p_link_data, member) or None,
                    speed=p2p_link.speed,
                )
                ethernet_interface.channel_group.id = p2p_link_data["port_channel_id"]
                ethernet_interface.channel_group.mode = p2p_link.port_channel.mode
                # Propagate campus_link_type for campus devices
                if self.shared_utils.is_campus_device and p2p_link.campus_link_type:
                    ethernet_interface._internal_data.campus_link_type = list(p2p_link.campus_link_type)

                if p2p_link.ethernet_structured_config:
                    self.custom_structured_configs.nested.ethernet_interfaces.obtain(ethernet_interface.name)._deepmerge(
                        p2p_link.ethernet_structured_config,
                        list_merge=self.custom_structured_configs.list_merge_strategy,
                    )

                self.structured_config.ethernet_interfaces.append(ethernet_interface)

    def _p2p_link_ethernet_description(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link_data: dict) -> str:
        return self.shared_utils.interface_descriptions.underlay_ethernet_interface(
            InterfaceDescriptionData(
                shared_utils=self.shared_utils,
                description=p2p_link_data.get("description"),
                interface=p2p_link_data["interface"],
                link_type=self.data_model,
                peer=p2p_link_data["peer"],
                peer_interface=p2p_link_data["peer_interface"],
            ),
        )

    def _port_channel_member_description(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link_data: dict, member: dict) -> str:
        return self.shared_utils.interface_descriptions.underlay_ethernet_interface(
            InterfaceDescriptionData(
                shared_utils=self.shared_utils,
                description=p2p_link_data.get("description"),
                interface=member["interface"],
                link_type=self.data_model,
                peer=p2p_link_data["peer"],
                peer_interface=member["peer_interface"],
            ),
        )
