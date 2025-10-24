import os
from pathlib import Path

from showtracetable.tracer import trace_file


def _run_and_read_csv(tmpdir: Path, script_body: str, csv_full: bool = False):
    script = tmpdir / "tmp_long_output.py"
    script.write_text(script_body, encoding="utf-8")

    cwd = os.getcwd()
    try:
        os.chdir(tmpdir)
        # run tracer (show-equivalent)
        trace_file(str(script), table=True, csv=True, csv_full=csv_full)
        csv_path = tmpdir / f"{script.stem}.trace.csv"
        assert csv_path.exists(), "CSV should be created"
        data = csv_path.read_text(encoding="utf-8-sig" if os.name == 'nt' else 'utf-8')
        return data
    finally:
        os.chdir(cwd)


def test_csv_truncates_by_default(tmp_path):
    long_payload = "x" * 200
    script_body = f"""
print({{'value': '{long_payload}'}})
"""
    data = _run_and_read_csv(tmp_path, script_body, csv_full=False)
    # default should include '...' truncation somewhere
    assert '...' in data


def test_csv_full_disables_truncation(tmp_path):
    long_payload = "x" * 200
    script_body = f"""
print({{'value': '{long_payload}'}})
"""
    data = _run_and_read_csv(tmp_path, script_body, csv_full=True)
    # full CSV should contain the entire payload without '...'
    assert long_payload in data
    assert '...' not in data
