#!/usr/bin/env python
# Create a copy of a directory structure while preserving as much metadata
# as possible and sanitizing any sensitive data.

# Everything, unless whitelisted, is truncated and the contents are replaced
# with the base file name itself.

import os
import shutil
import tempfile

from linaroscript import LinaroScript
from publish_to_snapshots import SnapshotsPublisher


class MakeSanitizedTreeCopyScript(LinaroScript):

    def setup_parser(self):
        super(MakeSanitizedTreeCopyScript, self).setup_parser()
        self.argument_parser.add_argument(
            'directory', metavar='DIR', type=str,
            help="Directory to create a sanitized deep copy of.")

    @staticmethod
    def filter_accepted_files(directory, list_of_files):
        accepted_files = []
        for filename in list_of_files:
            full_path = os.path.join(directory, filename)
            if SnapshotsPublisher.is_accepted_for_staging(full_path):
                accepted_files.append(filename)
        return accepted_files

    def copy_sanitized_tree(self, source, target):
        """Copies the tree from `source` to `target` while sanitizing it.

        Performs a recursive copy trying to preserve as many file
        attributes as possible.
        """
        assert os.path.isdir(source) and os.path.isdir(target), (
            "Both source (%s) and target (%s) must be directories." % (
                source, target))
        self.logger.debug("copy_sanitized_tree('%s', '%s')", source, target)
        filenames = os.listdir(source)
        for filename in filenames:
            self.logger.debug("Copying '%s'...", filename)
            source_file = os.path.join(source, filename)
            target_file = os.path.join(target, filename)
            try:
                if os.path.isdir(source_file):
                    self.logger.debug("Making directory '%s'" % target_file)
                    os.makedirs(target_file)
                    self.copy_sanitized_tree(source_file, target_file)
                elif SnapshotsPublisher.is_accepted_for_staging(source_file):
                    self.logger.debug(
                        "Copying '%s' to '%s' with no sanitization...",
                        source_file, target_file)
                    shutil.copy2(source_file, target_file)
                else:
                    self.logger.debug(
                        "Creating sanitized file '%s'", target_file)
                    # This creates an target file.
                    open(target_file, "w").close()
                    shutil.copystat(source_file, target_file)
                    SnapshotsPublisher.sanitize_file(target_file)
            except (IOError, os.error) as why:
                self.logger.error(
                    "While copying '%s' to '%s' we hit:\n\t%s",
                    source_file, target_file, str(why))

        try:
            shutil.copystat(source, target)
        except OSError as why:
            self.logger.error(
                "While copying '%s' to '%s' we hit:\n\t%s",
                source, target, str(why))

    def work(self):
        source_directory = self.arguments.directory
        self.logger.info("Copying and sanitizing '%s'...", source_directory)
        target_directory = tempfile.mkdtemp()
        self.logger.info("Temporary directory: '%s'", target_directory)

        self.copy_sanitized_tree(
            self.arguments.directory, target_directory)

        print target_directory

if __name__ == '__main__':
    script = MakeSanitizedTreeCopyScript(
        'make-sanitized-tree-copy',
        description=(
            "Makes a copy of a directory tree in a temporary location "
            "and sanitize files that can contain potentially restricted "
            "content. "
            "Returns the path of a newly created temporary directory."))
    script.run()
