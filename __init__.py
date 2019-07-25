from mycroft import MycroftSkill, intent_file_handler


class RussellEnclosure(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('enclosure.russell.intent')
    def handle_enclosure_russell(self, message):
        self.speak_dialog('enclosure.russell')


def create_skill():
    return RussellEnclosure()

