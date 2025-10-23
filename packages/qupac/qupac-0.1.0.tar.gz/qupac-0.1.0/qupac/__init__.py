__all__ = [
    "compile_qupac_to_python",
    "run_qupac_file",
]


def compile_qupac_to_python(source: str) -> str:
    # Lazy import to keep __init__ lightweight and avoid IDE resolution issues
    from .parser import parse_qupac
    from .transpiler import transpile_to_python

    tree = parse_qupac(source)
    return transpile_to_python(tree)


def run_qupac_file(path: str, background: bool = True):
    from .executor import run_qupac_file as _run

    return _run(path, background=background)
