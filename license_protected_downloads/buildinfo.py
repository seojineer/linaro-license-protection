import os
import re
import glob


class IncorrectDataFormatException(Exception):
        ''' Build-info data is in incorrect format. '''

class BuildInfo:
    def __init__(self, fn):
        self.index = 0
        self.lines = []
        self.build_info_array = [{}]
        self.file_info_array = [{}]
        self.fields_defined = ["format-version", "files-pattern",
            "build-name", "theme", "license-type", "openid-launchpad-teams",
            "collect-user-data", "license-text"]
        self.full_file_name = fn
        self.search_path = os.path.dirname(fn)
        self.fname = os.path.basename(fn)
        self.build_info_file = os.path.join(self.search_path, "BUILD-INFO.txt")
        self.readFile()
        self.parseData(self.lines)
        self.file_info_array = self.getInfoForFile(self.fname)

    def _set(self, key, value):
        key = key.lower()
        if key in self.build_info_array[self.index]:
            # A repeated key indicates we have found another chunk of
            # build-info
            self.index += 1

            # Unless an external influence has messed with self.index, this
            # should be a new array element...
            assert(self.index == len(self.build_info_array))
            self.build_info_array.append({})

        self.build_info_array[self.index][key] = value

    def _append(self, key, value):
        key = key.lower()
        self.build_info_array[self.index][key] += value

    def readFile(self):
        with open(self.build_info_file, "r") as infile:
            lines = infile.readlines()
        for line in lines:
            if line.strip() != '':
                self.lines.append(line.rstrip())

    def getInfoForFile(self, fname):
        for block in self.build_info_array:
            for key in block:
                if key != "format-version":
                    files = glob.glob(os.path.join(self.search_path, key))
                    for filename in files:
                        if filename == self.full_file_name:
                            return block[key]
        return [{}]

    def getFormatVersion(self):
        for block in self.build_info_array:
            if "format-version" in block:
                return block["format-version"]
            else:
                return False;

    # Get value of specified field for corresponding file
    def get(self, field):
        for pair in self.file_info_array:
            if field in pair:
                return pair[field]
            else:
                return False

    def parseLine(self, line):
        values = line.split(":", 1)
        if len(values) != 2:
            raise IncorrectDataFormatException("'%s': Line is not in the correct format." % line)
        else:
            field = values[0].strip().lower()
            value = values[1].strip()
            if not self.isValidField(field):
                raise IncorrectDataFormatException("Field '%s' not allowed." % field)
            else:
                return {field: value}

    def isValidField(self, field_name):
        if field_name in self.fields_defined:
            return True
        else:
            return False

    def parseData(self, lines):
        result = [{}]
        if not isinstance(lines, list):
            raise IncorrectDataFormatException("No array provided.")
        format_line = lines.pop(0)
        values = self.parseLine(format_line)
        if not "format-version" in values:
            raise IncorrectDataFormatException("Format-Version field not found.")
        result = self._set("format-version", values["format-version"])

        self.line_no = 0
        while self.line_no < len(lines):
            line = lines[self.line_no]
            values = self.parseLine(line)
            if "files-pattern" in values:
                self.line_no += 1
                block = self.parseBlock(lines)
                if isinstance(block, list):
                    for pattern in values["files-pattern"].split(","):
                        self._set(pattern.strip(), block)

    def parseBlock(self, lines):
        result = [{}]
        while self.line_no < len(lines):
            line = lines[self.line_no]
            values = self.parseLine(line)
            if "license-text" in values:
                text = values["license-text"]
                self.line_no += 1
                text = text + self.parseContinuation(lines)
                result[0]["license-text"] = text
            elif "files-pattern" in values:
                return result
            else:
                self.line_no += 1
                key = values.keys()[0]
                result[0][key] = values[key]
        return result

    def parseContinuation(self, lines):
        text = ''
        while self.line_no < len(lines) and len(lines[self.line_no]) > 0:
            if lines[self.line_no][0] == ' ':
                text += "\n" + lines[self.line_no][1:]
                self.line_no += 1
            else:
                break
        return text

#if __name__ == "__main__":
#    bi = BuildInfo("/var/www/build-info/vexpress-open.txt")
#    print bi.build_info_array
#    print bi.file_info_array
#    print bi.getFormatVersion()
#    for field in bi.fields_defined:
#        print field + " = " + str(bi.get(field))
