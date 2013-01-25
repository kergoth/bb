"""Code common to the various python bb commands"""

import logging
import os
import sys
import warnings

PATH = os.getenv('PATH').split(':')
bitbake_paths = [os.path.join(path, '..', 'lib')
                 for path in PATH if os.path.exists(os.path.join(path, 'bitbake'))]
if not bitbake_paths:
    raise ImportError("Unable to locate bitbake, please ensure PATH is set correctly.")

sys.path[0:0] = bitbake_paths

import bb.msg
import bb.utils
import bb.providers
import bb.tinfoil


class Terminate(BaseException):
    pass


class Formatter(bb.msg.BBLogFormatter):
    def __init__(self, fmt=None, datefmt=None, output=sys.stdout):
        bb.msg.BBLogFormatter.__init__(self, fmt, datefmt)
        self.output = output

    def enable_color(self):
        self.color_enabled = True


# TODO: Let bb.tinfoil.Tinfoil support output files other than stdout, and to
# enable color support in the formatter when it's a tty.
class Tinfoil(bb.tinfoil.Tinfoil):
    def __init__(self, output=sys.stdout):
        # Needed to avoid deprecation warnings with python 2.6
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Set up logging
        self.logger = logging.getLogger('BitBake')
        console = logging.StreamHandler(output)
        format = Formatter("%(levelname)s: %(message)s", output=output)
        if output.isatty():
            format.enable_color()
        bb.msg.addDefaultlogFilter(console)
        console.setFormatter(format)
        self.logger.addHandler(console)

        initialenv = os.environ.copy()
        bb.utils.clean_environment()
        self.config = bb.tinfoil.TinfoilConfig(parse_only=True)
        self.cooker = bb.cooker.BBCooker(self.config, self.register_idle_function,
                                         initialenv)
        self.config_data = self.cooker.configuration.data
        bb.providers.logger.setLevel(logging.ERROR)
        self.cooker_data = None


def setup_logger(logger):
    log_format = Formatter("%(levelname)s: %(message)s")
    if sys.stderr.isatty():
        log_format.enable_color()
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(log_format)

    logger.addHandler(console)
    logger.setLevel(logging.INFO)


def sigterm_exception(signum, stackframe):
    raise Terminate()


def run_main(main):
    import signal
    signal.signal(signal.SIGTERM, sigterm_exception)
    try:
        sys.exit(main(sys.argv[1:]) or 0)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
    except Terminate:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
