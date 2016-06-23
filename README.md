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

See the [Todo](TODO.md) list.


Usage
-----

    bb <command> [<args>]

    Some useful bb commands are:
       commands         List all bb commands
       contents         Show package contents
       edit             Edit bitbake recipes, included files, and bbappends
       list             List available recipes / provides
       log              Show bitbake logs
       search           Search for bitbake recipes or packages
       search-packages  Search for bitbake packages
       search-recipes   Search for bitbake recipes
       shell            Enter an interactive mode shell (repl)
       show             Show bitbake metadata (global or recipe)
       whatdepends      Show what depends on the specified target


    bb contents [-h] recipe

    positional arguments:
      recipe      recipe name

    optional arguments:
      -h, --help  show this help message and exit


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


    bb list [-h] [-S SCOPE]

    optional arguments:
      -h, --help            show this help message and exit
      -S SCOPE, --scope SCOPE
                            specify a target scope (rather than all recipes. ex.
                            -S core-image-base)


    bb log [-h] [recipe] [task]

    positional arguments:
      recipe      recipe name
      task        task name

    optional arguments:
      -h, --help  show this help message and exit


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

    bb-whatdepends [-h] [-r] [-B | -R] target [recipes [recipes ...]]

    positional arguments:
      target
      recipes               recipes to check for dependencies on target (default:
                            universe)

    optional arguments:
      -h, --help            show this help message and exit
      -r, --recursive       operate recursively, with indent reflecting depth
      -B, --build-time-only
                            show build-time dependencies only
      -R, --run-time-only   show run-time dependencies only


Examples
--------

    $ bb contents bash
    bash
    /bin/bash
    /usr/bin/bashbug

    bash-dbg
    /bin/.debug/bash
    /usr/src/debug/bash/4.2-r6/bash-4.2/alias.c
    /usr/src/debug/bash/4.2-r6/bash-4.2/alias.h
    /usr/src/debug/bash/4.2-r6/bash-4.2/array.c
    /usr/src/debug/bash/4.2-r6/bash-4.2/array.h
    [.. output snipped ..]
    /usr/src/debug/bash/4.2-r6/bash-4.2/support/signames.c

    bash-dev

    bash-doc
    /usr/share/doc/bash.html
    /usr/share/doc/bashref.html
    /usr/share/info/bash.info
    /usr/share/man/man1/bash.1
    /usr/share/man/man1/bashbug.1

    bash-locale

    bash-staticdev

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

    $ bb list -S pseudo-native
    util-linux-native
    libtool-native
    gettext-minimal-native
    lzo-native
    m4-native
    sqlite3-native
    zlib-native
    ncurses-native
    automake-native
    pseudo-native
      virtual/fakeroot-native
    quilt-native
    autoconf-native
    gnu-config-native
    pkgconfig-native

    $ bb search bash
    bash
    glib-2.0:
      Packages:
        glib-2.0-bash-completion
    nativesdk-glib-2.0:
      Packages:
        nativesdk-glib-2.0-bash-completion
    nativesdk-bash
    dbus-glib:
      Packages:
        dbus-glib-bash-completion

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
    # Determine what pulls ncurses into a build of core-image-minimal

    $ bb whatdepends -B ncurses core-image-minimal
    Parsing recipes..done.
    Preparing task data...done
    readline
    util-linux
    dpkg
    bash
    slang
    attr

    $ bb whatdepends -r -B ncurses core-image-minimal
    Parsing recipes..done.
    Preparing task data...done
    readline
      systemd
        dbus
      gawk
    util-linux
      systemd..
      e2fsprogs
    dpkg
    bash
    slang
      libnewt
        chkconfig
    attr
      acl
        systemd..
      libcap
        systemd..
