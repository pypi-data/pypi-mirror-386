"""Simple tracer that records function call events and renders an ASCII trace table.

This tracer intentionally keeps implementation small for demonstration and unit tests.
"""

import inspect
import json
import os
import runpy
import shutil
import sys
import sysconfig
import trace
from typing import Iterable, List, Optional, Tuple

# simple ANSI color helpers
ANSI_RESET = "\x1b[0m"
ANSI_BOLD = "\x1b[1m"
ANSI_CYAN = "\x1b[36m"
ANSI_YELLOW = "\x1b[33m"

# Global formatting limit for values; None to disable truncation
FORMAT_MAXLEN: Optional[int] = 60


def _is_nonempty_cell(s: str) -> bool:
    """Return True if the cell string s should be considered non-empty for display.

    Treat '-' or empty/whitespace-only strings as empty.
    """
    try:
        ss = s.strip()
    except Exception:
        ss = str(s)
    if not ss or ss == '-':
        return False
    # Treat angle-bracket placeholders like '<ClassName object at 0x...>' or '<func>' as empty
    # These are usually unhelpful default reprs that don't convey variable state.
    if ss.startswith('<') and ss.endswith('>'):
        # inside content like 'ClassName object at 0x' or 'func' or 'unrepr'
        inner = ss[1:-1].strip()
        # treat generic markers or ones containing memory addresses as empty
        if ' object at ' in inner or inner in ('func', 'unrepr', 'unrepr>') or inner.endswith('>'):
            return False
        # also treat simple single-word markers like 'NoneType' as empty
        if len(inner.split()) == 1 and inner.isidentifier():
            return False
        # treat module representations like <module 'sys' (built-in)> as empty
        if inner.startswith('module '):
            return False
    # treat function object display like 'pkg.func()' as empty
    try:
        if ss.endswith('()'):
            return False
    except Exception:
        pass
    return True


class SimpleTracer(trace.Trace):
    def __init__(
        self,
        project_root: Optional[str] = None,
        step_over: bool = False,
        skip_stdlib: bool = True,
        always_include: Optional[Iterable[str]] = None,
    ):
        super().__init__(trace=False, count=False)
        self.events: List[Tuple[str, int, str, str]] = []  # (event, lineno, funcname, filename)
        self.project_root = os.path.normcase(os.path.normpath(os.path.abspath(project_root))) if project_root else None
        self.skip_stdlib = skip_stdlib
        self._always_include = set()
        if always_include:
            for path in always_include:
                try:
                    norm = os.path.normcase(os.path.normpath(os.path.abspath(path)))
                    self._always_include.add(norm)
                except Exception:
                    continue
        self._stdlib_prefixes = set()
        if self.skip_stdlib:
            try:
                paths = sysconfig.get_paths()
                for key in ('stdlib', 'platstdlib'):
                    val = paths.get(key)
                    if val:
                        self._stdlib_prefixes.add(os.path.normcase(os.path.normpath(os.path.abspath(val))))
            except Exception:
                pass
            for prefix in (
                getattr(sys, 'base_prefix', None),
                getattr(sys, 'exec_prefix', None),
                getattr(sys, 'prefix', None),
            ):
                if not prefix:
                    continue
                lib_path = os.path.normcase(os.path.normpath(os.path.abspath(os.path.join(prefix, 'Lib'))))
                self._stdlib_prefixes.add(lib_path)
            # Normalize to remove duplicates/non-existent paths
            normalized = set()
            for p in self._stdlib_prefixes:
                try:
                    if p and os.path.isdir(p):
                        normalized.add(p)
                except Exception:
                    continue
            self._stdlib_prefixes = normalized
        # (no flowchart edges/call-stack - removed)
        # For trace table: record line events and outputs
        # line_events entries: (step, lineno, func, locals, event, filename, call_args)
        self.line_events: List[Tuple[int, int, str, dict, str, str, dict]] = []
        # (step, lineno, func, locals, event, filename, call_args)
        self.step: int = 0
        self.outputs: List[Tuple[int, str]] = []  # (step, text)
        self.current_step: int = 0
        # storage for pending call-args keyed by frame id; used optionally
        self._pending_call_args = {}
        # raw self instances captured per step: step -> object
        self._self_instances = {}
        # when True, only record line events at module/top-level (i.e. step-over into functions)
        self.step_over = step_over
        # (no pending storage; call args will be attached retroactively to caller line events)

    def _in_project(self, filename: str) -> bool:
        # Exclude synthetic filenames like '<frozen ...>' or '<string>' and require real file
        if not filename:
            return False
        if filename.startswith('<') and filename.endswith('>'):
            return False

        try:
            if os.path.isabs(filename):
                abs_path = os.path.normcase(os.path.normpath(os.path.abspath(filename)))
            else:
                abs_path = os.path.normcase(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), filename))))
        except Exception:
            abs_path = None

        if abs_path:
            try:
                for inc in self._always_include:
                    if abs_path == inc or abs_path.startswith(inc + os.sep):
                        return True
            except Exception:
                pass

        if self.skip_stdlib and abs_path:
            try:
                for prefix in self._stdlib_prefixes:
                    if os.path.commonpath([abs_path, prefix]) == prefix:
                        return False
            except Exception:
                pass

        if self.project_root:
            try:
                if not abs_path or not os.path.exists(abs_path):
                    return False
                # ensure filename is inside project_root
                return os.path.commonpath([self.project_root, abs_path]) == self.project_root
            except Exception:
                return False

        if abs_path and os.path.exists(abs_path):
            return True
        return False

    def globaltrace(self, frame, event, arg):
        # only track call and return, and optionally filter by project root
        if event in ('call', 'return'):
            func = frame.f_code.co_name
            lineno = frame.f_lineno
            filename = frame.f_code.co_filename
            if self._in_project(filename):
                self.events.append((event, lineno, func, filename))
                # capture call-site arguments from this frame's locals (common pattern)
                if event == 'call':
                    try:
                        ai = inspect.getargvalues(frame)
                        fa = {}
                        for name in ai.args or []:
                            if name in ai.locals:
                                fa[name] = _format_value(ai.locals[name])
                        if ai.varargs and ai.varargs in ai.locals:
                            fa['*' + ai.varargs] = _format_value(ai.locals[ai.varargs])
                        if ai.keywords and ai.keywords in ai.locals:
                            fa['**' + ai.keywords] = _format_value(ai.locals[ai.keywords])
                        caller = frame.f_back
                        if caller is not None and fa:
                            caller_file = caller.f_code.co_filename
                            caller_line = caller.f_lineno
                            for i in range(len(self.line_events) - 1, -1, -1):
                                try:
                                    s, ln, fnc, locs, ev, fname, ca = self.line_events[i]
                                except Exception:
                                    continue
                                if fname == caller_file and ln == caller_line:
                                    self.line_events[i] = (s, ln, fnc, locs, ev, fname, fa)
                                    break
                    except Exception:
                        pass
        # track line events and capture locals
        if event == 'line':
            try:
                filename = frame.f_code.co_filename
                if self._in_project(filename):
                    # if step_over is enabled, only record lines that are executing in module scope
                    # i.e., skip line events inside functions (their co_name won't be '<module>')
                    if self.step_over and frame.f_code.co_name != '<module>':
                        return self.globaltrace
                    self.step += 1
                    self.current_step = self.step
                    # capture raw self instance for this step if present
                    try:
                        sv = frame.f_locals.get('self', None)
                        if sv is not None:
                            # store a shallow snapshot of public attributes (formatted)
                            snap = {}
                            try:
                                # prefer __dict__ when available (instance attributes)
                                attrs = list(vars(sv).keys())
                            except Exception:
                                # fallback: pick public names from dir but filter out callables
                                attrs = [a for a in dir(sv) if not a.startswith('_')]
                            for a in attrs:
                                if a.startswith('_'):
                                    continue
                                try:
                                    val = None
                                    try:
                                        val = getattr(sv, a)
                                    except Exception:
                                        # skip if attribute can't be read
                                        continue
                                    # skip callables (methods)
                                    if callable(val):
                                        continue
                                    snap[a] = _format_value(val)
                                except Exception:
                                    snap[a] = '<unrepr>'
                            self._self_instances[self.step] = snap
                    except Exception:
                        pass
                    func = frame.f_code.co_name
                    lineno = frame.f_lineno
                    # shallow copy of locals with safe reprs
                    locs = {}
                    # get pending call args for this frame if present
                    call_args = self._pending_call_args.pop(id(frame), {})

                    for k, v in frame.f_locals.items():
                        locs[k] = _format_value(v)
                    self.line_events.append((self.step, lineno, func, locs, 'line', filename, call_args))
            except Exception:
                pass
        return self.globaltrace


