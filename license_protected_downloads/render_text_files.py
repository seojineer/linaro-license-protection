from textile.textilefactory import TextileFactory


class RenderTextFiles:

    def __init__(self):
        pass

    @classmethod
    def find_and_render(cls, path):

        result = {}

        try:
            # This method should raise some custom error if there is more
            # then one file of the same type recursively found.
            filepaths = cls.find_relevant_files(path)
        except:
            # this is ok, no tabs when none is returned.
            return None

        if filepaths:
            for filepath in filepaths:
                try:
                    file_obj = open(filepath, 'r')
                    title, formatted = cls.render_file(file_obj)
                    result[title] = formatted
                except:
                    # TODO: log error or something.
                    continue
        else:
            return None

        return result

    @classmethod
    def render_file(cls, file_obj):
        # TODO: introduce special options to textile factory if necessary.
        textile_factory = TextileFactory()
        title = file_obj.readline()
        file_obj.seek(0)
        return title, textile_factory.process(file_obj.read())

    @classmethod
    def find_relevant_files(cls, path):
        # Go recursively and find howto's, readme's, hackings, installs.
        # If there are more of the same type then one, throw custom error as
        # written above.
        return None
