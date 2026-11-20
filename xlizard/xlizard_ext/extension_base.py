"""Base stuff for extensions"""
try:
    from xlizard.xlizard_languages.code_reader import CodeStateMachine
except ImportError:  # running from a flat layout
    from xlizard_languages.code_reader import CodeStateMachine


class ExtensionBase(CodeStateMachine):
    """Base class for all xlizard extensions"""

    def __call__(self, tokens, reader=None):
        self.context = reader.context
        for token in tokens:
            self._state(token)
            yield token
