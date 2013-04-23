import os

from buildinfo import BuildInfo

IGNORED_FILES = ["BUILD-INFO.txt", "EULA.txt", "OPEN-EULA.txt"]


class SpliceBuildInfos:

    def __init__(self, build_info_paths):
        """Initiates a splice build info object.

        :param build_info_paths: list of dir paths containing
        the BUILD-INFO.txt files.
        """
        self.build_infos = []
        for build_info_path in build_info_paths:
            for path, subdirs, files in os.walk(build_info_path):
                for filename in files:
                    if path == build_info_path:
                        if filename not in IGNORED_FILES:
                            build_info = BuildInfo(os.path.join(path,
                                                                filename))
                            if len(build_info.file_info_array[0]):
                                self.build_infos.append(build_info)

    def splice(self, build_info_path):

        build_info_res = {}
        for build_info in self.build_infos:
            build_info_res[build_info.fname] = build_info.file_info_array

        build_info_res = self.merge_duplicates(build_info_res)
        BuildInfo.write_from_array([build_info_res], build_info_path)

    @classmethod
    def merge_duplicates(cls, build_info_dict):
        build_info_res = {}
        for key in build_info_dict:
            if build_info_dict[key] in build_info_res.values():
                found_key = [name for name, value in
                             build_info_res.iteritems()
                             if value == build_info_dict[key]][0]
                if key != found_key:
                    new_key = "%s, %s" % (found_key, key)
                    build_info_res[new_key] = build_info_dict[key]
                    del build_info_res[found_key]
            else:
                build_info_res[key] = build_info_dict[key]

        return build_info_res
