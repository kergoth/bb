bb
==

Experimentation with a subcommand-based bitbake UI (initially just inspection tools)


Known Issues
------------

- Provider and pn aren't always correctly mapped back and forth.

    - As one concrete example, whatdepends only reports what explicitly lists
      this exact element in its DEPENDS, it doesn't traverse the providers to
      find indirect dependencies at this time.


To Install
----------

Run bin/bb init for installation instructions.


Future plans
------------

See [Todo][TODO.md].


Usage
-----

    bb <command> [<args>]

    Some useful bb commands are:
       commands     List all bb commands
       edit         edit bitbake recipes, included files, and bbappends
       search       search for bitbake recipes/targets
       shell        Enter an interactive mode shell (repl)
       show         Show bitbake metadata (global or recipe)
       whatdepends  Show what depends on the specified target


    bb edit [-h] [-e EDITOR] [-p] [-r] targets [targets ...]

    positional arguments:
      targets             targets to edit

    optional arguments:
      -h, --help          show this help message and exit
      -e EDITOR, --editor EDITOR
                          specify the editor to run (default: $VISUAL or $EDITOR
                          or vi)
      -p, --prompt        rather than opening all the files at once, prompt the
                          user
      -r, --just-recipes  only edit recipes and appends, not included files


    bb search [-h] [-i] [-S SCOPE] [-s | -e | -r | -w] pattern

    positional arguments:
      pattern               pattern to search for

    optional arguments:
      -h, --help            show this help message and exit
      -i, --ignore-case     perform a case insensistive search
      -S SCOPE, --scope SCOPE
                            specify a target scope (rather than all recipes. ex.
                            -S core-image-base)
      -s, --substring       perform a substring search (default)
      -e, --exact           look for an exact string match
      -r, --regex           perform a regex search
      -w, --wildcard        perform a glob/wildcard search


    bb show [-h] [-d] [-f] [-r RECIPE] [variables [variables ...]]

    positional arguments:
      variables             variables to show (default: all variables)

    optional arguments:
      -h, --help            show this help message and exit
      -d, --dependencies    also show functions the vars depend on
      -f, --flags           also show flags
      -r RECIPE, --recipe RECIPE
                            operate against this recipe

    bb whatdepends [-h] [-r] target [recipes [recipes ...]]

    positional arguments:
      target
      recipes          recipes to check for dependencies on target (default:
                       universe)

    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  operate recursively, with indent reflecting depth


Examples
--------

    $ bb edit busybox
    Parsing recipes..done.
    NOTE: Editing these files:
    /scratch/mel7/bb/poky/meta/recipes-core/busybox/busybox_1.20.2.bb
    /scratch/mel7/bb/poky/meta/recipes-core/busybox/busybox.inc
    /scratch/mel7/bb/meta-oe/meta-oe/recipes-core/busybox/busybox_1.20.2.bbappend
    /scratch/mel7/bb/poky/meta-yocto/recipes-core/busybox/busybox_1.20.2.bbappend
    /scratch/mel7/bb/meta-mentor/recipes/busybox/busybox_1.20.2.bbappend

    # vim spawned here
    5 files to edit

    $ bb search -S core-image-sato ncurses
    ncurses:
      Matches in the build target namespace:
        ncurses
        ncurses-5.9
        ncurses-5.9-r13.1
      Matches in the runtime namespace:
        ^ncurses-locale-.*
    ncurses-native:
      Matches in the build target namespace:
        ncurses-native
        ncurses-native-5.9
        ncurses-native-5.9-r13.1
      Matches in the runtime namespace:
        ncurses-native
    nativesdk-ncurses:
      Matches in the build target namespace:
        nativesdk-ncurses
        nativesdk-ncurses-5.9
        nativesdk-ncurses-5.9-r13.1
      Matches in the runtime namespace:
        ^nativesdk-ncurses-locale-.*

    # Determine what pulls ncurses into a build of core-image-minimal

    $ bb whatdepends ncurses core-image-minimal
    Parsing recipes..done.
    virtual/gettext
    virtual/libintl
    readline
    util-linux
    sqlite3
    attr

    # Show the reverse dependencies recursively. So, see what depends on attr
    # in a build of core-image-minmal, then what depends on the items that
    # depend on attr, etc.

    $ bb whatdepends -r attr core-image-minimal
    Parsing recipes..done.
    acl
    libcap
      avahi
      libgcrypt
        gtk+
          libglade

    $ bb show DISTRO MACHINE TUNE_ARCH TUNE_FEATURES
    # DISTRO="mel"
    # MACHINE="p4080ds"
    # TUNE_ARCH="${@bb.utils.contains("TUNE_FEATURES", "m32", "powerpc", "", d)}"
    TUNE_ARCH="powerpc"
    # TUNE_FEATURES="${TUNE_FEATURES_tune-${DEFAULTTUNE}}"
    TUNE_FEATURES="m32 fpu-hard ppce500mc"

    $ bb show -d -f COPYLEFT_RECIPE_TYPE
    # COPYLEFT_RECIPE_TYPE="${@copyleft_recipe_type(d)}"
    COPYLEFT_RECIPE_TYPE="target"
    COPYLEFT_RECIPE_TYPE[doc]="The "type" of the current recipe (e.g. target, native, cross)"
    def copyleft_recipe_type(d):
        for recipe_type in oe.data.typed_value('COPYLEFT_AVAILABLE_RECIPE_TYPES', d):
            if oe.utils.inherits(d, recipe_type):
                return recipe_type
        return 'target'

    $ bb show -r virtual/kernel PROVIDES
    Parsing recipes..done.
    PROVIDES="linux-qoriq-sdk-3.0.34 linux-qoriq-sdk-3.0.34-r9b linux-qoriq-sdk  virtual/kernel"
