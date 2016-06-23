"""Code common to the various python bb commands"""

import argparse
import contextlib
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
from bb.cookerdata import CookerConfiguration, ConfigParameters


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

        self.config = self.config = CookerConfiguration()
        configparams = bb.tinfoil.TinfoilConfigParameters(parse_only=True)
        self.config.setConfigParameters(configparams)
        self.config.setServerRegIdleCallback(self.register_idle_function)
        self.cooker = bb.cooker.BBCooker(self.config)
        self.config_data = self.cooker.data
        bb.providers.logger.setLevel(logging.ERROR)
        bb.taskdata.logger.setLevel(logging.CRITICAL)
        self.cooker_data = None
        self.taskdata = None

        self.localdata = bb.data.createCopy(self.config_data)
        self.localdata.finalize()
        # TODO: why isn't expandKeys a method of DataSmart?
        bb.data.expandKeys(self.localdata)


    def prepare_taskdata(self, provided=None, rprovided=None):
        self.cache_data = self.cooker.recipecache
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
        provided = list(provided)
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

    def rec_get_all_dependees(self, fn, depth=0, seen=None):
        if seen is None:
            seen = set()

        all_dependees = self.get_all_dependees(fn) or []
        for dependee in all_dependees:
            yield dependee, depth

            if dependee in seen:
                continue
            seen.add(dependee)
            for _dependee, _depth in self.rec_get_all_dependees(dependee, depth+1, seen):
                yield _dependee, _depth

    def get_all_dependees(self, fn):
        all_dependees = set()

        for target, fns in self.taskdata.build_targets.items():
            if fns and fns[0] == fn:
                all_dependees |= set(self.taskdata.get_dependees(target))

        for rtarget, fns in self.taskdata.run_targets.items():
            if fns and fns[0] == fn:
                all_dependees |= set(self.taskdata.get_rdependees(rtarget))

        if fn in all_dependees:
            all_dependees.remove(fn)

        return all_dependees

    def rec_get_dependees(self, fn, depth=0, seen=None):
        if seen is None:
            seen = set()

        dependees = self.get_dependees(fn) or []
        for dependee in dependees:
            yield dependee, depth

            if dependee in seen:
                continue
            seen.add(dependee)
            for _dependee, _depth in self.rec_get_dependees(dependee, depth+1, seen):
                yield _dependee, _depth

    def get_dependees(self, fn):
        dependees = set()
        for target, fns in self.taskdata.build_targets.items():
            if fns and fns[0] == fn:
                dependees |= set(self.taskdata.get_dependees(target))
        return dependees

    def rec_get_rdependees(self, fn, depth=0, seen=None):
        if seen is None:
            seen = set()

        dependees = self.get_rdependees(fn) or []
        for dependee in dependees:
            yield dependee, depth
            if dependee in seen:
                continue
            seen.add(dependee)

            for _dependee, _depth in self.rec_get_rdependees(dependee, depth+1, seen):
                yield _dependee, _depth

    def get_rdependees(self, fn):
        dependees = set()
        for target, fns in self.taskdata.run_targets.items():
            if fns and fns[0] == fn:
                dependees |= set(self.taskdata.get_rdependees(target))
        return dependees

    def get_filename(self, target):
        if not self.taskdata.have_build_target(target):
            if target in self.cooker.recipecache.ignored_dependencies:
                return

            reasons = self.taskdata.get_reasons(target)
            if reasons:
                self.logger.error("No buildable '%s' recipe found:\n%s", target, "\n".join(reasons))
            else:
                self.logger.error("No '%s' recipe found", target)
            return
        else:
            return self.taskdata.build_targets[target][0]

    def target_filenames(self):
        """Return the filenames of all of taskdata's targets"""
        filenames = set()

        for target in self.taskdata.build_targets:
            target_fns = self.taskdata.build_targets[target]
            if target_fns:
                filenames.add(target_fns[0])

        for target in self.taskdata.run_targets:
            target_fns = self.taskdata.run_targets[target]
            if target_fns:
                filenames.add(target_fns[0])

        return filenames

    def all_filenames(self):
        return self.cooker.recipecache.file_checksums.keys()

    def all_preferred_filenames(self):
        """Return all the recipes we have cached, filtered by providers.

        Unlike target_filenames, this doesn't operate against taskdata.
        """
        filenames = set()
        excluded = set()
        for provide, fns in self.cooker.recipecache.providers.items():
            eligible, foundUnique = bb.providers.filterProviders(fns, provide,
                                                                 self.localdata,
                                                                 self.cooker.recipecache)
            preferred = eligible[0]
            if len(fns) > 1:
                # Excluding non-preferred providers in multiple-provider
                # situations.
                for fn in fns:
                    if fn != preferred:
                        excluded.add(fn)
            filenames.add(preferred)

        filenames -= excluded
        return filenames

    def provide_to_fn(self, provide):
        """Return the preferred recipe for the specified provide"""
        filenames = self.cooker.recipecache.providers[provide]
        eligible, foundUnique = bb.providers.filterProviders(filenames, provide, self.localdata)
        return eligible[0]

    def build_target_to_fn(self, target):
        """Given a target, prepare taskdata and return a filename"""
        self.prepare_taskdata([target])
        filename = self.get_filename(target)
        return filename

    def parse_recipe_file(self, recipe_filename):
        """Given a recipe filename, do a full parse of it"""
        appends = self.cooker.collection.get_file_appends(recipe_filename)
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


@contextlib.contextmanager
def status(message, outfile=sys.stderr):
    """Show the user what we're doing, and whether we succeed"""
    outfile.write('{0}..'.format(message))
    outfile.flush()
    try:
        yield
    except KeyboardInterrupt:
        outfile.write('.interrupted\n')
        raise
    except Terminate:
        outfile.write('.terminated\n')
        raise
    except BaseException:
        outfile.write('.failed\n')
        raise
    outfile.write('.done\n')


def setup_log_handler(logger, output=sys.stderr):
    log_format = bb.msg.BBLogFormatter("%(levelname)s: %(message)s")
    if output.isatty() and hasattr(log_format, 'enable_color'):
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
    except bb.BBHandledException:
        sys.exit(1)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
    except Terminate:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
