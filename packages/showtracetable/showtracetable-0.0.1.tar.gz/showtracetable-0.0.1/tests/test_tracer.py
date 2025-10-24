from showtracetable.tracer import trace_file


def test_trace_sample(capsys):
    trace_file('tests/test_sample_script.py')
    captured = capsys.readouterr()
    out = captured.out
    # output should contain call/return markers '>' and '<' and mention the traced script
    assert '>' in out or '<' in out
    assert 'test_sample_script.py' in out
