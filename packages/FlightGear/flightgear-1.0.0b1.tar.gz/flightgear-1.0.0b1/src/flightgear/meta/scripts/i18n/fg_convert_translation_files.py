# SPDX-FileCopyrightText: 2017 Florent Rougon
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileComment: Extract translatable strings from XML files

"""Convert from pre-2017 format of FlightGear translation files."""

import argparse
import collections
import locale
import os
import sys

import flightgear.meta.logging
import flightgear.meta.i18n as fg_i18n


PROGNAME = os.path.basename(sys.argv[0])

# Only messages with severity >= info will be printed to the terminal (it's
# possible to also log all messages to a file regardless of their level, see
# the Logger class). Of course, there is also the standard logging module...
logger = flightgear.meta.logging.Logger(
    progname=PROGNAME,
    logLevel=flightgear.meta.logging.LogLevel.info,
    defaultOutputStream=sys.stderr)

debug = logger.debug
info = logger.info
notice = logger.notice
warning = logger.warning
error = logger.error
critical = logger.critical


# We could use Translation.__str__(): not as readable (for now) but more
# accurate on metadata
def printPlainText(l10nResPoolMgr, translations):
    """Print output suitable for a quick review (by the programmer)."""
    firstLang = True

    for langCode, (transl, nbWhitespacePbs) in translations.items():
        # 'transl' is a Translation instance
        if firstLang:
            firstLang = False
        else:
            print()

        print("-" * 78 + "\n" + langCode + "\n" + "-" * 78)
        print("\nNumber of leading and/or trailing whitespace problems: {}"
              .format(nbWhitespacePbs))

        for cat in transl:
            print("\nCategory: {cat}\n{underline}".format(
                cat=cat, underline="~"*(len("Category: ") + len(cat))))
            t = transl[cat]

            for tid, translUnit in sorted(t.items()):
                # - Using '{master!r}' and '{transl!r}' prints stuff such as
                #   \xa0 for nobreak spaces, which can lead to the erroneous
                #   conclusion that there was an encoding problem.
                # - Only printing the first target text here (no plural forms)
                print("\n{id}\n  '{sourceText}'\n  '{targetText}'"
                      .format(id=tid.id(), sourceText=translUnit.sourceText,
                              targetText=translUnit.targetTexts[0]))


def writeXliff(l10nResPoolMgr, translations):
    formatHandler = fg_i18n.XliffFormatHandler()

    for langCode, translData in translations.items():
        translation = translData.transl # Translation instance

        if params.output_dir is None:
            # Use default locations for the written xliff files
            l10nResPoolMgr.writeTranslation(formatHandler, translation)
        else:
            basename = "{}-{}.{}".format(
                formatHandler.defaultFileStem(langCode),
                langCode,
                formatHandler.standardExtension)
            filePath = os.path.join(params.output_dir, basename)
            formatHandler.writeTranslation(translation, filePath)


def processCommandLine():
    params = argparse.Namespace()

    parser = argparse.ArgumentParser(
        usage="""\
%(prog)s [OPTION ...] LANGUAGE_CODE...
Convert FlightGear's old XML translation files into other formats.""",
        description="""\
Most notably, XLIFF format can be chosen for output. The script performs
a few automated checks on the input files too.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # I want --help but not -h (it might be useful for something else)
        add_help=False)

    parser.add_argument("-t", "--transl-dir",
                        help="""\
                        directory containing all translation subdirs (such as
                        {default!r}, 'en_GB', 'fr_FR', 'de', 'it'...). This
                        "option" MUST be specified.""".format(
                        default=fg_i18n.DEFAULT_LANG_DIR))
    parser.add_argument("lang_code", metavar="LANGUAGE_CODE", nargs="+",
                        help="""\
                        codes of languages to read translations for (don't
                        specify {default!r} this way, it is special and not a
                        language code)"""
                        .format(default=fg_i18n.DEFAULT_LANG_DIR))
    parser.add_argument("-o", "--output-dir",
                        help="""\
                        output directory for written XLIFF files
                        (default: for each output file, use a suitable location
                        under TRANSL_DIR)""")
    parser.add_argument("-f", "--output-format", default="xliff",
                        choices=("xliff", "text"), help="""\
                        format to use for the output files""")
    parser.add_argument("--help", action="help",
                        help="display this message and exit")

    params = parser.parse_args(namespace=params)

    if params.transl_dir is None:
        error("--transl-dir must be given, aborting")
        sys.exit(1)

    return params


def main():
    global params

    locale.setlocale(locale.LC_ALL, '')
    params = processCommandLine()

    l10nResPoolMgr = fg_i18n.L10NResourcePoolManager(params.transl_dir, logger)
    # English version of all translatable strings
    masterTransl, nbWhitespaceProblemsInMaster = \
                                        l10nResPoolMgr.readFgMasterTranslation()
    translations = collections.OrderedDict()

    # Sort elements of 'translations' according to language code (= the keys)
    for langCode in sorted(params.lang_code):
        translationData = l10nResPoolMgr.readFgTranslation(masterTransl,
                                                           langCode)
        translations[translationData.transl.targetLanguage] = translationData

    if params.output_format == "xliff":
        writeFunc = writeXliff           # write to files
    elif params.output_format == "text":
        writeFunc = printPlainText       # print to stdout
    else:
        assert False, \
            "Unexpected output format: '{}'".format(params.output_format)

    writeFunc(l10nResPoolMgr, translations)

    nbWhitespaceProblemsInTransl = sum(
        (translData.nbWhitespacePbs for translData in translations.values() ))
    info("total number of leading and/or trailing whitespace problems: {}"
          .format(nbWhitespaceProblemsInMaster + nbWhitespaceProblemsInTransl))

    return 0


if __name__ == "__main__":
    sys.exit(main())