def render_ascii_indented(events: List[Tuple[str, int, str, str]]) -> str:
    """Render an indented ASCII trace from call/return events.

    Strategy: maintain a stack depth counter; on 'call' increase depth and print with '>' mark,
    on 'return' print with '<' and decrease depth.
    """
    lines = []
    depth = 0
    for ev, lineno, func, filename in events:
        shortfile = os.path.relpath(filename)
        if ev == 'call':
            indent = '  ' * depth
            lines.append(f"{indent}> {func}()  ({shortfile}:{lineno})")
            depth += 1
        elif ev == 'return':
            depth = max(depth - 1, 0)
            indent = '  ' * depth
            lines.append(f"{indent}< {func}()  ({shortfile}:{lineno})")
    return "\n".join(lines)


def _read_single_key(prompt: str = '') -> Optional[str]:
    """Read a single keypress. On Windows use msvcrt to get arrow keys without Enter.

    Returns:
      - 'left' or 'right' for arrow keys
      - single character string for normal keys (e.g. 'q', 'n', digits)
      - None on EOF or failure
    """
    # First try Windows-specific fast path
    try:
        import msvcrt

        if prompt:
            # print prompt but don't add newline
            print(prompt, end='', flush=True)
        ch = msvcrt.getwch()
        # special keys start with \x00 or \xe0 then a second code
        if ch in ('\x00', '\xe0'):
            ch2 = msvcrt.getwch()
            # typical codes: 'K' = left, 'M' = right, 'H' = up, 'P' = down
            if ch2 == 'K':
                return 'left'
            if ch2 == 'M':
                return 'right'
            if ch2 == 'H':
                return 'up'
            if ch2 == 'P':
                return 'down'
            return None
        # printable key
        return ch
    except Exception:
        pass

    # Next try Unix-like raw terminal using termios + tty
    try:
        import sys as _sys
        import termios
        import tty

        fd = _sys.stdin.fileno()
        if prompt:
            # print prompt but don't add newline
            print(prompt, end='', flush=True)
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # read one char; this will block until a key is pressed
            ch1 = _sys.stdin.read(1)
            if not ch1:
                return None
            # if escape sequence start, try to read the rest
            if ch1 == '\x1b':
                # typical sequence is ESC [ A/B/C/D
                rest = _sys.stdin.read(2)
                seq = ch1 + rest
                # match arrow keys
                if seq.endswith('A'):
                    return 'up'
                if seq.endswith('B'):
                    return 'down'
                if seq.endswith('C'):
                    return 'right'
                if seq.endswith('D'):
                    return 'left'
                # if not a known sequence, return full string
                return seq
            # normal key
            return ch1
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass
    except Exception:
        pass

    # fallback: use input() (requires Enter)
    try:
        s = input(prompt)
        return s
    except Exception:
        return None


