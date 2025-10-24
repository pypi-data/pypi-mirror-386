import os

from showtracetable.tracer import SimpleTracer


def _normalize(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def test_target_is_traced_inside_stdlib_prefix(tmp_path):
    stdlib_dir = tmp_path / "Lib"
    stdlib_dir.mkdir()

    target = stdlib_dir / "target_script.py"
    target.write_text("value = 1\n")

    other = stdlib_dir / "other_script.py"
    other.write_text("value = 2\n")

    tracer = SimpleTracer(skip_stdlib=True, always_include=[str(target)])
    tracer._stdlib_prefixes = {_normalize(str(stdlib_dir))}

    assert tracer._in_project(str(target)), "target script should always be included"
    assert not tracer._in_project(str(other)), "other files under stdlib prefix remain excluded"
