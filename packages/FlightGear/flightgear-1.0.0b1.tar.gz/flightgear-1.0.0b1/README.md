# Python Tooling for Flightgear Development

This package contains Python modules and scripts used for development of the
[FlightGear](https://www.flightgear.org/) flight simulator. It is built from
an official FlightGear repository called
[fgmeta-python](https://gitlab.com/flightgear/fgmeta-python), uploaded by
FlightGear developers but does not contain the flight simulator itself. If you
are interested in the latter, please visit its [home
page](https://www.flightgear.org/).

This package is mostly of interest to FlightGear developers and
contributors. For instance:

- the internationalization scripts it ships can be useful for aircraft and
  add-on developers that want to add translations to their work;
- catalog scripts for preparing aircraft catalogs;
- `git-date.py` for easily finding commits close to a given date in
  several FlightGear repositories;
- `fg-validate-PropertyList` for checking XML files in PropertyList
  format;
- etc.

There is nothing special about the packaging. The following instructions
are for people familiar with FlightGear but not necessarily with `pip` and
Python `venv`s.

## Quick Installation Instructions

This is for people who want to use the latest state of the code:

    git clone https://gitlab.com/flightgear/fgmeta-python.git
    cd fgmeta-python
    python3 -m venv .venv
    .venv/bin/pip install -e .

If the last command shows an error, this is likely due to outdated
packages. In such a case, run the following:

    .venv/bin/pip install -U build pip setuptools

then redo the `pip install` step.

Scripts declared in `pyproject.toml` have been created by that step in the
`.venv/bin` directory. Updates are obtained by updating the
`fgmeta-python` clone (`git pull`). If your Python installation is updated
(version change) or if you move the directories in the above commands
elsewhere, delete the `.venv` directory, recreate the venv and redo the
`pip install` step.

## Long Installation Instructions

Normal installation of the package is done with the Python package
installer [pip](https://pip.pypa.io/).

### A Word on `pip`

Telling people to just `pip install ...` is quite common but reality is a
bit more complex. If you installed Python without a package manager, this
should be just fine (on Windows, you may have to use something like
`py -m pip install ...` if `pip` is not in your `PATH` but the Python
Launcher for Windows `py` is).

The main case where straight `pip install ...` commands are not
appropriate is if your Python installation (at large, including Python
packages that don't belong to the Python standard library) is managed by a
package manager such as `dpkg` or `rpm`. This is typically the case on
Linux distributions (unless you are using a Python you compiled yourself).
In that case, permissions would require you to run `pip` as root, which
would modify files and directories in places that are normally under
complete control of the package manager, “behind its back”. That would
likely lead to problems with your Python installation.

For this reason, in such cases where the whole Python installation is
managed by a package manager, we advise you to perform the installation
inside a `venv`—which is very quick and easy, see below.

### Installation Inside a Venv

According to the above, you may possibly skip this section.

A Python [venv](https://docs.python.org/3/library/venv.html) (a kind of
virtual environment) is a directory tree that is linked to a Python
installation and can be used to install packages in a way that doesn't
alter the Python installation itself nor other venvs. Venvs are quick and
easy to create. You can store them where you see fit. They are convenient
for installing Python packages without messing with the rest of the
system. Another strong point of venvs (probably the initial motivation) is
that using several ones, you can install Python packages that have
incompatible dependencies (each in its own venv).

Installation of Python packages inside a venv is very easy:

1. First, you create a venv in some some directory `⟨dir⟩` of your choice:

        python3 -m venv ⟨dir⟩

   When using per-project venvs, people often choose the `.venv`
   subdirectory of the project root.

2. Then you use the `pip` executable from the venv, for instance:

        ⟨dir⟩/bin/pip install flightgear

After these commands, `⟨dir⟩/bin` contains all scripts declared as such in
the installed package. Besides, `⟨dir⟩/bin/python` is a Python interpreter
pretty much like the one from the base installation, except it has access
to all modules belonging to packages installed in the venv (not to
third-party modules from the underlying Python installation, unless the
venv was created with option `--system-site-packages`).

Uninstalling the package would be done with
`⟨dir⟩/bin/pip uninstall flightgear`, etc. If you have many commands to run
from the venv and don't want to write `⟨dir⟩/bin/` over and over, you may
want to read about `activate` in a venv tutorial or in the
[documentation](https://docs.python.org/3/library/venv.html#how-venvs-work).

In the rest of this documentation, whenever you see a `pip` command, you
should read it as `⟨dir⟩/bin/pip` if you chose to work in a venv whose
base directory is `⟨dir⟩`.

After installing a package in a venv, if you want to have the installed
scripts in your `PATH`, there are basically two ways:

- create symbolic links from a directory that is in your `PATH`;

- add `⟨dir⟩/bin` to your `PATH`; this can be convenient if you use a
  “main venv” but before doing so, please note that `⟨dir⟩/bin` normally
  contains `python`, `python3` and `pip` executables that would then also
  be in your `PATH`—your call.

If the underlying Python installation for a venv is updated (as in,
upgraded from Python X.Y to Python X.Y+1) or if the venv directory is
moved elsewhere (which includes one of its parents being moved or
renamed), you'll have to recreate the venv: simply delete the `⟨dir⟩`
directory and redo the preceding steps (if you use a “main venv” with a
bunch of packages, having a script to recreate it is convenient).

### Installing Using `pip`

The Python distribution package this document belongs to is called
`flightgear` (case doesn't matter) and normal installations should be done
with [pip](https://pip.pypa.io/), for instance:

    pip install flightgear

This would install the latest release. It is also possible to install
using the URL of a Git repository:

    pip install git+https://gitlab.com/flightgear/fgmeta-python.git@next

(here, `@next` could be removed as `next` is the default branch). Another
interesting possibility is to install from a local clone of the
repository. Assuming you have one in directory `/path/to/fgmeta-python`,
you could install the package with:

    pip install /path/to/fgmeta-python

(This may show an error due to outdated packages; in this case, run
`pip install -U build pip setuptools` and retry.)

Finally, given the target audience of this package and since releases may
not be that frequent, an interesting variation is to add option `-e`, like
so:

    pip install -e /path/to/fgmeta-python

This performs the installation in *editable mode*. This has the
consequence that updates to Python files that belong to the package under
`/path/to/fgmeta-python` are immediately visible to the Python
installation or venv in which you installed the package. This is perfect
for developing the package, or if you want to get the latest state of the
code by simply updating the `fgmeta-python` repository.

Installations done with `pip` perform two things:

- they install Python modules so that Python can import them (here, the
  `flightgear` import package would be in Python's `sys.path`);

- they create scripts in the `bin` subdirectory of the Python installation
  or venv: this is the case for scripts declared as such in the
  `pyproject.toml` file.

Another possibility that doesn't use `pip`, explained below in more
detail, is to modify `PYTHONPATH` yourself; however, this only covers the
first item of the previous list.

### Upgrading Using `pip`

If you installed a release of the package, upgrading it can be done with
the following command, where option `-U` is a shorthand for `--upgrade`:

    pip install -U flightgear

If, on the other hand, you installed in editable mode from a clone of the
`fgmeta-python` repository, simply update the repository (for changes like
installed scripts or dependencies being added to or removed from
`pyproject.toml`, you'll need to redo the `pip install -e` step too).

### Uninstalling Using `pip`

Uninstallation of the package using `pip` can be done with:

    pip uninstall flightgear

(yes, even if you installed with `pip install -e /path/to/fgmeta-python`).

### Partial Installation Without `pip`

This section describes a partial installation method. It may be helpful in
some cases but isn't equivalent to normal installation with `pip`.

This method consists in modifying the `sys.path` value seen by the Python
interpreter, either by adding an element (directory) to the `PYTHONPATH`
environment variable or by creating a `.pth` file. This has a few
drawbacks as compared to the installation with `pip`:

- it won't warn you if your Python version is unsuitable for running the
  code contained in the package;

- it won't warn you if you don't have required dependencies (whereas `pip`
  would automatically install them for you);

- it won't create the scripts declared in the `pyproject.toml` file
  (however, they can currently be invoked as Python modules).

So, how does it work? For instance, you can use something like the
following in your shell setup:

    export PYTHONPATH="/path/to/fgmeta-python/src"

This example uses Bourne-style shell syntax; adjust for your particular
shell. Several directories may be added this way using a colon separator
on Unix or macOS (`:`), and a semicolon on Windows (`;`).

An alternative to setting `PYTHONPATH` is to add `.pth` files in special
directories of your Python installation(s). For instance, you could create
a file, say, `fgmeta-python.pth`, containing a single line (with no space
at the beginning):

    /path/to/fgmeta-python/src

If you want the modules present in `/path/to/fgmeta-python/src` to be
accessible to a particular Python interpreter (say, a Python 3.13), simply
put the `.pth` file in
`/path/to/python-install-dir/lib/python3.13/site-packages/`. For the
system Python interpreters on Debian, you can put the `.pth` file in, e.g,
`/usr/local/lib/python3.13/dist-packages/`. You may put several lines in a
`.pth` file in case you want to add several paths to the Python
interpreter's `sys.path`.

Note that if you use this method, you won't have the scripts declared in
the `pyproject.toml` file that `pip` would create in normal installations.

## The Scripts

Regardless of the method chosen for installation, the Python modules from
`fgmeta-python/src` should be available to the chosen Python interpreter
(if you installed in a venv whose base directory is `⟨dir⟩`, the
interpreter is `⟨dir⟩/bin/python`). What about scripts that rely on these
modules?

Normally, scripts are declared in the `pyproject.toml` file and
automatically created by the `pip install` command in the `bin`
subdirectory of the Python installation or venv. These scripts work out of
the box, can be invoked directly.

There are a few other scripts, like currently `catalog/update-catalog.py`,
which exist as files in the repository rather than being declared in
`pyproject.toml`. As long as the required modules are available to the
Python interpreter in use (i.e., accessible via its `sys.path`), such
scripts will work too. For instance, if you installed the package in a
`⟨dir⟩` venv, `⟨dir⟩/bin/python` is a Python interpreter that can see the
modules, therefore `⟨dir⟩/bin/python some-script` would be a suitable
command for running `some-script`.

The only remaining problem is therefore the following: if you used the
partial installation method, you don't have the scripts that `pip install`
would have normally created for you. However, these scripts are currently
available as Python modules. For instance, the file
`src/flightgear/meta/scripts/i18n/fg_extract_translatable_strings.py`
can be imported as a Python module. Example: the command

    python3 -m flightgear.meta.scripts.i18n.fg_extract_translatable_strings --help

is equivalent to

    fg-extract-translatable-strings --help

This might be useful for one-off uses of the scripts where one doesn't
necessarily want to run `pip`: one could set `PYTHONPATH` and run the
desired module(s) as shown above (the obvious alternative being to create
a temporary venv and use the normal installation method).

## Running the Unit Tests

Once the modules from this package are visible to Python (regardless of
the method used), the unit tests can be run with the following command
from the root of the `fgmeta-python` repository:

    python3 -m unittest

(this is equivalent to `python3 -m unittest discover`; for more details,
see `tests/README.md`).

## Building the Package

In case you want to build the package, you can run the following command
from the root of the `fgmeta-python` repository:

    python3 -m build

This requires the Python `build` tool as explained in the
[Python Packaging User Guide](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#packaging-your-project).