def _measure_column_widths(line_events, outputs, var_names, self_instances):
    """Measure widths for columns similar to render_trace_table and return widths.

    Returns (widths, var_widths, out_width) where widths is [step_w, source_w]
    """
    # Remap original step numbers to sequential display steps (1..N) in order of occurrence
    step_map = {}
    next_idx = 1
    rows = []
    for step, lineno, func, locs, ev, filename, call_args in line_events:
        if step not in step_map:
            step_map[step] = next_idx
            next_idx += 1
        disp_step = step_map[step]
        source = f"{os.path.basename(filename)}:{lineno}"
        row_vars = []
        for v in var_names:
            val = '-'
            try:
                if isinstance(v, str) and v.startswith('self.'):
                    attr = v.split('.', 1)[1]
                    try:
                        if self_instances and step in self_instances:
                            snap = self_instances[step]
                            if isinstance(snap, dict) and attr in snap:
                                val = snap.get(attr, '-')
                            else:
                                val = '-'
                        else:
                            val = '-'
                    except Exception:
                        val = '-'
                else:
                    if call_args and v in call_args:
                        val = call_args.get(v)
                    else:
                        val = locs.get(v, '-')
            except Exception:
                val = '-'
            single = str(val).splitlines()[0] if val is not None else '-'
            if len(single) > 30:
                single = single[:27] + '...'
            row_vars.append(single)
        out_lines = [t for s, t in outputs if s == step]
        out_text = '\n'.join(out_lines) if out_lines else '-'
        rows.append((disp_step, lineno, source, row_vars, out_text))

    # We no longer show a separate "line" column; only step and source are kept
    widths = [
        max(len('step'), max(len(str(r[0])) for r in rows) if rows else 0),
        max(len('source'), max(len(str(r[2])) for r in rows) if rows else 0),
    ]

    var_widths = []
    for i, v in enumerate(var_names):
        w = max(len(v), max(len(str(r[3][i])) for r in rows) if rows else len(v))
        if w > 40:
            w = 40
        var_widths.append(w)

    out_width = max(len('output'), max(len(r[4]) for r in rows) if rows else len('output'))
    return widths, var_widths, out_width


def _colorize(s: str, color: Optional[str], enable: bool) -> str:
    if not enable or not color:
        return s
    return f"{color}{s}{ANSI_RESET}"


def _format_value(v):
    try:
        # functions and callables: show a compact readable form
        if callable(v):
            # prefer qualified name when available
            try:
                qn = getattr(v, '__qualname__', None) or getattr(v, '__name__', None)
                mod = getattr(v, '__module__', None)
                if qn:
                    if mod and mod not in ('builtins', None):
                        return f"{mod}.{qn}()"
                    else:
                        return f"{qn}()"
            except Exception:
                # fallback to simple marker
                try:
                    return f"<{type(v).__name__}>"
                except Exception:
                    return '<func>'

        # simple scalar types -> repr
        if isinstance(v, (int, float, bool, str)):
            s = repr(v)
        else:
            # prefer a user-friendly str() if it's customized
            try:
                sv = str(v)
            except Exception:
                sv = None
            try:
                rv = repr(v)
            except Exception:
                rv = None

            # detect default object repr like <ClassName object at 0x...>
            default_repr = None
            try:
                default_repr = object.__repr__(v)
            except Exception:
                default_repr = None

            # choose best available representation (prefer str if it differs from default)
            if sv and default_repr and sv != default_repr:
                s = sv
            elif sv and (not default_repr):
                s = sv
            elif rv and default_repr and rv != default_repr:
                s = rv
            elif rv:
                # fallback to a simple type name
                # avoid exposing memory addresses
                s = f"<{type(v).__name__}>"
            else:
                s = '<unrepr>'
    except Exception:
        s = '<unrepr>'
    try:
        maxlen = FORMAT_MAXLEN
    except Exception:
        maxlen = 60
    if isinstance(maxlen, int) and maxlen > 0 and len(s) > maxlen:
        cut = max(0, maxlen - 3)
        s = (s[:cut] + '...') if cut > 0 else s[:maxlen]
    return s


# Flowchart rendering removed (no ASCII flowchart functions remain)


def _compute_var_names(
    line_events: List[Tuple[int, int, str, dict, str, str, dict]],
    self_instances: Optional[dict],
    auto: bool = False,
    top_n: int = 5,
):
    """Compute ordered list of variable column names from collected line_events and self_instances.

    Returns a list of variable names like ['n', 'self.value', 'x']
    """
    NOISE_NAMES = {
        'self',
        'annotations',
        '__annotations__',
        '__builtins__',
        '__doc__',
        '__loader__',
        '__spec__',
        '__package__',
        '__name__',
        '__file__',
    }
    all_var_names = []
    for step, lineno, func, locs, ev, filename, call_args in line_events:
        # use both keys and their string values to filter out noisy names
        for k, v in (locs or {}).items():
            try:
                if k in NOISE_NAMES or k.startswith('__'):
                    continue
                # v is stringified by _format_value; filter typical noise
                sv = str(v)
                # modules like <module 'sys' ...>
                if sv.startswith("<module "):
                    continue
                # callables shown as name()
                if sv.endswith('()'):
                    continue
            except Exception:
                pass
            all_var_names.append(k)
        for k in (call_args or {}).keys():
            if k.startswith('__'):
                continue
            all_var_names.append(k)
        try:
            if self_instances and step in self_instances:
                obj = self_instances[step]
                attrs = []
                if isinstance(obj, dict):
                    attrs = list(obj.keys())
                else:
                    try:
                        attrs = list(vars(obj).keys())
                    except Exception:
                        attrs = [a for a in dir(obj) if not a.startswith('_')]
                for a in attrs:
                    if a.startswith('_'):
                        continue
                    all_var_names.append('self.' + a)
        except Exception:
            pass

    if auto:
        from collections import Counter

        cnt = Counter(all_var_names)
        var_names = [n for n, _ in cnt.most_common(top_n)]
    else:
        var_names = sorted(set(all_var_names))
    return var_names


