from showtracetable.tracer import SimpleTracer, render_trace_table


def test_noise_columns_hidden(tmp_path):
    # script with module/func objects in locals
    body = """
import sys

def foo():
    pass

x = sys

y = foo

print('done')
"""
    script = tmp_path / 'noise.py'
    script.write_text(body, encoding='utf-8')

    tracer = SimpleTracer(always_include=[str(script)])
    import runpy
    import sys as _sys

    _old = _sys.argv
    try:
        _sys.argv = [str(script)]
        _sys.settrace(tracer.globaltrace)
        runpy.run_path(str(script), run_name='__main__')
    finally:
        _sys.settrace(None)
        _sys.argv = _old

    table = render_trace_table(tracer.line_events, tracer.outputs, self_instances=tracer._self_instances)
    header = table.splitlines()[0]
    # header should not contain 'x' (module) or 'y' (function)
    assert ' x ' not in header
    assert ' y ' not in header
