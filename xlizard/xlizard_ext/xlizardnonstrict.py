'''
Non-strict CCN: do NOT count boolean operators (&&, ||, and, or) as
decision points. Default xlizard CCN counts them; this extension removes
them from the conditions set (same idea as lizard -Enonstrict).
'''


class xlizardExtension(object):  # pylint: disable=R0903

    # pylint: disable=W0221
    def __call__(self, tokens, reader):
        reader.conditions -= set(['&&', '||', 'and', 'or'])
        if hasattr(reader, 'logical_operators'):
            reader.logical_operators -= set(['&&', '||', 'and', 'or'])
        return tokens