def render_trace_table(
    line_events: List[Tuple[int, int, str, dict, str, str]],
    outputs: List[Tuple[int, str]],
    auto: bool = False,
    top_n: int = 5,
    self_instances: Optional[dict] = None,
    visible_vars: Optional[list] = None,
    keep_all_rows: bool = False,
    keep_constant_columns: bool = False,
) -> str:
    """Render a trace table with columns per variable.

    Columns: step | source | <var1> | <var2> | ... | output
    """
    if not line_events:
        return '(no line events recorded)'

    # compute variable columns (optionally via helper)
    var_names = visible_vars if visible_vars is not None else _compute_var_names(line_events, self_instances, auto=auto, top_n=top_n)
    # If there are too many variable columns (which often indicates external/imported names
    # or noisy data), and the caller didn't request explicit auto=False, fall back to
    # showing only the top_n most common variables to keep the table readable.
    MAX_COLS = 8
    if visible_vars is None and not auto and len(var_names) > MAX_COLS:
        # recompute using frequency-based selection
        from collections import Counter

        cnt = Counter()
        for step, lineno, func, locs, ev, filename, call_args in line_events:
            for k in locs.keys():
                if k.startswith('__'):
                    continue
                if k == 'self':
                    continue
                cnt[k] += 1
            for k in (call_args or {}).keys():
                if k.startswith('__'):
                    continue
                cnt[k] += 1
            try:
                if self_instances and step in self_instances:
                    obj = self_instances[step]
                    if isinstance(obj, dict):
                        for a in obj.keys():
                            if not a.startswith('_'):
                                cnt['self.' + a] += 1
            except Exception:
                pass
        var_names = [n for n, _ in cnt.most_common(top_n)]

    # Prepare rows first (keep original step numbers). We'll filter empty rows
    # and then remap display step numbers (1..N) based on the filtered rows so
    # visible rows are numbered compactly starting at 1.
    raw_rows = []
    for step, lineno, func, locs, ev, filename, call_args in line_events:
        source = f"{os.path.basename(filename)}:{lineno}"
        # ensure single-line, truncated values
        row_vars = []
        for v in var_names:
            val = '-'
            try:
                # handle self.attribute columns
                if isinstance(v, str) and v.startswith('self.'):
                    attr = v.split('.', 1)[1]
                    try:
                        if self_instances and step in self_instances:
                            snap = self_instances[step]
                            if isinstance(snap, dict) and attr in snap:
                                val = snap.get(attr, '-')
                            else:
                                val = '-'
                        else:
                            val = '-'
                    except Exception:
                        val = '-'
                else:
                    # call args override locals if present
                    if call_args and v in call_args:
                        val = call_args.get(v)
                    else:
                        val = locs.get(v, '-')
            except Exception:
                val = '-'
            single = str(val).splitlines()[0] if val is not None else '-'
            if len(single) > 30:
                single = single[:27] + '...'
            row_vars.append(single)
        out_lines = [t for s, t in outputs if s == step]
        out_text = '\n'.join(out_lines) if out_lines else '-'
        # store original step with the row for later remapping
        raw_rows.append((step, lineno, source, row_vars, out_text))

    # (widths and visible columns will be computed after we filter and remap rows)

    # Determine which variable columns are non-empty across the raw rows so we can
    # filter rows based on visible columns. This uses raw_rows (all rows) to decide
    # which variable columns are meaningful.
    visible_indices_raw = [i for i in range(len(var_names)) if any((_is_nonempty_cell(rr[3][i]) for rr in raw_rows))]
    show_output_raw = any((_is_nonempty_cell(rr[4]) for rr in raw_rows))

    # Filter out rows that are entirely empty across visible variable columns and output,
    # unless the caller requested to keep all rows (keep_all_rows=True).
    if not keep_all_rows:
        filtered = []
        for r in raw_rows:
            # r: (step, lineno, source, row_vars, out_text)
            any_var_nonempty = False
            for idx in visible_indices_raw:
                try:
                    if _is_nonempty_cell(str(r[3][idx])):
                        any_var_nonempty = True
                        break
                except Exception:
                    continue
            any_output_nonempty = _is_nonempty_cell(str(r[4])) if show_output_raw else False
            if any_var_nonempty or any_output_nonempty:
                filtered.append(r)
        rows = filtered
    else:
        rows = list(raw_rows)

    # Now remap original step numbers to sequential display steps (1..N) in order of
    # first occurrence among the filtered rows so the visible steps are compact.
    step_map = {}
    next_idx = 1
    final_rows = []
    for raw_step, lineno, source, row_vars, out_text in rows:
        if raw_step not in step_map:
            step_map[raw_step] = next_idx
            next_idx += 1
        disp_step = step_map[raw_step]
        final_rows.append((disp_step, lineno, source, row_vars, out_text))
    # replace rows with the final remapped display rows
    rows = final_rows

    # compute widths (we no longer display a separate 'line' column)
    widths = [
        max(len('step'), max(len(str(r[0])) for r in rows) if rows else 0),
        max(len('source'), max(len(str(r[2])) for r in rows) if rows else 0),
    ]

    # compute var column widths and detect empty columns (all '-')
    var_widths = []
    for i, v in enumerate(var_names):
        w = max(len(v), max(len(str(r[3][i])) for r in rows) if rows else len(v))
        if w > 40:
            w = 40
        var_widths.append(w)

    # hide variable columns that are empty for all rows (i.e., all '-' or empty/whitespace)
    visible_indices = [i for i in range(len(var_names)) if any((_is_nonempty_cell(r[3][i]) for r in rows))]
    # optionally hide columns whose values never change across visible rows
    if not keep_constant_columns and visible_vars is None and rows and len(visible_indices) > 1:
        non_constant = []
        for idx in visible_indices:
            first_val = None
            constant = True
            for r in rows:
                cell_val = str(r[3][idx])
                if first_val is None:
                    first_val = cell_val
                elif cell_val != first_val:
                    constant = False
                    break
            if not constant:
                non_constant.append(idx)
        if non_constant:
            visible_indices = non_constant
        else:
            # keep at least one column so the table doesn't collapse entirely
            visible_indices = [visible_indices[0]]
    # reduce var_names and var_widths to only visible ones
    var_names_visible = [var_names[i] for i in visible_indices]
    var_widths_visible = [var_widths[i] for i in visible_indices]

    # determine whether output column has any non-empty values; hide if all '-' or empty
    show_output = any((_is_nonempty_cell(r[4]) for r in rows))

    # compute out_width if output column is shown
    out_width = max(len('output'), max(len(r[4]) for r in rows) if rows else len('output')) if show_output else 0

    # build header
    header_cells = ['step'.ljust(widths[0]), 'source'.ljust(widths[1])]
    header_cells += [v.ljust(var_widths_visible[i]) for i, v in enumerate(var_names_visible)]
    if show_output:
        header_cells.append('output'.ljust(out_width))
    header = ' | '.join(header_cells)
    sep = '-+-'.join('-' * len(c) for c in header_cells)

    lines = [header, sep]
    for r in rows:
        # r is (step, lineno, source, row_vars, out_text) but we omit the lineno column
        # r[0] already contains the display step sequential index
        cells = [str(r[0]).ljust(widths[0]), str(r[2]).ljust(widths[1])]
        # only include visible var columns
        for j, idx in enumerate(visible_indices):
            cells.append(str(r[3][idx]).ljust(var_widths_visible[j]))
        if show_output:
            cells.append(str(r[4]).ljust(out_width))
        lines.append(' | '.join(cells))

    return '\n'.join(lines)


