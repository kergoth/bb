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


Usage
-----

    bb <command> [<args>]

    Some useful bb commands are:
       commands     List all bb commands
       shell        Enter an interactive mode shell (repl)
       show         Show bitbake metadata (global or recipe)
       whatdepends  Show what depends on the specified target


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
