import os
from pathlib import Path

from showtracetable.tracer import trace_file


def _write(tmpdir: Path, name: str, body: str) -> Path:
    p = tmpdir / name
    p.write_text(body, encoding='utf-8')
    return p


def test_major_steps_creates_rows(tmp_path):
    body = """
print('start')

def f(x):
    return x + 1

print(f(1))
"""
    target = _write(tmp_path, 'msteps.py', body)
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        trace_file(str(target), table=True, csv=True, major_steps=True)
        csv_path = tmp_path / 'msteps.trace.csv'
        assert csv_path.exists(), 'CSV must be created'
        text = csv_path.read_text(encoding='utf-8-sig' if os.name == 'nt' else 'utf-8')
        # expect header and at least a few rows
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) >= 3
        assert lines[0].startswith('step,source')
    finally:
        os.chdir(cwd)
