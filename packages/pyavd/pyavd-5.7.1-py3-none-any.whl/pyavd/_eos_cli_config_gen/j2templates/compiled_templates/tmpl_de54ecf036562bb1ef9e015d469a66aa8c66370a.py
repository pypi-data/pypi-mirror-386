from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/static-routes.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_static_routes = resolve('static_routes')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_2((undefined(name='static_routes') if l_0_static_routes is missing else l_0_static_routes)):
        pass
        yield '\n### Static Routes\n\n#### Static Routes Summary\n\n| VRF | Destination Prefix | Next Hop IP | Exit interface | Administrative Distance | Tag | Route Name | Metric |\n| --- | ------------------ | ----------- | -------------- | ----------------------- | --- | ---------- | ------ |\n'
        for l_1_static_route in (undefined(name='static_routes') if l_0_static_routes is missing else l_0_static_routes):
            l_1_next_hop = resolve('next_hop')
            l_1_prefix = resolve('prefix')
            l_1_vrf = l_1_interface = l_1_distance = l_1_tag = l_1_name = l_1_metric = missing
            _loop_vars = {}
            pass
            l_1_vrf = t_1(environment.getattr(l_1_static_route, 'vrf'), 'default')
            _loop_vars['vrf'] = l_1_vrf
            if t_2(environment.getattr(l_1_static_route, 'next_hop')):
                pass
                l_1_next_hop = environment.getattr(l_1_static_route, 'next_hop')
                _loop_vars['next_hop'] = l_1_next_hop
                if t_2(environment.getattr(l_1_static_route, 'track_bfd'), True):
                    pass
                    l_1_next_hop = str_join(((undefined(name='next_hop') if l_1_next_hop is missing else l_1_next_hop), ' (tracked with BFD)', ))
                    _loop_vars['next_hop'] = l_1_next_hop
            elif t_2(environment.getattr(l_1_static_route, 'gateway')):
                pass
                l_1_next_hop = environment.getattr(l_1_static_route, 'gateway')
                _loop_vars['next_hop'] = l_1_next_hop
                if t_2(environment.getattr(l_1_static_route, 'track_bfd'), True):
                    pass
                    l_1_next_hop = str_join(((undefined(name='next_hop') if l_1_next_hop is missing else l_1_next_hop), ' (tracked with BFD)', ))
                    _loop_vars['next_hop'] = l_1_next_hop
            else:
                pass
                l_1_next_hop = '-'
                _loop_vars['next_hop'] = l_1_next_hop
            l_1_interface = t_1(environment.getattr(l_1_static_route, 'interface'), '-')
            _loop_vars['interface'] = l_1_interface
            l_1_distance = t_1(environment.getattr(l_1_static_route, 'distance'), '1')
            _loop_vars['distance'] = l_1_distance
            l_1_tag = t_1(environment.getattr(l_1_static_route, 'tag'), '-')
            _loop_vars['tag'] = l_1_tag
            l_1_name = t_1(environment.getattr(l_1_static_route, 'name'), '-')
            _loop_vars['name'] = l_1_name
            l_1_metric = t_1(environment.getattr(l_1_static_route, 'metric'), '-')
            _loop_vars['metric'] = l_1_metric
            if t_2(environment.getattr(l_1_static_route, 'prefix')):
                pass
                l_1_prefix = environment.getattr(l_1_static_route, 'prefix')
                _loop_vars['prefix'] = l_1_prefix
            elif t_2(environment.getattr(l_1_static_route, 'destination_address_prefix')):
                pass
                l_1_prefix = environment.getattr(l_1_static_route, 'destination_address_prefix')
                _loop_vars['prefix'] = l_1_prefix
            yield '| '
            yield str((undefined(name='vrf') if l_1_vrf is missing else l_1_vrf))
            yield ' | '
            yield str((undefined(name='prefix') if l_1_prefix is missing else l_1_prefix))
            yield ' | '
            yield str((undefined(name='next_hop') if l_1_next_hop is missing else l_1_next_hop))
            yield ' | '
            yield str((undefined(name='interface') if l_1_interface is missing else l_1_interface))
            yield ' | '
            yield str((undefined(name='distance') if l_1_distance is missing else l_1_distance))
            yield ' | '
            yield str((undefined(name='tag') if l_1_tag is missing else l_1_tag))
            yield ' | '
            yield str((undefined(name='name') if l_1_name is missing else l_1_name))
            yield ' | '
            yield str((undefined(name='metric') if l_1_metric is missing else l_1_metric))
            yield ' |\n'
        l_1_static_route = l_1_vrf = l_1_next_hop = l_1_interface = l_1_distance = l_1_tag = l_1_name = l_1_metric = l_1_prefix = missing
        yield '\n#### Static Routes Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/static-routes.j2', 'documentation/static-routes.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=24&15=27&16=33&17=35&18=37&19=39&20=41&22=43&23=45&24=47&25=49&28=53&30=55&31=57&32=59&33=61&34=63&35=65&36=67&37=69&38=71&40=74&46=92'