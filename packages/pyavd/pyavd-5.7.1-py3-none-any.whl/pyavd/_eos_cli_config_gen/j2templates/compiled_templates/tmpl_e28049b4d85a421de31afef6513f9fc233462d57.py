from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-bgp.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_bgp = resolve('router_bgp')
    l_0_timers_bgp_cli = resolve('timers_bgp_cli')
    l_0_distance_cli = resolve('distance_cli')
    l_0_rr_preserve_attributes_cli = resolve('rr_preserve_attributes_cli')
    l_0_paths_cli = resolve('paths_cli')
    l_0_redistribute_var = resolve('redistribute_var')
    l_0_redistribute_conn = resolve('redistribute_conn')
    l_0_redistribute_isis = resolve('redistribute_isis')
    l_0_redistribute_ospf = resolve('redistribute_ospf')
    l_0_redistribute_ospf_match = resolve('redistribute_ospf_match')
    l_0_redistribute_ospfv3 = resolve('redistribute_ospfv3')
    l_0_redistribute_ospfv3_match = resolve('redistribute_ospfv3_match')
    l_0_redistribute_static = resolve('redistribute_static')
    l_0_redistribute_rip = resolve('redistribute_rip')
    l_0_redistribute_host = resolve('redistribute_host')
    l_0_redistribute_dynamic = resolve('redistribute_dynamic')
    l_0_redistribute_bgp = resolve('redistribute_bgp')
    l_0_redistribute_user = resolve('redistribute_user')
    l_0_encapsulation_cli = resolve('encapsulation_cli')
    l_0_evpn_mpls_resolution_ribs = resolve('evpn_mpls_resolution_ribs')
    l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = resolve('evpn_neighbor_default_nhs_received_evpn_routes_cli')
    l_0_hostflap_detection_cli = resolve('hostflap_detection_cli')
    l_0_layer2_cli = resolve('layer2_cli')
    l_0_v4_bgp_lu_resolution_ribs = resolve('v4_bgp_lu_resolution_ribs')
    l_0_redistribute_dhcp = resolve('redistribute_dhcp')
    l_0_path_selection_roles = resolve('path_selection_roles')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.hide_passwords']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.hide_passwords' found.")
    try:
        t_3 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_4 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_5 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_6 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    try:
        t_7 = environment.tests['defined']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No test named 'defined' found.")
    try:
        t_8 = environment.tests['number']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No test named 'number' found.")
    pass
    if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as')):
        pass
        yield '!\nrouter bgp '
        yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as'))
        yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as_notation')):
            pass
            yield '   bgp asn notation '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as_notation'))
            yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'router_id')):
            pass
            yield '   router-id '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'router_id'))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'updates'), 'wait_for_convergence'), True):
            pass
            yield '   update wait-for-convergence\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'updates'), 'wait_install'), True):
            pass
            yield '   update wait-install\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast'), True):
            pass
            yield '   bgp default ipv4-unicast\n'
        elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast'), False):
            pass
            yield '   no bgp default ipv4-unicast\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast_transport_ipv6'), True):
            pass
            yield '   bgp default ipv4-unicast transport ipv6\n'
        elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast_transport_ipv6'), False):
            pass
            yield '   no bgp default ipv4-unicast transport ipv6\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers')):
            pass
            l_0_timers_bgp_cli = 'timers bgp'
            context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
            context.exported_vars.add('timers_bgp_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'keepalive_time')) and t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'hold_time'))):
                pass
                l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'keepalive_time'), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'hold_time'), ))
                context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                context.exported_vars.add('timers_bgp_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time')) or t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time'))):
                pass
                if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time')):
                    pass
                    l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' min-hold-time ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time'), ))
                    context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                    context.exported_vars.add('timers_bgp_cli')
                if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time')):
                    pass
                    l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' send-failure hold-time ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time'), ))
                    context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                    context.exported_vars.add('timers_bgp_cli')
            yield '   '
            yield str((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'external_routes')):
            pass
            l_0_distance_cli = str_join(('distance bgp ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'external_routes'), ))
            context.vars['distance_cli'] = l_0_distance_cli
            context.exported_vars.add('distance_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'internal_routes')) and t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'local_routes'))):
                pass
                l_0_distance_cli = str_join(((undefined(name='distance_cli') if l_0_distance_cli is missing else l_0_distance_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'internal_routes'), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'local_routes'), ))
                context.vars['distance_cli'] = l_0_distance_cli
                context.exported_vars.add('distance_cli')
            yield '   '
            yield str((undefined(name='distance_cli') if l_0_distance_cli is missing else l_0_distance_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'enabled'), True):
            pass
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'restart_time')):
                pass
                yield '   graceful-restart restart-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'restart_time'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'stalepath_time')):
                pass
                yield '   graceful-restart stalepath-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'stalepath_time'))
                yield '\n'
            yield '   graceful-restart\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_cluster_id')):
            pass
            yield '   bgp cluster-id '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_cluster_id'))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'enabled'), False):
            pass
            yield '   no graceful-restart-helper\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'enabled'), True):
            pass
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'restart_time')):
                pass
                yield '   graceful-restart-helper restart-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'restart_time'))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'long_lived'), True):
                pass
                yield '   graceful-restart-helper long-lived\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'route_reflector_preserve_attributes'), 'enabled'), True):
            pass
            l_0_rr_preserve_attributes_cli = 'bgp route-reflector preserve-attributes'
            context.vars['rr_preserve_attributes_cli'] = l_0_rr_preserve_attributes_cli
            context.exported_vars.add('rr_preserve_attributes_cli')
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'route_reflector_preserve_attributes'), 'always'), True):
                pass
                l_0_rr_preserve_attributes_cli = str_join(((undefined(name='rr_preserve_attributes_cli') if l_0_rr_preserve_attributes_cli is missing else l_0_rr_preserve_attributes_cli), ' always', ))
                context.vars['rr_preserve_attributes_cli'] = l_0_rr_preserve_attributes_cli
                context.exported_vars.add('rr_preserve_attributes_cli')
            yield '   '
            yield str((undefined(name='rr_preserve_attributes_cli') if l_0_rr_preserve_attributes_cli is missing else l_0_rr_preserve_attributes_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'paths')):
            pass
            l_0_paths_cli = str_join(('maximum-paths ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'paths'), ))
            context.vars['paths_cli'] = l_0_paths_cli
            context.exported_vars.add('paths_cli')
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'ecmp')):
                pass
                l_0_paths_cli = str_join(((undefined(name='paths_cli') if l_0_paths_cli is missing else l_0_paths_cli), ' ecmp ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'ecmp'), ))
                context.vars['paths_cli'] = l_0_paths_cli
                context.exported_vars.add('paths_cli')
            yield '   '
            yield str((undefined(name='paths_cli') if l_0_paths_cli is missing else l_0_paths_cli))
            yield '\n'
        for l_1_bgp_default in t_1(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_defaults'), []):
            _loop_vars = {}
            pass
            yield '   '
            yield str(l_1_bgp_default)
            yield '\n'
        l_1_bgp_default = missing
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'receive'), True):
            pass
            yield '   bgp additional-paths receive\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'receive'), False):
            pass
            yield '   no bgp additional-paths receive\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send')):
            pass
            if (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                pass
                yield '   no bgp additional-paths send\n'
            elif (t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                pass
                yield '   bgp additional-paths send ecmp limit '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit'))
                yield '\n'
            elif (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                pass
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit')):
                    pass
                    yield '   bgp additional-paths send limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
            else:
                pass
                yield '   bgp additional-paths send '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send'))
                yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'listen_ranges')):
            pass
            def t_9(fiter):
                for l_1_listen_range in fiter:
                    if ((t_6(environment.getattr(l_1_listen_range, 'peer_group')) and t_6(environment.getattr(l_1_listen_range, 'prefix'))) and (t_6(environment.getattr(l_1_listen_range, 'peer_filter')) or t_6(environment.getattr(l_1_listen_range, 'remote_as')))):
                        yield l_1_listen_range
            for l_1_listen_range in t_9(t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'listen_ranges'), 'peer_group')):
                l_1_listen_range_cli = missing
                _loop_vars = {}
                pass
                l_1_listen_range_cli = str_join(('bgp listen range ', environment.getattr(l_1_listen_range, 'prefix'), ))
                _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                if t_6(environment.getattr(l_1_listen_range, 'peer_id_include_router_id'), True):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-id include router-id', ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-group ', environment.getattr(l_1_listen_range, 'peer_group'), ))
                _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                if t_6(environment.getattr(l_1_listen_range, 'peer_filter')):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-filter ', environment.getattr(l_1_listen_range, 'peer_filter'), ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                elif t_6(environment.getattr(l_1_listen_range, 'remote_as')):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' remote-as ', environment.getattr(l_1_listen_range, 'remote_as'), ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                yield '   '
                yield str((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli))
                yield '\n'
            l_1_listen_range = l_1_listen_range_cli = missing
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'bestpath'), 'd_path'), True):
            pass
            yield '   bgp bestpath d-path\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community'), 'all'):
            pass
            yield '   neighbor default send-community\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community')):
            pass
            yield '   neighbor default send-community '
            yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community'))
            yield '\n'
        for l_1_peer_group in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'peer_groups'), 'name'):
            l_1_remove_private_as_cli = resolve('remove_private_as_cli')
            l_1_allowas_in_cli = resolve('allowas_in_cli')
            l_1_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_default_originate_cli = resolve('default_originate_cli')
            l_1_maximum_routes_cli = resolve('maximum_routes_cli')
            l_1_link_bandwidth_cli = resolve('link_bandwidth_cli')
            l_1_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
            _loop_vars = {}
            pass
            yield '   neighbor '
            yield str(environment.getattr(l_1_peer_group, 'name'))
            yield ' peer group\n'
            if t_6(environment.getattr(l_1_peer_group, 'remote_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_peer_group, 'remote_as'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_self'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-self\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_peer'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-peer\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_unchanged'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-unchanged\n'
            if t_6(environment.getattr(l_1_peer_group, 'shutdown'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' shutdown\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'enabled'), True):
                pass
                l_1_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' remove-private-as', ))
                _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'all'), True):
                    pass
                    l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' all', ))
                    _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'replace_as'), True):
                        pass
                        l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                yield '   '
                yield str((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remove-private-as\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'as_path'), 'prepend_own_disabled'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' as-path prepend-own disabled\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'as_path'), 'remote_as_replace_out'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' as-path remote-as replace out\n'
            if t_6(environment.getattr(l_1_peer_group, 'local_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' local-as '
                yield str(environment.getattr(l_1_peer_group, 'local_as'))
                yield ' no-prepend replace-as\n'
            if t_6(environment.getattr(l_1_peer_group, 'weight')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' weight '
                yield str(environment.getattr(l_1_peer_group, 'weight'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'passive'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' passive\n'
            if t_6(environment.getattr(l_1_peer_group, 'update_source')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' update-source '
                yield str(environment.getattr(l_1_peer_group, 'update_source'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'bfd'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' bfd\n'
                if ((t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'multiplier'))):
                    pass
                    yield '   neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' bfd interval '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'interval'))
                    yield ' min-rx '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'min_rx'))
                    yield ' multiplier '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'multiplier'))
                    yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'description')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' description '
                yield str(environment.getattr(l_1_peer_group, 'description'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'enabled'), True):
                pass
                l_1_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' allowas-in', ))
                _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'times')):
                    pass
                    l_1_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'times'), ))
                    _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                yield '   '
                yield str((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'enabled'), True):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'all'), True):
                    pass
                    l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'enabled'), False):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_1_peer_group, 'name'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'ebgp_multihop')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' ebgp-multihop '
                yield str(environment.getattr(l_1_peer_group, 'ebgp_multihop'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'ttl_maximum_hops')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' ttl maximum-hops '
                yield str(environment.getattr(l_1_peer_group, 'ttl_maximum_hops'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_reflector_client'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-reflector-client\n'
            if t_6(environment.getattr(l_1_peer_group, 'session_tracker')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' session tracker '
                yield str(environment.getattr(l_1_peer_group, 'session_tracker'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'timers')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' timers '
                yield str(environment.getattr(l_1_peer_group, 'timers'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-map '
                yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                yield ' in\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-map '
                yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                yield ' out\n'
            if t_6(environment.getattr(l_1_peer_group, 'password')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' password 7 '
                yield str(t_2(environment.getattr(l_1_peer_group, 'password'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'profile')) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'hash_algorithm'))):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' password shared-secret profile '
                yield str(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'profile'))
                yield ' algorithm '
                yield str(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'hash_algorithm'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'enabled'), True):
                pass
                l_1_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-originate', ))
                _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map')):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map'), ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'always'), True):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' always', ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                yield '   '
                yield str((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'send_community'), 'all'):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' send-community\n'
            elif t_6(environment.getattr(l_1_peer_group, 'send_community')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' send-community '
                yield str(environment.getattr(l_1_peer_group, 'send_community'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'maximum_routes')):
                pass
                l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' maximum-routes ', environment.getattr(l_1_peer_group, 'maximum_routes'), ))
                _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_peer_group, 'maximum_routes_warning_limit')):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_peer_group, 'maximum_routes_warning_limit'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_peer_group, 'maximum_routes_warning_only'), True):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-only', ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                yield '   '
                yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'missing_policy')):
                pass
                for l_2_direction in ['in', 'out']:
                    l_2_missing_policy_cli = resolve('missing_policy_cli')
                    l_2_dir = l_2_policy = missing
                    _loop_vars = {}
                    pass
                    l_2_dir = str_join(('direction_', l_2_direction, ))
                    _loop_vars['dir'] = l_2_dir
                    l_2_policy = environment.getitem(environment.getattr(l_1_peer_group, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                    _loop_vars['policy'] = l_2_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                        pass
                        l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' missing-policy address-family all', ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                            pass
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        yield '   '
                        yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                        yield '\n'
                l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
            if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' peer-tag in '
                yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' peer-tag out discard '
                yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'enabled'), True):
                pass
                l_1_link_bandwidth_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' link-bandwidth', ))
                _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'default')):
                    pass
                    l_1_link_bandwidth_cli = str_join(((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli), ' default ', environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'default'), ))
                    _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                yield '   '
                yield str((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'enabled'), True):
                pass
                l_1_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' remove-private-as ingress', ))
                _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'replace_as'), True):
                    pass
                    l_1_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli), ' replace-as', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                yield '   '
                yield str((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remove-private-as ingress\n'
        l_1_peer_group = l_1_remove_private_as_cli = l_1_allowas_in_cli = l_1_neighbor_rib_in_pre_policy_retain_cli = l_1_hide_passwords = l_1_default_originate_cli = l_1_maximum_routes_cli = l_1_link_bandwidth_cli = l_1_remove_private_as_ingress_cli = missing
        for l_1_neighbor in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbors'), 'ip_address'):
            l_1_remove_private_as_cli = resolve('remove_private_as_cli')
            l_1_allowas_in_cli = resolve('allowas_in_cli')
            l_1_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_default_originate_cli = resolve('default_originate_cli')
            l_1_maximum_routes_cli = resolve('maximum_routes_cli')
            l_1_link_bandwidth_cli = resolve('link_bandwidth_cli')
            l_1_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
            _loop_vars = {}
            pass
            if t_6(environment.getattr(l_1_neighbor, 'peer_group')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer group '
                yield str(environment.getattr(l_1_neighbor, 'peer_group'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'remote_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_neighbor, 'remote_as'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'next_hop_self'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' next-hop-self\n'
            if t_6(environment.getattr(l_1_neighbor, 'next_hop_peer'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' next-hop-peer\n'
            if t_6(environment.getattr(l_1_neighbor, 'shutdown'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' shutdown\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'enabled'), True):
                pass
                l_1_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' remove-private-as', ))
                _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'all'), True):
                    pass
                    l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' all', ))
                    _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'replace_as'), True):
                        pass
                        l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                yield '   '
                yield str((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remove-private-as\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'as_path'), 'prepend_own_disabled'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' as-path prepend-own disabled\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'as_path'), 'remote_as_replace_out'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' as-path remote-as replace out\n'
            if t_6(environment.getattr(l_1_neighbor, 'local_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' local-as '
                yield str(environment.getattr(l_1_neighbor, 'local_as'))
                yield ' no-prepend replace-as\n'
            if t_6(environment.getattr(l_1_neighbor, 'weight')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' weight '
                yield str(environment.getattr(l_1_neighbor, 'weight'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'passive'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' passive\n'
            if t_6(environment.getattr(l_1_neighbor, 'update_source')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' update-source '
                yield str(environment.getattr(l_1_neighbor, 'update_source'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'bfd'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' bfd\n'
                if ((t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'multiplier'))):
                    pass
                    yield '   neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' bfd interval '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'interval'))
                    yield ' min-rx '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'min_rx'))
                    yield ' multiplier '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'multiplier'))
                    yield '\n'
            elif (t_6(environment.getattr(l_1_neighbor, 'bfd'), False) and t_6(environment.getattr(l_1_neighbor, 'peer_group'))):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' bfd\n'
            if t_6(environment.getattr(l_1_neighbor, 'description')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' description '
                yield str(environment.getattr(l_1_neighbor, 'description'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'enabled'), True):
                pass
                l_1_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' allowas-in', ))
                _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'times')):
                    pass
                    l_1_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'times'), ))
                    _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                yield '   '
                yield str((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), True):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'all'), True):
                    pass
                    l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), False):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'ebgp_multihop')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' ebgp-multihop '
                yield str(environment.getattr(l_1_neighbor, 'ebgp_multihop'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'ttl_maximum_hops')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' ttl maximum-hops '
                yield str(environment.getattr(l_1_neighbor, 'ttl_maximum_hops'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_reflector_client'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-reflector-client\n'
            elif t_6(environment.getattr(l_1_neighbor, 'route_reflector_client'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-reflector-client\n'
            if t_6(environment.getattr(l_1_neighbor, 'session_tracker')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' session tracker '
                yield str(environment.getattr(l_1_neighbor, 'session_tracker'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'timers')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' timers '
                yield str(environment.getattr(l_1_neighbor, 'timers'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-map '
                yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                yield ' in\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-map '
                yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                yield ' out\n'
            if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'profile')) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'hash_algorithm'))):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' password shared-secret profile '
                yield str(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'profile'))
                yield ' algorithm '
                yield str(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'hash_algorithm'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'password')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' password 7 '
                yield str(t_2(environment.getattr(l_1_neighbor, 'password'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'enabled'), True):
                pass
                l_1_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-originate', ))
                _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map')):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map'), ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'always'), True):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' always', ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                yield '   '
                yield str((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'send_community'), 'all'):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' send-community\n'
            elif t_6(environment.getattr(l_1_neighbor, 'send_community')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' send-community '
                yield str(environment.getattr(l_1_neighbor, 'send_community'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'maximum_routes')):
                pass
                l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' maximum-routes ', environment.getattr(l_1_neighbor, 'maximum_routes'), ))
                _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_neighbor, 'maximum_routes_warning_limit')):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_neighbor, 'maximum_routes_warning_limit'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_neighbor, 'maximum_routes_warning_only'), True):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-only', ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                yield '   '
                yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'missing_policy')):
                pass
                for l_2_direction in ['in', 'out']:
                    l_2_missing_policy_cli = resolve('missing_policy_cli')
                    l_2_dir = l_2_policy = missing
                    _loop_vars = {}
                    pass
                    l_2_dir = str_join(('direction_', l_2_direction, ))
                    _loop_vars['dir'] = l_2_dir
                    l_2_policy = environment.getitem(environment.getattr(l_1_neighbor, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                    _loop_vars['policy'] = l_2_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                        pass
                        l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' missing-policy address-family all', ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                            pass
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        yield '   '
                        yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                        yield '\n'
                l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
            if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer-tag in '
                yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer-tag out discard '
                yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'enabled'), True):
                pass
                l_1_link_bandwidth_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' link-bandwidth', ))
                _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'default')):
                    pass
                    l_1_link_bandwidth_cli = str_join(((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli), ' default ', environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'default'), ))
                    _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                yield '   '
                yield str((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'enabled'), True):
                pass
                l_1_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' remove-private-as ingress', ))
                _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'replace_as'), True):
                    pass
                    l_1_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli), ' replace-as', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                yield '   '
                yield str((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remove-private-as ingress\n'
        l_1_neighbor = l_1_remove_private_as_cli = l_1_allowas_in_cli = l_1_neighbor_rib_in_pre_policy_retain_cli = l_1_hide_passwords = l_1_default_originate_cli = l_1_maximum_routes_cli = l_1_link_bandwidth_cli = l_1_remove_private_as_ingress_cli = missing
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'redistribute_internal'), True):
            pass
            yield '   bgp redistribute-internal\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'redistribute_internal'), False):
            pass
            yield '   no bgp redistribute-internal\n'
        for l_1_aggregate_address in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'aggregate_addresses'), 'prefix'):
            l_1_aggregate_address_cli = missing
            _loop_vars = {}
            pass
            l_1_aggregate_address_cli = str_join(('aggregate-address ', environment.getattr(l_1_aggregate_address, 'prefix'), ))
            _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'as_set'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' as-set', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'summary_only'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' summary-only', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'attribute_map')):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' attribute-map ', environment.getattr(l_1_aggregate_address, 'attribute_map'), ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'match_map')):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' match-map ', environment.getattr(l_1_aggregate_address, 'match_map'), ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'advertise_only'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' advertise-only', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            yield '   '
            yield str((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli))
            yield '\n'
        l_1_aggregate_address = l_1_aggregate_address_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute')):
            pass
            l_0_redistribute_var = environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute')
            context.vars['redistribute_var'] = l_0_redistribute_var
            context.exported_vars.add('redistribute_var')
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                pass
                l_0_redistribute_conn = 'redistribute connected'
                context.vars['redistribute_conn'] = l_0_redistribute_conn
                context.exported_vars.add('redistribute_conn')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                yield '   '
                yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                pass
                l_0_redistribute_isis = 'redistribute isis'
                context.vars['redistribute_isis'] = l_0_redistribute_isis
                context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                yield '   '
                yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                pass
                l_0_redistribute_ospf = 'redistribute ospf'
                context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                yield '   '
                yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                pass
                l_0_redistribute_ospf = 'redistribute ospf match internal'
                context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                yield '   '
                yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospf_match = 'redistribute ospf match external'
                context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                yield '   '
                yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                yield '   '
                yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                pass
                l_0_redistribute_static = 'redistribute static'
                context.vars['redistribute_static'] = l_0_redistribute_static
                context.exported_vars.add('redistribute_static')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                yield '   '
                yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'enabled'), True):
                pass
                l_0_redistribute_rip = 'redistribute rip'
                context.vars['redistribute_rip'] = l_0_redistribute_rip
                context.exported_vars.add('redistribute_rip')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map')):
                    pass
                    l_0_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map'), ))
                    context.vars['redistribute_rip'] = l_0_redistribute_rip
                    context.exported_vars.add('redistribute_rip')
                yield '   '
                yield str((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                pass
                l_0_redistribute_host = 'redistribute attached-host'
                context.vars['redistribute_host'] = l_0_redistribute_host
                context.exported_vars.add('redistribute_host')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                    pass
                    l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                yield '   '
                yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                pass
                l_0_redistribute_dynamic = 'redistribute dynamic'
                context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                context.exported_vars.add('redistribute_dynamic')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                    pass
                    l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                    pass
                    l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                yield '   '
                yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                pass
                l_0_redistribute_bgp = 'redistribute bgp leaked'
                context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                context.exported_vars.add('redistribute_bgp')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                    pass
                    l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                yield '   '
                yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                pass
                l_0_redistribute_user = 'redistribute user'
                context.vars['redistribute_user'] = l_0_redistribute_user
                context.exported_vars.add('redistribute_user')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                    pass
                    l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                yield '   '
                yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                yield '\n'
        elif t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute_routes')):
            pass
            for l_1_redistribute_route in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute_routes'), 'source_protocol'):
                l_1_redistribute_route_cli = missing
                _loop_vars = {}
                pass
                l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
                _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                if (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                    pass
                    if t_6(environment.getattr(l_1_redistribute_route, 'ospf_route_type')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                if (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'bgp'):
                    pass
                    l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' leaked', ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                elif t_6(environment.getattr(l_1_redistribute_route, 'include_leaked'), True):
                    pass
                    l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                if t_6(environment.getattr(l_1_redistribute_route, 'route_map')):
                    pass
                    l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                elif (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                    pass
                    if t_6(environment.getattr(l_1_redistribute_route, 'rcf')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' rcf ', environment.getattr(l_1_redistribute_route, 'rcf'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                yield '   '
                yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
                yield '\n'
            l_1_redistribute_route = l_1_redistribute_route_cli = missing
        for l_1_neighbor_interface in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_interfaces'), 'name'):
            _loop_vars = {}
            pass
            if (t_6(environment.getattr(l_1_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_1_neighbor_interface, 'remote_as'))):
                pass
                yield '   neighbor interface '
                yield str(environment.getattr(l_1_neighbor_interface, 'name'))
                yield ' peer-group '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_group'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_neighbor_interface, 'remote_as'))
                yield '\n'
            elif (t_6(environment.getattr(l_1_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_1_neighbor_interface, 'peer_filter'))):
                pass
                yield '   neighbor interface '
                yield str(environment.getattr(l_1_neighbor_interface, 'name'))
                yield ' peer-group '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_group'))
                yield ' peer-filter '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_filter'))
                yield '\n'
        l_1_neighbor_interface = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlans')):
            pass
            for l_1_vlan in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlans')):
                _loop_vars = {}
                pass
                yield '   !\n   vlan '
                yield str(environment.getattr(l_1_vlan, 'id'))
                yield '\n'
                if t_6(environment.getattr(l_1_vlan, 'rd')):
                    pass
                    yield '      rd '
                    yield str(environment.getattr(l_1_vlan, 'rd'))
                    yield '\n'
                if (t_6(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'domain')) and t_6(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'rd'))):
                    pass
                    yield '      rd evpn domain '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'domain'))
                    yield ' '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'rd'))
                    yield '\n'
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'both')):
                    _loop_vars = {}
                    pass
                    yield '      route-target both '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'export')):
                    _loop_vars = {}
                    pass
                    yield '      route-target export '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'export_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target export evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import_export_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import export evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_redistribute_route in t_3(environment.getattr(l_1_vlan, 'redistribute_routes')):
                    _loop_vars = {}
                    pass
                    yield '      redistribute '
                    yield str(l_2_redistribute_route)
                    yield '\n'
                l_2_redistribute_route = missing
                for l_2_no_redistribute_route in t_3(environment.getattr(l_1_vlan, 'no_redistribute_routes')):
                    _loop_vars = {}
                    pass
                    yield '      no redistribute '
                    yield str(l_2_no_redistribute_route)
                    yield '\n'
                l_2_no_redistribute_route = missing
                if t_6(environment.getattr(l_1_vlan, 'eos_cli')):
                    pass
                    yield '      !\n      '
                    yield str(t_4(environment.getattr(l_1_vlan, 'eos_cli'), 6, False))
                    yield '\n'
            l_1_vlan = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vpws')):
            pass
            for l_1_vpws_service in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vpws'), 'name'):
                _loop_vars = {}
                pass
                yield '   !\n'
                if t_6(environment.getattr(l_1_vpws_service, 'name')):
                    pass
                    yield '   vpws '
                    yield str(environment.getattr(l_1_vpws_service, 'name'))
                    yield '\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'rd')):
                        pass
                        yield '      rd '
                        yield str(environment.getattr(l_1_vpws_service, 'rd'))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(l_1_vpws_service, 'route_targets'), 'import_export')):
                        pass
                        yield '      route-target import export evpn '
                        yield str(environment.getattr(environment.getattr(l_1_vpws_service, 'route_targets'), 'import_export'))
                        yield '\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'mpls_control_word'), True):
                        pass
                        yield '      mpls control-word\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'label_flow'), True):
                        pass
                        yield '      label flow\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'mtu')):
                        pass
                        yield '      mtu '
                        yield str(environment.getattr(l_1_vpws_service, 'mtu'))
                        yield '\n'
                    for l_2_pw in t_3(environment.getattr(l_1_vpws_service, 'pseudowires'), 'name'):
                        _loop_vars = {}
                        pass
                        if ((t_6(environment.getattr(l_2_pw, 'name')) and t_6(environment.getattr(l_2_pw, 'id_local'))) and t_6(environment.getattr(l_2_pw, 'id_remote'))):
                            pass
                            yield '      !\n      pseudowire '
                            yield str(environment.getattr(l_2_pw, 'name'))
                            yield '\n         evpn vpws id local '
                            yield str(environment.getattr(l_2_pw, 'id_local'))
                            yield ' remote '
                            yield str(environment.getattr(l_2_pw, 'id_remote'))
                            yield '\n'
                    l_2_pw = missing
            l_1_vpws_service = missing
        for l_1_vlan_aware_bundle in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlan_aware_bundles'), 'name'):
            _loop_vars = {}
            pass
            yield '   !\n   vlan-aware-bundle '
            yield str(environment.getattr(l_1_vlan_aware_bundle, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_vlan_aware_bundle, 'rd')):
                pass
                yield '      rd '
                yield str(environment.getattr(l_1_vlan_aware_bundle, 'rd'))
                yield '\n'
            if (t_6(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'domain')) and t_6(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'rd'))):
                pass
                yield '      rd evpn domain '
                yield str(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'domain'))
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'rd'))
                yield '\n'
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'both')):
                _loop_vars = {}
                pass
                yield '      route-target both '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import')):
                _loop_vars = {}
                pass
                yield '      route-target import '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'export')):
                _loop_vars = {}
                pass
                yield '      route-target export '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target import evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'export_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target export evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import_export_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target import export evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_redistribute_route in t_3(environment.getattr(l_1_vlan_aware_bundle, 'redistribute_routes')):
                _loop_vars = {}
                pass
                yield '      redistribute '
                yield str(l_2_redistribute_route)
                yield '\n'
            l_2_redistribute_route = missing
            for l_2_no_redistribute_route in t_3(environment.getattr(l_1_vlan_aware_bundle, 'no_redistribute_routes')):
                _loop_vars = {}
                pass
                yield '      no redistribute '
                yield str(l_2_no_redistribute_route)
                yield '\n'
            l_2_no_redistribute_route = missing
            yield '      vlan '
            yield str(environment.getattr(l_1_vlan_aware_bundle, 'vlan'))
            yield '\n'
            if t_6(environment.getattr(l_1_vlan_aware_bundle, 'eos_cli')):
                pass
                yield '      !\n      '
                yield str(t_4(environment.getattr(l_1_vlan_aware_bundle, 'eos_cli'), 6, False))
                yield '\n'
        l_1_vlan_aware_bundle = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn')):
            pass
            yield '   !\n   address-family evpn\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'export_ethernet_segment_ip_mass_withdraw'), True):
                pass
                yield '      route export ethernet-segment ip mass-withdraw\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_ethernet_segment_ip_mass_withdraw'), True):
                pass
                yield '      route import ethernet-segment ip mass-withdraw\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'any'), True):
                pass
                yield '      bgp additional-paths send any\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'backup'), True):
                pass
                yield '      bgp additional-paths send backup\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'ecmp'), True):
                pass
                yield '      bgp additional-paths send ecmp\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'ecmp_limit')):
                pass
                yield '      bgp additional-paths send ecmp limit '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'ecmp_limit'))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'limit')):
                pass
                yield '      bgp additional-paths send limit '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp_additional_paths'), 'send'), 'limit'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_unchanged'), True):
                pass
                yield '      bgp next-hop-unchanged\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation')):
                pass
                l_0_encapsulation_cli = str_join(('neighbor default encapsulation ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation'), ))
                context.vars['encapsulation_cli'] = l_0_encapsulation_cli
                context.exported_vars.add('encapsulation_cli')
                if (t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation'), 'mpls') and t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_source_interface'))):
                    pass
                    l_0_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_0_encapsulation_cli is missing else l_0_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_source_interface'), ))
                    context.vars['encapsulation_cli'] = l_0_encapsulation_cli
                    context.exported_vars.add('encapsulation_cli')
                yield '      '
                yield str((undefined(name='encapsulation_cli') if l_0_encapsulation_cli is missing else l_0_encapsulation_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_mpls_resolution_ribs')):
                pass
                l_0_evpn_mpls_resolution_ribs = []
                context.vars['evpn_mpls_resolution_ribs'] = l_0_evpn_mpls_resolution_ribs
                context.exported_vars.add('evpn_mpls_resolution_ribs')
                for l_1_rib in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_mpls_resolution_ribs'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib-colored'):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), 'tunnel-rib colored system-colored-tunnel-rib', _loop_vars=_loop_vars)
                    elif (t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib') and t_6(environment.getattr(l_1_rib, 'rib_name'))):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), str_join(('tunnel-rib ', environment.getattr(l_1_rib, 'rib_name'), )), _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type')):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), environment.getattr(l_1_rib, 'rib_type'), _loop_vars=_loop_vars)
                l_1_rib = missing
                if (undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs):
                    pass
                    yield '      next-hop mpls resolution ribs '
                    yield str(t_5(context.eval_ctx, (undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), ' '))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                l_1_encapsulation_cli = l_0_encapsulation_cli
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'encapsulation')):
                    pass
                    l_1_encapsulation_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' encapsulation ', environment.getattr(l_1_peer_group, 'encapsulation'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if ((environment.getattr(l_1_peer_group, 'encapsulation') == 'mpls') and t_6(environment.getattr(l_1_peer_group, 'next_hop_self_source_interface'))):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(l_1_peer_group, 'next_hop_self_source_interface'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    yield '      '
                    yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'domain_remote'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' domain remote\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = l_1_encapsulation_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                l_1_encapsulation_cli = l_0_encapsulation_cli
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'encapsulation')):
                    pass
                    l_1_encapsulation_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' encapsulation ', environment.getattr(l_1_neighbor, 'encapsulation'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if ((environment.getattr(l_1_neighbor, 'encapsulation') == 'mpls') and t_6(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'))):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    yield '      '
                    yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = l_1_encapsulation_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier_remote')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier_remote'))
                yield ' remote\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop'), 'resolution_disabled'), True):
                pass
                yield '      next-hop resolution disabled\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_received_evpn_routes'), 'enable'), True):
                pass
                l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = 'neighbor default next-hop-self received-evpn-routes route-type ip-prefix'
                context.vars['evpn_neighbor_default_nhs_received_evpn_routes_cli'] = l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli
                context.exported_vars.add('evpn_neighbor_default_nhs_received_evpn_routes_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_received_evpn_routes'), 'inter_domain'), True):
                    pass
                    l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = str_join(((undefined(name='evpn_neighbor_default_nhs_received_evpn_routes_cli') if l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli is missing else l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli), ' inter-domain', ))
                    context.vars['evpn_neighbor_default_nhs_received_evpn_routes_cli'] = l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli
                    context.exported_vars.add('evpn_neighbor_default_nhs_received_evpn_routes_cli')
                yield '      '
                yield str((undefined(name='evpn_neighbor_default_nhs_received_evpn_routes_cli') if l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli is missing else l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'enabled'), False):
                pass
                yield '      no host-flap detection\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'enabled'), True):
                pass
                l_0_hostflap_detection_cli = ''
                context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'window')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' window ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'window'), ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'threshold')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' threshold ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'threshold'), ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'expiry_timeout')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' expiry timeout ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'expiry_timeout'), ' seconds', ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if ((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli) != ''):
                    pass
                    yield '      host-flap detection'
                    yield str((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli))
                    yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'enabled'), True):
                pass
                l_0_layer2_cli = 'layer-2 fec in-place update'
                context.vars['layer2_cli'] = l_0_layer2_cli
                context.exported_vars.add('layer2_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'timeout')):
                    pass
                    l_0_layer2_cli = str_join(((undefined(name='layer2_cli') if l_0_layer2_cli is missing else l_0_layer2_cli), ' timeout ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'timeout'), ' seconds', ))
                    context.vars['layer2_cli'] = l_0_layer2_cli
                    context.exported_vars.add('layer2_cli')
                yield '      '
                yield str((undefined(name='layer2_cli') if l_0_layer2_cli is missing else l_0_layer2_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_overlay_index_gateway'), True):
                pass
                yield '      route import overlay-index gateway\n'
            for l_1_segment in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_ethernet_segment'), 'domain'):
                _loop_vars = {}
                pass
                yield '      !\n      evpn ethernet-segment domain '
                yield str(environment.getattr(l_1_segment, 'domain'))
                yield '\n'
                if t_6(environment.getattr(l_1_segment, 'identifier')):
                    pass
                    yield '         identifier '
                    yield str(environment.getattr(l_1_segment, 'identifier'))
                    yield '\n'
                if t_6(environment.getattr(l_1_segment, 'route_target_import')):
                    pass
                    yield '         route-target import '
                    yield str(environment.getattr(l_1_segment, 'route_target_import'))
                    yield '\n'
            l_1_segment = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4')):
            pass
            yield '   !\n   address-family flow-spec ipv4\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6')):
            pass
            yield '   !\n   address-family flow-spec ipv6\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4')):
            pass
            yield '   !\n   address-family ipv4\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'peer_groups'), 'name'):
                l_1_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_1_add_path_cli = resolve('add_path_cli')
                l_1_nexthop_v6_cli = resolve('nexthop_v6_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'default_originate')):
                    pass
                    l_1_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map')):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'always'), True):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'prefix_list')) and t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_peer_group, 'next_hop'), 'address_family_ipv6'), 'enabled'), True):
                    pass
                    l_1_nexthop_v6_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' next-hop address-family ipv6', ))
                    _loop_vars['nexthop_v6_cli'] = l_1_nexthop_v6_cli
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_peer_group, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                        pass
                        l_1_nexthop_v6_cli = str_join(((undefined(name='nexthop_v6_cli') if l_1_nexthop_v6_cli is missing else l_1_nexthop_v6_cli), ' originate', ))
                        _loop_vars['nexthop_v6_cli'] = l_1_nexthop_v6_cli
                    yield '      '
                    yield str((undefined(name='nexthop_v6_cli') if l_1_nexthop_v6_cli is missing else l_1_nexthop_v6_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_neighbor_default_originate_cli = l_1_add_path_cli = l_1_nexthop_v6_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_1_add_path_cli = resolve('add_path_cli')
                l_1_ipv6_originate_cli = resolve('ipv6_originate_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'default_originate')):
                    pass
                    l_1_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map')):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'always'), True):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled')):
                    pass
                    if environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled'):
                        pass
                        l_1_ipv6_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' next-hop address-family ipv6', ))
                        _loop_vars['ipv6_originate_cli'] = l_1_ipv6_originate_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                            pass
                            l_1_ipv6_originate_cli = str_join(((undefined(name='ipv6_originate_cli') if l_1_ipv6_originate_cli is missing else l_1_ipv6_originate_cli), ' originate', ))
                            _loop_vars['ipv6_originate_cli'] = l_1_ipv6_originate_cli
                        yield '      '
                        yield str((undefined(name='ipv6_originate_cli') if l_1_ipv6_originate_cli is missing else l_1_ipv6_originate_cli))
                        yield '\n'
                    else:
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' next-hop address-family ipv6\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_originate_cli = l_1_add_path_cli = l_1_ipv6_originate_cli = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield '\n'
            l_1_network = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_0_redistribute_bgp = 'redistribute bgp leaked'
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                        context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                        context.exported_vars.add('redistribute_bgp')
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_0_redistribute_dynamic = 'redistribute dynamic'
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_0_redistribute_user = 'redistribute user'
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                        context.vars['redistribute_user'] = l_0_redistribute_user
                        context.exported_vars.add('redistribute_user')
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'enabled'), True):
                    pass
                    l_0_redistribute_rip = 'redistribute rip'
                    context.vars['redistribute_rip'] = l_0_redistribute_rip
                    context.exported_vars.add('redistribute_rip')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map')):
                        pass
                        l_0_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map'), ))
                        context.vars['redistribute_rip'] = l_0_redistribute_rip
                        context.exported_vars.add('redistribute_rip')
                    yield '      '
                    yield str((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute_routes')):
                pass
                for l_1_redistribute_route in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute_routes'), 'source_protocol'):
                    l_1_redistribute_route_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'ospf_route_type')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'bgp'):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif (t_6(environment.getattr(l_1_redistribute_route, 'include_leaked'), True) and (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'ospf', 'ospfv3'])):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if t_6(environment.getattr(l_1_redistribute_route, 'route_map')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'rcf')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' rcf ', environment.getattr(l_1_redistribute_route, 'rcf'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    yield '      '
                    yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
                    yield '\n'
                l_1_redistribute_route = l_1_redistribute_route_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast')):
            pass
            yield '   !\n   address-family ipv4 labeled-unicast\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'update_wait_for_convergence'), True):
                pass
                yield '      update wait-for-convergence\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'missing_policy')):
                pass
                for l_1_direction in ['in', 'out']:
                    l_1_missing_policy_cli = resolve('missing_policy_cli')
                    l_1_dir = l_1_policy = missing
                    _loop_vars = {}
                    pass
                    l_1_dir = str_join(('direction_', l_1_direction, ))
                    _loop_vars['dir'] = l_1_dir
                    l_1_policy = environment.getitem(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'missing_policy'), (undefined(name='dir') if l_1_dir is missing else l_1_dir))
                    _loop_vars['policy'] = l_1_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'action')):
                        pass
                        l_1_missing_policy_cli = 'bgp missing-policy'
                        _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_sub_route_map'), True)):
                            pass
                            l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_community_list'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_prefix_list'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_sub_route_map'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' direction ', l_1_direction, ' action ', environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        yield '      '
                        yield str((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli))
                        yield '\n'
                l_1_direction = l_1_dir = l_1_policy = l_1_missing_policy_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'next_hop_unchanged'), True):
                pass
                yield '      bgp next-hop-unchanged\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'neighbor_default'), 'next_hop_self'), True):
                pass
                yield '      neighbor default next-hop-self\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hop_resolution_ribs')):
                pass
                l_0_v4_bgp_lu_resolution_ribs = []
                context.vars['v4_bgp_lu_resolution_ribs'] = l_0_v4_bgp_lu_resolution_ribs
                context.exported_vars.add('v4_bgp_lu_resolution_ribs')
                for l_1_rib in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hop_resolution_ribs'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib-colored'):
                        pass
                        context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), 'tunnel-rib colored system-colored-tunnel-rib', _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib'):
                        pass
                        if t_6(environment.getattr(l_1_rib, 'rib_name')):
                            pass
                            context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), str_join(('tunnel-rib ', environment.getattr(l_1_rib, 'rib_name'), )), _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type')):
                        pass
                        context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), environment.getattr(l_1_rib, 'rib_type'), _loop_vars=_loop_vars)
                l_1_rib = missing
                if (undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs):
                    pass
                    yield '      next-hop resolution ribs '
                    yield str(t_5(context.eval_ctx, (undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), ' '))
                    yield '\n'
            for l_1_peer in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'peer_groups'), 'name'):
                l_1_maximum_routes_cli = resolve('maximum_routes_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' activate\n'
                else:
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer, 'graceful_restart'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' graceful-restart\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'graceful_restart_helper'), 'stale_route_map')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' graceful-restart-helper stale-route route-map '
                    yield str(environment.getattr(environment.getattr(l_1_peer, 'graceful_restart_helper'), 'stale_route_map'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_unchanged'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-unchanged\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_self_v4_mapped_v6_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self v4-mapped-v6 source-interface '
                    yield str(environment.getattr(l_1_peer, 'next_hop_self_v4_mapped_v6_source_interface'))
                    yield '\n'
                elif t_6(environment.getattr(l_1_peer, 'next_hop_self_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self source-interface '
                    yield str(environment.getattr(l_1_peer, 'next_hop_self_source_interface'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'maximum_advertised_routes')):
                    pass
                    l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_peer, 'name'), ' maximum-advertised-routes ', environment.getattr(l_1_peer, 'maximum_advertised_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    if t_6(environment.getattr(l_1_peer, 'maximum_advertised_routes_warning_limit')):
                        pass
                        l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_peer, 'maximum_advertised_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'missing_policy')):
                    pass
                    for l_2_direction in ['in', 'out']:
                        l_2_missing_policy_cli = resolve('missing_policy_cli')
                        l_2_dir = l_2_policy = missing
                        _loop_vars = {}
                        pass
                        l_2_dir = str_join(('direction_', l_2_direction, ))
                        _loop_vars['dir'] = l_2_dir
                        l_2_policy = environment.getitem(environment.getattr(l_1_peer, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                        _loop_vars['policy'] = l_2_policy
                        if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                            pass
                            l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_peer, 'name'), ' missing-policy', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            yield '      '
                            yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                            yield '\n'
                    l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
                if t_6(environment.getattr(l_1_peer, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'aigp_session'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' aigp-session\n'
                if t_6(environment.getattr(l_1_peer, 'multi_path'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' multi-path\n'
            l_1_peer = l_1_maximum_routes_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'neighbors'), 'ip_address'):
                l_1_maximum_routes_cli = resolve('maximum_routes_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                else:
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'graceful_restart'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' graceful-restart\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'graceful_restart_helper'), 'stale_route_map')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' graceful-restart-helper stale-route route-map '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'graceful_restart_helper'), 'stale_route_map'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_unchanged'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-unchanged\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_self_v4_mapped_v6_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self v4-mapped-v6 source-interface '
                    yield str(environment.getattr(l_1_neighbor, 'next_hop_self_v4_mapped_v6_source_interface'))
                    yield '\n'
                elif t_6(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self source-interface '
                    yield str(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'maximum_advertised_routes')):
                    pass
                    l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' maximum-advertised-routes ', environment.getattr(l_1_neighbor, 'maximum_advertised_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    if t_6(environment.getattr(l_1_neighbor, 'maximum_advertised_routes_warning_limit')):
                        pass
                        l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_neighbor, 'maximum_advertised_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'missing_policy')):
                    pass
                    for l_2_direction in ['in', 'out']:
                        l_2_missing_policy_cli = resolve('missing_policy_cli')
                        l_2_dir = l_2_policy = missing
                        _loop_vars = {}
                        pass
                        l_2_dir = str_join(('direction_', l_2_direction, ))
                        _loop_vars['dir'] = l_2_dir
                        l_2_policy = environment.getitem(environment.getattr(l_1_neighbor, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                        _loop_vars['policy'] = l_2_policy
                        if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                            pass
                            l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' missing-policy ', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            yield '      '
                            yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                            yield '\n'
                    l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'aigp_session'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' aigp-session\n'
                if t_6(environment.getattr(l_1_neighbor, 'multi_path'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' multi-path\n'
            l_1_neighbor = l_1_maximum_routes_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'networks')):
                pass
                for l_1_network in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'networks'):
                    l_1_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_network_cli = str_join(('network ', environment.getattr(l_1_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_1_network_cli
                    if t_6(environment.getattr(l_1_network, 'route_map')):
                        pass
                        l_1_network_cli = str_join(((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli), ' route-map ', environment.getattr(l_1_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_1_network_cli
                    yield '      '
                    yield str((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli))
                    yield '\n'
                l_1_network = l_1_network_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hops')):
                pass
                for l_1_next_hop in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hops'):
                    l_1_next_hop_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_next_hop_cli = str_join(('next-hop ', environment.getattr(l_1_next_hop, 'ip_address'), ' originate', ))
                    _loop_vars['next_hop_cli'] = l_1_next_hop_cli
                    if t_6(environment.getattr(l_1_next_hop, 'lfib_backup_ip_forwarding'), True):
                        pass
                        l_1_next_hop_cli = str_join(((undefined(name='next_hop_cli') if l_1_next_hop_cli is missing else l_1_next_hop_cli), ' lfib-backup ip-forwarding', ))
                        _loop_vars['next_hop_cli'] = l_1_next_hop_cli
                    yield '      '
                    yield str((undefined(name='next_hop_cli') if l_1_next_hop_cli is missing else l_1_next_hop_cli))
                    yield '\n'
                l_1_next_hop = l_1_next_hop_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'lfib_entry_installation_skipped'), True):
                pass
                yield '      lfib entry installation skipped\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'label_local_termination')):
                pass
                yield '      label local-termination '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'label_local_termination'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'graceful_restart'), True):
                pass
                yield '      graceful-restart\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'tunnel_source_protocols')):
                pass
                for l_1_tunnel_source_protocol in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'tunnel_source_protocols'):
                    l_1_tunnel_source_protocol_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_tunnel_source_protocol_cli = str_join(('tunnel source-protocol ', environment.getattr(l_1_tunnel_source_protocol, 'protocol'), ))
                    _loop_vars['tunnel_source_protocol_cli'] = l_1_tunnel_source_protocol_cli
                    if t_6(environment.getattr(l_1_tunnel_source_protocol, 'rcf')):
                        pass
                        l_1_tunnel_source_protocol_cli = str_join(((undefined(name='tunnel_source_protocol_cli') if l_1_tunnel_source_protocol_cli is missing else l_1_tunnel_source_protocol_cli), ' rcf ', environment.getattr(l_1_tunnel_source_protocol, 'rcf'), ))
                        _loop_vars['tunnel_source_protocol_cli'] = l_1_tunnel_source_protocol_cli
                    yield '      '
                    yield str((undefined(name='tunnel_source_protocol_cli') if l_1_tunnel_source_protocol_cli is missing else l_1_tunnel_source_protocol_cli))
                    yield '\n'
                l_1_tunnel_source_protocol = l_1_tunnel_source_protocol_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'aigp_session')):
                pass
                for l_1_aigp_session_type in ['ibgp', 'confederation', 'ebgp']:
                    _loop_vars = {}
                    pass
                    if t_6(environment.getitem(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'aigp_session'), l_1_aigp_session_type), True):
                        pass
                        yield '      aigp-session '
                        yield str(l_1_aigp_session_type)
                        yield '\n'
                l_1_aigp_session_type = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast')):
            pass
            yield '   !\n   address-family ipv4 multicast\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute_routes')):
                pass
                for l_1_redistribute_route in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute_routes'), 'source_protocol'):
                    l_1_redistribute_route_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'ospf_route_type')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (t_6(environment.getattr(l_1_redistribute_route, 'include_leaked'), True) and (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'isis')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if t_6(environment.getattr(l_1_redistribute_route, 'route_map')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif ((environment.getattr(l_1_redistribute_route, 'source_protocol') == 'isis') and t_6(environment.getattr(l_1_redistribute_route, 'rcf'))):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' rcf ', environment.getattr(l_1_redistribute_route, 'rcf'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    yield '      '
                    yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
                    yield '\n'
                l_1_redistribute_route = l_1_redistribute_route_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te')):
            pass
            yield '   !\n   address-family ipv4 sr-te\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6')):
            pass
            yield '   !\n   address-family ipv6\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'peer_groups'), 'name'):
                l_1_add_path_cli = resolve('add_path_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_add_path_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'neighbors'), 'ip_address'):
                l_1_add_path_cli = resolve('add_path_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_add_path_cli = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield '\n'
            l_1_network = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_0_redistribute_bgp = 'redistribute bgp leaked'
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                        context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                        context.exported_vars.add('redistribute_bgp')
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'enabled'), True):
                    pass
                    l_0_redistribute_dhcp = 'redistribute dhcp'
                    context.vars['redistribute_dhcp'] = l_0_redistribute_dhcp
                    context.exported_vars.add('redistribute_dhcp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'route_map')):
                        pass
                        l_0_redistribute_dhcp = str_join(((undefined(name='redistribute_dhcp') if l_0_redistribute_dhcp is missing else l_0_redistribute_dhcp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'route_map'), ))
                        context.vars['redistribute_dhcp'] = l_0_redistribute_dhcp
                        context.exported_vars.add('redistribute_dhcp')
                    yield '      '
                    yield str((undefined(name='redistribute_dhcp') if l_0_redistribute_dhcp is missing else l_0_redistribute_dhcp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_0_redistribute_dynamic = 'redistribute dynamic'
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_0_redistribute_user = 'redistribute user'
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                        context.vars['redistribute_user'] = l_0_redistribute_user
                        context.exported_vars.add('redistribute_user')
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute_routes')):
                pass
                for l_1_redistribute_route in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute_routes'), 'source_protocol'):
                    l_1_redistribute_route_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'ospfv3'):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'ospf_route_type')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') == 'bgp'):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif t_6(environment.getattr(l_1_redistribute_route, 'include_leaked'), True):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if t_6(environment.getattr(l_1_redistribute_route, 'route_map')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'rcf')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' rcf ', environment.getattr(l_1_redistribute_route, 'rcf'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    yield '      '
                    yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
                    yield '\n'
                l_1_redistribute_route = l_1_redistribute_route_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast')):
            pass
            yield '   !\n   address-family ipv6 multicast\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'networks'), 'prefix'):
                l_1_network_cli = missing
                _loop_vars = {}
                pass
                l_1_network_cli = str_join(('network ', environment.getattr(l_1_network, 'prefix'), ))
                _loop_vars['network_cli'] = l_1_network_cli
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    l_1_network_cli = str_join(((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli), ' route-map ', environment.getattr(l_1_network, 'route_map'), ))
                    _loop_vars['network_cli'] = l_1_network_cli
                yield '      '
                yield str((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli))
                yield '\n'
            l_1_network = l_1_network_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute_routes')):
                pass
                for l_1_redistribute_route in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute_routes'), 'source_protocol'):
                    l_1_redistribute_route_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_1_redistribute_route, 'source_protocol'), ))
                    _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if (environment.getattr(l_1_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                        pass
                        if t_6(environment.getattr(l_1_redistribute_route, 'ospf_route_type')):
                            pass
                            l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' match ', environment.getattr(l_1_redistribute_route, 'ospf_route_type'), ))
                            _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if t_6(environment.getattr(l_1_redistribute_route, 'include_leaked'), True):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' include leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    if t_6(environment.getattr(l_1_redistribute_route, 'route_map')):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' route-map ', environment.getattr(l_1_redistribute_route, 'route_map'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    elif ((environment.getattr(l_1_redistribute_route, 'source_protocol') == 'isis') and t_6(environment.getattr(l_1_redistribute_route, 'rcf'))):
                        pass
                        l_1_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli), ' rcf ', environment.getattr(l_1_redistribute_route, 'rcf'), ))
                        _loop_vars['redistribute_route_cli'] = l_1_redistribute_route_cli
                    yield '      '
                    yield str((undefined(name='redistribute_route_cli') if l_1_redistribute_route_cli is missing else l_1_redistribute_route_cli))
                    yield '\n'
                l_1_redistribute_route = l_1_redistribute_route_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te')):
            pass
            yield '   !\n   address-family ipv6 sr-te\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state')):
            pass
            yield '   !\n   address-family link-state\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_out_action'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_out_action'))
                    yield '\n'
            l_1_neighbor = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection')):
                pass
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'producer'), True):
                    pass
                    yield '      path-selection\n'
                if (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'consumer'), True) or t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'propagator'), True)):
                    pass
                    l_0_path_selection_roles = 'path-selection role'
                    context.vars['path_selection_roles'] = l_0_path_selection_roles
                    context.exported_vars.add('path_selection_roles')
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'consumer'), True):
                        pass
                        l_0_path_selection_roles = str_join(((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles), ' consumer', ))
                        context.vars['path_selection_roles'] = l_0_path_selection_roles
                        context.exported_vars.add('path_selection_roles')
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'propagator'), True):
                        pass
                        l_0_path_selection_roles = str_join(((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles), ' propagator', ))
                        context.vars['path_selection_roles'] = l_0_path_selection_roles
                        context.exported_vars.add('path_selection_roles')
                    yield '      '
                    yield str((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection')):
            pass
            yield '   !\n   address-family path-selection\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                        pass
                        if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp'):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'))
                        yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_rtc')):
            pass
            yield '   !\n   address-family rt-membership\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_rtc'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_7(environment.getattr(l_1_peer_group, 'default_route_target')):
                    pass
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route_target'), 'only'), True):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' default-route-target only\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' default-route-target\n'
                if t_7(environment.getattr(environment.getattr(l_1_peer_group, 'default_route_target'), 'encoding_origin_as_omit')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' default-route-target encoding origin-as omit\n'
            l_1_peer_group = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4')):
            pass
            yield '   !\n   address-family vpn-ipv4\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface')):
                pass
                yield '      neighbor default encapsulation mpls next-hop-self source-interface '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6')):
            pass
            yield '   !\n   address-family vpn-ipv6\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface')):
                pass
                yield '      neighbor default encapsulation mpls next-hop-self source-interface '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
        for l_1_vrf in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vrfs'), 'name'):
            l_1_paths_cli = l_0_paths_cli
            l_1_redistribute_var = l_0_redistribute_var
            l_1_redistribute_conn = l_0_redistribute_conn
            l_1_redistribute_isis = l_0_redistribute_isis
            l_1_redistribute_ospf = l_0_redistribute_ospf
            l_1_redistribute_ospf_match = l_0_redistribute_ospf_match
            l_1_redistribute_ospfv3 = l_0_redistribute_ospfv3
            l_1_redistribute_ospfv3_match = l_0_redistribute_ospfv3_match
            l_1_redistribute_static = l_0_redistribute_static
            l_1_redistribute_rip = l_0_redistribute_rip
            l_1_redistribute_host = l_0_redistribute_host
            l_1_redistribute_dynamic = l_0_redistribute_dynamic
            l_1_redistribute_bgp = l_0_redistribute_bgp
            l_1_redistribute_user = l_0_redistribute_user
            l_1_redistribute_dhcp = l_0_redistribute_dhcp
            _loop_vars = {}
            pass
            yield '   !\n   vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'rd')):
                pass
                yield '      rd '
                yield str(environment.getattr(l_1_vrf, 'rd'))
                yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'default_route_exports')):
                pass
                for l_2_default_route_export in t_3(environment.getattr(l_1_vrf, 'default_route_exports'), 'address_family'):
                    l_2_vrf_default_route_export_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_vrf_default_route_export_cli = str_join(('default-route export ', environment.getattr(l_2_default_route_export, 'address_family'), ))
                    _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    if t_6(environment.getattr(l_2_default_route_export, 'always'), True):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' always', ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    if t_6(environment.getattr(l_2_default_route_export, 'rcf')):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' rcf ', environment.getattr(l_2_default_route_export, 'rcf'), ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    elif t_6(environment.getattr(l_2_default_route_export, 'route_map')):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' route-map ', environment.getattr(l_2_default_route_export, 'route_map'), ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    yield '      '
                    yield str((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli))
                    yield '\n'
                l_2_default_route_export = l_2_vrf_default_route_export_cli = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'import')):
                pass
                for l_2_address_family in environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'import'):
                    _loop_vars = {}
                    pass
                    for l_3_route_target in environment.getattr(l_2_address_family, 'route_targets'):
                        _loop_vars = {}
                        pass
                        yield '      route-target import '
                        yield str(environment.getattr(l_2_address_family, 'address_family'))
                        yield ' '
                        yield str(l_3_route_target)
                        yield '\n'
                    l_3_route_target = missing
                    if (environment.getattr(l_2_address_family, 'address_family') in ['evpn', 'vpn-ipv4', 'vpn-ipv6']):
                        pass
                        if t_6(environment.getattr(l_2_address_family, 'rcf')):
                            pass
                            if (t_6(environment.getattr(l_2_address_family, 'vpn_route_filter_rcf')) and (environment.getattr(l_2_address_family, 'address_family') in ['vpn-ipv4', 'vpn-ipv6'])):
                                pass
                                yield '      route-target import '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield ' vpn-route filter-rcf '
                                yield str(environment.getattr(l_2_address_family, 'vpn_route_filter_rcf'))
                                yield '\n'
                            else:
                                pass
                                yield '      route-target import '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield '\n'
                        if t_6(environment.getattr(l_2_address_family, 'route_map')):
                            pass
                            yield '      route-target import '
                            yield str(environment.getattr(l_2_address_family, 'address_family'))
                            yield ' route-map '
                            yield str(environment.getattr(l_2_address_family, 'route_map'))
                            yield '\n'
                l_2_address_family = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'export')):
                pass
                for l_2_address_family in environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'export'):
                    _loop_vars = {}
                    pass
                    for l_3_route_target in environment.getattr(l_2_address_family, 'route_targets'):
                        _loop_vars = {}
                        pass
                        yield '      route-target export '
                        yield str(environment.getattr(l_2_address_family, 'address_family'))
                        yield ' '
                        yield str(l_3_route_target)
                        yield '\n'
                    l_3_route_target = missing
                    if (environment.getattr(l_2_address_family, 'address_family') in ['evpn', 'vpn-ipv4', 'vpn-ipv6']):
                        pass
                        if t_6(environment.getattr(l_2_address_family, 'rcf')):
                            pass
                            if (t_6(environment.getattr(l_2_address_family, 'vrf_route_filter_rcf')) and (environment.getattr(l_2_address_family, 'address_family') in ['vpn-ipv4', 'vpn-ipv6'])):
                                pass
                                yield '      route-target export '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield ' vrf-route filter-rcf '
                                yield str(environment.getattr(l_2_address_family, 'vrf_route_filter_rcf'))
                                yield '\n'
                            else:
                                pass
                                yield '      route-target export '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield '\n'
                        if t_6(environment.getattr(l_2_address_family, 'route_map')):
                            pass
                            yield '      route-target export '
                            yield str(environment.getattr(l_2_address_family, 'address_family'))
                            yield ' route-map '
                            yield str(environment.getattr(l_2_address_family, 'route_map'))
                            yield '\n'
                l_2_address_family = missing
            if t_6(environment.getattr(l_1_vrf, 'router_id')):
                pass
                yield '      router-id '
                yield str(environment.getattr(l_1_vrf, 'router_id'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'updates'), 'wait_for_convergence'), True):
                pass
                yield '      update wait-for-convergence\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'updates'), 'wait_install'), True):
                pass
                yield '      update wait-install\n'
            if t_6(environment.getattr(l_1_vrf, 'timers')):
                pass
                yield '      timers bgp '
                yield str(environment.getattr(l_1_vrf, 'timers'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'enabled'), True):
                pass
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'restart_time')):
                    pass
                    yield '      graceful-restart restart-time '
                    yield str(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'restart_time'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'stalepath_time')):
                    pass
                    yield '      graceful-restart stalepath-time '
                    yield str(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'stalepath_time'))
                    yield '\n'
                yield '      graceful-restart\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'paths')):
                pass
                l_1_paths_cli = str_join(('maximum-paths ', environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'paths'), ))
                _loop_vars['paths_cli'] = l_1_paths_cli
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'ecmp')):
                    pass
                    l_1_paths_cli = str_join(((undefined(name='paths_cli') if l_1_paths_cli is missing else l_1_paths_cli), ' ecmp ', environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'ecmp'), ))
                    _loop_vars['paths_cli'] = l_1_paths_cli
                yield '      '
                yield str((undefined(name='paths_cli') if l_1_paths_cli is missing else l_1_paths_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'listen_ranges')):
                pass
                def t_10(fiter):
                    for l_2_listen_range in fiter:
                        if ((t_6(environment.getattr(l_2_listen_range, 'peer_group')) and t_6(environment.getattr(l_2_listen_range, 'prefix'))) and (t_6(environment.getattr(l_2_listen_range, 'peer_filter')) or t_6(environment.getattr(l_2_listen_range, 'remote_as')))):
                            yield l_2_listen_range
                for l_2_listen_range in t_10(t_3(environment.getattr(l_1_vrf, 'listen_ranges'), 'peer_group')):
                    l_2_listen_range_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_listen_range_cli = str_join(('bgp listen range ', environment.getattr(l_2_listen_range, 'prefix'), ))
                    _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    if t_6(environment.getattr(l_2_listen_range, 'peer_id_include_router_id'), True):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-id include router-id', ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-group ', environment.getattr(l_2_listen_range, 'peer_group'), ))
                    _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    if t_6(environment.getattr(l_2_listen_range, 'peer_filter')):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-filter ', environment.getattr(l_2_listen_range, 'peer_filter'), ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    elif t_6(environment.getattr(l_2_listen_range, 'remote_as')):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' remote-as ', environment.getattr(l_2_listen_range, 'remote_as'), ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    yield '      '
                    yield str((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli))
                    yield '\n'
                l_2_listen_range = l_2_listen_range_cli = missing
            for l_2_neighbor in t_3(environment.getattr(l_1_vrf, 'neighbors'), 'ip_address'):
                l_2_remove_private_as_cli = resolve('remove_private_as_cli')
                l_2_allowas_in_cli = resolve('allowas_in_cli')
                l_2_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
                l_2_neighbor_ebgp_multihop_cli = resolve('neighbor_ebgp_multihop_cli')
                l_2_hide_passwords = resolve('hide_passwords')
                l_2_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_2_maximum_routes_cli = resolve('maximum_routes_cli')
                l_2_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_2_neighbor, 'peer_group')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer group '
                    yield str(environment.getattr(l_2_neighbor, 'peer_group'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'remote_as')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remote-as '
                    yield str(environment.getattr(l_2_neighbor, 'remote_as'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_2_neighbor, 'next_hop_peer'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' next-hop-peer\n'
                if t_6(environment.getattr(l_2_neighbor, 'shutdown'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' shutdown\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'enabled'), True):
                    pass
                    l_2_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' remove-private-as', ))
                    _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'all'), True):
                        pass
                        l_2_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli), ' all', ))
                        _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                        if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'replace_as'), True):
                            pass
                            l_2_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli), ' replace-as', ))
                            _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                    yield '      '
                    yield str((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'enabled'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remove-private-as\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'as_path'), 'prepend_own_disabled'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' as-path prepend-own disabled\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'as_path'), 'remote_as_replace_out'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' as-path remote-as replace out\n'
                if t_6(environment.getattr(l_2_neighbor, 'local_as')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' local-as '
                    yield str(environment.getattr(l_2_neighbor, 'local_as'))
                    yield ' no-prepend replace-as\n'
                if t_6(environment.getattr(l_2_neighbor, 'weight')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' weight '
                    yield str(environment.getattr(l_2_neighbor, 'weight'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'passive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' passive\n'
                if t_6(environment.getattr(l_2_neighbor, 'update_source')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' update-source '
                    yield str(environment.getattr(l_2_neighbor, 'update_source'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'bfd'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' bfd\n'
                    if ((t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'multiplier'))):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' bfd interval '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'interval'))
                        yield ' min-rx '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'min_rx'))
                        yield ' multiplier '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'multiplier'))
                        yield '\n'
                elif (t_6(environment.getattr(l_2_neighbor, 'bfd'), False) and t_6(environment.getattr(l_2_neighbor, 'peer_group'))):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' bfd\n'
                if t_6(environment.getattr(l_2_neighbor, 'description')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' description '
                    yield str(environment.getattr(l_2_neighbor, 'description'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'enabled'), True):
                    pass
                    l_2_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' allowas-in', ))
                    _loop_vars['allowas_in_cli'] = l_2_allowas_in_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'times')):
                        pass
                        l_2_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_2_allowas_in_cli is missing else l_2_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'times'), ))
                        _loop_vars['allowas_in_cli'] = l_2_allowas_in_cli
                    yield '      '
                    yield str((undefined(name='allowas_in_cli') if l_2_allowas_in_cli is missing else l_2_allowas_in_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), True):
                    pass
                    l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'all'), True):
                        pass
                        l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                        _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    yield '      '
                    yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), False):
                    pass
                    l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    yield '      '
                    yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'ebgp_multihop')):
                    pass
                    l_2_neighbor_ebgp_multihop_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' ebgp-multihop', ))
                    _loop_vars['neighbor_ebgp_multihop_cli'] = l_2_neighbor_ebgp_multihop_cli
                    if t_8(environment.getattr(l_2_neighbor, 'ebgp_multihop')):
                        pass
                        l_2_neighbor_ebgp_multihop_cli = str_join(((undefined(name='neighbor_ebgp_multihop_cli') if l_2_neighbor_ebgp_multihop_cli is missing else l_2_neighbor_ebgp_multihop_cli), ' ', environment.getattr(l_2_neighbor, 'ebgp_multihop'), ))
                        _loop_vars['neighbor_ebgp_multihop_cli'] = l_2_neighbor_ebgp_multihop_cli
                    yield '      '
                    yield str((undefined(name='neighbor_ebgp_multihop_cli') if l_2_neighbor_ebgp_multihop_cli is missing else l_2_neighbor_ebgp_multihop_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_reflector_client'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-reflector-client\n'
                elif t_6(environment.getattr(l_2_neighbor, 'route_reflector_client'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-reflector-client\n'
                if t_6(environment.getattr(l_2_neighbor, 'timers')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' timers '
                    yield str(environment.getattr(l_2_neighbor, 'timers'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_2_neighbor, 'password')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' password 7 '
                    yield str(t_2(environment.getattr(l_2_neighbor, 'password'), (undefined(name='hide_passwords') if l_2_hide_passwords is missing else l_2_hide_passwords)))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'default_originate')):
                    pass
                    l_2_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'route_map')):
                        pass
                        l_2_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'always'), True):
                        pass
                        l_2_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'send_community'), 'all'):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' send-community\n'
                elif t_6(environment.getattr(l_2_neighbor, 'send_community')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' send-community '
                    yield str(environment.getattr(l_2_neighbor, 'send_community'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'maximum_routes')):
                    pass
                    l_2_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' maximum-routes ', environment.getattr(l_2_neighbor, 'maximum_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    if t_6(environment.getattr(l_2_neighbor, 'maximum_routes_warning_limit')):
                        pass
                        l_2_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli), ' warning-limit ', environment.getattr(l_2_neighbor, 'maximum_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    if t_6(environment.getattr(l_2_neighbor, 'maximum_routes_warning_only'), True):
                        pass
                        l_2_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli), ' warning-only', ))
                        _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'enabled'), True):
                    pass
                    l_2_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' remove-private-as ingress', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_2_remove_private_as_ingress_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'replace_as'), True):
                        pass
                        l_2_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_2_remove_private_as_ingress_cli is missing else l_2_remove_private_as_ingress_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_ingress_cli'] = l_2_remove_private_as_ingress_cli
                    yield '      '
                    yield str((undefined(name='remove_private_as_ingress_cli') if l_2_remove_private_as_ingress_cli is missing else l_2_remove_private_as_ingress_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'enabled'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remove-private-as ingress\n'
            l_2_neighbor = l_2_remove_private_as_cli = l_2_allowas_in_cli = l_2_neighbor_rib_in_pre_policy_retain_cli = l_2_neighbor_ebgp_multihop_cli = l_2_hide_passwords = l_2_neighbor_default_originate_cli = l_2_maximum_routes_cli = l_2_remove_private_as_ingress_cli = missing
            for l_2_network in t_3(environment.getattr(l_1_vrf, 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_2_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_2_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_2_network, 'prefix'))
                    yield '\n'
            l_2_network = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            for l_2_aggregate_address in t_3(environment.getattr(l_1_vrf, 'aggregate_addresses'), 'prefix'):
                l_2_aggregate_address_cli = missing
                _loop_vars = {}
                pass
                l_2_aggregate_address_cli = str_join(('aggregate-address ', environment.getattr(l_2_aggregate_address, 'prefix'), ))
                _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'as_set'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' as-set', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'summary_only'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' summary-only', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'attribute_map')):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' attribute-map ', environment.getattr(l_2_aggregate_address, 'attribute_map'), ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'match_map')):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' match-map ', environment.getattr(l_2_aggregate_address, 'match_map'), ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'advertise_only'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' advertise-only', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                yield '      '
                yield str((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli))
                yield '\n'
            l_2_aggregate_address = l_2_aggregate_address_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'redistribute')):
                pass
                l_1_redistribute_var = environment.getattr(l_1_vrf, 'redistribute')
                _loop_vars['redistribute_var'] = l_1_redistribute_var
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_1_redistribute_conn = 'redistribute connected'
                    _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_1_redistribute_isis = 'redistribute isis'
                    _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf = 'redistribute ospf'
                    _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf = 'redistribute ospf match internal'
                    _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf_match = 'redistribute ospf match external'
                    _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                    _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_1_redistribute_static = 'redistribute static'
                    _loop_vars['redistribute_static'] = l_1_redistribute_static
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'enabled'), True):
                    pass
                    l_1_redistribute_rip = 'redistribute rip'
                    _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map')):
                        pass
                        l_1_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map'), ))
                        _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                    yield '      '
                    yield str((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_1_redistribute_host = 'redistribute attached-host'
                    _loop_vars['redistribute_host'] = l_1_redistribute_host
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_1_redistribute_dynamic = 'redistribute dynamic'
                    _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_1_redistribute_bgp = 'redistribute bgp leaked'
                    _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_1_redistribute_user = 'redistribute user'
                    _loop_vars['redistribute_user'] = l_1_redistribute_user
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                    yield '\n'
            elif t_6(environment.getattr(l_1_vrf, 'redistribute_routes')):
                pass
                for l_2_redistribute_route in t_3(environment.getattr(l_1_vrf, 'redistribute_routes'), 'source_protocol'):
                    l_2_redistribute_route_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_2_redistribute_route, 'source_protocol'), ))
                    _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    if (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                        pass
                        if t_6(environment.getattr(l_2_redistribute_route, 'ospf_route_type')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' match ', environment.getattr(l_2_redistribute_route, 'ospf_route_type'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    if (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'bgp'):
                        pass
                        l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    elif t_6(environment.getattr(l_2_redistribute_route, 'include_leaked'), True):
                        pass
                        l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' include leaked', ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    if t_6(environment.getattr(l_2_redistribute_route, 'route_map')):
                        pass
                        l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' route-map ', environment.getattr(l_2_redistribute_route, 'route_map'), ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    elif (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                        pass
                        if t_6(environment.getattr(l_2_redistribute_route, 'rcf')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' rcf ', environment.getattr(l_2_redistribute_route, 'rcf'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                    yield '      '
                    yield str((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli))
                    yield '\n'
                l_2_redistribute_route = l_2_redistribute_route_cli = missing
            for l_2_neighbor_interface in t_3(environment.getattr(l_1_vrf, 'neighbor_interfaces'), 'name'):
                _loop_vars = {}
                pass
                if (t_6(environment.getattr(l_2_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_2_neighbor_interface, 'remote_as'))):
                    pass
                    yield '      neighbor interface '
                    yield str(environment.getattr(l_2_neighbor_interface, 'name'))
                    yield ' peer-group '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_group'))
                    yield ' remote-as '
                    yield str(environment.getattr(l_2_neighbor_interface, 'remote_as'))
                    yield '\n'
                elif (t_6(environment.getattr(l_2_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_2_neighbor_interface, 'peer_filter'))):
                    pass
                    yield '      neighbor interface '
                    yield str(environment.getattr(l_2_neighbor_interface, 'name'))
                    yield ' peer-group '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_group'))
                    yield ' peer-filter '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_filter'))
                    yield '\n'
            l_2_neighbor_interface = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4')):
                pass
                yield '      !\n      address-family flow-spec ipv4\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                l_2_neighbor = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6')):
                pass
                yield '      !\n      address-family flow-spec ipv6\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                l_2_neighbor = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv4')):
                pass
                yield '      !\n      address-family ipv4\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install'), True):
                    pass
                    yield '         bgp additional-paths install\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                    pass
                    yield '         bgp additional-paths install ecmp-primary\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '         no bgp additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '         bgp additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')):
                            pass
                            yield '         bgp additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '         bgp additional-paths send '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send'))
                        yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'neighbors'), 'ip_address'):
                    l_2_ipv6_originate_cli = resolve('ipv6_originate_cli')
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf in '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf out '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_out'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                        pass
                        if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send\n'
                        elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                yield '         neighbor '
                                yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                                yield ' additional-paths send limit '
                                yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                                yield '\n'
                        else:
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                            yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled')):
                        pass
                        if environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled'):
                            pass
                            l_2_ipv6_originate_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' next-hop address-family ipv6', ))
                            _loop_vars['ipv6_originate_cli'] = l_2_ipv6_originate_cli
                            if t_6(environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                                pass
                                l_2_ipv6_originate_cli = str_join(((undefined(name='ipv6_originate_cli') if l_2_ipv6_originate_cli is missing else l_2_ipv6_originate_cli), ' originate', ))
                                _loop_vars['ipv6_originate_cli'] = l_2_ipv6_originate_cli
                            yield '         '
                            yield str((undefined(name='ipv6_originate_cli') if l_2_ipv6_originate_cli is missing else l_2_ipv6_originate_cli))
                            yield '\n'
                        else:
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' next-hop address-family ipv6\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = l_2_ipv6_originate_cli = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), True):
                    pass
                    yield '         bgp redistribute-internal\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), False):
                    pass
                    yield '         no bgp redistribute-internal\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                        pass
                        l_1_redistribute_bgp = 'redistribute bgp leaked'
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                            pass
                            l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                            _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        yield '         '
                        yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                        pass
                        l_1_redistribute_dynamic = 'redistribute dynamic'
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        yield '         '
                        yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                        pass
                        l_1_redistribute_user = 'redistribute user'
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                            pass
                            l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                            _loop_vars['redistribute_user'] = l_1_redistribute_user
                        yield '         '
                        yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'enabled'), True):
                        pass
                        l_1_redistribute_rip = 'redistribute rip'
                        _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map')):
                            pass
                            l_1_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map'), ))
                            _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                        yield '         '
                        yield str((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute_routes')):
                    pass
                    for l_2_redistribute_route in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute_routes'), 'source_protocol'):
                        l_2_redistribute_route_cli = missing
                        _loop_vars = {}
                        pass
                        l_2_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_2_redistribute_route, 'source_protocol'), ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'ospf_route_type')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' match ', environment.getattr(l_2_redistribute_route, 'ospf_route_type'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'bgp'):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (t_6(environment.getattr(l_2_redistribute_route, 'include_leaked'), True) and (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['connected', 'isis', 'ospf', 'ospfv3', 'static'])):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' include leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'route_map')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' route-map ', environment.getattr(l_2_redistribute_route, 'route_map'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'rcf')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' rcf ', environment.getattr(l_2_redistribute_route, 'rcf'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        yield '         '
                        yield str((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli))
                        yield '\n'
                    l_2_redistribute_route = l_2_redistribute_route_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast')):
                pass
                yield '      !\n      address-family ipv4 multicast\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute_routes')):
                    pass
                    for l_2_redistribute_route in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute_routes'), 'source_protocol'):
                        l_2_redistribute_route_cli = missing
                        _loop_vars = {}
                        pass
                        l_2_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_2_redistribute_route, 'source_protocol'), ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'ospf_route_type')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' match ', environment.getattr(l_2_redistribute_route, 'ospf_route_type'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'include_leaked'), True):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' include leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'route_map')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' route-map ', environment.getattr(l_2_redistribute_route, 'route_map'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'isis'):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'rcf')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' rcf ', environment.getattr(l_2_redistribute_route, 'rcf'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        yield '         '
                        yield str((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli))
                        yield '\n'
                    l_2_redistribute_route = l_2_redistribute_route_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv6')):
                pass
                yield '      !\n      address-family ipv6\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install'), True):
                    pass
                    yield '         bgp additional-paths install\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                    pass
                    yield '         bgp additional-paths install ecmp-primary\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '         no bgp additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '         bgp additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')):
                            pass
                            yield '         bgp additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '         bgp additional-paths send '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send'))
                        yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf in '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf out '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_out'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                        pass
                        if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send\n'
                        elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                yield '         neighbor '
                                yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                                yield ' additional-paths send limit '
                                yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                                yield '\n'
                        else:
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                            yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), True):
                    pass
                    yield '         bgp redistribute-internal\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), False):
                    pass
                    yield '         no bgp redistribute-internal\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                        pass
                        l_1_redistribute_bgp = 'redistribute bgp leaked'
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                            pass
                            l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                            _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        yield '         '
                        yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'enabled'), True):
                        pass
                        l_1_redistribute_dhcp = 'redistribute dhcp'
                        _loop_vars['redistribute_dhcp'] = l_1_redistribute_dhcp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'route_map')):
                            pass
                            l_1_redistribute_dhcp = str_join(((undefined(name='redistribute_dhcp') if l_1_redistribute_dhcp is missing else l_1_redistribute_dhcp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'route_map'), ))
                            _loop_vars['redistribute_dhcp'] = l_1_redistribute_dhcp
                        yield '         '
                        yield str((undefined(name='redistribute_dhcp') if l_1_redistribute_dhcp is missing else l_1_redistribute_dhcp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                        pass
                        l_1_redistribute_dynamic = 'redistribute dynamic'
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        yield '         '
                        yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                        pass
                        l_1_redistribute_user = 'redistribute user'
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                            pass
                            l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                            _loop_vars['redistribute_user'] = l_1_redistribute_user
                        yield '         '
                        yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute_routes')):
                    pass
                    for l_2_redistribute_route in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute_routes'), 'source_protocol'):
                        l_2_redistribute_route_cli = missing
                        _loop_vars = {}
                        pass
                        l_2_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_2_redistribute_route, 'source_protocol'), ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'ospfv3'):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'ospf_route_type')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' match ', environment.getattr(l_2_redistribute_route, 'ospf_route_type'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'bgp'):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (t_6(environment.getattr(l_2_redistribute_route, 'include_leaked'), True) and (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['connected', 'isis', 'ospfv3', 'static'])):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' include leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'route_map')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' route-map ', environment.getattr(l_2_redistribute_route, 'route_map'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['connected', 'static', 'isis', 'user', 'dynamic']):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'rcf')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' rcf ', environment.getattr(l_2_redistribute_route, 'rcf'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        yield '         '
                        yield str((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli))
                        yield '\n'
                    l_2_redistribute_route = l_2_redistribute_route_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast')):
                pass
                yield '      !\n      address-family ipv6 multicast\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute_routes')):
                    pass
                    for l_2_redistribute_route in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute_routes'), 'source_protocol'):
                        l_2_redistribute_route_cli = missing
                        _loop_vars = {}
                        pass
                        l_2_redistribute_route_cli = str_join(('redistribute ', environment.getattr(l_2_redistribute_route, 'source_protocol'), ))
                        _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if (environment.getattr(l_2_redistribute_route, 'source_protocol') in ['ospf', 'ospfv3']):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'ospf_route_type')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' match ', environment.getattr(l_2_redistribute_route, 'ospf_route_type'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'include_leaked'), True):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' include leaked', ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        if t_6(environment.getattr(l_2_redistribute_route, 'route_map')):
                            pass
                            l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' route-map ', environment.getattr(l_2_redistribute_route, 'route_map'), ))
                            _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        elif (environment.getattr(l_2_redistribute_route, 'source_protocol') == 'isis'):
                            pass
                            if t_6(environment.getattr(l_2_redistribute_route, 'rcf')):
                                pass
                                l_2_redistribute_route_cli = str_join(((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli), ' rcf ', environment.getattr(l_2_redistribute_route, 'rcf'), ))
                                _loop_vars['redistribute_route_cli'] = l_2_redistribute_route_cli
                        yield '         '
                        yield str((undefined(name='redistribute_route_cli') if l_2_redistribute_route_cli is missing else l_2_redistribute_route_cli))
                        yield '\n'
                    l_2_redistribute_route = l_2_redistribute_route_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'evpn_multicast'), True):
                pass
                yield '      evpn multicast\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm') == 'preference'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'preference_value')):
                            pass
                            yield '         gateway dr election algorithm preference '
                            yield str(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'preference_value'))
                            yield '\n'
                    else:
                        pass
                        yield '         gateway dr election algorithm '
                        yield str(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm'))
                        yield '\n'
                if (t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4')) and t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4'), 'transit'), True)):
                    pass
                    yield '         address-family ipv4\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4'), 'transit'), True):
                        pass
                        yield '            transit\n'
            if t_6(environment.getattr(l_1_vrf, 'eos_cli')):
                pass
                yield '      !\n      '
                yield str(t_4(environment.getattr(l_1_vrf, 'eos_cli'), 6, False))
                yield '\n'
        l_1_vrf = l_1_paths_cli = l_1_redistribute_var = l_1_redistribute_conn = l_1_redistribute_isis = l_1_redistribute_ospf = l_1_redistribute_ospf_match = l_1_redistribute_ospfv3 = l_1_redistribute_ospfv3_match = l_1_redistribute_static = l_1_redistribute_rip = l_1_redistribute_host = l_1_redistribute_dynamic = l_1_redistribute_bgp = l_1_redistribute_user = l_1_redistribute_dhcp = missing
        for l_1_session_tracker in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'session_trackers'), 'name'):
            _loop_vars = {}
            pass
            yield '   session tracker '
            yield str(environment.getattr(l_1_session_tracker, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_session_tracker, 'recovery_delay')):
                pass
                yield '      recovery delay '
                yield str(environment.getattr(l_1_session_tracker, 'recovery_delay'))
                yield ' seconds\n'
        l_1_session_tracker = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'eos_cli')):
            pass
            yield '   !\n   '
            yield str(t_4(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'eos_cli'), 3, False))
            yield '\n'

