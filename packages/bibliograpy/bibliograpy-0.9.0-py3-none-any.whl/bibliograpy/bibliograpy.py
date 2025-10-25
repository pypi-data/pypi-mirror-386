"""
bibliograpy command entrypoint
"""
import logging

from argparse import ArgumentParser, Namespace

from bibliograpy.api_core import Formats
from bibliograpy.process import _process

LOG = logging.getLogger(__name__)


DEFAULT_FILE = "bibliography"
DEFAULT_ENCODING = 'utf-8'
DEFAULT_OUTPUT_DIR = '.'
DEFAULT_OUTPUT_FILE = 'bibliography.py'
DEFAULT_INIT_SCOPE = '{}'


def _create_parser() -> ArgumentParser:

    # parse argument line
    parser = ArgumentParser(description='Bibliography management.')

    subparsers = parser.add_subparsers(dest='CMD', help='available commands')

    bibtex = subparsers.add_parser(name=Formats.BIBTEX.command,
                                   help='generates bibliograpy Python source bibliography '
                                        f'from {Formats.BIBTEX.title} format')
    bibtex.add_argument('file',
                         nargs='?',
                         help=f"path to the input bibliography file (default to {DEFAULT_FILE}.bib)",
                         default=DEFAULT_FILE + '.bib')
    bibtex.add_argument('--encoding', '-e',
                         nargs='?',
                         help='the bibliograpy configuration file encoding (default to utf-8)',
                         default=DEFAULT_ENCODING)
    bibtex.add_argument('--output-dir', '-O',
                         nargs='?',
                         help='the source bibliograpy file output directory (default to .)',
                         default=DEFAULT_OUTPUT_DIR)
    bibtex.add_argument('--output-file', '-o',
                         nargs='?',
                         help='the source bibliograpy output file name (default to bibliography.py)',
                         default=DEFAULT_OUTPUT_FILE)
    bibtex.add_argument('--symbolizer',
                       nargs='?',
                       help='an helper class my.symbolizer.module:MySymbolizerClass used to build python symbols')
    group = bibtex.add_mutually_exclusive_group()
    group.add_argument('--scope', '-s',
                       nargs='?',
                       help="the local scope name")
    group.add_argument('--shared-scope', '-S',
                       action='store_true',
                       help='use the bibtex bibliograpy shared scope named SHARED_SCOPE')
    bibtex.add_argument('--init-scope', '-i',
                        nargs='?',
                        help='the local scope initialization (default to "{}")',
                        default=DEFAULT_INIT_SCOPE)


    for fmt in [f for f in Formats if f.command is not None and f is not Formats.BIBTEX]:

        f = subparsers.add_parser(name=fmt.command,
                                  help=f'generates bibliograpy Python source bibliography from {fmt.title} format')
        default_file = DEFAULT_FILE + '.' + fmt.io_extension[0]
        f.add_argument('file',
                       nargs='?',
                       help=f"path to the input bibliography file (default to {default_file})",
                       default=default_file)
        f.add_argument('--encoding', '-e',
                       nargs='?',
                       help='the bibliograpy configuration file encoding (default to utf-8)',
                       default=DEFAULT_ENCODING)
        f.add_argument('--output-dir', '-O',
                       nargs='?',
                       help='the source bibliograpy file output directory (default to .)',
                       default=DEFAULT_OUTPUT_DIR)
        f.add_argument('--output-file', '-o',
                       nargs='?',
                       help='the source bibliograpy output file name (default to bibliography.py)',
                       default=DEFAULT_OUTPUT_FILE)
        f.add_argument('--symbolizer',
                       nargs='?',
                       help='an helper class my.symbolizer.module:MySymbolizerClass used to build python symbols')

    return parser


def entrypoint():
    """The pyenvs command entrypoint."""

    commands = { f.command: _process for f in Formats if f.command is not None }

    ns: Namespace = _create_parser().parse_args()

    commands.get(ns.CMD)(ns)
