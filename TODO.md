General
-------

Some of the functionality implemented in this tool could well be shifted into
bitbake as new commands in command.py. I don't think adding commands like
'search' there would probably be a good idea, as that includes elements of the
UI, conceptually (technically, so do the 'show' commands, and arguably those
should go away), but adding commands which return useful information from
taskdata and the cooker would be of use.


Subcommands
-----------

- `show`

    - Add the ability to show the information collected by the variable
      tracking support which now exists in bitbake, both the inclusion history
      and the information about how and where variables were defined. This is
      necessary for feature parity with `bitbake -e`.

- `search`

  This command will let the user search for something they can build. It
  will handle both recipes and packages, and will check both `PROVIDES`
  and `RPROVIDES`. This should be able to support multiple modes of operation:
  exact match, substring, wildcards, regex.

- `edit`

  - Add the ability to cross over into the package namespace when/if
    appropriate, in case the user doesn't actually know the recipe that
    provides what they want to edit. Add an argument to specify it explicitly,
    also, and show a warning message if automatically crossing namespaces.

- `showprovides`

  This command will show what a given target provides. This will include `PN`,
  `PROVIDES`, `PACKAGES`, and `RPROVIDES`. This will essentially be
  a convenience wrapper around the `show` subcommand. By default, its
  command-line argument is a target/provide, much like the other sub-commands,
  but this could potentially be confusing in certain cases (as one example,
  `bb showprovides eglibc` could show the provides of
  `external-sourcery-toolchain` rather than the exact match recipe `eglibc`).
  Given this, it should display a warning whenever it crosses this boundary,
  and there should be a command-line option to request an exact match with
  a recipe name (and when using that argument, it should warn if this recipe
  isn't the current preferred provider for a target of that name). We may want
  to follow this pattern for the other recipes with a similar interface, but
  it's most confusing for this one, as it's entire purpose is to show the
  provides, not to follow them.

- `showdepends`

  This command will show detailed information on the dependencies of
  a recipe, of all forms. Task dependencies can be shown, but as this is
  a less common need, they will be shown via a command-line option, rather
  than by default.

- `whatdepends`

  This command will act as an opposite to `showdepends`, showing all the
  same information, but in reverse, showing what depends on something,
  rather than what something depends on. Its syntax, behavior, and
  command-line options will all mirror `showdepends`. While this command
  does exist currently, it will need to be reworked.

- `showversions`

  This command will act as an enhanced `bitbake -s`. It will show available
  versions of recipes, either for a specified target alone, for all recipes,
  or limited to a particular scope of recipes (e.g. 'what we build for
  core-image-base'). The current preferred version and 'latest version'
  (according to bitbake) will be identified as such.

- `build` or `bake`

  This command will spawn a bitbake UI and initiate a bitbake build. It
  will support specifying either build time or run time targets, unlike
  the current bitbake command-line interface.

  - Add a '-r' argument which specifies that the targets specified are in
    the recipe namespace.
  - Add a '-p' argument which specifies that the targets specified are in
    the package namespace.
  - Enhance the default behavior to assume neither namespace, check both,
    and either error or prompt (or perhaps both, depending on whether
    a non-interactive argument is specified) in cases of ambiguity.

- `inspectvariable`

  This command will essentially be an enhanced, more user friendly (but
  potentially less scriptable) form of the `show` command. Ideally, it would
  attempt to distinguish usage of a variable from a class or config metadata
  vs usage by actual recipe content, and indicate this to the user, leveraging
  the variable tracking patches. In the long term, this could potentially
  replace the `show` command, and we could add a `dump` command for the more
  raw output with shell-like formatting.

    - What a variable is set to (and how/where)
    - What a variable is used for ('doc' flag)
    - What values are allowed ('type' and related flags)
    - What uses a variable (other variables, tasks, recipes)
    - Whether this variable is used in the current configuration (that is,
      walk the variable and task graphs down from BB_DEFAULT_TASK)

- Convenience subcommands for tasks (`clean`, `devshell`, etc.)

  This will be controlled via a configuration variable, which lists the
  tasks to make available in this manner (e.g. `BB_TASK_SUBCOMMANDS`).

- Layer subcommands, from bitbake-layers

  This one is uncertain, and needs consideration. We would also need to
  decide whether all the layer subcommands become direct bb sub-commands,
  or if we add a subcommand with its own subcommands.

- Post-build subcommands

  These commands will operate against data which was emitted by a build,
  rather than operating against the metadata alone. Areas to consider
  covering: buildstats, license manifest and package license information,
  buildhistory, pkgdata, `DEPLOY_DIR`

    - `compare-buildhistory`

      This command will simply be a convenience wrapper around the
      buildhistory-diff external tool.

    - `show-image-manifest`

      This command will show the emitted image license manifest. It will
      support showing it both in the existing format and in CSV form.

    - `filesearch`

      This command will act like the `search` command, but will instead
      operate against the output of a build to search for a path in
      a filesystem, both against the built images and via the built packages.


Considering
-----------

- Wildcards for `show` via fnmatch
- Add additional types of variable filtering for `show`.

    - Filter out 'unused' variables (not used by any tasks for the recipe).
    - Potentially improve flexibility regarding dependency traversal (e.g.
      show all dependencies rather than just function dependencies).
    - Consider adding an argument to disable variable expansion. This adds
      complexity but gives you output not unlike you would see in a config
      file or recipe, which has a certain amount of value, and file paths in
      particular are awfully unwieldy when expanded. A prototype of this is on
      a branch ('unexpanded').

- target vs pn arguments. In some cases, the user may be expecting that their
  input be interpreted more directly, as a recipe name, rather than as
  a target. For example, it could be unintuitive that 'bb showprovides eglibc'
  when using an external toolchain may actually show the provides of the
  external-sourcery-toolchain recipe.

    - For each command, determine which is most appropriate as a default
    - Consider adding an argument to change how the primary argument is
      interpreted
    - Add messages, possibly verbose/debug ones, which indicate how the input
      is mapped to an actual recipe file, or what recipe file is being used

- Show what the user can set in PACKAGECONFIG, either generally or per recipe
- Consider analyzing `base_contains()` calls to determine possible values for
  the various FEATURES and PACKAGECONFIG variables


Requirements from others
------------------------

- Variable inspection

    - what the variable is for
    - what recipes use it
    - what values are permitted
    - what variables it uses
    - whether the variable is used in the current configuration

- Find recipe

    - Text search of recipe name/summary/description
    - Text search of 'files contributed to the package or images'

        - Not doable before a build, only after

    - Package name
    - File location on target system

        - Not doable before a build, only after

- Inspect recipe

    - Runtime dependencies
    - Build dependencies
    - Reverse build and runtime dependencies
    - Why this recipe is being included in an image
    - Alternate versions
    - Bbappends
    - Layer overrides