blocks = {}
debug_info = '7=85&9=88&10=90&11=93&13=95&14=98&16=100&19=103&22=106&24=109&27=112&29=115&32=118&33=120&34=123&35=125&37=128&38=130&39=132&41=135&42=137&45=141&47=143&48=145&49=148&50=150&52=154&54=156&55=158&56=161&58=163&59=166&63=169&64=172&66=174&68=177&69=179&70=182&71=184&75=187&76=189&77=192&78=194&80=198&82=200&83=202&84=205&85=207&87=211&89=213&90=217&92=220&95=223&98=226&99=228&101=231&102=234&103=236&104=238&105=241&108=246&111=248&113=250&112=254&114=258&115=260&116=262&118=264&119=266&120=268&121=270&122=272&124=275&127=278&130=281&132=284&133=287&135=289&136=301&137=303&138=306&140=310&141=313&143=315&144=318&146=320&147=323&149=325&150=328&152=330&153=332&154=334&155=336&156=338&157=340&160=343&161=345&162=348&164=350&165=353&167=355&168=358&170=360&171=363&173=367&174=370&176=374&177=377&179=379&180=382&182=386&183=389&184=391&187=394&190=402&191=405&193=409&194=411&195=413&196=415&198=418&200=420&201=422&202=424&203=426&205=429&206=431&207=433&208=436&210=438&211=441&213=445&214=448&216=452&217=455&219=457&220=460&222=464&223=467&225=471&226=474&228=478&229=481&231=485&232=488&234=492&235=495&237=501&238=503&239=505&240=507&242=509&243=511&245=514&247=516&248=519&249=521&250=524&252=528&253=530&254=532&255=534&257=536&258=538&260=541&262=543&263=545&264=550&265=552&266=554&267=556&268=558&269=560&270=562&271=564&273=566&274=568&276=570&277=572&280=574&281=577&285=580&286=583&288=587&289=590&291=594&292=596&293=598&294=600&296=603&298=605&299=607&300=609&301=611&303=614&304=616&305=619&308=622&309=633&310=636&312=640&313=643&315=647&316=650&318=652&319=655&321=657&322=660&324=662&325=664&326=666&327=668&328=670&329=672&332=675&333=677&334=680&336=682&337=685&339=687&340=690&342=692&343=695&345=699&346=702&348=706&349=709&351=711&352=714&354=718&355=721&356=723&359=726&361=734&362=737&364=739&365=742&367=746&368=748&369=750&370=752&372=755&374=757&375=759&376=761&377=763&379=766&380=768&381=770&382=773&384=775&385=778&387=782&388=785&390=789&391=792&392=794&393=797&395=799&396=802&398=806&399=809&401=813&402=816&404=820&405=823&407=827&408=830&410=836&411=839&413=843&414=845&415=847&416=849&418=851&419=853&421=856&423=858&424=861&425=863&426=866&428=870&429=872&430=874&431=876&433=878&434=880&436=883&438=885&439=887&440=892&441=894&442=896&443=898&444=900&445=902&446=904&447=906&449=908&450=910&452=912&453=914&456=916&457=919&461=922&462=925&464=929&465=932&467=936&468=938&469=940&470=942&472=945&474=947&475=949&476=951&477=953&479=956&480=958&481=961&484=964&486=967&489=970&490=974&491=976&492=978&494=980&495=982&497=984&498=986&500=988&501=990&503=992&504=994&506=997&508=1000&509=1002&510=1005&511=1007&512=1010&513=1012&515=1015&516=1017&517=1020&518=1022&520=1026&522=1028&523=1030&524=1033&525=1035&527=1038&528=1040&530=1043&531=1045&532=1048&533=1050&535=1054&537=1056&538=1058&539=1061&540=1063&542=1066&543=1068&545=1072&546=1074&547=1076&548=1079&549=1081&551=1084&552=1086&554=1090&556=1092&557=1094&558=1097&559=1099&561=1102&562=1104&564=1108&566=1110&567=1112&568=1115&569=1117&571=1120&572=1122&574=1125&575=1127&577=1131&579=1133&580=1135&581=1138&582=1140&584=1143&585=1145&587=1149&588=1151&589=1153&590=1156&591=1158&593=1161&594=1163&596=1167&598=1169&599=1171&600=1174&601=1176&603=1179&604=1181&606=1185&608=1187&609=1189&610=1192&611=1194&613=1197&614=1199&616=1202&617=1204&619=1208&621=1210&622=1212&623=1215&624=1217&626=1220&627=1222&628=1225&629=1227&631=1231&633=1233&634=1235&635=1238&636=1240&638=1244&640=1246&641=1248&642=1251&643=1253&645=1257&647=1259&648=1261&649=1264&650=1266&651=1269&652=1271&654=1275&656=1277&657=1279&658=1282&659=1284&661=1288&663=1290&664=1292&665=1295&666=1297&668=1301&670=1303&671=1305&672=1309&673=1311&674=1313&675=1315&678=1317&679=1319&680=1321&681=1323&683=1325&684=1327&685=1329&686=1331&687=1333&690=1336&693=1339&694=1342&695=1345&696=1351&697=1354&701=1361&702=1363&704=1367&705=1369&706=1372&708=1374&709=1377&711=1381&712=1385&714=1388&715=1392&717=1395&718=1399&720=1402&721=1406&723=1411&724=1415&726=1420&727=1424&729=1429&730=1433&732=1436&733=1440&735=1443&737=1446&742=1449&743=1451&745=1455&746=1458&747=1460&748=1463&750=1465&751=1468&753=1470&756=1473&759=1476&760=1479&762=1481&763=1484&765=1487&766=1489&773=1495&775=1499&776=1501&777=1504&779=1506&780=1509&782=1513&783=1517&785=1520&786=1524&788=1527&789=1531&791=1534&792=1538&794=1543&795=1547&797=1552&798=1556&800=1561&801=1565&803=1568&804=1572&806=1576&807=1578&809=1581&814=1584&817=1587&820=1590&823=1593&825=1596&828=1599&829=1601&831=1604&832=1607&833=1609&834=1611&835=1614&838=1619&840=1621&842=1624&844=1627&846=1630&847=1633&848=1635&849=1638&851=1640&854=1643&855=1645&856=1648&857=1650&859=1654&861=1656&862=1658&863=1661&864=1664&865=1666&866=1667&867=1669&868=1670&869=1672&872=1674&873=1677&876=1679&877=1684&878=1687&879=1689&880=1692&882=1694&883=1697&885=1699&886=1702&888=1706&889=1709&891=1713&892=1716&894=1720&895=1723&897=1727&898=1729&899=1731&900=1733&901=1735&902=1737&904=1740&906=1742&907=1744&908=1747&909=1749&910=1752&911=1756&912=1758&913=1761&916=1768&919=1772&920=1775&922=1779&923=1782&925=1786&926=1788&927=1790&928=1792&930=1795&932=1797&933=1800&936=1803&937=1808&938=1811&939=1813&940=1816&942=1818&943=1821&945=1823&946=1826&948=1830&949=1833&951=1837&952=1840&954=1844&955=1847&957=1851&958=1853&959=1855&960=1857&961=1859&962=1861&964=1864&966=1866&967=1868&968=1871&969=1873&970=1876&971=1880&972=1882&973=1885&976=1892&979=1896&980=1899&982=1903&983=1906&985=1910&986=1912&987=1914&988=1916&990=1919&993=1922&994=1925&996=1927&997=1930&999=1932&1002=1935&1005=1938&1006=1940&1007=1943&1008=1945&1010=1949&1012=1951&1014=1954&1015=1956&1016=1959&1017=1961&1019=1964&1020=1966&1022=1969&1023=1971&1025=1974&1026=1977&1029=1979&1030=1981&1031=1984&1032=1986&1034=1990&1036=1992&1039=1995&1041=1999&1042=2001&1043=2004&1045=2006&1046=2009&1051=2012&1054=2015&1055=2018&1057=2020&1058=2023&1060=2025&1061=2028&1062=2031&1063=2033&1064=2036&1067=2039&1068=2042&1069=2045&1074=2048&1077=2051&1078=2054&1080=2056&1081=2059&1083=2061&1084=2064&1085=2067&1086=2069&1087=2072&1090=2075&1091=2078&1092=2081&1097=2084&1100=2087&1102=2090&1105=2093&1108=2096&1109=2098&1111=2101&1112=2104&1113=2106&1114=2108&1115=2111&1118=2116&1121=2118&1122=2124&1123=2127&1124=2129&1125=2132&1127=2134&1128=2137&1130=2139&1131=2142&1133=2146&1134=2149&1136=2153&1137=2156&1139=2160&1140=2163&1142=2167&1143=2170&1145=2174&1146=2177&1148=2181&1149=2183&1150=2185&1151=2187&1153=2189&1154=2191&1156=2194&1158=2196&1159=2198&1160=2201&1162=2205&1163=2207&1164=2209&1165=2211&1166=2213&1169=2217&1171=2219&1172=2221&1174=2223&1175=2226&1179=2228&1180=2230&1181=2232&1182=2234&1184=2237&1186=2239&1187=2242&1189=2246&1190=2249&1193=2254&1194=2260&1195=2263&1196=2265&1197=2268&1199=2270&1200=2273&1202=2275&1203=2278&1205=2282&1206=2285&1208=2289&1209=2292&1211=2296&1212=2299&1214=2303&1215=2306&1217=2310&1218=2313&1220=2317&1221=2319&1222=2321&1223=2323&1225=2325&1226=2327&1228=2330&1230=2332&1231=2334&1232=2337&1234=2341&1235=2343&1236=2345&1237=2347&1238=2349&1241=2353&1243=2355&1244=2357&1246=2359&1247=2362&1251=2364&1252=2366&1253=2368&1254=2370&1255=2372&1257=2375&1259=2380&1262=2382&1263=2385&1265=2389&1266=2392&1269=2397&1270=2400&1271=2403&1273=2410&1276=2413&1278=2416&1281=2419&1282=2421&1283=2424&1284=2426&1285=2429&1286=2431&1288=2435&1290=2437&1291=2439&1292=2442&1293=2444&1295=2448&1297=2450&1298=2452&1299=2455&1300=2457&1302=2460&1303=2462&1304=2465&1305=2467&1307=2471&1309=2473&1310=2475&1311=2478&1312=2480&1313=2483&1314=2485&1316=2489&1318=2491&1319=2493&1320=2496&1321=2498&1323=2502&1325=2504&1326=2506&1327=2509&1328=2511&1330=2514&1331=2516&1333=2519&1334=2521&1335=2524&1336=2526&1338=2530&1340=2532&1341=2534&1342=2537&1343=2539&1345=2542&1346=2544&1348=2548&1349=2550&1350=2552&1351=2555&1352=2557&1354=2560&1355=2562&1357=2566&1359=2568&1360=2570&1361=2573&1362=2575&1364=2578&1365=2580&1367=2584&1368=2586&1369=2588&1370=2591&1371=2593&1373=2596&1374=2598&1376=2602&1378=2604&1379=2606&1380=2609&1381=2611&1383=2614&1384=2616&1386=2620&1388=2622&1389=2624&1390=2627&1391=2629&1393=2632&1394=2634&1396=2637&1397=2639&1399=2643&1401=2645&1402=2647&1403=2650&1404=2652&1406=2655&1407=2657&1409=2661&1411=2663&1412=2665&1413=2668&1414=2670&1416=2673&1417=2675&1419=2678&1420=2680&1422=2684&1424=2686&1425=2688&1426=2691&1427=2693&1429=2697&1431=2699&1432=2701&1433=2704&1434=2706&1436=2709&1437=2711&1438=2714&1439=2716&1441=2720&1443=2722&1444=2724&1445=2728&1446=2730&1447=2732&1448=2734&1451=2736&1452=2738&1453=2740&1454=2742&1456=2744&1457=2746&1458=2748&1459=2750&1460=2752&1463=2755&1468=2758&1471=2761&1474=2764&1475=2766&1476=2771&1477=2773&1478=2775&1479=2777&1480=2779&1481=2781&1482=2783&1483=2785&1485=2787&1486=2789&1488=2791&1489=2793&1492=2795&1493=2798&1497=2801&1500=2804&1501=2806&1503=2809&1504=2812&1505=2814&1506=2816&1507=2819&1510=2824&1513=2826&1516=2829&1519=2832&1520=2834&1521=2837&1522=2840&1523=2842&1524=2843&1525=2845&1526=2847&1528=2848&1529=2850&1532=2852&1533=2855&1536=2857&1537=2861&1538=2864&1540=2869&1542=2871&1543=2874&1545=2876&1546=2879&1548=2881&1549=2884&1551=2888&1552=2891&1554=2895&1555=2898&1557=2902&1558=2905&1560=2909&1561=2912&1563=2916&1564=2918&1565=2921&1566=2923&1567=2926&1568=2930&1569=2932&1570=2935&1573=2942&1576=2946&1577=2949&1579=2951&1580=2954&1582=2956&1583=2959&1584=2963&1585=2966&1587=2970&1588=2972&1589=2974&1590=2976&1592=2979&1594=2981&1595=2983&1596=2988&1597=2990&1598=2992&1599=2994&1600=2996&1601=2998&1602=3000&1603=3002&1605=3004&1606=3006&1608=3008&1609=3010&1612=3012&1613=3015&1617=3018&1618=3021&1620=3025&1621=3028&1623=3032&1624=3035&1626=3037&1627=3040&1630=3043&1631=3047&1632=3050&1634=3055&1636=3057&1637=3060&1639=3062&1640=3065&1642=3067&1643=3070&1645=3074&1646=3077&1648=3081&1649=3084&1651=3088&1652=3091&1654=3095&1655=3098&1657=3102&1658=3104&1659=3107&1660=3109&1661=3112&1662=3116&1663=3118&1664=3121&1667=3128&1670=3132&1671=3135&1673=3137&1674=3140&1676=3142&1677=3145&1678=3149&1679=3152&1681=3156&1682=3158&1683=3160&1684=3162&1686=3165&1688=3167&1689=3169&1690=3174&1691=3176&1692=3178&1693=3180&1694=3182&1695=3184&1696=3186&1697=3188&1699=3190&1700=3192&1702=3194&1703=3196&1706=3198&1707=3201&1711=3204&1712=3207&1714=3211&1715=3214&1717=3218&1718=3221&1720=3223&1721=3226&1724=3229&1725=3231&1726=3235&1727=3237&1728=3239&1730=3242&1733=3245&1734=3247&1735=3251&1736=3253&1737=3255&1739=3258&1742=3261&1745=3264&1746=3267&1748=3269&1751=3272&1752=3274&1753=3278&1754=3280&1755=3282&1757=3285&1760=3288&1761=3290&1762=3293&1763=3296&1769=3299&1772=3302&1775=3305&1776=3308&1777=3311&1778=3313&1779=3316&1781=3318&1782=3321&1784=3323&1785=3326&1787=3330&1788=3333&1790=3337&1791=3340&1793=3344&1794=3347&1797=3352&1798=3355&1799=3358&1800=3360&1801=3363&1803=3365&1804=3368&1806=3370&1807=3373&1809=3377&1810=3380&1812=3384&1813=3387&1815=3391&1816=3394&1819=3399&1820=3401&1821=3404&1822=3406&1823=3409&1824=3411&1826=3415&1828=3417&1829=3419&1830=3422&1831=3424&1833=3428&1835=3430&1836=3432&1837=3435&1838=3437&1840=3440&1841=3442&1843=3445&1844=3447&1845=3450&1846=3452&1848=3456&1850=3458&1851=3460&1852=3463&1853=3465&1855=3469&1856=3471&1857=3473&1858=3476&1859=3478&1861=3482&1863=3484&1864=3486&1865=3489&1866=3491&1868=3495&1869=3497&1870=3499&1871=3502&1872=3504&1874=3508&1876=3510&1877=3512&1878=3515&1879=3517&1881=3521&1883=3523&1884=3525&1885=3528&1886=3530&1888=3533&1889=3535&1891=3539&1893=3541&1894=3543&1895=3546&1896=3548&1898=3552&1900=3554&1901=3556&1902=3559&1903=3561&1905=3564&1906=3566&1908=3570&1910=3572&1911=3574&1912=3577&1913=3579&1915=3583&1917=3585&1918=3587&1919=3591&1920=3593&1921=3595&1922=3597&1925=3599&1926=3601&1928=3603&1929=3605&1930=3607&1931=3609&1933=3612&1938=3615&1941=3618&1942=3621&1943=3624&1944=3626&1945=3629&1947=3631&1948=3634&1950=3638&1951=3641&1953=3645&1954=3648&1956=3652&1957=3655&1960=3660&1961=3663&1962=3666&1963=3668&1964=3671&1966=3673&1967=3676&1969=3680&1970=3683&1972=3687&1973=3690&1975=3694&1976=3697&1981=3702&1984=3705&1986=3708&1989=3711&1992=3714&1993=3716&1995=3719&1996=3722&1997=3724&1998=3726&1999=3729&2002=3734&2005=3736&2006=3740&2007=3743&2008=3745&2009=3748&2011=3750&2012=3753&2014=3755&2015=3758&2017=3762&2018=3765&2020=3769&2021=3772&2023=3776&2024=3779&2026=3783&2027=3786&2029=3790&2030=3793&2032=3797&2033=3799&2034=3802&2036=3806&2037=3808&2038=3810&2039=3812&2040=3814&2043=3818&2045=3820&2046=3822&2048=3824&2049=3827&2053=3829&2054=3832&2056=3836&2057=3839&2060=3844&2061=3848&2062=3851&2063=3853&2064=3856&2066=3858&2067=3861&2069=3863&2070=3866&2072=3870&2073=3873&2075=3877&2076=3880&2078=3884&2079=3887&2081=3891&2082=3894&2084=3898&2085=3901&2087=3905&2088=3907&2089=3910&2091=3914&2092=3916&2093=3918&2094=3920&2095=3922&2098=3926&2100=3928&2101=3930&2103=3932&2104=3935&2108=3937&2109=3940&2111=3944&2112=3947&2115=3952&2116=3955&2117=3958&2119=3965&2122=3968&2124=3971&2127=3974&2128=3976&2129=3979&2130=3981&2131=3984&2132=3986&2134=3990&2136=3992&2137=3994&2138=3997&2139=3999&2141=4003&2143=4005&2144=4007&2145=4010&2146=4012&2148=4016&2150=4018&2151=4020&2152=4023&2153=4025&2155=4028&2156=4030&2157=4033&2158=4035&2160=4039&2162=4041&2163=4043&2164=4046&2165=4048&2166=4051&2167=4053&2169=4057&2171=4059&2172=4061&2173=4064&2174=4066&2176=4070&2178=4072&2179=4074&2180=4077&2181=4079&2183=4082&2184=4084&2186=4087&2187=4089&2188=4092&2189=4094&2191=4098&2193=4100&2194=4102&2195=4105&2196=4107&2198=4110&2199=4112&2201=4116&2202=4118&2203=4120&2204=4123&2205=4125&2207=4128&2208=4130&2210=4134&2212=4136&2213=4138&2214=4141&2215=4143&2217=4146&2218=4148&2220=4152&2222=4154&2223=4156&2224=4159&2225=4161&2227=4164&2228=4166&2230=4169&2231=4171&2233=4175&2235=4177&2236=4179&2237=4182&2238=4184&2240=4187&2241=4189&2242=4192&2243=4194&2245=4198&2247=4200&2248=4202&2249=4206&2250=4208&2251=4210&2252=4212&2255=4214&2256=4216&2257=4218&2258=4220&2260=4222&2261=4224&2262=4226&2263=4228&2264=4230&2267=4233&2272=4236&2275=4239&2276=4242&2278=4244&2279=4247&2281=4249&2284=4252&2285=4255&2286=4258&2287=4260&2288=4263&2290=4265&2291=4268&2294=4271&2295=4274&2296=4277&2298=4279&2299=4282&2301=4284&2302=4287&2304=4291&2305=4294&2307=4298&2308=4301&2310=4305&2311=4308&2314=4313&2315=4317&2316=4319&2317=4321&2319=4324&2321=4327&2322=4329&2323=4332&2324=4334&2325=4337&2326=4339&2328=4343&2330=4345&2331=4347&2332=4350&2333=4352&2335=4355&2336=4357&2338=4360&2339=4362&2340=4365&2341=4367&2343=4371&2345=4373&2346=4375&2347=4378&2348=4380&2350=4384&2351=4386&2352=4388&2353=4391&2354=4393&2356=4397&2358=4399&2359=4401&2360=4404&2361=4406&2363=4410&2364=4412&2365=4414&2366=4417&2367=4419&2369=4423&2371=4425&2372=4427&2373=4430&2374=4432&2376=4436&2378=4438&2379=4440&2380=4443&2381=4445&2383=4448&2384=4450&2386=4454&2388=4456&2389=4458&2390=4461&2391=4463&2393=4467&2395=4469&2396=4471&2397=4474&2398=4476&2400=4479&2401=4481&2403=4485&2405=4487&2406=4489&2407=4492&2408=4494&2410=4498&2412=4500&2413=4502&2414=4506&2415=4508&2416=4510&2417=4512&2420=4514&2421=4516&2423=4518&2424=4520&2425=4522&2426=4524&2428=4527&2433=4530&2436=4533&2437=4536&2438=4539&2439=4541&2440=4544&2442=4546&2443=4549&2445=4553&2446=4556&2448=4560&2449=4563&2451=4567&2452=4570&2455=4575&2456=4578&2457=4581&2458=4583&2459=4586&2461=4588&2462=4591&2464=4595&2465=4598&2467=4602&2468=4605&2470=4609&2471=4612&2476=4617&2479=4620&2480=4623&2482=4625&2483=4628&2485=4630&2486=4633&2487=4636&2488=4638&2489=4641&2491=4643&2492=4646&2494=4650&2495=4653&2498=4658&2499=4661&2500=4664&2502=4666&2503=4669&2505=4673&2506=4676&2509=4681&2510=4683&2513=4686&2514=4688&2515=4691&2516=4693&2518=4696&2519=4698&2521=4702&2526=4704&2529=4707&2532=4710&2533=4712&2535=4715&2536=4718&2537=4720&2538=4722&2539=4725&2542=4730&2545=4732&2546=4735&2547=4738&2548=4740&2549=4743&2551=4745&2552=4748&2554=4750&2555=4752&2556=4755&2557=4757&2558=4759&2559=4762&2560=4766&2561=4769&2564=4776&2568=4781&2569=4784&2570=4787&2571=4789&2572=4792&2574=4794&2575=4797&2577=4799&2578=4801&2579=4804&2580=4806&2581=4809&2582=4813&2583=4815&2584=4818&2587=4825&2593=4830&2596=4833&2597=4836&2598=4839&2599=4841&2600=4844&2602=4846&2603=4848&2604=4851&2606=4856&2609=4858&2610=4861&2615=4864&2618=4867&2619=4871&2620=4874&2621=4876&2622=4879&2624=4881&2625=4884&2627=4888&2628=4891&2630=4895&2631=4898&2633=4902&2634=4905&2636=4909&2637=4911&2638=4913&2639=4915&2640=4917&2641=4919&2643=4922&2645=4924&2646=4927&2648=4931&2649=4934&2652=4939&2653=4943&2654=4946&2655=4948&2656=4951&2658=4953&2659=4956&2661=4960&2662=4963&2664=4967&2665=4970&2667=4974&2668=4977&2670=4981&2671=4983&2672=4985&2673=4987&2674=4989&2675=4991&2677=4994&2679=4996&2680=4999&2682=5003&2683=5006&2686=5011&2687=5014&2689=5016&2690=5019&2692=5021&2697=5024&2700=5027&2701=5031&2702=5034&2703=5036&2704=5039&2706=5041&2707=5044&2709=5048&2710=5051&2712=5055&2713=5058&2715=5062&2716=5065&2718=5069&2719=5071&2720=5073&2721=5075&2722=5077&2723=5079&2725=5082&2727=5084&2728=5087&2730=5091&2731=5094&2734=5099&2735=5103&2736=5106&2737=5108&2738=5111&2740=5113&2741=5116&2743=5120&2744=5123&2746=5127&2747=5130&2749=5134&2750=5137&2752=5141&2753=5143&2754=5145&2755=5147&2756=5149&2757=5151&2759=5154&2761=5156&2762=5159&2764=5163&2765=5166&2768=5171&2769=5174&2771=5176&2772=5179&2774=5181&2779=5184&2781=5203&2782=5205&2783=5208&2785=5210&2786=5212&2787=5216&2788=5218&2789=5220&2791=5222&2792=5224&2793=5226&2794=5228&2796=5231&2799=5234&2800=5236&2801=5239&2802=5243&2804=5248&2805=5250&2806=5252&2807=5255&2809=5264&2812=5268&2813=5271&2818=5276&2819=5278&2820=5281&2821=5285&2823=5290&2824=5292&2825=5294&2826=5297&2828=5306&2831=5310&2832=5313&2837=5318&2838=5321&2840=5323&2843=5326&2846=5329&2847=5332&2849=5334&2850=5336&2851=5339&2853=5341&2854=5344&2858=5347&2859=5349&2860=5351&2861=5353&2863=5356&2865=5358&2867=5361&2870=5364&2873=5367&2874=5369&2876=5372&2877=5375&2878=5377&2879=5379&2880=5382&2883=5387&2886=5389&2888=5391&2887=5395&2889=5399&2890=5401&2891=5403&2893=5405&2894=5407&2895=5409&2896=5411&2897=5413&2899=5416&2902=5419&2903=5430&2904=5433&2906=5437&2907=5440&2909=5444&2910=5447&2912=5449&2913=5452&2915=5454&2916=5457&2918=5459&2919=5461&2920=5463&2921=5465&2922=5467&2923=5469&2926=5472&2927=5474&2928=5477&2930=5479&2931=5482&2933=5484&2934=5487&2936=5489&2937=5492&2939=5496&2940=5499&2942=5503&2943=5506&2945=5508&2946=5511&2948=5515&2949=5518&2950=5520&2953=5523&2955=5531&2956=5534&2958=5536&2959=5539&2961=5543&2962=5545&2963=5547&2964=5549&2966=5552&2968=5554&2969=5556&2970=5558&2971=5560&2973=5563&2974=5565&2975=5567&2976=5570&2978=5572&2979=5574&2980=5576&2981=5578&2983=5581&2985=5583&2986=5586&2987=5588&2988=5591&2990=5593&2991=5596&2993=5600&2994=5603&2996=5607&2997=5610&2999=5612&3000=5614&3001=5617&3002=5619&3003=5622&3004=5626&3005=5628&3006=5631&3009=5638&3012=5642&3013=5645&3015=5649&3016=5652&3018=5656&3019=5658&3020=5660&3021=5662&3023=5664&3024=5666&3026=5669&3028=5671&3029=5674&3030=5676&3031=5679&3033=5683&3034=5685&3035=5687&3036=5689&3038=5691&3039=5693&3041=5696&3043=5698&3044=5701&3046=5705&3047=5708&3049=5712&3050=5714&3051=5716&3052=5718&3054=5721&3055=5723&3056=5726&3059=5729&3060=5732&3061=5735&3063=5742&3066=5745&3068=5748&3071=5751&3072=5755&3073=5757&3074=5759&3076=5761&3077=5763&3079=5765&3080=5767&3082=5769&3083=5771&3085=5773&3086=5775&3088=5778&3090=5781&3091=5783&3092=5785&3093=5787&3094=5789&3095=5791&3097=5793&3098=5795&3099=5797&3100=5799&3102=5802&3104=5804&3105=5806&3106=5808&3107=5810&3109=5812&3110=5814&3112=5816&3113=5818&3114=5820&3115=5822&3117=5825&3119=5827&3120=5829&3121=5831&3122=5833&3124=5835&3125=5837&3127=5840&3128=5842&3129=5844&3130=5846&3131=5848&3133=5850&3134=5852&3136=5855&3138=5857&3139=5859&3140=5861&3141=5863&3143=5865&3144=5867&3146=5870&3148=5872&3149=5874&3150=5876&3151=5878&3153=5880&3154=5882&3156=5884&3157=5886&3159=5889&3161=5891&3162=5893&3163=5895&3164=5897&3166=5899&3167=5901&3169=5904&3170=5906&3171=5908&3172=5910&3173=5912&3175=5914&3176=5916&3178=5919&3180=5921&3181=5923&3182=5925&3183=5927&3185=5929&3186=5931&3188=5934&3190=5936&3191=5938&3192=5940&3193=5942&3195=5944&3196=5946&3198=5948&3199=5950&3201=5953&3203=5955&3204=5957&3205=5959&3206=5961&3208=5963&3209=5965&3210=5967&3211=5969&3213=5972&3215=5974&3216=5976&3217=5978&3218=5980&3220=5983&3222=5985&3223=5987&3224=5989&3225=5991&3227=5994&3229=5996&3230=5998&3231=6000&3232=6002&3233=6004&3234=6006&3236=6009&3238=6011&3239=6013&3240=6015&3241=6017&3243=6020&3245=6022&3246=6024&3247=6026&3248=6028&3250=6031&3252=6033&3253=6035&3254=6039&3255=6041&3256=6043&3257=6045&3260=6047&3261=6049&3262=6051&3263=6053&3265=6055&3266=6057&3267=6059&3268=6061&3269=6063&3272=6066&3275=6069&3276=6072&3277=6075&3278=6081&3279=6084&3282=6091&3285=6094&3286=6097&3288=6099&3289=6102&3291=6104&3292=6107&3293=6110&3297=6113&3300=6116&3301=6119&3303=6121&3304=6124&3306=6126&3307=6129&3308=6132&3312=6135&3315=6138&3317=6141&3320=6144&3321=6147&3323=6149&3324=6152&3326=6154&3329=6157&3330=6159&3332=6162&3333=6165&3334=6167&3335=6169&3336=6172&3339=6177&3342=6179&3343=6183&3344=6186&3346=6188&3347=6191&3349=6193&3350=6196&3352=6200&3353=6203&3355=6207&3356=6210&3358=6214&3359=6217&3361=6221&3362=6224&3364=6228&3365=6231&3367=6235&3368=6237&3369=6240&3370=6242&3371=6245&3372=6249&3373=6251&3374=6254&3377=6261&3380=6265&3381=6267&3382=6269&3383=6271&3384=6273&3386=6276&3388=6281&3391=6283&3392=6286&3394=6290&3395=6293&3398=6298&3399=6302&3400=6304&3401=6306&3403=6309&3405=6312&3407=6315&3410=6318&3411=6320&3412=6322&3413=6324&3414=6326&3415=6328&3417=6331&3419=6333&3420=6335&3421=6337&3422=6339&3424=6342&3426=6344&3427=6346&3428=6348&3429=6350&3431=6352&3432=6354&3433=6356&3434=6358&3436=6361&3438=6363&3439=6365&3440=6367&3441=6369&3442=6371&3443=6373&3445=6376&3447=6378&3448=6380&3449=6382&3450=6384&3452=6387&3454=6389&3455=6391&3456=6393&3457=6395&3459=6397&3460=6399&3462=6401&3463=6403&3464=6405&3465=6407&3467=6410&3469=6412&3470=6414&3471=6416&3472=6418&3474=6420&3475=6422&3477=6425&3478=6427&3479=6429&3480=6431&3481=6433&3483=6435&3484=6437&3486=6440&3488=6442&3489=6444&3490=6446&3491=6448&3493=6450&3494=6452&3496=6455&3497=6457&3498=6459&3499=6461&3500=6463&3502=6465&3503=6467&3505=6470&3507=6472&3508=6474&3509=6476&3510=6478&3512=6480&3513=6482&3515=6485&3517=6487&3518=6489&3519=6491&3520=6493&3522=6495&3523=6497&3525=6499&3526=6501&3528=6504&3530=6506&3531=6508&3532=6510&3533=6512&3535=6514&3536=6516&3538=6519&3540=6521&3541=6523&3542=6525&3543=6527&3545=6529&3546=6531&3548=6533&3549=6535&3551=6538&3553=6540&3554=6542&3555=6544&3556=6546&3558=6549&3560=6551&3561=6553&3562=6555&3563=6557&3565=6559&3566=6561&3567=6563&3568=6565&3570=6568&3572=6570&3573=6572&3574=6576&3575=6578&3576=6580&3577=6582&3580=6584&3581=6586&3582=6588&3583=6590&3585=6592&3586=6594&3587=6596&3588=6598&3589=6600&3592=6603&3596=6606&3599=6609&3600=6612&3602=6614&3603=6617&3605=6619&3608=6622&3609=6625&3610=6628&3612=6630&3613=6633&3615=6635&3616=6638&3618=6642&3619=6645&3621=6649&3622=6652&3624=6656&3625=6659&3628=6664&3629=6668&3630=6670&3631=6672&3633=6675&3635=6678&3636=6680&3637=6682&3638=6684&3639=6686&3640=6688&3642=6691&3644=6693&3645=6695&3646=6697&3647=6699&3649=6702&3651=6704&3652=6706&3653=6708&3654=6710&3656=6712&3657=6714&3659=6716&3660=6718&3661=6720&3662=6722&3664=6725&3666=6727&3667=6729&3668=6731&3669=6733&3671=6736&3672=6738&3673=6740&3674=6742&3675=6744&3677=6747&3679=6749&3680=6751&3681=6753&3682=6755&3684=6758&3685=6760&3686=6762&3687=6764&3688=6766&3690=6769&3692=6771&3693=6773&3694=6775&3695=6777&3697=6780&3699=6782&3700=6784&3701=6786&3702=6788&3704=6790&3705=6792&3707=6795&3709=6797&3710=6799&3711=6801&3712=6803&3714=6806&3716=6808&3717=6810&3718=6812&3719=6814&3721=6816&3722=6818&3724=6821&3726=6823&3727=6825&3728=6827&3729=6829&3731=6832&3733=6834&3734=6836&3735=6840&3736=6842&3737=6844&3738=6846&3741=6848&3742=6850&3744=6852&3745=6854&3746=6856&3747=6858&3748=6860&3751=6863&3755=6866&3758=6869&3760=6872&3763=6875&3764=6878&3766=6880&3767=6883&3769=6885&3772=6888&3773=6890&3775=6893&3776=6896&3777=6898&3778=6900&3779=6903&3782=6908&3785=6910&3786=6913&3787=6916&3789=6918&3790=6921&3792=6923&3793=6926&3795=6930&3796=6933&3798=6937&3799=6940&3801=6944&3802=6947&3804=6951&3805=6954&3807=6958&3808=6961&3810=6965&3811=6967&3812=6970&3813=6972&3814=6975&3815=6979&3816=6981&3817=6984&3820=6991&3823=6995&3824=6998&3826=7002&3827=7005&3830=7010&3831=7014&3832=7016&3833=7018&3835=7021&3837=7024&3839=7027&3842=7030&3843=7032&3844=7034&3845=7036&3846=7038&3847=7040&3849=7043&3851=7045&3852=7047&3853=7049&3854=7051&3856=7054&3858=7056&3859=7058&3860=7060&3861=7062&3863=7065&3865=7067&3866=7069&3867=7071&3868=7073&3870=7075&3871=7077&3872=7079&3873=7081&3875=7084&3877=7086&3878=7088&3879=7090&3880=7092&3881=7094&3882=7096&3884=7099&3886=7101&3887=7103&3888=7105&3889=7107&3891=7110&3893=7112&3894=7114&3895=7116&3896=7118&3898=7120&3899=7122&3901=7124&3902=7126&3903=7128&3904=7130&3906=7133&3908=7135&3909=7137&3910=7139&3911=7141&3913=7143&3914=7145&3916=7148&3917=7150&3918=7152&3919=7154&3920=7156&3922=7158&3923=7160&3925=7163&3927=7165&3928=7167&3929=7169&3930=7171&3932=7173&3933=7175&3935=7178&3937=7180&3938=7182&3939=7184&3940=7186&3942=7188&3943=7190&3945=7192&3946=7194&3948=7197&3950=7199&3951=7201&3952=7203&3953=7205&3955=7207&3956=7209&3957=7211&3958=7213&3960=7216&3962=7218&3963=7220&3964=7224&3965=7226&3966=7228&3967=7230&3970=7232&3971=7234&3972=7236&3973=7238&3975=7240&3976=7242&3977=7244&3978=7246&3979=7248&3982=7251&3986=7254&3989=7257&3990=7260&3992=7262&3993=7265&3995=7267&3998=7270&3999=7273&4000=7276&4002=7278&4003=7281&4005=7283&4006=7286&4008=7290&4009=7293&4011=7297&4012=7300&4014=7304&4015=7307&4018=7312&4019=7316&4020=7318&4021=7320&4023=7323&4025=7326&4026=7328&4027=7330&4028=7332&4029=7334&4030=7336&4032=7339&4034=7341&4035=7343&4036=7345&4037=7347&4039=7349&4040=7351&4042=7353&4043=7355&4044=7357&4045=7359&4047=7362&4049=7364&4050=7366&4051=7368&4052=7370&4054=7373&4055=7375&4056=7377&4057=7379&4058=7381&4060=7384&4062=7386&4063=7388&4064=7390&4065=7392&4067=7395&4068=7397&4069=7399&4070=7401&4071=7403&4073=7406&4075=7408&4076=7410&4077=7412&4078=7414&4080=7417&4082=7419&4083=7421&4084=7423&4085=7425&4087=7427&4088=7429&4090=7432&4092=7434&4093=7436&4094=7438&4095=7440&4097=7443&4099=7445&4100=7447&4101=7449&4102=7451&4104=7453&4105=7455&4107=7458&4109=7460&4110=7462&4111=7464&4112=7466&4114=7469&4116=7471&4117=7473&4118=7477&4119=7479&4120=7481&4121=7483&4124=7485&4125=7487&4127=7489&4128=7491&4129=7493&4130=7495&4131=7497&4134=7500&4138=7503&4140=7506&4141=7508&4142=7510&4143=7513&4146=7518&4149=7520&4152=7523&4157=7526&4159=7529&4163=7532&4164=7536&4165=7538&4166=7541&4169=7544&4171=7547'