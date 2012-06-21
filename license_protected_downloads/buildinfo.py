import re


class BuildInfo:

    def __init__(self):
        self.data = {}
        self.multi_line_variables = {}
        self.multi_line_variables["License-Text"] = True

    def parse_buildinfo_lines(self, lines):
        in_multi_line = False
        key = ""

        for line in lines:
            line_search = re.search("^(\S+)\s*:\s*(.*)$", line)
            if line_search:
                in_multi_line = False
                self.data[line_search.group(1)] = line_search.group(2)
            elif in_multi_line:
                self.data[key] += " " + line

            # Some variables have a value that takes more than one line...
            if line_search and line_search.group(1) in self.multi_line_variables:
                in_multi_line = True
                key = line_search.group(1)



    def parse_buildinfo(buildinfo_file_location):
        return True
