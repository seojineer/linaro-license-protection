# Copyright 2012 Linaro.

"""Helper class for creating new scripts.

It pre-defines a logger using the script_name (passed through the constructor)
and allows different verbosity levels.

Overload the work() method to define the main work to be done by the script.

You can use the logger by accessing instance.logger attribute.
You can use the parser (eg. to add another argument) by accessing
instance.argument_parser attribute.

Parsed arguments are available to your work() method in instance.arguments.
"""

import argparse
import logging


class LinaroScript(object):
    def __init__(self, script_name, description=None):
        self.script_name = script_name
        self.description = description
        self.argument_parser = argparse.ArgumentParser(
            description=self.description)
        self.setup_parser()

    def work(self):
        """The main body of the script.  Overload when subclassing."""
        raise NotImplementedError

    def run(self):
        self.arguments = self.argument_parser.parse_args()
        logging_level = self.get_logging_level_from_verbosity(
            self.arguments.verbose)
        self.logger = logging.getLogger(self.script_name)
        self.logger.setLevel(logging_level)
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s: %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.work()

    def setup_parser(self):
        self.argument_parser.add_argument(
            "-v", "--verbose", action='count',
            help=("Increase the output verbosity. "
                  "Can be used multiple times"))

    def get_logging_level_from_verbosity(self, verbosity):
        """Return a logging level based on the number of -v arguments."""
        if verbosity == 0:
            logging_level = logging.ERROR
        elif verbosity == 1:
            logging_level = logging.WARNING
        elif verbosity == 2:
            logging_level = logging.INFO
        elif verbosity >= 3:
            logging_level = logging.DEBUG
        else:
            logging_level = logging.ERROR
        return logging_level
