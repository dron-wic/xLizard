'''
Fan in / fan out and HIS CALLS / CALLING (unique names, best-effort).
'''
from .extension_base import ExtensionBase


class xlizardExtension(ExtensionBase):
    '''
    Structural fan-in / fan-out plus HIS-style unique CALLS / CALLING.

    calls:   unique project functions referenced in the body
    calling: unique project functions that reference this one
    '''

    FUNCTION_INFO = {
        "fan_in": {
            "caption": " fan_in ",
            "average_caption": " avg_fan_in "},
        "fan_out": {
            "caption": " fan_out ",
            "average_caption": " avg_fan_out "},
        "general_fan_out": {
            "caption": " general_fan_out ",
            "average_caption": " avg_general_fan_out "},
        "calls": {
            "caption": " CALLS ",
            "average_caption": " avg_CALLS "},
        "calling": {
            "caption": " CALLING ",
            "average_caption": " avg_CALLING "},
    }

    def __init__(self, context=None):
        self.all_methods = {}
        super(xlizardExtension, self).__init__(context)

    def _state_global(self, token):
        if not hasattr(self.context.current_function, 'tokens'):
            self.context.current_function.tokens = list()
        self.context.current_function.tokens.append(token)

    def cross_file_process(self, fileinfos):
        files = list(fileinfos)
        by_name = {}
        for fileinfo in files:
            for func in fileinfo.function_list:
                if not hasattr(func, 'tokens'):
                    func.tokens = []
                func.calls = 0
                func.calling = 0
                func.fan_in = 0
                func.fan_out = 0
                func.general_fan_out = getattr(func, 'general_fan_out', 0) or 0
                by_name[func.unqualified_name] = func

        structures = set([
            'if', 'else', 'elif', 'for', 'foreach', 'while', 'do', 'try',
            'catch', 'switch', 'finally', 'except', 'with', 'case', 'return',
            'goto', 'break', 'continue',
        ])
        punctuations = set(['(', ')', '{', '}', ';', ',', ':', '?', '=',
                            '+', '-', '*', '/', '%', '&', '|', '!', '<', '>',
                            '[', ']', '.', '->', '::'])

        callee_map = {}
        for name, func in by_name.items():
            callees = set()
            tokens = func.tokens or []
            for idx, tok in enumerate(tokens):
                if tok in by_name and tok != name:
                    # Prefer tokens that look like calls: name (
                    nxt = tokens[idx + 1] if idx + 1 < len(tokens) else None
                    if nxt == '(' or tok not in structures:
                        callees.add(tok)
            # Also count general_fan_out style: identifier before '('
            for idx, tok in enumerate(tokens):
                if tok == '(' and idx > 0:
                    prev = tokens[idx - 1]
                    if (prev not in structures and prev not in punctuations
                            and prev.isidentifier()):
                        func.general_fan_out += 1
            callee_map[name] = callees
            func.calls = len(callees)
            func.fan_out = func.calls

        callers = {name: set() for name in by_name}
        for name, callees in callee_map.items():
            for callee in callees:
                if callee in callers:
                    callers[callee].add(name)

        for name, func in by_name.items():
            func.calling = len(callers[name])
            func.fan_in = func.calling

        for fileinfo in files:
            yield fileinfo
