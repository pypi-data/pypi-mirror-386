# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class StaticRoutesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def static_routes(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """
        Set the structured config for static_routes.

        Consist of
        - static_routes defined under the vrfs
        - static routes added automatically for VARP with prefixes
        """
        if not self.shared_utils.network_services_l3:
            return

        for tenant in self.shared_utils.filtered_tenants:
            for vrf in tenant.vrfs:
                # Static routes are already filtered inside filtered_tenants
                for static_route in vrf.static_routes:
                    static_route_item = EosCliConfigGen.StaticRoutesItem(
                        vrf=vrf.name,
                        prefix=static_route.prefix or static_route.destination_address_prefix,
                        interface=static_route.interface,
                        next_hop=static_route.next_hop or static_route.gateway,
                        track_bfd=static_route.track_bfd,
                        distance=static_route.distance,
                        tag=static_route.tag,
                        metric=static_route.metric,
                        name=static_route.name,
                    )
                    self.structured_config.static_routes.append_unique(static_route_item)

                for svi in vrf.svis:
                    if not svi.ip_virtual_router_addresses or not svi.ip_address:
                        # Skip svi if VARP is not set or if there is no unique ip_address
                        continue

                    for virtual_router_address in svi.ip_virtual_router_addresses:
                        if "/" not in virtual_router_address:
                            # Only create static routes for VARP entries with masks
                            continue

                        static_route_item = EosCliConfigGen.StaticRoutesItem(
                            prefix=str(ipaddress.ip_network(virtual_router_address, strict=False)),
                            vrf=vrf.name,
                            name="VARP",
                            interface=f"Vlan{svi.id}",
                        )

                        self.structured_config.static_routes.append_unique(static_route_item)

    def set_zscaler_ie_connection_static_route(self: AvdStructuredConfigNetworkServicesProtocol, destination_ip: str, name: str, next_hop: str) -> None:
        """Set the static route for one Zscaler Internet Exit connection."""
        self.structured_config.static_routes.append_new(
            prefix=f"{destination_ip}/32",
            name=name,
            next_hop=next_hop,
        )
