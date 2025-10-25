#!/usr/bin/env python
"""
photosorter - https://github.com/MinchinWeb/minchin.scripts.photosorter
-----------------------------------------------------------------------

A little Python daemon to keep my photos organized on Dropbox.

It watches a *source directory* for modifications and moves new image
files to a *target directory* depending on when the photo was taken,
using EXIF data and creation date as a fallback.

Inspired by
    - https://github.com/dbader/photosorter
    - http://simplicitybliss.com/exporting-your-iphoto-library-to-dropbox/
    - https://github.com/wting/exifrenamer
    - http://chambersdaily.com/learning-to-love-photo-management/

"""
import argparse
import collections
import datetime
import hashlib
import logging
import os
from pathlib import Path
import queue
import re
import shutil
import sys
import threading
import time
from typing import Dict, List, Mapping, Optional, Set, Tuple  # noqa

import exifread
import watchdog
import watchdog.events
import watchdog.observers

# Metadata
__title__ = "minchin.scripts.photosorter"
__version__ = "2.2.0"
__description__ = "A Python script to keep my photos from Dropbox organized."
__author__ = "William Minchin"
__email__ = "w_minchin@hotmail.com"
__url__ = "https://github.com/MinchinWeb/minchin.scripts.photosorter"
__license__ = "MIT License"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("photosorter")

# lowercased file extensions to move
VALID_EXTENSIONS = [".jpg", ".jpeg", ".png", ".mov", ".mp4"]


class HashCache:
    """
    Gives a quick answer to the question if there's an identical file
    in the given target folder.
    """

    def __init__(self) -> None:
        # folder -> (hashes, filename -> hash)
        self.hashes = collections.defaultdict(
            lambda: (set(), dict())
        )  # type: Mapping[str, Tuple[Set[str], Dict[str, str]]]

    def has_file(self, target_folder: str, path: str) -> bool:
        """Determine if a file already exists in our target directory."""
        # Strip trailing slashes etc.
        target_folder = os.path.normpath(target_folder)

        # Update the cache by ensuring that we have the hashes of all
        # files in the target folder. `_add_file` is smart enough to
        # skip any files we already hashed.
        for f in self._files_in_folder(target_folder):
            self._add_file(f)

        # Hash the new file at `path`.
        file_hash = self._hash(path)

        # Check if we already have an identical file in the target folder.
        return file_hash in self.hashes[target_folder][0]

    def _add_file(self, path: str):
        # Bail out if we already have a hash for the file at `path`.
        folder = self._target_folder(path)
        if path in self.hashes[folder][1]:
            return

        file_hash = self._hash(path)

        basename = os.path.basename(path)
        self.hashes[folder][0].add(file_hash)
        self.hashes[folder][1][basename] = file_hash

    @staticmethod
    def _hash(path: str) -> str:
        hasher = hashlib.sha1()
        with open(path, "rb") as f:
            data = f.read()
            hasher.update(data)
        return hasher.hexdigest()

    @staticmethod
    def _target_folder(path: str) -> str:
        return os.path.dirname(path)

    @staticmethod
    def _files_in_folder(folder_path: str) -> List[str]:
        """Return Iterable with full paths to all files in `folder_path`."""
        try:
            names = (os.path.join(folder_path, f) for f in os.listdir(folder_path))
            return [f for f in names if os.path.isfile(f)]
        except OSError:
            return []


hash_cache = HashCache()


def move_file(root_folder: str, path: str):
    if not os.path.exists(path):
        logger.debug("File no longer exists: %s", path)
        return

    if not is_valid_filename(path):
        logger.debug("Not a valid filename: %s", path)
        return

    dst = dest_path(root_folder, path)
    dirs = os.path.dirname(dst)

    if hash_cache.has_file(dirs, path):
        logger.info("%s is a duplicate, skipping", path)
        return

    try:
        os.makedirs(dirs)
        logger.debug("Created folder %s", dirs)
    except OSError as ex:
        # Catch "File exists"
        if ex.errno != 17:
            raise ex

    logger.info("Moving %s to %s", path, dst)
    shutil.move(path, dst)


