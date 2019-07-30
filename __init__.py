from datetime import datetime, timedelta

from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill
from mycroft.util import connected
from mycroft.util.log import LOG
from mycroft.util.parse import normalize
from mycroft.audio import wait_while_speaking
from mycroft import intent_file_handler
from mycroft import MycroftSkill, intent_file_handler


class RussellEnclosure(MycroftSkill):
    IDLE_CHECK_FREQUENCY = 6  # in seconds

    def __init__(self):
        super(RussellEnclosure, self).__init__("RussellEnclosure")
        self.should_converse = False
        self._settings_loaded = False
        self.converse_context = None
        self.idle_count = 99
        self.hourglass_info = {}
        self.interaction_id = 0

        self.settings['use_listening_beep'] = True

    def initialize(self):
        # Initialize...
        self.brightness_dict = self.translate_namedvalues('brightness.levels')
        self.color_dict = self.translate_namedvalues('colors')
        self.settings['web eye color'] = self.settings['eye color']

        try:
            # Handle changing the eye color once Mark 1 is ready to go
            # (Part of the statup sequence)
            self.add_event('mycroft.internet.connected',
                           self.handle_internet_connected)

            # Handle the 'waking' visual
            self.add_event('recognizer_loop:record_begin',
                           self.handle_listener_started)
            self.start_idle_check()

            # Handle the 'busy' visual
            self.bus.on('mycroft.skill.handler.start',
                        self.on_handler_started)
            self.bus.on('mycroft.skill.handler.complete',
                        self.on_handler_complete)

            self.bus.on('recognizer_loop:audio_output_start',
                        self.on_handler_interactingwithuser)
            self.bus.on('enclosure.mouth.think',
                        self.on_handler_interactingwithuser)
            self.bus.on('enclosure.mouth.events.deactivate',
                        self.on_handler_interactingwithuser)
            self.bus.on('enclosure.mouth.text',
                        self.on_handler_interactingwithuser)

            self.bus.on('mycroft.ready', self.reset_face)
        except Exception:
            LOG.exception('In Russell Enclosure Skill')

        # TODO: Add MycroftSkill.register_entity_list() and use the
        #  self.color_dict.keys() instead of duplicating data

        # Update use of wake-up beep
        self._sync_wake_beep_setting()

        self.settings.set_changed_callback(self.on_websettings_changed)


    #####################################################################
    # Manage "busy" visual

    def on_handler_started(self, message):
        handler = message.data.get("handler", "")
        # Ignoring handlers from this skill and from the background clock
        if "RussellEnclosure" in handler:
            return
        if "TimeSkill.update_display" in handler:
            return

        self.hourglass_info[handler] = self.interaction_id
        time.sleep(0.25)
        if self.hourglass_info[handler] == self.interaction_id:
            # Nothing has happend to indicate to the user that we are active,
            # so start a thinking interaction
            self.hourglass_info[handler] = -1

    def on_handler_interactingwithuser(self, message):
        # Every time we do something that the user would notice, increment
        # an interaction counter.
        self.interaction_id += 1

    def on_handler_complete(self, message):
        handler = message.data.get("handler", "")
        # Ignoring handlers from this skill and from the background clock
        if "Mark1" in handler:
            return
        if "TimeSkill.update_display" in handler:
            return

        try:
            if self.hourglass_info[handler] == -1:
                self.enclosure.reset()
            del self.hourglass_info[handler]
        except:
            # There is a slim chance the self.hourglass_info might not
            # be populated if this skill reloads at just the right time
            # so that it misses the mycroft.skill.handler.start but
            # catches the mycroft.skill.handler.complete
            pass


def create_skill():
    return RussellEnclosure()