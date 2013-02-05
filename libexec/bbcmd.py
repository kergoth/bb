"""Code common to the various python bb commands"""

import argparse
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


class Tinfoil(bb.tinfoil.Tinfoil):
    def __init__(self, output=sys.stdout):
        # Needed to avoid deprecation warnings with python 2.6
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Set up logging
        self.logger = logging.getLogger('BitBake')
        if output is not None:
            setup_log_handler(self.logger, output)

        initialenv = os.environ.copy()
        bb.utils.clean_environment()
        self.config = bb.tinfoil.TinfoilConfig(parse_only=True)
        self.cooker = bb.cooker.BBCooker(self.config, self.register_idle_function,
                                         initialenv)
        self.config_data = self.cooker.configuration.data
        bb.providers.logger.setLevel(logging.ERROR)
        bb.taskdata.logger.setLevel(logging.CRITICAL)
        self.cooker_data = None
        self.taskdata = None

        self.localdata = bb.data.createCopy(self.config_data)
        self.localdata.finalize()
        # TODO: why isn't expandKeys a method of DataSmart?
        bb.data.expandKeys(self.localdata)


    def prepare_taskdata(self, provided=None, rprovided=None):
        self.cache_data = self.cooker.status
        if self.taskdata is None:
            self.taskdata = bb.taskdata.TaskData(abort=False)

        if provided:
            self.add_provided(provided)

        if rprovided:
            self.add_rprovided(rprovided)

    def add_rprovided(self, rprovided):
        for item in rprovided:
            self.taskdata.add_rprovider(self.localdata, self.cache_data, item)

        self.taskdata.add_unresolved(self.localdata, self.cache_data)

    def add_provided(self, provided):
        if 'world' in provided:
            if not self.cache_data.world_target:
                self.cooker.buildWorldTargetList()
            provided.remove('world')
            provided.extend(self.cache_data.world_target)

        if 'universe' in provided:
            provided.remove('universe')
            provided.extend(self.cache_data.universe_target)

        for item in provided:
            self.taskdata.add_provider(self.localdata, self.cache_data, item)

        self.taskdata.add_unresolved(self.localdata, self.cache_data)

    def rec_get_dependees(self, targetid, depth=0, seen=None):
        if seen is None:
            seen = set()

        for dependee_fnid, dependee_id in self.get_dependees(targetid, seen):
            yield dependee_id, depth

            for _id, _depth in self.rec_get_dependees(dependee_id, depth+1, seen):
                yield _id, _depth

    def get_dependees(self, targetid, seen):
        dep_fnids = self.taskdata.get_dependees(targetid)
        for dep_fnid in dep_fnids:
            if dep_fnid in seen:
                continue
            seen.add(dep_fnid)
            for target in self.taskdata.build_targets:
                if dep_fnid in self.taskdata.build_targets[target]:
                    yield dep_fnid, target

    def get_buildid(self, target):
        if not self.taskdata.have_build_target(target):
            reasons = self.taskdata.get_reasons(target)
            if reasons:
                self.logger.error("No buildable '%s' recipe found:\n%s", target, "\n".join(reasons))
            else:
                self.logger.error("No '%s' recipe found", target)
            return
        else:
            return self.taskdata.getbuild_id(target)

    def provide_to_fn(self, provide):
        """Return the preferred recipe for the specified provide"""
        filenames = self.cooker.status.providers[provide]
        eligible, foundUnique = bb.providers.filterProviders(filenames, provide, self.localdata)
        return eligible[0]

    def build_target_to_fn(self, target):
        """Given a target, prepare taskdata and return a filename"""
        self.prepare_taskdata([target])
        targetid = self.get_buildid(target)
        if targetid is None:
            return
        fnid = self.taskdata.build_targets[targetid][0]
        fn = self.taskdata.fn_index[fnid]
        return fn

    def parse_recipe_file(self, recipe_filename):
        """Given a recipe filename, do a full parse of it"""
        appends = self.cooker.get_file_appends(recipe_filename)
        try:
            recipe_data = bb.cache.Cache.loadDataFull(recipe_filename,
                                                      appends,
                                                      self.config_data)
        except Exception:
            raise
        return recipe_data

    def parse_metadata(self, recipe=None):
        """Return metadata, either global or for a particular recipe"""
        if recipe:
            self.prepare_taskdata([recipe])
            filename = self.build_target_to_fn(recipe)
            return self.parse_recipe_file(filename)
        else:
            return self.localdata


class CompleteParser(argparse.ArgumentParser):
    """Argument parser which handles '--complete' for completions"""
    def __init__(self, *args, **kwargs):
        self.complete_parser = argparse.ArgumentParser(add_help=False)
        self.complete_parser.add_argument('--complete', action='store_true')
        super(CompleteParser, self).__init__(*args, **kwargs)

    def parse_args(self, args=None, namespace=None):
        parsed, remaining = self.complete_parser.parse_known_args(args)
        if parsed.complete:
            for action in self._actions:
                for string in action.option_strings:
                    print(string)
        else:
            return super(CompleteParser, self).parse_args(remaining, namespace)


def iter_uniq(iterable):
    """Yield unique elements of an iterable"""
    seen = set()
    for i in iterable:
        if i not in seen:
            seen.add(i)
            yield i


def setup_log_handler(logger, output=sys.stderr):
    log_format = bb.msg.BBLogFormatter("%(levelname)s: %(message)s")
    if output.isatty():
        log_format.enable_color()
    handler = logging.StreamHandler(output)
    handler.setFormatter(log_format)

    bb.msg.addDefaultlogFilter(handler)
    logger.addHandler(handler)
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
