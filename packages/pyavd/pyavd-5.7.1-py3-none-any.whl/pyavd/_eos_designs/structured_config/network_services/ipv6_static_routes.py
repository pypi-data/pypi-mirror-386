# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pyavd._eos_cli_config_gen.schema import EosCliConfigGen
from pyavd._eos_designs.structured_config.structured_config_generator import structured_config_contributor

if TYPE_CHECKING:
    from . import AvdStructuredConfigNetworkServicesProtocol


class Ipv6StaticRoutesMixin(Protocol):
    """
    Mixin Class used to generate structured config for one key.

    Class should only be used as Mixin to a AvdStructuredConfig class.
    """

    @structured_config_contributor
    def ipv6_static_routes(self: AvdStructuredConfigNetworkServicesProtocol) -> None:
        """
        Set the structured config for ipv6_static_routes.

        Consist of
        - ipv6 static_routes defined under the vrfs
        - static routes added automatically for VARPv6 with prefixes
        """
        if not self.shared_utils.network_services_l3:
            return

        for tenant in self.shared_utils.filtered_tenants:
            for vrf in tenant.vrfs:
                for static_route in vrf.ipv6_static_routes:
                    static_route_item = EosCliConfigGen.Ipv6StaticRoutesItem()
                    static_route_item._update(
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
                    self.structured_config.ipv6_static_routes.append_unique(static_route_item)
