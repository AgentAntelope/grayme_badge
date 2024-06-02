import time
import app
import settings
from app_components import TextDialog, clear_background
from events.input import BUTTON_TYPES, Buttons
from system.eventbus import eventbus
from perf_timer import PerfTimer
from system.patterndisplay.events import *
from tildagonos import tildagonos


class GraymeBadge(app.App):
    name = None

    # colors used
    black = (0, 0, 0)
    white = (255, 255, 255)
    orange = (255,50,0)
    red = (255,0,0)

    # colors used for the 'hello my name is' part
    header_fg_color = (0, 0, 0)

    def __init__(self):
        super().__init__()
        self.button_states = Buttons(self)
        self.state = "name"
        self.states = {
            "name": {
                "heading": "Hello",
                "subheading": "my name is",
                "text": settings.get("name"),
                "colour": self.white,
            },
            "context": {
                "heading": "You",
                "subheading": "killed my",
                "text": "Father",
                "led_colours": self.orange,
                "colour": self.orange,
            },
            "threat": {
                "heading": "prepare",
                "subheading": "to",
                "text": "DIE!",
                "led_colours": self.red,
                "colour": self.red,
            },
        }
        self.update_state()

    async def run(self, render_update):
        last_time = time.ticks_ms()
        while True:
            cur_time = time.ticks_ms()
            delta_ticks = time.ticks_diff(cur_time, last_time)
            with PerfTimer(f"Updating {self}"):
                self.update(delta_ticks)
            await render_update()
            last_time = cur_time

            if self.text is None:
                dialog = TextDialog("What is your name?", self)
                self.overlays = [dialog]

                if await dialog.run(render_update):
                    self.text = dialog.text
                    settings.set("name", dialog.text)

                    try:
                        settings.save()
                    except Exception as ex:
                        print("failed to save settings", ex)
                else:
                    self.minimise()

                self.overlays = []

    def update(self, delta):
        # quit the app
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            for i in range(0,12):
                tildagonos.leds[i+1] = self.black
            eventbus.emit(PatternEnable())
            self.minimise()
            self.button_states.clear()
        # Inigo Montoya Escalation
        elif self.button_states.get(BUTTON_TYPES["DOWN"]):
            if self.state == "name":
                self.state = "context"
                eventbus.emit(PatternDisable())
            elif self.state == "context":
                self.state = "threat"
            self.update_state()
        # Inigo Montoya De-escalation
        elif self.button_states.get(BUTTON_TYPES["UP"]):
            if self.state == "threat":
                self.state = "context"
            elif self.state == "context":
                self.state = "name"
                eventbus.emit(PatternEnable())
            self.update_state()

    def draw(self, ctx):
        clear_background(ctx)

        ctx.text_align = ctx.CENTER

        # draw backgrounds
        ctx.rgb(*self.black).rectangle(-120, -120, 240, 240).fill()
        ctx.rgb(*self.colour).rectangle(-120, -120, 240, 100).fill()

        ctx.font_size = 56
        ctx.font = "Arimo Bold"
        ctx.rgb(*self.black).move_to(0, -60).text(self.heading)
        if self.text is not None:
            ctx.rgb(*self.colour).move_to(0, 60).text(self.text)

        ctx.font_size = 28
        ctx.font = "Arimo Bold"
        ctx.rgb(*self.black).move_to(0, -30).text(self.subheading)

        if self.text is None:
            ctx.font = "Arimo Italic"
            ctx.rgb(*self.colour).move_to(0, 20).text(
                "Set your name in\nthe settings app!"
            )

        self.draw_overlays(ctx)

    def update_state(self):
        self.heading = self.states[self.state]["heading"]
        self.subheading = self.states[self.state]["subheading"]
        self.text = self.states[self.state]["text"]
        self.colour = self.states[self.state]["colour"]
        if "led_colours" in self.states[self.state]:
            for i in range(0,12):
                tildagonos.leds[i+1] = self.states[self.state]["led_colours"]
        # if the badge was off, then turn off before we hand back to the pattern
        # since the pattern doesn't rewrite the LEDs to off
        elif settings.get("pattern") == "off":
            for i in range(0,12):
                tildagonos.leds[i+1] = self.black

        self.button_states.clear()

__app_export__ = GraymeBadge
