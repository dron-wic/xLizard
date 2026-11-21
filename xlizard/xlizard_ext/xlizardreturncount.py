"""Count return statements per function (HIS RETURN)."""


class xlizardExtension:  # pylint: disable=R0903

    FUNCTION_INFO = {"return_count": {"caption": "returns"}}

    def __call__(self, tokens, reader):
        for token in tokens:
            if not hasattr(reader.context.current_function, "return_count"):
                reader.context.current_function.return_count = 0
            if token == "return":
                reader.context.current_function.return_count += 1
            yield token
