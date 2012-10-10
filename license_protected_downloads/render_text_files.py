from textile.textilefactory import TextileFactory


class RenderTextFiles:

    def __init__(self):
        pass

    @classmethod
    def find_and_render(cls, path):

        result = {}

        try:
            file_obj = open(path, 'r')
        except:
            return None

        # TODO: this goes in a loop
        title, formatted = cls.render_file(file_obj)
        result[title] = formatted

        return result

    @classmethod
    def render_file(cls, file_obj):
        textile_factory = TextileFactory()
        title = file_obj.readline()
        file_obj.seek(0)
        return title, textile_factory.process(file_obj.read())
