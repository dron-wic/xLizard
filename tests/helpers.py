# -*- coding: utf-8 -*-
from pathlib import Path

from xlizard.xlizard import analyze_files, get_extensions

CORE_EXTS = ["cognitive", "nd"]
HIS_EXTS = ["cognitive", "nd", "gotocount", "returncount", "pathcount", "io"]


def analyze_file_list(paths, extensions, threads=1):
    """Analyze one or more paths; return list of FileInformation."""
    path_strs = [str(p) for p in paths]
    return list(
        analyze_files(
            path_strs,
            threads=threads,
            exts=get_extensions(extensions),
        )
    )


def analyze_map(path, extensions):
    """Return {function_name: FunctionInfo} for a single C file."""
    files = analyze_file_list([path], extensions)
    assert files, "no analysis result for %s" % path
    return {fn.name: fn for fn in files[0].function_list}


def analyze_project_map(paths, extensions):
    """Return {function_name: FunctionInfo} across many files (last wins on clash)."""
    files = analyze_file_list(paths, extensions)
    assert files, "no analysis result for %s" % paths
    out = {}
    for fi in files:
        for fn in fi.function_list:
            out[fn.name] = fn
    return out


def c_files_in(directory):
    return sorted(Path(directory).glob("*.c"))
