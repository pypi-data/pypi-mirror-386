from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/ip-extcommunity-lists-regexp.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ip_extcommunity_lists_regexp = resolve('ip_extcommunity_lists_regexp')
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
    if t_3((undefined(name='ip_extcommunity_lists_regexp') if l_0_ip_extcommunity_lists_regexp is missing else l_0_ip_extcommunity_lists_regexp)):
        pass
        yield '\n### IP Extended Community RegExp Lists\n\n#### IP Extended Community RegExp Lists Summary\n\n| List Name | Type | Regular Expression |\n| --------- | ---- | ------------------ |\n'
        for l_1_ip_extcommunity_list in t_2((undefined(name='ip_extcommunity_lists_regexp') if l_0_ip_extcommunity_lists_regexp is missing else l_0_ip_extcommunity_lists_regexp), 'name'):
            _loop_vars = {}
            pass
            for l_2_entry in t_1(environment.getattr(l_1_ip_extcommunity_list, 'entries'), []):
                _loop_vars = {}
                pass
                if (t_3(environment.getattr(l_2_entry, 'type')) and t_3(environment.getattr(l_2_entry, 'regexp'))):
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_ip_extcommunity_list, 'name'))
                    yield ' | '
                    yield str(environment.getattr(l_2_entry, 'type'))
                    yield ' | `'
                    yield str(environment.getattr(l_2_entry, 'regexp'))
                    yield '` |\n'
            l_2_entry = missing
        l_1_ip_extcommunity_list = missing
        yield '\n#### IP Extended Community RegExp Lists Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/ip-extcommunity-lists-regexp.j2', 'documentation/ip-extcommunity-lists-regexp.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=30&15=33&16=36&17=39&18=42&26=51'