def render_flowchart(edges: List[Tuple[str, str]]) -> str:
    # Flowchart support removed; keep compatibility by returning a fixed message
    return '(flowchart support removed)'


def _build_csv_from_events(
    line_events: List[Tuple[int, int, str, dict, str, str, dict]],
    outputs: List[Tuple[int, str]],
    *,
    auto: bool = False,
    top_n: int = 5,
    self_instances: Optional[dict] = None,
    keep_all_rows: bool = False,
    keep_constant_columns: bool = False,
    visible_vars: Optional[list] = None,
    max_cell_len: Optional[int] = 30,
    single_line: bool = True,
) -> Tuple[List[str], List[List[str]]]:
    """Build CSV header and rows directly from tracing data (no table text parsing).

    Returns (headers, rows). Headers include: step, source, <vars...>, [output?]
    Rows are aligned with remapped sequential steps and filtered columns/rows like render_trace_table.
    """
    if not line_events:
        # Only header with step/source
        return ['step', 'source'], []

    # 1) decide variable columns
    var_names = visible_vars if visible_vars is not None else _compute_var_names(line_events, self_instances, auto=auto, top_n=top_n)
    MAX_COLS = 8
    if visible_vars is None and not auto and len(var_names) > MAX_COLS:
        from collections import Counter

        cnt = Counter()
        for step, lineno, func, locs, ev, filename, call_args in line_events:
            for k in locs.keys():
                if k.startswith('__') or k == 'self':
                    continue
                cnt[k] += 1
            for k in (call_args or {}).keys():
                if k.startswith('__'):
                    continue
                cnt[k] += 1
            try:
                if self_instances and step in self_instances:
                    obj = self_instances[step]
                    if isinstance(obj, dict):
                        for a in obj.keys():
                            if not a.startswith('_'):
                                cnt['self.' + a] += 1
            except Exception:
                pass
        var_names = [n for n, _ in cnt.most_common(top_n)]

    # 2) build raw rows (original step preserved)
    raw_rows: List[Tuple[int, int, str, List[str], str]] = []
    for step, lineno, func, locs, ev, filename, call_args in line_events:
        source = f"{os.path.basename(filename)}:{lineno}"
        row_vars: List[str] = []
        for v in var_names:
            val = '-'
            try:
                if isinstance(v, str) and v.startswith('self.'):
                    attr = v.split('.', 1)[1]
                    try:
                        if self_instances and step in self_instances:
                            snap = self_instances[step]
                            if isinstance(snap, dict) and attr in snap:
                                val = snap.get(attr, '-')
                            else:
                                val = '-'
                        else:
                            val = '-'
                    except Exception:
                        val = '-'
                else:
                    if call_args and v in call_args:
                        val = call_args.get(v)
                    else:
                        val = locs.get(v, '-')
            except Exception:
                val = '-'
            if val is None:
                text = '-'
            else:
                sv = str(val)
                text = sv.splitlines()[0] if single_line else sv
            if isinstance(max_cell_len, int) and max_cell_len > 0 and len(text) > max_cell_len:
                cut = max(0, max_cell_len - 3)
                text = (text[:cut] + '...') if cut > 0 else text[:max_cell_len]
            row_vars.append(text)
        out_lines = [t for s, t in outputs if s == step]
        if out_lines:
            # apply same single-line and max length handling to output column
            combined = '\n'.join(out_lines)
            out_text = combined.splitlines()[0] if single_line else combined
            if isinstance(max_cell_len, int) and max_cell_len > 0 and len(out_text) > max_cell_len:
                cut = max(0, max_cell_len - 3)
                out_text = (out_text[:cut] + '...') if cut > 0 else out_text[:max_cell_len]
        else:
            out_text = '-'
        raw_rows.append((step, lineno, source, row_vars, out_text))

    # 3) compute visibility over raw rows
    visible_indices_raw = [i for i in range(len(var_names)) if any((_is_nonempty_cell(rr[3][i]) for rr in raw_rows))]
    show_output_raw = any((_is_nonempty_cell(rr[4]) for rr in raw_rows))

    # 4) filter empty rows unless keep_all_rows
    rows = []
    if not keep_all_rows:
        for r in raw_rows:
            any_var_nonempty = False
            for idx in visible_indices_raw:
                try:
                    if _is_nonempty_cell(str(r[3][idx])):
                        any_var_nonempty = True
                        break
                except Exception:
                    continue
            any_output_nonempty = _is_nonempty_cell(str(r[4])) if show_output_raw else False
            if any_var_nonempty or any_output_nonempty:
                rows.append(r)
    else:
        rows = list(raw_rows)

    # 5) remap steps to sequential display steps 1..N
    step_map = {}
    next_idx = 1
    final_rows: List[Tuple[int, int, str, List[str], str]] = []
    for raw_step, lineno, source, row_vars, out_text in rows:
        if raw_step not in step_map:
            step_map[raw_step] = next_idx
            next_idx += 1
        disp = step_map[raw_step]
        final_rows.append((disp, lineno, source, row_vars, out_text))
    rows = final_rows

    # 6) choose visible var columns; optionally drop constant columns
    visible_indices = [i for i in range(len(var_names)) if any((_is_nonempty_cell(r[3][i]) for r in rows))]
    if not keep_constant_columns and visible_vars is None and rows and len(visible_indices) > 1:
        non_constant = []
        for idx in visible_indices:
            first_val = None
            constant = True
            for r in rows:
                cell_val = str(r[3][idx])
                if first_val is None:
                    first_val = cell_val
                elif cell_val != first_val:
                    constant = False
                    break
            if not constant:
                non_constant.append(idx)
        if non_constant:
            visible_indices = non_constant
        else:
            visible_indices = [visible_indices[0]]

    var_names_visible = [var_names[i] for i in visible_indices]
    show_output = any((_is_nonempty_cell(r[4]) for r in rows))

    # 7) build headers and csv rows
    headers: List[str] = ['step', 'source'] + var_names_visible + (['output'] if show_output else [])
    csv_rows: List[List[str]] = []
    for r in rows:
        rec = [str(r[0]), str(r[2])]
        for idx in visible_indices:
            rec.append(str(r[3][idx]))
        if show_output:
            rec.append(str(r[4]))
        csv_rows.append(rec)

    return headers, csv_rows


