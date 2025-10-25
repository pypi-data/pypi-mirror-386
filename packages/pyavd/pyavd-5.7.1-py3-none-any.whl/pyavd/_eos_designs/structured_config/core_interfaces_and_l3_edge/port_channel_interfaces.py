# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor
from pyavd._utils import default, get
from pyavd.api.interface_descriptions import InterfaceDescriptionData

if TYPE_CHECKING:
    from . import AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol


class PortChannelInterfacesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def port_channel_interfaces(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol) -> None:
        """Set the structured config for port_channel_interfaces."""
        for p2p_link, p2p_link_data in self._filtered_p2p_links:
            if p2p_link_data["port_channel_id"] is None:
                continue

            # Port-Channel interface
            port_channel_interface = EosCliConfigGen.PortChannelInterfacesItem()
            self._update_common_interface_cfg(p2p_link, p2p_link_data, port_channel_interface)
            port_channel_interface.ptp = self._get_ptp_config_interface(p2p_link, output_type=EosCliConfigGen.PortChannelInterfacesItem.Ptp)
            port_channel_interface.description = self._p2p_link_port_channel_description(p2p_link_data)

            if p2p_link.port_channel_structured_config:
                self.custom_structured_configs.nested.port_channel_interfaces.obtain(port_channel_interface.name)._deepmerge(
                    p2p_link.port_channel_structured_config,
                    list_merge=self.custom_structured_configs.list_merge_strategy,
                )

            self.structured_config.port_channel_interfaces.append(port_channel_interface)

    def _p2p_link_port_channel_description(self: AvdStructuredConfigCoreInterfacesAndL3EdgeProtocol, p2p_link_data: dict) -> str:
        return self.shared_utils.interface_descriptions.underlay_port_channel_interface(
            InterfaceDescriptionData(
                shared_utils=self.shared_utils,
                port_channel_description=default(get(p2p_link_data, "port_channel_description"), get(p2p_link_data, "description")),
                interface=p2p_link_data["interface"],
                port_channel_id=p2p_link_data["port_channel_id"],
                peer_channel_group_id=p2p_link_data["peer_port_channel_id"],
                link_type=self.data_model,
                peer=p2p_link_data["peer"],
                peer_interface=p2p_link_data["peer_interface"],
            ),
        )
