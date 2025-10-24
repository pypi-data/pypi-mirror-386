import argparse
import os
import sys

from . import __version__
from .tracer import trace_file


def main():
    parser = argparse.ArgumentParser(description='Trace any Python script and show traces or a trace table')
    parser.add_argument('--version', action='version', version=f'showtracetable {__version__}')
    subparsers = parser.add_subparsers(dest='command')

    # trace command
    trace_p = subparsers.add_parser('trace', help='Trace a Python script')
    trace_p.add_argument(
        'script',
        help='Path to the target Python script (any .py file). Example: examples/sample.py',
    )
    trace_p.add_argument('--project-root', '-p', help='Only show frames under this directory')
    trace_p.add_argument(
        '--format',
        '-f',
        choices=['text', 'json'],
        default='text',
        help='Output format: text or json',
    )
    trace_p.add_argument(
        '--color/--no-color',
        dest='color',
        default=True,
        help='Enable or disable ANSI color in text output',
    )
    trace_p.add_argument('--width', type=int, default=80, help='Approximate width for ASCII rendering')
    trace_p.add_argument(
        '--table',
        dest='table',
        action='store_true',
        help='Show classic trace table (variables per source line)',
    )
    trace_p.add_argument('--no-table', dest='table', action='store_false', help='Disable trace table display')
    trace_p.set_defaults(table=True)
    trace_p.add_argument(
        '--table-auto',
        action='store_true',
        help='Automatically pick the most-used variables as columns for the trace table',
    )
    trace_p.add_argument(
        '--table-top',
        type=int,
        default=5,
        help='When using --table-auto, limit to the top N variable columns',
    )
    trace_p.add_argument('--table-pager', action='store_true', help='Enable interactive column pager for wide tables')
    trace_p.add_argument(
        '--table-page-size',
        type=int,
        default=0,
        help='Number of variable columns to show per pager page (0 = auto-fit)',
    )
    trace_p.add_argument(
        '--table-keep-const',
        dest='table_keep_const',
        action='store_true',
        help='Keep variable columns even if their values stay constant across all visible rows',
    )
    trace_p.add_argument(
        '--step-over',
        action='store_true',
        help='When showing a table, advance one top-level source line at a time',
    )
    trace_p.add_argument('--stepwise', action='store_true', help='Interactively step through the trace table')
    trace_p.add_argument(
        '--call',
        dest='call',
        help='(Optional) Name of a function defined in the target script to call after loading it (no args).',
    )
    trace_p.add_argument(
        '--call-isolate',
        dest='call_isolate',
        action='store_true',
        help='Attempt to call --call without running other top-level code (best-effort).',
    )
    trace_p.add_argument(
        '--remap-steps',
        dest='remap_steps',
        action='store_true',
        help='When outputting JSON, remap step numbers to a compact 1..N order based on occurrence',
    )
    trace_p.add_argument(
        '--table-keep-empty',
        dest='table_keep_empty',
        action='store_true',
        help='When showing/saving a trace table, keep rows even if all variable/output cells are empty',
    )
    trace_p.add_argument(
        '--csv',
        action='store_true',
        default=True,
        help='Output trace table to CSV file (default: enabled)',
    )
    trace_p.add_argument('--no-csv', action='store_false', dest='csv', help='Disable CSV output')
    trace_p.add_argument(
        '--major-steps',
        action='store_true',
        help='Filter to show only major steps (function calls and returns) in CSV output',
    )
    trace_p.add_argument(
        '--csv-full',
        action='store_true',
        help='Do not truncate values in CSV; allow multi-line cells and long strings',
    )
    trace_p.add_argument(
        '--include-stdlib',
        action='store_true',
        help='Include Python standard library frames in trace output (default: skip them)',
    )

    # simplified 'show' subcommand: convenience wrapper to run the tracer
    show_p = subparsers.add_parser('show', help='Quick: run tracer on a Python script (minimal options)')
    show_p.add_argument('script', help='Path to the target Python script.')
    show_p.add_argument('--table', action='store_true', default=True, help='Show trace table (default: enabled)')
    show_p.add_argument('--no-table', action='store_false', dest='table', help='Disable table display')
    show_p.add_argument(
        '--table-keep-const',
        dest='table_keep_const',
        action='store_true',
        help='Keep variable columns even if their values stay constant across all visible rows',
    )
    show_p.add_argument(
        '--major-steps',
        action='store_true',
        help='Filter to show only major steps (function calls and returns) in CSV output',
    )
    show_p.add_argument(
        '--include-stdlib',
        action='store_true',
        help='Include Python standard library frames in trace output (default: skip them)',
    )
    show_p.add_argument(
        '--csv-full',
        action='store_true',
        help='Do not truncate values in CSV; allow multi-line cells and long strings',
    )

    # If called without subcommand and a script path is passed, default to 'show'
    if len(sys.argv) > 1 and sys.argv[1] not in ('trace', 'show'):
        sys.argv.insert(1, 'show')

    args = parser.parse_args()

    if args.command == 'show':
        path = args.script
        # Reuse trace_file to run tracer and write trace artifacts if requested.
        trace_file(
            path,
            table=getattr(args, 'table', True),
            table_auto=getattr(args, 'table_auto', False),
            top_n=getattr(args, 'table_top', 5),
            table_keep_empty=getattr(args, 'table_keep_empty', False),
            table_keep_constant=getattr(args, 'table_keep_const', False),
            csv=True,
            major_steps=getattr(args, 'major_steps', False),
            include_stdlib=getattr(args, 'include_stdlib', False),
            csv_full=getattr(args, 'csv_full', False),
        )
        return

    # default: trace command
    project_root = args.project_root
    if project_root:
        project_root = os.path.abspath(project_root)
    else:
        project_root = None

    trace_file(
        args.script,
        project_root=project_root,
        fmt=args.format,
        color=args.color,
        width=args.width,
        table=args.table,
        table_auto=args.table_auto,
        top_n=args.table_top,
        step_over=args.step_over,
        stepwise=args.stepwise,
        table_pager=args.table_pager,
        page_size=args.table_page_size,
        call_func=args.call,
        call_isolate=args.call_isolate,
        remap_steps=args.remap_steps,
        table_keep_empty=getattr(args, 'table_keep_empty', False),
        table_keep_constant=getattr(args, 'table_keep_const', False),
        csv=args.csv,
        major_steps=getattr(args, 'major_steps', False),
        include_stdlib=args.include_stdlib,
        csv_full=getattr(args, 'csv_full', False),
    )


if __name__ == '__main__':
    main()
