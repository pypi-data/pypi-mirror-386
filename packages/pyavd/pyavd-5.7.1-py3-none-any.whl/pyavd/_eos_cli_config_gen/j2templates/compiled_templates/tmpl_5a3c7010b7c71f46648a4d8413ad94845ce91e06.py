from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/management-api-models.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_management_api_models = resolve('management_api_models')
    l_0_enabled_paths = resolve('enabled_paths')
    l_0_disabled_paths = resolve('disabled_paths')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['lower']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'lower' found.")
    try:
        t_3 = environment.filters['sort']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'sort' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models)):
        pass
        yield '!\nmanagement api models\n'
        if t_4(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider')):
            pass
            if (t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'interfaces'), True) or t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'mka'), True)):
                pass
                yield '   provider macsec\n'
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'interfaces'), True):
                    pass
                    yield '      interfaces\n'
                if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'mka'), True):
                    pass
                    yield '      mka\n'
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'smash'), 'paths')):
                pass
                yield '   !\n   provider smash\n'
                l_0_enabled_paths = []
                context.vars['enabled_paths'] = l_0_enabled_paths
                context.exported_vars.add('enabled_paths')
                l_0_disabled_paths = []
                context.vars['disabled_paths'] = l_0_disabled_paths
                context.exported_vars.add('disabled_paths')
                for l_1_path in environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'smash'), 'paths'):
                    _loop_vars = {}
                    pass
                    if t_4(environment.getattr(l_1_path, 'disabled'), True):
                        pass
                        context.call(environment.getattr((undefined(name='disabled_paths') if l_0_disabled_paths is missing else l_0_disabled_paths), 'append'), l_1_path, _loop_vars=_loop_vars)
                    else:
                        pass
                        context.call(environment.getattr((undefined(name='enabled_paths') if l_0_enabled_paths is missing else l_0_enabled_paths), 'append'), l_1_path, _loop_vars=_loop_vars)
                l_1_path = missing
                for l_1_path in (t_3(environment, (undefined(name='enabled_paths') if l_0_enabled_paths is missing else l_0_enabled_paths), attribute='path') + t_3(environment, (undefined(name='disabled_paths') if l_0_disabled_paths is missing else l_0_disabled_paths), attribute='path')):
                    l_1_provider_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_provider_cli = str_join(('path ', environment.getattr(l_1_path, 'path'), ))
                    _loop_vars['provider_cli'] = l_1_provider_cli
                    if t_4(environment.getattr(l_1_path, 'disabled'), True):
                        pass
                        l_1_provider_cli = str_join(((undefined(name='provider_cli') if l_1_provider_cli is missing else l_1_provider_cli), ' disabled', ))
                        _loop_vars['provider_cli'] = l_1_provider_cli
                    yield '      '
                    yield str((undefined(name='provider_cli') if l_1_provider_cli is missing else l_1_provider_cli))
                    yield '\n'
                l_1_path = l_1_provider_cli = missing
            if t_4(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'sysdb'), 'disabled_paths')):
                pass
                yield '   !\n   provider sysdb\n'
                for l_1_path in t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'sysdb'), 'disabled_paths')):
                    _loop_vars = {}
                    pass
                    yield '      path '
                    yield str(l_1_path)
                    yield ' disabled\n'
                l_1_path = missing
        elif t_4(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'providers')):
            pass
            for l_1_provider in t_1(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'providers'), 'name'):
                _loop_vars = {}
                pass
                if (t_4(environment.getattr(l_1_provider, 'name')) and (t_2(environment.getattr(l_1_provider, 'name')) in ['smash', 'sysdb'])):
                    pass
                    yield '   !\n   provider '
                    yield str(environment.getattr(l_1_provider, 'name'))
                    yield '\n'
                    for l_2_path in t_1(environment.getattr(l_1_provider, 'paths'), 'path'):
                        l_2_provider_cli = missing
                        _loop_vars = {}
                        pass
                        l_2_provider_cli = str_join(('path ', environment.getattr(l_2_path, 'path'), ))
                        _loop_vars['provider_cli'] = l_2_provider_cli
                        if t_4(environment.getattr(l_2_path, 'disabled'), True):
                            pass
                            l_2_provider_cli = str_join(((undefined(name='provider_cli') if l_2_provider_cli is missing else l_2_provider_cli), ' disabled', ))
                            _loop_vars['provider_cli'] = l_2_provider_cli
                        yield '      '
                        yield str((undefined(name='provider_cli') if l_2_provider_cli is missing else l_2_provider_cli))
                        yield '\n'
                    l_2_path = l_2_provider_cli = missing
            l_1_provider = missing

blocks = {}
debug_info = '7=38&10=41&11=43&13=46&16=49&20=52&23=55&24=58&25=61&26=64&27=66&29=69&32=71&33=75&34=77&35=79&37=82&40=85&43=88&44=92&47=95&48=97&49=100&51=103&52=105&53=109&54=111&55=113&57=116'