import argparse
import logging
import sys

from . import __version__
from .server import SERVER
from .utils import set_stan_path

def get_version() -> str:
    """Get the program version."""
    return __version__


def cli() -> None:
    """STAN language server CLI"""
    parser = argparse.ArgumentParser(
        prog="stan-language-server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="STAN Language Server: implements the LSP for STAN.",
        epilog="""\
Examples:

    Run over stdio     : stan-language-server
    Run over tcp       : stan-language-server --tcp
""",
    )
    parser.add_argument(
        "--version",
        help="display version information and exit",
        action="store_true",
    )
    parser.add_argument(
        "--tcp",
        help="use TCP web server instead of stdio",
        action="store_true",
    )
    parser.add_argument(
        "--stan-path",
        help="path to stanc executable (stanc3)",
        type=str,
        default="stanc"
    )
    parser.add_argument(
        "--host",
        help="host for web server (default 127.0.0.1)",
        type=str,
        default="127.0.0.1",
    )
    parser.add_argument(
        "--port",
        help="port for web server (default 2087)",
        type=int,
        default=2087,
    )
    parser.add_argument(
        "--log-file",
        help="redirect logs to file specified",
        type=str,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase verbosity of log output",
        action="count",
        default=0,
    )
    args = parser.parse_args()
    if args.version:
        print(get_version())
        sys.exit(0)
    log_level = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}.get(
        args.verbose,
        logging.DEBUG,
    )

    if args.log_file:
        logging.basicConfig(
            filename=args.log_file,
            filemode="w",
            level=log_level,
        )
    else:
        logging.basicConfig(stream=sys.stderr, level=log_level)

    set_stan_path(args.stan_path)
    
    if args.tcp:
        SERVER.start_tcp(host=args.host, port=args.port)
    else:
        SERVER.start_io()