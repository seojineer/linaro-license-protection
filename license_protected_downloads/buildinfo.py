import os
import fnmatch


class IncorrectDataFormatException(Exception):
        ''' Build-info data is in incorrect format. '''


class BuildInfoBase(object):
    fields_defined = [
        "format-version", "files-pattern", "build-name", "theme",
        "license-type", "auth-groups", "collect-user-data",
        "license-text",
        # Deprecated
        "openid-launchpad-teams",
    ]

    def __init__(self, full_name, content):
        self.fname = os.path.basename(full_name)

        self.index = 0
        self.build_info_array = [{}]

        lines = [x for x in content.split('\n') if x.strip()]
        self.parseData(lines)

        self.file_info_array = self.getInfoForFile()
        self.remove_false_positives()
        self.max_index = len(self.file_info_array)

    # Get value of specified field in block index for
    # corresponding file
    def get(self, field, index=0):
        if index > self.max_index:
            return False
        block = self.file_info_array[index]
        return block.get(field, False)

    def _set(self, key, value):
        """Record set of directives applying to a file pattern
        key: file pattern
        value: list of dicts of field/val pairs"""
        if key in self.build_info_array[self.index]:
            # A repeated key indicates we have found another chunk of
            # build-info
            self.build_info_array[self.index][key].append(value[0])
        else:
            self.build_info_array[self.index][key] = value

    def assertValidField(self, field):
        if field not in self.fields_defined:
            raise IncorrectDataFormatException(
                "Field '%s' not allowed." % field)

    def parseLine(self, line):
        values = line.split(":", 1)
        if len(values) != 2:
            raise IncorrectDataFormatException(
                "'%s': Line is not in the correct format." % line)
        else:
            field = values[0].strip().lower()
            self.assertValidField(field)
            value = values[1].strip()

            # Rename any deprecated field names to new names
            field_renames = {"openid-launchpad-teams": "auth-groups"}
            field = field_renames.get(field, field)
            return {field: value}

    def parseContinuation(self, lines):
        text = ''
        while self.line_no < len(lines) and len(lines[self.line_no]) > 0:
            if lines[self.line_no][0] == ' ':
                text += '\n' + lines[self.line_no][1:]
                self.line_no += 1
            else:
                break
        return text

    def parseBlock(self, lines):
        result = [{}]
        while self.line_no < len(lines):
            line = lines[self.line_no]
            values = self.parseLine(line)
            if 'license-text' in values:
                text = values['license-text']
                self.line_no += 1
                text += self.parseContinuation(lines)
                result[0]['license-text'] = text
            elif 'files-pattern' in values:
                return result
            else:
                self.line_no += 1
                key = values.keys()[0]
                result[0][key] = values[key]
        return result

    def parseData(self, lines):
        if not isinstance(lines, list):
            raise IncorrectDataFormatException("No array provided.")
        if not list:
            raise IncorrectDataFormatException("Empty BUILD-INFO")
        format_line = lines.pop(0)
        values = self.parseLine(format_line)
        if 'format-version' not in values:
            raise IncorrectDataFormatException(
                'Format-Version field not found.')
        self._set("format-version", values["format-version"])

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

    def getInfoForFile(self):
        for block in self.build_info_array:
            if self.fname in block:
                # File name matches a key directly - don't need to iterate
                # through each using fnmatch to implement globs.
                return block[self.fname]
            for key in block:
                if key != 'format-version':
                    if fnmatch.fnmatch(self.fname, key):
                        return block[key]
        return [{}]

    def remove_false_positives(self):
        open_type = []
        protected_type = []
        index = 0
        for block in self.file_info_array:
            if 'license-type' in block.keys():
                if block["license-type"] == 'open':
                    open_type.append(index)
                if block["license-type"] == 'protected':
                    protected_type.append(index)
                index += 1
            else:
                return False
        if len(protected_type) != 0 and len(open_type) != 0:
            for index in open_type:
                self.file_info_array.pop(index)


class BuildInfo(BuildInfoBase):
    def __init__(self, fn):

        search_path = self.get_search_path(fn)
        build_info_file = os.path.join(search_path, "BUILD-INFO.txt")

        with open(build_info_file, "r") as f:
            super(BuildInfo, self).__init__(fn, f.read())

    @classmethod
    def get_search_path(cls, path):
        "Return BUILD-INFO.txt search path for a given filesystem path."
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        return path

    @classmethod
    def build_info_exists(cls, path):
        "Check if BUILD-INFO.txt exists for a given filesystem path."
        return os.path.exists(
            os.path.join(cls.get_search_path(path), "BUILD-INFO.txt"))

    @classmethod
    def write_from_array(cls, build_info_array, file_path):
        if len(build_info_array[0]):
            with open(file_path, "w") as outfile:
                outfile.write("Format-Version: 0.5\n\n")
                for key in build_info_array[0]:
                    if key != "format-version":
                        outfile.write("Files-Pattern: %s\n" % key)
                        for item in build_info_array[0][key][0]:
                            text = build_info_array[0][key][0][item]
                            if item == "license-text":
                                text = text.replace("\n", "\n ")
                            outfile.write("%s: %s\n" % (item, text))
                        outfile.write("\n")


if __name__ == "__main__":
    import sys
    bi = BuildInfo(sys.argv[1])
    for field in bi.fields_defined:
        print field + " = " + str(bi.get(field))
