#!/usr/bin/env python
import argparse
import os
import re
import time
import sys


def search_and_run(root_dir, command, trigger_age_string):
    """Run command on old directories

    Search under root_dir. If a directory is found that is older than the
    age specified by trigger_age_string, run command on it.

    Does not recurse down into subdirectories.
    """
    trigger_age_seconds = None

    age_search = re.search("^(\d+)(\w+)$", trigger_age_string)

    if age_search:
        if age_search.group(2) == "m":
            trigger_age_seconds = int(age_search.group(1)) * 60
        elif age_search.group(2) == "h":
            trigger_age_seconds = int(age_search.group(1)) * 60 * 60
        elif age_search.group(2) == "s":
            trigger_age_seconds = int(age_search.group(1))

    if not trigger_age_seconds:
        print >> sys.stderr, "Time string format unrecognised."
        print >> sys.stderr, "Format should be <number><unit>, for example:"
        print >> sys.stderr, "  2h  = two hours."
        print >> sys.stderr, "  30m = 30 minutes."
        print >> sys.stderr, "  45s = 45 seconds."
        sys.exit(1)

    root = os.path.abspath(root_dir)

    for thing in os.listdir(root):
        if os.path.isdir(os.path.join(root, thing)):
            folder = os.path.join(root, thing)
            path = os.path.join(root, folder)
            mod_time = os.path.getmtime(path)

            if (time.time() - mod_time) > trigger_age_seconds:
                os.system(command + " " + path)


if __name__ == '__main__':
    """Run command on directories that are older than trigger-age."""

    parser = argparse.ArgumentParser(description="Run command on directories"
                "that are older than trigger-age.")

    parser.add_argument('--root-dir', type=str, nargs=1, required=True,
                        help="Root directory to search")
    parser.add_argument('--trigger-age', type=str, nargs=1, required=True,
                help="Age of directory (or files in it) to trigger command")
    parser.add_argument('--command', type=str, nargs=1, required=True,
                        help="Command to run on directory")

    args = parser.parse_args()

    search_and_run(args.root_dir[0], args.command[0], args.trigger_age[0])
