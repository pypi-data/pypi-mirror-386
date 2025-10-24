import os

from showtracetable.tracer import trace_file


def test_sys_argv_is_isolated(tmp_path):
    body = """
import sys
print(len(sys.argv))
"""
    target = tmp_path / 'argv_check.py'
    target.write_text(body, encoding='utf-8')
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        trace_file(str(target), table=True)
        csv_file = tmp_path / 'argv_check.trace.csv'
        assert csv_file.exists()
        text = csv_file.read_text(encoding='utf-8-sig' if os.name == 'nt' else 'utf-8')
        # the output column should contain '1' (len(sys.argv) == 1)
        assert ',1' in text or text.strip().endswith('1')
    finally:
        os.chdir(cwd)