def trace_file(
    path: str,
    project_root: Optional[str] = None,
    mode: str = 'trace',
    fmt: str = 'text',
    color: bool = True,
    width: int = 80,
    table: bool = False,
    table_auto: bool = False,
    top_n: int = 5,
    step_over: bool = False,
    stepwise: bool = False,
    table_pager: bool = False,
    page_size: int = 5,
    call_func: Optional[str] = None,
    call_isolate: bool = False,
    remap_steps: bool = False,
    table_keep_empty: bool = False,
    table_keep_constant: bool = False,
    csv: bool = False,
    major_steps: bool = False,
    include_stdlib: bool = False,
    csv_full: bool = False,
) -> None:
    """Execute a Python file and print an indented ascii trace of calls/returns.

    If project_root is provided, only frames whose filename is inside that root are recorded.
    """
    try:
        target_abs = os.path.normcase(os.path.normpath(os.path.abspath(path)))
    except Exception:
        target_abs = None
    always_include = [target_abs] if target_abs else None

    tracer = SimpleTracer(
        project_root=project_root,
        step_over=step_over,
        skip_stdlib=not include_stdlib,
        always_include=always_include,
    )
    tracer._stepwise_mode = stepwise
    # decide whether to keep all rows when rendering tables:
    # - explicit CLI request (table_keep_empty)
    # - when stdout is not a tty (likely redirected to a file)
    # - or when the tracer instance requests it (used by __main__.py for flowchart save)
    try:
        _stdout_is_tty = sys.stdout.isatty()  # noqa: F841
    except Exception:
        _stdout_is_tty = False  # noqa: F841
    keep_all_rows_default = table_keep_empty or getattr(tracer, '_table_keep_all', False)
    # capture stdout prints to include in trace table outputs
    old_stdout = sys.stdout
    buf = None
    try:
        import ast
        import io

        buf = io.StringIO()
        sys.stdout = buf
        # configure formatting length for this run
        global FORMAT_MAXLEN
        _old_format_maxlen = FORMAT_MAXLEN
        if csv_full:
            FORMAT_MAXLEN = None  # disable truncation while capturing
        # If isolation requested, attempt to parse and exec only safe top-level nodes
        isolated_used = False

        # default behavior: set trace and run normally, possibly with a later call
        sys.settrace(tracer.globaltrace)
        try:
            if call_func and call_isolate:
                # Try best-effort isolated load: parse AST and exec only imports, defs, classes, and simple assigns
                try:
                    src = open(path, 'r', encoding='utf-8').read()
                    m = ast.parse(src, filename=path)
                    allowed = (
                        ast.Import,
                        ast.ImportFrom,
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                        ast.Assign,
                        ast.AnnAssign,
                    )
                    module_globals = {}
                    # prepare __name__ so that some modules behave as imported
                    module_globals['__name__'] = os.path.splitext(os.path.basename(path))[0]
                    module_globals['__file__'] = path
                    for node in m.body:
                        if isinstance(node, allowed):
                            # create a Module node wrapping this single node and compile/exec it
                            mod = ast.Module(body=[node], type_ignores=[]) if hasattr(ast, 'Module') else ast.Module([node])
                            code = compile(ast.fix_missing_locations(mod), path, 'exec')
                            exec(code, module_globals)
                        else:
                            # skip other top-level nodes (calls, expressions with side-effects, etc.)
                            continue
                    # call the function if present
                    fn = module_globals.get(call_func)
                    if callable(fn):
                        try:
                            fn()
                            isolated_used = True
                        except Exception:
                            # if the isolated call fails, do NOT fallback when in forced-isolate mode
                            isolated_used = False
                except Exception:
                    isolated_used = False
            if not isolated_used:
                # Ensure the traced script sees a clean argv (avoid leaking our CLI args like 'show')
                _old_argv = sys.argv
                sys.argv = [path]
                try:
                    if call_func:
                        if call_isolate:
                            # Forced isolate requested but failed -> skip execution to avoid side-effects
                            print(f"[showtracetable] isolated call requested for '{call_func}' but isolation failed; skipping execution.")
                        else:
                            # Non-isolated call requested: load module under its module name (not '__main__')
                            mod_name = os.path.splitext(os.path.basename(path))[0]
                            mod_globals = runpy.run_path(path, run_name=mod_name)
                            fn = mod_globals.get(call_func)
                            if callable(fn):
                                try:
                                    fn()
                                except Exception:
                                    pass
                    else:
                        # No call_func requested: run script normally as __main__
                        try:
                            runpy.run_path(path, run_name='__main__')
                        except ImportError as e:
                            # Some example scripts use package-relative imports which fail when run via run_path
                            # ("attempted relative import with no known parent package"). Try running as a module
                            # by guessing a module name from the path.
                            msg = str(e)
                            if 'attempted relative import' in msg or 'no known parent package' in msg:
                                rel = None
                                try:
                                    rel = os.path.relpath(path, os.getcwd())
                                except Exception:
                                    rel = path
                                candidates = []
                                # candidate: path -> dotted module name
                                if rel:
                                    if rel.endswith('.py'):
                                        candidates.append(rel[:-3].replace(os.sep, '.'))
                                    else:
                                        candidates.append(rel.replace(os.sep, '.'))
                                # also try under 'examples' package if applicable
                                if rel and rel.startswith('examples' + os.sep):
                                    candidates.append(('examples.' + rel[len('examples' + os.sep) :])[:-3].replace(os.sep, '.'))

                                ran = False
                                # Temporarily add the script's parent dir to sys.path to help module resolution
                                script_dir = os.path.dirname(os.path.abspath(path))
                                added = False
                                try:
                                    if script_dir not in sys.path:
                                        sys.path.insert(0, script_dir)
                                        added = True
                                    for mod in candidates:
                                        if not mod:
                                            continue
                                        try:
                                            # run as real module so that package-relative imports work
                                            runpy.run_module(mod)
                                            ran = True
                                            break
                                        except Exception:
                                            continue
                                finally:
                                    if added:
                                        try:
                                            sys.path.remove(script_dir)
                                        except Exception:
                                            pass
                                if not ran:
                                    # couldn't run as module; re-raise original ImportError
                                    raise
                            else:
                                # Different ImportError cause -> re-raise original
                                raise
                finally:
                    # Restore original argv
                    try:
                        sys.argv = _old_argv
                    except Exception:
                        pass
        finally:
            sys.settrace(None)
        # collect printed output lines and associate with last step
        sys.stdout.seek(0)
        text = sys.stdout.read()
        if text:
            # splitlines and attach to the current step
            for line in text.splitlines():
                tracer.outputs.append((tracer.current_step or 0, line))
    finally:
        sys.stdout = old_stdout
        try:
            # restore formatting limit
            FORMAT_MAXLEN = _old_format_maxlen  # type: ignore[name-defined]
        except Exception:
            pass

    # (debug counts removed)
    output = render_ascii_indented(tracer.events)
    # flowchart/chart generation removed
    chart = None

    if fmt == 'json':
        # produce structured JSON with nodes and events
        # optionally remap step numbers to sequential 1..N in order of occurrence
        if remap_steps:
            step_map = {}
            next_idx = 1
            remapped_line_events = []
            for s, ln, fnc, locs, ev, fn, ca in tracer.line_events:
                if s not in step_map:
                    step_map[s] = next_idx
                    next_idx += 1
                remapped_line_events.append(
                    dict(
                        step=step_map[s],
                        lineno=ln,
                        func=fnc,
                        locals=locs,
                        event=ev,
                        filename=fn,
                        call_args=ca,
                    )
                )
            remapped_outputs = [{'step': step_map.get(s, s), 'text': t} for (s, t) in tracer.outputs]
            data = {
                'events': [dict(event=e, lineno=ln, func=f, filename=fn) for (e, ln, f, fn) in tracer.events],
                'line_events': remapped_line_events,
                'outputs': remapped_outputs,
            }
        else:
            data = {
                'events': [dict(event=e, lineno=ln, func=f, filename=fn) for (e, ln, f, fn) in tracer.events],
                'line_events': [
                    dict(
                        step=s,
                        lineno=ln,
                        func=fnc,
                        locals=locs,
                        event=ev,
                        filename=fn,
                        call_args=ca,
                    )
                    for (s, ln, fnc, locs, ev, fn, ca) in tracer.line_events
                ],
                'outputs': [{'step': s, 'text': t} for (s, t) in tracer.outputs],
            }
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # text output
    if table:
        # If stepwise display requested, show one line_event at a time interactively
        stepwise = False
        # detect if caller passed stepwise via kwargs in __main__ (avoid changing signature here)
        try:
            # the CLI forwards stepwise as an attribute on tracer object temporarily
            stepwise = getattr(tracer, '_stepwise_mode', False)
        except Exception:
            stepwise = False

        if stepwise:
            total = len(tracer.line_events)
            idx = 0
            while idx < total:
                # show up to current idx (inclusive) as table
                sub = tracer.line_events[: idx + 1]
                print(
                    render_trace_table(
                        sub,
                        tracer.outputs,
                        auto=table_auto,
                        top_n=top_n,
                        self_instances=tracer._self_instances,
                        keep_all_rows=keep_all_rows_default,
                        keep_constant_columns=table_keep_constant,
                    )
                )
                # prompt
                try:
                    s = input("Press Enter to advance, q to quit: ")
                except EOFError:
                    break
                if s.strip().lower() == 'q':
                    break
                idx += 1
            return
        else:
            # support optional interactive pager for variable columns
            if table_pager:
                # compute full ordered var list
                full_vars = _compute_var_names(tracer.line_events, tracer._self_instances, auto=table_auto, top_n=top_n)
                if not full_vars:
                    print(
                        render_trace_table(
                            tracer.line_events,
                            tracer.outputs,
                            auto=table_auto,
                            top_n=top_n,
                            self_instances=tracer._self_instances,
                            keep_all_rows=keep_all_rows_default,
                            keep_constant_columns=table_keep_constant,
                        )
                    )
                    return
                # paging state: offset of first visible var
                offset = 0
                page = page_size
                # if page_size is not provided or <= 0, auto-fit to terminal width
                if not page or page <= 0:
                    page = 1
                # attempt to auto-fit page to terminal columns: compute column widths and see how many var cols fit
                try:
                    term_cols = shutil.get_terminal_size((80, 20)).columns
                    # compute widths for increasing number of var columns until exceeding terminal width
                    # measure using first N vars
                    # fallback: if measurement fails, keep provided page
                    # first filter out columns that are empty for all rows (same logic as render_trace_table)
                    filtered_full = []
                    # compute per-var emptiness by measuring first with _measure_column_widths per candidate
                    for v in full_vars:
                        widths_, var_widths_, out_width_ = _measure_column_widths(
                            tracer.line_events, tracer.outputs, [v], tracer._self_instances
                        )
                        # check if values in that single column are all '-' by scanning produced rows
                        # simpler approach: render and inspect rows via _measure_column_widths returned widths
                        # but since _measure_column_widths doesn't return rows, we fallback to computing emptiness directly
                        # compute emptiness directly here
                        is_nonempty = False
                        for step, lineno, func, locs, ev, filename, call_args in tracer.line_events:
                            if isinstance(v, str) and v.startswith('self.'):
                                attr = v.split('.', 1)[1]
                                try:
                                    if tracer._self_instances and step in tracer._self_instances:
                                        snap = tracer._self_instances[step]
                                        if isinstance(snap, dict) and attr in snap and _is_nonempty_cell(str(snap[attr])):
                                            is_nonempty = True
                                            break
                                except Exception:
                                    pass
                            else:
                                try:
                                    if call_args and v in call_args and _is_nonempty_cell(str(call_args[v])):
                                        is_nonempty = True
                                        break
                                except Exception:
                                    pass
                                try:
                                    if locs and v in locs and _is_nonempty_cell(str(locs[v])):
                                        is_nonempty = True
                                        break
                                except Exception:
                                    pass
                        if is_nonempty:
                            filtered_full.append(v)

                    for try_n in range(1, len(filtered_full) + 1):
                        vis_try = filtered_full[:try_n]
                        widths, var_widths, out_width = _measure_column_widths(
                            tracer.line_events, tracer.outputs, vis_try, tracer._self_instances
                        )
                        # total width estimate: separators and columns
                        # widths is [step_w, source_w]
                        total = widths[0] + widths[1] + out_width
                        total += sum(var_widths)
                        # add for separators between columns (' | ' roughly 3 chars per extra column)
                        total += 3 * (2 + len(var_widths))  # step + source + var cols
                        if total > term_cols:
                            # last try_n - 1 fitted
                            page = max(1, try_n - 1)
                            break
                    else:
                        page = len(filtered_full)
                except Exception:
                    page = max(1, page)
                total_vars = len(full_vars)
                while True:
                    # compute visible slice from filtered set to ensure we don't show empty columns
                    vis_candidates = []
                    for v in full_vars:
                        is_nonempty = False
                        for step, lineno, func, locs, ev, filename, ca in tracer.line_events:
                            if isinstance(v, str) and v.startswith('self.'):
                                attr = v.split('.', 1)[1]
                                try:
                                    if tracer._self_instances and step in tracer._self_instances:
                                        snap = tracer._self_instances[step]
                                        if isinstance(snap, dict) and attr in snap and _is_nonempty_cell(str(snap[attr])):
                                            is_nonempty = True
                                            break
                                except Exception:
                                    pass
                            else:
                                try:
                                    if ca and v in ca and _is_nonempty_cell(str(ca[v])):
                                        is_nonempty = True
                                        break
                                except Exception:
                                    pass
                                try:
                                    if locs and v in locs and _is_nonempty_cell(str(locs[v])):
                                        is_nonempty = True
                                        break
                                except Exception:
                                    pass
                        if is_nonempty:
                            vis_candidates.append(v)
                    vis = vis_candidates[offset : offset + page]
                    print(f"Columns {offset + 1}-{min(offset + page, total_vars)} of {total_vars}: {', '.join(vis)}")
                    print(
                        render_trace_table(
                            tracer.line_events,
                            tracer.outputs,
                            auto=table_auto,
                            top_n=top_n,
                            self_instances=tracer._self_instances,
                            visible_vars=vis,
                            keep_all_rows=keep_all_rows_default,
                            keep_constant_columns=table_keep_constant,
                        )
                    )
                    # read a single key (supports arrow keys on Windows via msvcrt)
                    key = _read_single_key("(←/→ or n/p,d/a,h) q to quit: ")
                    if key is None:
                        break
                    # normalize returned key
                    if isinstance(key, str):
                        c = key.strip().lower()
                    else:
                        c = ''
                    if c in ('q', 'quit'):
                        break
                    # handle arrow strings returned by _read_single_key
                    if c in ('right',) or c in ('n', 'd', 'p'):
                        # move right
                        if offset + page < total_vars:
                            offset += page
                        else:
                            print("Already at right-most page")
                        continue
                    if c in ('left',) or c in ('b', 'a', 'h'):
                        # move left
                        if offset - page >= 0:
                            offset -= page
                        else:
                            offset = 0
                            print("Already at left-most page")
                        continue
                    # allow numeric jump to page index
                    try:
                        iv = int(c)
                        # interpret as 1-based page index
                        if iv >= 1:
                            new_off = (iv - 1) * page
                            if new_off < total_vars:
                                offset = new_off
                                continue
                    except Exception:
                        pass
                    print("Unknown command")
                return
            else:
                table_text = render_trace_table(
                    tracer.line_events,
                    tracer.outputs,
                    auto=table_auto,
                    top_n=top_n,
                    self_instances=tracer._self_instances,
                    keep_all_rows=keep_all_rows_default,
                    keep_constant_columns=table_keep_constant,
                )
                print(table_text)

            # CSV output (direct from events, not via rendered table)
            # Auto-save CSV when showing a table, even if csv flag isn't explicitly set.
            if csv or table:
                # Prepare line_events source: full or major-steps filtered
                if major_steps:
                    filtered_events = []
                    for i, (event, lineno, func, filename) in enumerate(tracer.events):
                        if event in ('call', 'return') and tracer._in_project(filename):
                            filtered_events.append((i + 1, lineno, func, {}, event, filename, {}))
                    le_source = filtered_events
                else:
                    le_source = tracer.line_events

                try:
                    headers, rows = _build_csv_from_events(
                        le_source,
                        tracer.outputs,
                        auto=table_auto,
                        top_n=top_n,
                        self_instances=tracer._self_instances,
                        keep_all_rows=True if major_steps else keep_all_rows_default,
                        keep_constant_columns=table_keep_constant,
                        max_cell_len=None if csv_full else 30,
                        single_line=False if csv_full else True,
                    )
                    csv_filename = os.path.splitext(os.path.basename(path))[0] + '.trace.csv'
                    import csv as _csv

                    _enc = 'utf-8-sig' if os.name == 'nt' else 'utf-8'
                    with open(csv_filename, 'w', encoding=_enc, newline='') as f:
                        writer = _csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(rows)
                    print(f"CSV file saved: {csv_filename}")
                except Exception as e:
                    print(f"Warning: Failed to save CSV file: {e}")

            return

    if mode == 'both':
        if chart:
            print(chart)
        print('\nTrace:')
        print(_colorize(output, ANSI_RESET, color))
    elif mode == 'chart':
        if chart:
            print(chart)
    else:
        # default and 'trace'
        print(_colorize(output, ANSI_RESET, color))
