# SPDX-FileCopyrightText: 2017 Florent Rougon
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileComment: Helper script for rebuilding FGData-resources.[ch]xx

# Only standard modules so that distributors can easily run this script, in
# case they want to recreate FGData-resources.[ch]xx from source.
import argparse
import json
import locale
import logging
import os
import subprocess
import sys

PROGNAME = os.path.basename(sys.argv[0])
CONFIG_FILE = os.path.join(os.path.expanduser('~'),
                           ".fgmeta",
                           PROGNAME + ".json")

# chLevel: console handler level
def setupLogging(level=logging.NOTSET, chLevel=None):
    global logger

    if chLevel is None:
        chLevel = level

    logger = logging.getLogger(__name__)
    # Effective level for all child loggers with NOTSET level
    logger.setLevel(level)
    # Create console handler and set its level
    ch = logging.StreamHandler() # Uses sys.stderr by default
    ch.setLevel(chLevel)  # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
    # Logger name with :%(name)s... many other things available, including
    # %(levelname)s
    formatter = logging.Formatter("{}: %(message)s".format(PROGNAME))
    # Add formatter to ch
    ch.setFormatter(formatter)
    # Add ch to logger
    logger.addHandler(ch)


# Modifies 'params' in-place
def loadCfgFileSection(params, jsonTree, title, items):
    # NB: !!! each item is subject to os.path.expanduser() !!!
    try:
        section = jsonTree[title]
    except KeyError:
        pass
    else:
        for name in items:
            try:
                path = section[name]
            except KeyError:
                pass
            else:
                setattr(params, name.lower(), os.path.expanduser(path))


# Modifies 'params' in-place
def loadConfigFile(params):
    if not os.path.isfile(CONFIG_FILE):
        return

    # The log level is set too late for this one -> commented out
    # logger.info("Loading config file {}...".format(CONFIG_FILE))

    with open(CONFIG_FILE, "r", encoding="utf-8") as cfgFile:
        tree = json.load(cfgFile)

    loadCfgFileSection(params, tree, "repositories", ("FlightGear", "FGData"))
    loadCfgFileSection(params, tree, "executables", ("fgrcc",))


def processCommandLine(params):
    parser = argparse.ArgumentParser(
        usage="""\
%(prog)s [OPTION ...]
Rebuild FGData embedded resources for FlightGear.""",
        description="""\

Use fgrcc with FGData-resources.xml and the corresponding files in FGData to
(re)create the FGData-resources.[ch]xx files used in the FlightGear build. The
existing files in the FlightGear repository are always overwritten
(FGData-resources.[ch]xx in <FlightGear-repo>/src/EmbeddedResources).

This is a dumb script that simply calls fgrcc with appropriate parameters. In
order to save some typing, you may want to use a configuration file like this
(~/.fgmeta/%(prog)s.json):

{"repositories": {"FlightGear": "~/flightgear/src/flightgear",
                  "FGData":     "~/flightgear/src/fgdata"},
 "executables": {"fgrcc":
                 "~/flightgear/src/build-fg/src/EmbeddedResources/fgrcc"
                }
}""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # I want --help but not -h (it might be useful for something else)
        add_help=False)

    parser.add_argument('--flightgear', action='store', help="""\
      Path to the FlightGear repository""")
    parser.add_argument('--fgdata', action='store', help="""\
      Path to the FGData repository""")
    parser.add_argument('--fgrcc', action='store', help="""\
      Path to the fgrcc executable""")
    parser.add_argument('--log-level', action='store',
                        choices=("debug", "info", "warning", "error",
                                 "critical"),
                        default=None, help="""Set the log level""")
    parser.add_argument('--help', action="help",
                        help="display this message and exit")

    parser.parse_args(namespace=params)

    # Don't use the 'default' argparse mechanism for this, in order to allow
    # the config file to set the log level in a meaningful way if we want (not
    # implemented at the time of this writing).
    if params.log_level is not None:
        logger.setLevel(getattr(sys.modules["logging"],
                                params.log_level.upper()))


def main():
    locale.setlocale(locale.LC_ALL, '')
    setupLogging(level=logging.INFO) # may be overridden by options

    params = argparse.Namespace()
    loadConfigFile(params)      # could set the log level
    processCommandLine(params)

    if (params.flightgear is None or params.fgdata is None or
        params.fgrcc is None):
        logger.error(
            "--flightgear, --fgdata and --fgrcc must all be specified (they "
            "may be set in the config file; use --help for more info)")
        sys.exit(1)

    resDir = os.path.join(params.flightgear, "src", "EmbeddedResources")
    inputXMLFile = os.path.join(resDir, "FGData-resources.xml")
    cxxFile = os.path.join(resDir, "FGData-resources.cxx")
    hxxFile = os.path.join(resDir, "FGData-resources.hxx")
    args = [params.fgrcc,
            "--root={}".format(params.fgdata),
            "--output-cpp-file={}".format(cxxFile),
            "--init-func-name=initFGDataEmbeddedResources",
            "--output-header-file={}".format(hxxFile),
            "--output-header-identifier=_FG_FGDATA_EMBEDDED_RESOURCES",
            inputXMLFile]

    # encoding="utf-8" requires Python >= 3.6 -> will add it later
    # (it's not really needed, as we don't process the output)
    subprocess.run(args, check=True)

    return 0
