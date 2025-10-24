# SPDX-FileCopyrightText: James Turner <james@flightgear.org>
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
import hashlib
import os


def process_dir(baseDir, relPath, *, date=None):
    """Recursively create .dirindex files in os.path.join(baseDir, relPath).

    Return the SHA-1 sum of the top-level .dirindex file that is
    created.

    If 'date' is None, use the current date and time in the .dirindex
    files; otherwise, use 'date' as is. Using a fixed string, this
    allows one to obtain reproducible SHA-1 sums (useful for testing).

    """
    absPath = os.path.join(baseDir, relPath)
    # Generate the list of directory entries before creating .dirindex there
    entries = sorted(os.scandir(absPath), key=lambda entry: entry.name)

    dirIndexPath = os.path.join(absPath, '.dirindex')
    with open(dirIndexPath, 'w') as indexFile:
        _write_index_file(baseDir, relPath, indexFile, entries, date)

    return _file_hash(dirIndexPath)


def _file_hash(filePath):
    """Return the SHA-1 hash of the given file."""
    with open(filePath, "rb") as f:
        sha = hashlib.sha1(f.read()).hexdigest()

    return sha


def _write_index_file(baseDir, relPath, indexFile, entries, date):
    now = date if date is not None else datetime.datetime.now()

    indexFile.write(f'#Index created on {now}\n')
    indexFile.write('version:1\n')
    indexFile.write(f'path:{relPath}\n')

    for entry in entries:       # os.DirEntry objects
        name = entry.name       # file or directory base name
        assert name, repr(name)

        # Skip hidden files or directories (scandir() already skipped . and ..)
        if name[0] == '.':
            pass
        elif entry.is_dir():
            # Ensure we don't name first-level directories as ./Foo
            subdirPath = name if relPath == '.' else os.path.join(relPath, name)

            # Process the dir first
            sha = process_dir(baseDir, subdirPath, date=date)
            indexFile.write(f"d:{name}:{sha}\n")
        else:
            indexFile.write("f:{name}:{hash}:{size}\n".format(
                name=name, hash=_file_hash(entry.path),
                size=entry.stat().st_size))
