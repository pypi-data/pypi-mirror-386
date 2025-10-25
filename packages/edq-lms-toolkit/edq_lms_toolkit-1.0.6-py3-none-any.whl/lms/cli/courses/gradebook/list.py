"""
List the gradebook for a course.
"""

import argparse
import sys

import lms.backend.instance
import lms.cli.common
import lms.cli.parser

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    config = args._config

    backend = lms.backend.instance.get_backend(**config)

    course_query = lms.cli.common.check_required_course(backend, config)
    if (course_query is None):
        return 1

    gradebook = backend.courses_gradebook_resolve_and_list(course_query)

    output = lms.model.base.base_list_to_output_format([gradebook], args.output_format,
            skip_headers = args.skip_headers,
            pretty_headers = args.pretty_headers,
            include_extra_fields = args.include_extra_fields,
            extract_single_list = True,
    )

    print(output)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """
    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    return lms.cli.parser.get_parser(__doc__.strip(),
            include_token = True,
            include_output_format = True,
            include_course = True,
    )

if (__name__ == '__main__'):
    sys.exit(main())
