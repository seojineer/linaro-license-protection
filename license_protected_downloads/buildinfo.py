import re


class BuildInfo:
    def __init__(self):
        self.data = [{}]
        self.multi_line_variables = {}
        self.multi_line_variables["License-Text"] = True
        self.index = 0

    def _set(self, key, value):
        # A repeated key indicates we have found another chunk of build-info
        if key in self.data[self.index]:
            self.index += 1

            # Unless an external influence has messed with self.index, this
            # should be a new array element...
            assert(self.index == len(self.data))
            self.data.append({})

        self.data[self.index][key] = value

    def _append(self, key, value):
        self.data[self.index][key] += value

    def parse_buildinfo_lines(self, lines):
        in_multi_line = False
        key = ""

        for line in lines:
            line_search = re.search("^(\S+)\s*:\s*(.*)$", line)
            if line_search:
                in_multi_line = False
                self._set(line_search.group(1), line_search.group(2))
            elif in_multi_line:
                self._append(key, " " + line)

            # Some variables have a value that takes more than one line...
            if (line_search and
                line_search.group(1) in self.multi_line_variables):
                in_multi_line = True
                key = line_search.group(1)

    def parse_buildinfo(buildinfo_file_location):
        return True
