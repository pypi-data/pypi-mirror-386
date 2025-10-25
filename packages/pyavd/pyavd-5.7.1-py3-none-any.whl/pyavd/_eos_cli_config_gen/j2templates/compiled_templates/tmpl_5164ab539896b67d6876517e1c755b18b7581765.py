from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/hardware.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_hardware = resolve('hardware')
    l_0_hardware_counters = resolve('hardware_counters')
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
        t_3 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if (t_3((undefined(name='hardware') if l_0_hardware is missing else l_0_hardware)) or t_3((undefined(name='hardware_counters') if l_0_hardware_counters is missing else l_0_hardware_counters))):
        pass
        yield '\n### Hardware\n'
        if t_3((undefined(name='hardware_counters') if l_0_hardware_counters is missing else l_0_hardware_counters)):
            pass
            yield '\n#### Hardware Counters\n\n##### Hardware Counters Summary\n'
            if t_3(environment.getattr((undefined(name='hardware_counters') if l_0_hardware_counters is missing else l_0_hardware_counters), 'features')):
                pass
                yield '\n###### Hardware Counter Features\n\n**NOTE:** Not all options (columns) in the table below are compatible with every available feature, it is the user responsibility to configure valid options for each feature.\n\n| Feature | Enabled | Flow Direction | Address Type | Layer3 | VRF | Prefix | Units Packets |\n| ------- | ------- | -------------- | ------------ | ------ | --- | ------ | ------------- |\n'
                for l_1_feature in t_2(environment.getattr((undefined(name='hardware_counters') if l_0_hardware_counters is missing else l_0_hardware_counters), 'features'), 'name'):
                    l_1_feature_enabled = l_1_feature_direction = l_1_feature_address_type = l_1_feature_vrf = l_1_feature_layer3 = l_1_feature_prefix = l_1_feature_units_packets = missing
                    _loop_vars = {}
                    pass
                    l_1_feature_enabled = t_1(environment.getattr(l_1_feature, 'enabled'), 'True')
                    _loop_vars['feature_enabled'] = l_1_feature_enabled
                    l_1_feature_direction = t_1(environment.getattr(l_1_feature, 'direction'), '-')
                    _loop_vars['feature_direction'] = l_1_feature_direction
                    l_1_feature_address_type = t_1(environment.getattr(l_1_feature, 'address_type'), '-')
                    _loop_vars['feature_address_type'] = l_1_feature_address_type
                    l_1_feature_vrf = t_1(environment.getattr(l_1_feature, 'vrf'), '-')
                    _loop_vars['feature_vrf'] = l_1_feature_vrf
                    l_1_feature_layer3 = t_1(environment.getattr(l_1_feature, 'layer3'), '-')
                    _loop_vars['feature_layer3'] = l_1_feature_layer3
                    l_1_feature_prefix = t_1(environment.getattr(l_1_feature, 'prefix'), '-')
                    _loop_vars['feature_prefix'] = l_1_feature_prefix
                    l_1_feature_units_packets = t_1(environment.getattr(l_1_feature, 'units_packets'), '-')
                    _loop_vars['feature_units_packets'] = l_1_feature_units_packets
                    yield '| '
                    yield str(environment.getattr(l_1_feature, 'name'))
                    yield ' | '
                    yield str((undefined(name='feature_enabled') if l_1_feature_enabled is missing else l_1_feature_enabled))
                    yield ' | '
                    yield str((undefined(name='feature_direction') if l_1_feature_direction is missing else l_1_feature_direction))
                    yield ' | '
                    yield str((undefined(name='feature_address_type') if l_1_feature_address_type is missing else l_1_feature_address_type))
                    yield ' | '
                    yield str((undefined(name='feature_vrf') if l_1_feature_vrf is missing else l_1_feature_vrf))
                    yield ' | '
                    yield str((undefined(name='feature_layer3') if l_1_feature_layer3 is missing else l_1_feature_layer3))
                    yield ' | '
                    yield str((undefined(name='feature_prefix') if l_1_feature_prefix is missing else l_1_feature_prefix))
                    yield ' | '
                    yield str((undefined(name='feature_units_packets') if l_1_feature_units_packets is missing else l_1_feature_units_packets))
                    yield ' |\n'
                l_1_feature = l_1_feature_enabled = l_1_feature_direction = l_1_feature_address_type = l_1_feature_vrf = l_1_feature_layer3 = l_1_feature_prefix = l_1_feature_units_packets = missing
        yield '\n#### Hardware Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/hardware.j2', 'documentation/hardware.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        template = environment.get_template('eos/hardware-speed-groups.j2', 'documentation/hardware.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        template = environment.get_template('eos/hardware-access-list-update-default-result-permit.j2', 'documentation/hardware.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=31&10=34&15=37&23=40&24=44&25=46&26=48&27=50&28=52&29=54&30=56&31=59&39=77&40=83&41=89'