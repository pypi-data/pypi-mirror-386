import argparse
import logging
import typing

DEFAULT_LOGGING_LEVEL: str = logging.getLevelName(logging.INFO)
DEFAULT_LOGGING_FORMAT: str = '%(asctime)s [%(levelname)-8s] - %(filename)s:%(lineno)s -- %(message)s'

LEVELS: typing.List[str] = [
    'TRACE',
    logging.getLevelName(logging.DEBUG),
    logging.getLevelName(logging.INFO),
    logging.getLevelName(logging.WARNING),
    logging.getLevelName(logging.ERROR),
    logging.getLevelName(logging.CRITICAL),
]

def init(level: str = DEFAULT_LOGGING_LEVEL, log_format: str = DEFAULT_LOGGING_FORMAT,
        warn_loggers: typing.Union[typing.List[str], None] = None,
        **kwargs: typing.Any) -> None:
    """
    Initialize or re-initialize the logging infrastructure.
    The list of warning loggers is a list of identifiers for loggers (usually third-party) to move up to warning on init.
    """

    # Add trace.
    _add_logging_level('TRACE', logging.DEBUG - 5)

    logging.basicConfig(level = level, format = log_format, force = True)

    if (warn_loggers is not None):
        for warn_logger in warn_loggers:
            logging.getLogger(warn_logger).setLevel(logging.WARNING)

    logging.trace("Logging initialized with level '%s'.", level)  # type: ignore[attr-defined]

def set_cli_args(parser: argparse.ArgumentParser, extra_state: typing.Dict[str, typing.Any]) -> None:
    """
    Set common CLI arguments.
    This is a sibling to init_from_args(), as the arguments set here can be interpreted there.
    """

    parser.add_argument('--log-level', dest = 'log_level',
            action = 'store', type = str, default = logging.getLevelName(logging.INFO),
            choices = LEVELS,
            help = 'Set the logging level (default: %(default)s).')

    parser.add_argument('--quiet', dest = 'quiet',
            action = 'store_true', default = False,
            help = 'Set the logging level to warning (overrides --log-level) (default: %(default)s).')

    parser.add_argument('--debug', dest = 'debug',
            action = 'store_true', default = False,
            help = 'Set the logging level to debug (overrides --log-level and --quiet) (default: %(default)s).')

def init_from_args(
        parser: argparse.ArgumentParser,
        args: argparse.Namespace,
        extra_state: typing.Dict[str, typing.Any]) -> None:
    """
    Take in args from a parser that was passed to set_cli_args(),
    and call init() with the appropriate arguments.
    """

    level = args.log_level

    if (args.quiet):
        level = logging.getLevelName(logging.WARNING)

    if (args.debug):
        level = logging.getLevelName(logging.DEBUG)

    init(level)

def _add_logging_level(level_name: str, level_number: int, method_name: typing.Union[str, None] = None) -> None:
    """
    Add a new logging level.

    See https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945 .
    """

    if (method_name is None):
        method_name = level_name.lower()

    # Level has already been defined.
    if hasattr(logging, level_name):
        return

    def log_for_level(self: typing.Any, message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        if self.isEnabledFor(level_number):
            self._log(level_number, message, args, **kwargs)

    def log_to_root(message: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        logging.log(level_number, message, *args, **kwargs)

    logging.addLevelName(level_number, level_name)
    setattr(logging, level_name, level_number)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)

# Load the default logging when this module is loaded.
init()
