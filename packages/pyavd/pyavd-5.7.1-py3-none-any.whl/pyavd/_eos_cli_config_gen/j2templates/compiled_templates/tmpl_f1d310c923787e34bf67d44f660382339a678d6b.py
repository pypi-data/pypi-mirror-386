from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/router-adaptive-virtual-topology.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_adaptive_virtual_topology = resolve('router_adaptive_virtual_topology')
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
        t_3 = environment.filters['length']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'length' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology)):
        pass
        yield '\n### Router Adaptive Virtual Topology\n\n#### Router Adaptive Virtual Topology Summary\n'
        if t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'topology_role')):
            pass
            yield '\nTopology role: '
            yield str(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'topology_role'))
            yield '\n'
            if (t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'gateway_vxlan'), True) and (environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'topology_role') in ['edge', 'transit zone', 'transit region'])):
                pass
                yield '\nVXLAN gateway: Enabled\n'
        if ((t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'region')) or t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'zone'))) or t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'site'))):
            pass
            yield '\n| Hierarchy | Name | ID |\n| --------- | ---- | -- |\n'
            if (t_4(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'region'), 'name')) and environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'region'), 'id')):
                pass
                yield '| Region | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'region'), 'name'))
                yield ' | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'region'), 'id'))
                yield ' |\n'
            if (t_4(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'zone'), 'name')) and environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'zone'), 'id')):
                pass
                yield '| Zone | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'zone'), 'name'))
                yield ' | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'zone'), 'id'))
                yield ' |\n'
            if (t_4(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'site'), 'name')) and environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'site'), 'id')):
                pass
                yield '| Site | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'site'), 'name'))
                yield ' | '
                yield str(environment.getattr(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'site'), 'id'))
                yield ' |\n'
        if (t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'profiles')) and (t_3(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'profiles')) > 0)):
            pass
            yield '\n#### AVT Profiles\n\n| Profile name | Load balance policy | Internet exit policy | Metric Order | Jitter Threshold (ms) | Latency Threshold (ms) | Load (%) | Loss Rate (%) |\n| ------------ | ------------------- | -------------------- | ------------ | --------------------- | ---------------------- | -------- | ------------- |\n'
            for l_1_profile in t_2(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'profiles'), 'name'):
                l_1_load_balance_policy = l_1_internet_exit_policy = l_1_metric_order = l_1_jitter = l_1_latency = l_1_load = l_1_loss_rate = missing
                _loop_vars = {}
                pass
                l_1_load_balance_policy = t_1(environment.getattr(l_1_profile, 'load_balance_policy'), '-')
                _loop_vars['load_balance_policy'] = l_1_load_balance_policy
                l_1_internet_exit_policy = t_1(environment.getattr(l_1_profile, 'internet_exit_policy'), '-')
                _loop_vars['internet_exit_policy'] = l_1_internet_exit_policy
                l_1_metric_order = t_1(environment.getattr(environment.getattr(l_1_profile, 'metric_order'), 'preferred_metric'), '-')
                _loop_vars['metric_order'] = l_1_metric_order
                l_1_jitter = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'outlier_elimination'), 'threshold'), 'jitter'), '-')
                _loop_vars['jitter'] = l_1_jitter
                l_1_latency = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'outlier_elimination'), 'threshold'), 'latency'), '-')
                _loop_vars['latency'] = l_1_latency
                l_1_load = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'outlier_elimination'), 'threshold'), 'load'), '-')
                _loop_vars['load'] = l_1_load
                l_1_loss_rate = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_profile, 'outlier_elimination'), 'threshold'), 'loss_rate'), '-')
                _loop_vars['loss_rate'] = l_1_loss_rate
                yield '| '
                yield str(environment.getattr(l_1_profile, 'name'))
                yield ' | '
                yield str((undefined(name='load_balance_policy') if l_1_load_balance_policy is missing else l_1_load_balance_policy))
                yield ' | '
                yield str((undefined(name='internet_exit_policy') if l_1_internet_exit_policy is missing else l_1_internet_exit_policy))
                yield ' | '
                yield str((undefined(name='metric_order') if l_1_metric_order is missing else l_1_metric_order))
                yield ' | '
                yield str((undefined(name='jitter') if l_1_jitter is missing else l_1_jitter))
                yield ' | '
                yield str((undefined(name='latency') if l_1_latency is missing else l_1_latency))
                yield ' | '
                yield str((undefined(name='load') if l_1_load is missing else l_1_load))
                yield ' | '
                yield str((undefined(name='loss_rate') if l_1_loss_rate is missing else l_1_loss_rate))
                yield ' |\n'
            l_1_profile = l_1_load_balance_policy = l_1_internet_exit_policy = l_1_metric_order = l_1_jitter = l_1_latency = l_1_load = l_1_loss_rate = missing
        if (t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'policies')) and (t_3(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'policies')) > 0)):
            pass
            yield '\n#### AVT Policies\n'
            for l_1_policy in t_2(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'policies'), 'name'):
                _loop_vars = {}
                pass
                yield '\n##### AVT policy '
                yield str(environment.getattr(l_1_policy, 'name'))
                yield '\n\n| Application profile | AVT Profile | Traffic Class | DSCP |\n| ------------------- | ----------- | ------------- | ---- |\n'
                for l_2_match in environment.getattr(l_1_policy, 'matches'):
                    _loop_vars = {}
                    pass
                    yield '| '
                    yield str(environment.getattr(l_2_match, 'application_profile'))
                    yield ' | '
                    yield str(t_1(environment.getattr(l_2_match, 'avt_profile'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(l_2_match, 'traffic_class'), '-'))
                    yield ' | '
                    yield str(t_1(environment.getattr(l_2_match, 'dscp'), '-'))
                    yield ' |\n'
                l_2_match = missing
            l_1_policy = missing
        if (t_4(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'vrfs')) and (t_3(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'vrfs')) > 0)):
            pass
            yield '\n#### VRFs configuration\n'
            for l_1_vrf in t_2(environment.getattr((undefined(name='router_adaptive_virtual_topology') if l_0_router_adaptive_virtual_topology is missing else l_0_router_adaptive_virtual_topology), 'vrfs'), 'name'):
                _loop_vars = {}
                pass
                yield '\n##### VRF '
                yield str(environment.getattr(l_1_vrf, 'name'))
                yield '\n'
                if t_4(environment.getattr(l_1_vrf, 'policy')):
                    pass
                    yield '\n| AVT policy |\n| ---------- |\n| '
                    yield str(t_1(environment.getattr(l_1_vrf, 'policy'), '-'))
                    yield ' |\n'
                if (t_4(environment.getattr(l_1_vrf, 'profiles')) and (t_3(environment.getattr(l_1_vrf, 'profiles')) > 0)):
                    pass
                    yield '\n| AVT Profile | AVT ID |\n| ----------- | ------ |\n'
                    for l_2_profile in t_2(environment.getattr(l_1_vrf, 'profiles'), 'id'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_2_profile, 'name'))
                        yield ' | '
                        yield str(environment.getattr(l_2_profile, 'id'))
                        yield ' |\n'
                    l_2_profile = missing
            l_1_vrf = missing
        yield '\n#### Router Adaptive Virtual Topology Configuration\n\n```eos\n'
        template = environment.get_template('eos/router-adaptive-virtual-topology.j2', 'documentation/router-adaptive-virtual-topology.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=36&12=39&14=42&15=44&20=47&24=50&25=53&27=57&28=60&30=64&31=67&34=71&41=74&42=78&43=80&44=82&45=84&46=86&47=88&48=90&49=93&52=110&56=113&58=117&62=119&63=123&67=133&71=136&73=140&74=142&78=145&80=147&85=150&86=154&95=161'