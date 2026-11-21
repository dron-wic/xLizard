"""
Estimate acyclic path count per function (HIS PATH, lightweight).

Not a full industrial CFG — multiplicative estimate from control tokens.
"""


_PATH_CAP = 81  # report >80 as exceedance against HIS limit 80


class xlizardExtension:  # pylint: disable=R0903

    FUNCTION_INFO = {"path_count": {"caption": "paths"}}

    def __call__(self, tokens, reader):
        paths = 1
        pending_if = False
        for token in tokens:
            if not hasattr(reader.context.current_function, "path_count"):
                reader.context.current_function.path_count = 1

            if token in ("if", "for", "while", "do", "?"):
                paths = min(_PATH_CAP, paths * 2)
                pending_if = token == "if"
            elif token == "else":
                # else does not add a new independent factor beyond if
                pending_if = False
            elif token == "case":
                paths = min(_PATH_CAP, paths + 1)
            elif token == "switch":
                pending_if = False

            reader.context.current_function.path_count = max(1, paths)
            yield token