def resolve_duplicate(path: str) -> str:
    if not os.path.exists(path):
        return path

    basename = os.path.basename(path)
    filename, ext = os.path.splitext(basename)
    dirname = os.path.dirname(path)
    dedup_index = 1

    while True:
        new_fname = "%s-%i%s" % (filename, dedup_index, ext)
        new_path = os.path.join(dirname, new_fname)
        if not os.path.exists(new_path):
            logger.debug("De-duplicating %s to %s", path, new_path)
            break
        dedup_index += 1

    return new_path


def is_valid_filename(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in VALID_EXTENSIONS


def dest_path(root_folder: str, path: str) -> str:
    cdate = creation_date(path)
    path = path_from_datetime(root_folder, cdate, path)
    return resolve_duplicate(path)


def path_from_datetime(root_folder: str, dt: datetime.datetime, path: str) -> str:
    folder = folder_from_datetime(dt)
    filename = filename_from_datetime(dt, path)
    return os.path.join(root_folder, folder, filename)


def folder_from_datetime(dt: datetime.datetime) -> str:
    """Determine the folder path to store moved files in."""
    # return dt.strftime('%Y' + os.sep + '%Y-%m')
    return dt.strftime("%Y-%m" + os.sep + "%Y_%m_%d")


def filename_from_datetime(dt: datetime.datetime, path: str) -> str:
    """Returns basename + original extension."""
    base = basename_from_datetime(dt)
    ext = os.path.splitext(path)[1]
    return base + ext.lower()


def basename_from_datetime(dt: datetime.datetime) -> str:
    """Return a string formatted like this '2004-05-07 20.16.31'."""
    return dt.strftime("%Y-%m-%d %H.%M.%S")


def creation_date(path: str) -> datetime.datetime:
    exif_date = exif_creation_date(path)
    if exif_date:
        return exif_date
    return file_creation_date(path)


def file_creation_date(path: str) -> datetime.datetime:
    """
    Use mtime as creation date because ctime returns the
    the time when the file's inode was last modified; which is
    wrong and almost always later.
    """
    mtime = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(mtime)


def exif_creation_date(path: str) -> Optional[datetime.datetime]:
    try:
        ts = exif_creation_timestamp(path)
    except MissingExifTimestampError:
        logger.debug("Missing exif timestamp", exc_info=True)
        return None

    try:
        return exif_timestamp_to_datetime(ts)
    except BadExifTimestampError:
        logger.debug("Failed to parse exif timestamp", exc_info=True)
        return None


class BadExifTimestampError(Exception):
    pass


class MissingExifTimestampError(Exception):
    pass


class PhotosorterCompleteInterrupt(Exception):
    pass


def exif_creation_timestamp(path: str) -> str:
    with open(path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    if "EXIF DateTimeOriginal" in tags:
        return str(tags["EXIF DateTimeOriginal"])
    elif "EXIF DateTimeDigitized" in tags:
        return str(tags["EXIF DateTimeDigitized"])

    raise MissingExifTimestampError()


def exif_timestamp_to_datetime(ts: str) -> datetime.datetime:
    elements = [int(_) for _ in re.split(":| ", ts)]

    if len(elements) != 6:
        raise BadExifTimestampError

    return datetime.datetime(
        elements[0], elements[1], elements[2], elements[3], elements[4], elements[5]
    )


class EventHandler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, shared_queue: queue.Queue, target_folder: str) -> None:
        self.shared_queue = shared_queue
        self.target_folder = target_folder
        super().__init__(ignore_directories=True)

    def on_created(self, event):
        self.shared_queue.put(event.src_path)

    def on_modified(self, event):
        self.shared_queue.put(event.src_path)

    def on_moved(self, event):
        self.shared_queue.put(event.src_path)


class MoveFileThread(threading.Thread):
    def __init__(self, shared_queue: queue.Queue, dest_folder: str) -> None:
        super().__init__()
        self.shared_queue = shared_queue
        self.dest_folder = dest_folder
        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            try:
                file_path = self.shared_queue.get(block=False, timeout=1)
            except queue.Empty:  # type: ignore
                continue
            # wait for the file to be finished moving in to our source directory
            time.sleep(0.5)
            logger.debug("MoveFileThread got file %s", file_path)
            try:
                move_file(self.dest_folder, file_path)
            except Exception as ex:
                logger.exception(ex)
            self.shared_queue.task_done()
        logger.debug("MoveFileThread exiting")

    def stop(self) -> None:
        self.is_running = False


class ExistingFilesThread(threading.Thread):
    def __init__(self, shared_queue: queue.Queue, src_folder: str) -> None:
        super().__init__()
        self.shared_queue = shared_queue
        self.is_running = True
        self.all_dirs = [
            src_folder,
        ]

    def run(self) -> None:
        """Load all existing picture files into queue."""
        # print('running existing files thread')
        while self.is_running:
            # on first run, load all the files, one at a time
            # print(' ' + str(self.all_dirs))
            try:
                current_file = self.all_dirs.pop()
            except IndexError:
                logging.info("All existing files loaded into queue.")
                self.is_running = False

            current_file = Path(current_file)
            # print('   ' + str(current_file))
            for f in current_file.iterdir():
                # print('     ' + str(f))
                if f.is_dir():
                    self.all_dirs.append(str(f))
                elif f.suffix.lower() in VALID_EXTENSIONS:
                    self.shared_queue.put(str(f))
            # print('   ' + str(self.all_dirs))

    def stop(self) -> None:
        self.is_running = False


def parse_args():
    def _str_to_bool(s):
        """Convert string to bool (in argparse context)."""
        # from https://stackoverflow.com/a/36194213/4276230
        if s.lower() not in ["true", "false"]:
            raise ValueError("Need bool; got %r" % s)
        return {"true": True, "false": False}[s.lower()]

    def _add_boolean_argument(parser, name, default=False, help=None):
        """Add a boolean argument to an ArgumentParser instance."""
        # modified from https://stackoverflow.com/a/36194213/4276230
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--" + name, nargs="?", default=default, const=True, type=_str_to_bool
        )
        group.add_argument("--no-" + name, dest=name, action="store_false", help=help)

    parser = argparse.ArgumentParser()
    parser.add_argument("src_folder")
    parser.add_argument("dest_folder")
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="{}, version {}".format(__title__, __version__),
    )
    _add_boolean_argument(
        parser,
        "move-existing",
        default=False,
        help="move existing files (defaults to 'no')",
    )
    # _add_boolean_argument(parser, 'deamon-mode', default=False,
    #                       help="run forever (aka 'deamon mode') (defaults to 'no')")
    return parser.parse_args()


def run(src_folder: str, dest_folder: str, move_existing: bool, deamon_mode: bool):
    shared_queue = queue.Queue()  # type: queue.Queue[str]

    existing_thread = None
    if move_existing:
        existing_thread = ExistingFilesThread(shared_queue, src_folder)
        existing_thread.start()
        existing_thread.join()

    move_thread = MoveFileThread(shared_queue, dest_folder)
    move_thread.start()

    event_handler = EventHandler(shared_queue, dest_folder)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, src_folder, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
        if not deamon_mode and shared_queue.empty():
            raise PhotosorterCompleteInterrupt
    except KeyboardInterrupt:
        logger.info("Shutting down")
        pass
    except PhotosorterCompleteInterrupt:
        logger.info("Queue Complete, Shutting down.")
        pass

    observer.stop()
    observer.join()
    logger.debug("Observer thread stopped")

    shared_queue.join()
    move_thread.stop()
    move_thread.join()


def main():
    args = parse_args()
    logger.info(
        "Watching %s for changes, destination is %s", args.src_folder, args.dest_folder
    )
    run(
        args.src_folder,
        args.dest_folder,
        args.move_existing,
        # args.deamon_mode)
        False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
