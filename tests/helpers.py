# -*- coding: utf-8 -*-
from xlizard.xlizard import analyze_files, get_extensions


def analyze_map(path, extensions):
    """Return {function_name: FunctionInfo} for a single C file."""
    files = list(
        analyze_files(
            [str(path)],
            threads=1,
            exts=get_extensions(extensions),
        )
    )
    assert files, "no analysis result for %s" % path
    return {fn.name: fn for fn in files[0].function_list}
