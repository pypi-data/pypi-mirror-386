from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/vlans.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_vlans = resolve('vlans')
    l_0_namespace = resolve('namespace')
    l_0_ns = resolve('ns')
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
        t_3 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='vlans') if l_0_vlans is missing else l_0_vlans)):
        pass
        l_0_ns = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), show_private_vlan_table=False, show_e_tree_table=False)
        context.vars['ns'] = l_0_ns
        context.exported_vars.add('ns')
        yield '\n## VLANs\n\n### VLANs Summary\n\n| VLAN ID | Name | Trunk Groups |\n| ------- | ---- | ------------ |\n'
        for l_1_vlan in t_2((undefined(name='vlans') if l_0_vlans is missing else l_0_vlans), 'id'):
            l_1_row_trunk_groups = resolve('row_trunk_groups')
            l_1_row_name = missing
            _loop_vars = {}
            pass
            if t_4(environment.getattr(l_1_vlan, 'private_vlan')):
                pass
                if not isinstance(l_0_ns, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_ns['show_private_vlan_table'] = True
            if t_4(environment.getattr(environment.getattr(l_1_vlan, 'e_tree'), 'leaf_role')):
                pass
                if not isinstance(l_0_ns, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_ns['show_e_tree_table'] = True
            l_1_row_name = t_1(environment.getattr(l_1_vlan, 'name'), '-')
            _loop_vars['row_name'] = l_1_row_name
            if t_4(environment.getattr(l_1_vlan, 'trunk_groups')):
                pass
                l_1_row_trunk_groups = t_3(context.eval_ctx, environment.getattr(l_1_vlan, 'trunk_groups'), ' ')
                _loop_vars['row_trunk_groups'] = l_1_row_trunk_groups
            else:
                pass
                l_1_row_trunk_groups = '-'
                _loop_vars['row_trunk_groups'] = l_1_row_trunk_groups
            yield '| '
            yield str(environment.getattr(l_1_vlan, 'id'))
            yield ' | '
            yield str((undefined(name='row_name') if l_1_row_name is missing else l_1_row_name))
            yield ' | '
            yield str((undefined(name='row_trunk_groups') if l_1_row_trunk_groups is missing else l_1_row_trunk_groups))
            yield ' |\n'
        l_1_vlan = l_1_row_name = l_1_row_trunk_groups = missing
        if environment.getattr((undefined(name='ns') if l_0_ns is missing else l_0_ns), 'show_private_vlan_table'):
            pass
            yield '\n#### Private VLANs\n\n| Primary VLAN ID | Secondary VLAN ID | Private VLAN Type |\n| --------------- | ----------------- | ----------------- |\n'
            for l_1_vlan in t_2((undefined(name='vlans') if l_0_vlans is missing else l_0_vlans), 'id'):
                _loop_vars = {}
                pass
                if (t_4(environment.getattr(environment.getattr(l_1_vlan, 'private_vlan'), 'type')) and t_4(environment.getattr(environment.getattr(l_1_vlan, 'private_vlan'), 'primary_vlan'))):
                    pass
                    yield '| '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'private_vlan'), 'type'))
                    yield ' | '
                    yield str(environment.getattr(l_1_vlan, 'id'))
                    yield ' | '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'private_vlan'), 'primary_vlan'))
                    yield ' |\n'
            l_1_vlan = missing
        if environment.getattr((undefined(name='ns') if l_0_ns is missing else l_0_ns), 'show_e_tree_table'):
            pass
            yield '\n#### E-Tree Role\n\n| VLAN ID | VLAN Name | Role | Remote Leaf Host Drop |\n| ------- | --------- | ---- | --------------------- |\n'
            for l_1_vlan in t_2((undefined(name='vlans') if l_0_vlans is missing else l_0_vlans), 'id'):
                l_1_row_role = resolve('row_role')
                l_1_row_name = l_1_row_host_drop = missing
                _loop_vars = {}
                pass
                l_1_row_name = t_1(environment.getattr(l_1_vlan, 'name'), '-')
                _loop_vars['row_name'] = l_1_row_name
                if t_4(environment.getattr(environment.getattr(l_1_vlan, 'e_tree'), 'leaf_role'), True):
                    pass
                    l_1_row_role = 'Leaf'
                    _loop_vars['row_role'] = l_1_row_role
                else:
                    pass
                    l_1_row_role = 'Root'
                    _loop_vars['row_role'] = l_1_row_role
                l_1_row_host_drop = t_1(environment.getattr(environment.getattr(l_1_vlan, 'e_tree'), 'remote_leaf_host_drop'), '-')
                _loop_vars['row_host_drop'] = l_1_row_host_drop
                yield '| '
                yield str(environment.getattr(l_1_vlan, 'id'))
                yield ' | '
                yield str((undefined(name='row_name') if l_1_row_name is missing else l_1_row_name))
                yield ' | '
                yield str((undefined(name='row_role') if l_1_row_role is missing else l_1_row_role))
                yield ' | '
                yield str((undefined(name='row_host_drop') if l_1_row_host_drop is missing else l_1_row_host_drop))
                yield ' |\n'
            l_1_vlan = l_1_row_name = l_1_row_role = l_1_row_host_drop = missing
        yield '\n### VLANs Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/vlans.j2', 'documentation/vlans.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'ns': l_0_ns}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=38&8=40&16=44&17=49&18=53&20=54&21=58&23=59&24=61&25=63&27=67&29=70&31=77&37=80&38=83&40=86&44=93&50=96&51=101&52=103&53=105&55=109&57=111&58=114&65=124'