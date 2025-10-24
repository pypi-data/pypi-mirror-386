import argparse
import logging
from collections.abc import Iterator

from .cmk_dev_install import Edition
from .cmk_dev_install import main as cmk_dev_install
from .cmk_dev_site import main as cmk_dev_site
from .utils.log import get_logger
from .version import __version__

logger = get_logger(__name__)


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "version",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "edition",
        type=Edition,
        nargs="?",
        choices=Edition,
        default=Edition.ENTERPRISE,
    )
    parser.add_argument(
        "-d",
        "--distributed",
        metavar="N",
        help="specify the number of distributed sites to set up.",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-n",
        "--name",
        help="specify name of the site to be created",
    )
    parser.add_argument(
        "--dryrun",
        help="only print command, but do not execute",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="decrease output verbosity",
    )


def install_args(version: str | None, edition: str | None, arg_logging_level: str) -> Iterator[str]:
    if version:
        yield str(version)
        if edition:
            yield "--edition"
            yield str(edition)
    if arg_logging_level:
        yield arg_logging_level


def site_args(distributed: int, arg_logging_level: str, name: str | None) -> Iterator[str]:
    if distributed:
        yield "--distributed"
        yield str(distributed)
    if name:
        yield "--name"
        yield name
    yield "-f"
    if arg_logging_level:
        yield arg_logging_level


def core(
    version: str | None,
    edition: str | None,
    *,
    site_distributed: int,
    site_name: str | None,
    dryrun: bool,
    verbose: int,
    quiet: int,
) -> int:
    # we build the commandline and then feed it to the original tools
    # so what we print and execute is exactly the same...
    arg_logging_level = ""
    if verbose or quiet:
        arg_logging_level = f"-{''.join(['v' * verbose, 'q' * quiet])}"

    args_install = list(install_args(version, edition, arg_logging_level))
    args_site = list(site_args(site_distributed, arg_logging_level, site_name))

    print(
        "cmk-dev-install",
        " ".join(args_install),
        "&&",
        "cmk-dev-site",
        " ".join(args_site),
    )

    if not dryrun:
        result = cmk_dev_install(args_install)
        if result != 0:
            return result
        return cmk_dev_site(args_site)
    return 0


def execute(args: argparse.Namespace) -> int:
    try:
        logger.setLevel(max(logging.INFO - ((args.verbose - args.quiet) * 10), logging.DEBUG))
        return core(
            args.version,
            args.edition,
            site_distributed=args.distributed,
            site_name=args.name,
            dryrun=args.dryrun,
            verbose=args.verbose,
            quiet=args.quiet,
        )
    except RuntimeError as e:
        logger.error(str(e))
        return 1
    return 0


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main(sys_argv: list[str] | None = None) -> int:
    parser = create_parser()
    setup_parser(parser)

    args = parser.parse_args()
    return execute(args)
