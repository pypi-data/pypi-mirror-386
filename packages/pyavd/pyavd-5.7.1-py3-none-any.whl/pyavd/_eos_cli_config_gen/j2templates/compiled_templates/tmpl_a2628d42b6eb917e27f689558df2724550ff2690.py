from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/router-path-selection.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_path_selection = resolve('router_path_selection')
    l_0_tcp_mss_ceiling = resolve('tcp_mss_ceiling')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_3 = environment.filters['groupby']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'groupby' found.")
    try:
        t_4 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_5 = environment.filters['upper']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'upper' found.")
    try:
        t_6 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_6((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection)):
        pass
        yield '\n### Router Path-selection\n'
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'peer_dynamic_source')):
            pass
            yield '\n#### Router Path-selection Summary\n\n| Setting | Value |\n| ------  | ----- |\n| Dynamic peers source | '
            yield str(t_5(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'peer_dynamic_source')))
            yield ' |\n'
        if (t_6(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'tcp_mss_ceiling'), 'ipv4_segment_size')) or t_6(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'tcp_mss_ceiling'), 'ipv4'))):
            pass
            yield '\n#### TCP MSS Ceiling Configuration\n\n| IPV4 segment size | Direction |\n| ----------------- | --------- |\n'
            l_0_tcp_mss_ceiling = t_1(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'tcp_mss_ceiling'), 'ipv4'), environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'tcp_mss_ceiling'), 'ipv4_segment_size'))
            context.vars['tcp_mss_ceiling'] = l_0_tcp_mss_ceiling
            context.exported_vars.add('tcp_mss_ceiling')
            yield '| '
            yield str((undefined(name='tcp_mss_ceiling') if l_0_tcp_mss_ceiling is missing else l_0_tcp_mss_ceiling))
            yield ' | '
            yield str(t_1(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'tcp_mss_ceiling'), 'direction'), 'ingress'))
            yield ' |\n'
        if (t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_hosts')) or t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_interval'))):
            pass
            yield '\n#### MTU Discovery Summary\n\n'
            if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_interval')):
                pass
                yield '- MTU discovery interval: '
                yield str(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_interval'))
                yield ' seconds.\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_hosts'), 'enabled'), True):
                pass
                yield '- MTU discovery for hosts on the LAN: Enabled\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_hosts'), 'fragmentation_needed_rate_limit')):
                    pass
                    yield '- Maximum rate of ICMP packet generation per CPU core: '
                    yield str(environment.getattr(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'mtu_discovery_hosts'), 'fragmentation_needed_rate_limit'))
                    yield ' pps\n'
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'interfaces')):
            pass
            yield '\n#### Interfaces Metric Bandwidth\n\n| Interface name | Transmit Bandwidth (Mbps) | Receive Bandwidth (Mbps) |\n| -------------- | ------------------------- | ------------------------ |\n'
            for l_1_interface_data in t_2(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'interfaces'), 'name'):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_interface_data, 'name'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_interface_data, 'metric_bandwidth'), 'transmit'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(environment.getattr(l_1_interface_data, 'metric_bandwidth'), 'receive'), '-'))
                yield ' |\n'
            l_1_interface_data = missing
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'path_groups')):
            pass
            yield '\n#### Path Groups\n'
            for l_1_path_group in t_2(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'path_groups'), 'name'):
                _loop_vars = {}
                pass
                yield '\n##### Path Group '
                yield str(environment.getattr(l_1_path_group, 'name'))
                yield '\n\n| Setting | Value |\n| ------  | ----- |\n| Path Group ID | '
                yield str(t_1(environment.getattr(l_1_path_group, 'id'), '-'))
                yield ' |\n'
                if t_6(environment.getattr(l_1_path_group, 'ipsec_profile')):
                    pass
                    yield '| IPSec profile | '
                    yield str(environment.getattr(l_1_path_group, 'ipsec_profile'))
                    yield ' |\n'
                if t_6(environment.getattr(environment.getattr(l_1_path_group, 'keepalive'), 'auto'), True):
                    pass
                    yield '| Keepalive interval | auto |\n'
                elif (t_6(environment.getattr(environment.getattr(l_1_path_group, 'keepalive'), 'interval')) and t_6(environment.getattr(environment.getattr(l_1_path_group, 'keepalive'), 'failure_threshold'))):
                    pass
                    yield '| Keepalive interval(failure threshold) | '
                    yield str(environment.getattr(environment.getattr(l_1_path_group, 'keepalive'), 'interval'))
                    yield '('
                    yield str(environment.getattr(environment.getattr(l_1_path_group, 'keepalive'), 'failure_threshold'))
                    yield ') |\n'
                if t_6(environment.getattr(l_1_path_group, 'flow_assignment')):
                    pass
                    yield '| Flow assignment | '
                    yield str(t_5(environment.getattr(l_1_path_group, 'flow_assignment')))
                    yield ' |\n'
                if t_6(environment.getattr(l_1_path_group, 'local_interfaces')):
                    pass
                    yield '\n###### Local Interfaces\n\n| Interface name | Public address | STUN server profile(s) |\n| -------------- | -------------- | ---------------------- |\n'
                    for l_2_local_interface in t_2(environment.getattr(l_1_path_group, 'local_interfaces'), 'name'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_2_local_interface, 'name'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_local_interface, 'public_address'), '-'))
                        yield ' | '
                        yield str(t_4(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_local_interface, 'stun'), 'server_profiles'), []), '<br>'))
                        yield ' |\n'
                    l_2_local_interface = missing
                if t_6(environment.getattr(l_1_path_group, 'local_ips')):
                    pass
                    yield '\n###### Local IPs\n\n| IP address | Public address | STUN server profile(s) |\n| ---------- | -------------- | ---------------------- |\n'
                    for l_2_local_ip in t_2(environment.getattr(l_1_path_group, 'local_ips'), 'ip_address'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_2_local_ip, 'ip_address'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_local_ip, 'public_address'), '-'))
                        yield ' | '
                        yield str(t_4(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_local_ip, 'stun'), 'server_profiles'), []), '<br>'))
                        yield ' |\n'
                    l_2_local_ip = missing
                if t_6(environment.getattr(environment.getattr(l_1_path_group, 'dynamic_peers'), 'enabled'), True):
                    pass
                    yield '\n###### Dynamic Peers Settings\n\n| Setting | Value |\n| ------  | ----- |\n| IP Local | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_path_group, 'dynamic_peers'), 'ip_local'), '-'))
                    yield ' |\n| IPSec | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_path_group, 'dynamic_peers'), 'ipsec'), '-'))
                    yield ' |\n'
                if t_6(environment.getattr(l_1_path_group, 'static_peers')):
                    pass
                    yield '\n###### Static Peers\n\n| Router IP | Name | IPv4 address(es) |\n| --------- | ---- | ---------------- |\n'
                    for l_2_static_peer in t_2(environment.getattr(l_1_path_group, 'static_peers'), 'router_ip'):
                        l_2_ipv4_addresses = missing
                        _loop_vars = {}
                        pass
                        l_2_ipv4_addresses = t_4(context.eval_ctx, t_1(environment.getattr(l_2_static_peer, 'ipv4_addresses'), ['-']), '<br>')
                        _loop_vars['ipv4_addresses'] = l_2_ipv4_addresses
                        yield '| '
                        yield str(environment.getattr(l_2_static_peer, 'router_ip'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_static_peer, 'name'), '-'))
                        yield ' | '
                        yield str((undefined(name='ipv4_addresses') if l_2_ipv4_addresses is missing else l_2_ipv4_addresses))
                        yield ' |\n'
                    l_2_static_peer = l_2_ipv4_addresses = missing
            l_1_path_group = missing
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'load_balance_policies')):
            pass
            yield '\n#### Load-balance Policies\n\n| Policy Name | Jitter (ms) | Latency (ms) | Loss Rate (%) | Path Groups (priority) | Lowest Hop Count |\n| ----------- | ----------- | ------------ | ------------- | ---------------------- | ---------------- |\n'
            for l_1_load_balance_policy in t_2(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'load_balance_policies'), 'name'):
                l_1_lowest_hop_count = l_1_jitter = l_1_latency = l_1_loss_rate = l_1_path_groups_list = missing
                _loop_vars = {}
                pass
                l_1_lowest_hop_count = t_1(environment.getattr(l_1_load_balance_policy, 'lowest_hop_count'), False)
                _loop_vars['lowest_hop_count'] = l_1_lowest_hop_count
                l_1_jitter = t_1(environment.getattr(l_1_load_balance_policy, 'jitter'), '-')
                _loop_vars['jitter'] = l_1_jitter
                l_1_latency = t_1(environment.getattr(l_1_load_balance_policy, 'latency'), '-')
                _loop_vars['latency'] = l_1_latency
                l_1_loss_rate = t_1(environment.getattr(l_1_load_balance_policy, 'loss_rate'), '-')
                _loop_vars['loss_rate'] = l_1_loss_rate
                l_1_path_groups_list = []
                _loop_vars['path_groups_list'] = l_1_path_groups_list
                for (l_2_priority, l_2_entries) in t_3(environment, t_1(environment.getattr(l_1_load_balance_policy, 'path_groups'), []), 'priority', default=1):
                    _loop_vars = {}
                    pass
                    for l_3_entry in t_2(l_2_entries, 'name'):
                        _loop_vars = {}
                        pass
                        context.call(environment.getattr((undefined(name='path_groups_list') if l_1_path_groups_list is missing else l_1_path_groups_list), 'append'), str_join((environment.getattr(l_3_entry, 'name'), ' (', l_2_priority, ')', )), _loop_vars=_loop_vars)
                    l_3_entry = missing
                l_2_priority = l_2_entries = missing
                yield '| '
                yield str(environment.getattr(l_1_load_balance_policy, 'name'))
                yield ' | '
                yield str((undefined(name='jitter') if l_1_jitter is missing else l_1_jitter))
                yield ' | '
                yield str((undefined(name='latency') if l_1_latency is missing else l_1_latency))
                yield ' | '
                yield str((undefined(name='loss_rate') if l_1_loss_rate is missing else l_1_loss_rate))
                yield ' | '
                yield str(t_4(context.eval_ctx, (undefined(name='path_groups_list') if l_1_path_groups_list is missing else l_1_path_groups_list), '<br>'))
                yield ' | '
                yield str((undefined(name='lowest_hop_count') if l_1_lowest_hop_count is missing else l_1_lowest_hop_count))
                yield ' |\n'
            l_1_load_balance_policy = l_1_lowest_hop_count = l_1_jitter = l_1_latency = l_1_loss_rate = l_1_path_groups_list = missing
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'policies')):
            pass
            yield '\n#### DPS Policies\n'
            for l_1_policy in t_2(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'policies'), 'name'):
                _loop_vars = {}
                pass
                yield '\n##### DPS Policy '
                yield str(environment.getattr(l_1_policy, 'name'))
                yield '\n\n| Rule ID | Application profile | Load-balance policy |\n| ------- | ------------------- | ------------------- |\n'
                if t_6(environment.getattr(l_1_policy, 'default_match')):
                    pass
                    yield '| Default Match | - | '
                    yield str(t_1(environment.getattr(environment.getattr(l_1_policy, 'default_match'), 'load_balance'), '-'))
                    yield ' |\n'
                for l_2_rule in t_2(environment.getattr(l_1_policy, 'rules'), 'id'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_rule, 'application_profile')):
                        pass
                        yield '| '
                        yield str(environment.getattr(l_2_rule, 'id'))
                        yield ' | '
                        yield str(environment.getattr(l_2_rule, 'application_profile'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_rule, 'load_balance'), '-'))
                        yield ' |\n'
                l_2_rule = missing
            l_1_policy = missing
        if t_6(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'vrfs')):
            pass
            yield '\n#### VRFs Configuration\n\n| VRF name | DPS policy |\n| -------- | ---------- |\n'
            for l_1_vrf in t_2(environment.getattr((undefined(name='router_path_selection') if l_0_router_path_selection is missing else l_0_router_path_selection), 'vrfs'), 'name'):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_vrf, 'name'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_vrf, 'path_selection_policy'), '-'))
                yield ' |\n'
            l_1_vrf = missing
        yield '\n#### Router Path-selection Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/router-path-selection.j2', 'documentation/router-path-selection.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'tcp_mss_ceiling': l_0_tcp_mss_ceiling}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=49&10=52&16=55&18=57&24=60&25=64&27=68&31=71&32=74&34=76&36=79&37=82&41=84&47=87&48=91&51=98&54=101&56=105&60=107&61=109&62=112&64=114&66=117&68=120&70=124&71=127&73=129&79=132&80=136&83=143&89=146&90=150&93=157&99=160&100=162&102=164&108=167&109=171&110=174&115=182&121=185&122=189&123=191&124=193&125=195&126=197&127=199&128=202&129=205&132=209&135=222&138=225&140=229&144=231&145=234&147=236&148=239&149=242&154=250&160=253&161=257&168=263'