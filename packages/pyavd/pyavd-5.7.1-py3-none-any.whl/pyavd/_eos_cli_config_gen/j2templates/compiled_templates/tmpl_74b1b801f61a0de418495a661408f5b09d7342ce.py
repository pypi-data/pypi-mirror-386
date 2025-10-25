from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/aaa-server-groups-tacacs-plus.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_aaa_server_groups = resolve('aaa_server_groups')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_3 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    for l_1_aaa_server_group in t_2(context, t_1((undefined(name='aaa_server_groups') if l_0_aaa_server_groups is missing else l_0_aaa_server_groups), 'name'), 'type', 'equalto', 'tacacs+'):
        _loop_vars = {}
        pass
        yield '!\naaa group server tacacs+ '
        yield str(environment.getattr(l_1_aaa_server_group, 'name'))
        yield '\n'
        if t_3(environment.getattr(l_1_aaa_server_group, 'servers')):
            pass
            for l_2_server in environment.getattr(l_1_aaa_server_group, 'servers'):
                l_2_server_cli = resolve('server_cli')
                _loop_vars = {}
                pass
                if t_3(environment.getattr(l_2_server, 'server')):
                    pass
                    l_2_server_cli = str_join(('server ', environment.getattr(l_2_server, 'server'), ))
                    _loop_vars['server_cli'] = l_2_server_cli
                    if t_3(environment.getattr(l_2_server, 'vrf')):
                        pass
                        l_2_server_cli = str_join(((undefined(name='server_cli') if l_2_server_cli is missing else l_2_server_cli), ' vrf ', environment.getattr(l_2_server, 'vrf'), ))
                        _loop_vars['server_cli'] = l_2_server_cli
                    yield '   '
                    yield str((undefined(name='server_cli') if l_2_server_cli is missing else l_2_server_cli))
                    yield '\n'
            l_2_server = l_2_server_cli = missing
    l_1_aaa_server_group = missing

blocks = {}
debug_info = '7=30&9=34&10=36&11=38&12=42&13=44&14=46&15=48&17=51'