from enum import Enum
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError
import asyncio
import sys
import re


DEFAULT_HOST = "10.0.0.21"
DEFAULT_PORT = 55555


# More settings will be added once this PoC gets more traction and/or integrated in a real-world use case.
class Setting(Enum):
    AUDIO_INPUT_SOURCE = "audio_input_source"          # Typically 1, 2, 3, 4, 5
    SOUND_MODE = "sound_mode"                          # Typically 0 ("Pure"), 1 ("Voice"), 2 ("Night")
    DISPLAY_MAX_BRIGHTNESS = "display_max_brightness"  # Typically 0 -- 100
    LED_BRIGHTNESS = "led_brightness"                  # Typically 0 -- 100
    CHANNEL_CONFIGURATION = "channel_configuration"    # Typically 2 (left), 3 (right), 4 (stereo downmix)
    AUTO_STANDBY_DELAY = "auto_standby_delay"          # Typically 0 (off), 300, 900, 1800, 3600 (seconds)


class Component(ApplicationSession):
    players = {}
    current_prompt = ""

    async def onJoin(self, details):
        await self.get_player_info()

        input_text = ""
        selected_player = None
        selected_setting = None
        subscription_task_created = None

        while input_text != "q":
            if selected_player is None:
                first_player_uid = list(self.players.keys())[0]
                print("\nAvailable players:\n")

                for player_uid in self.players:
                    player = self.players[player_uid]
                    print("    [UID \"%s\"] \"%s\" in room \"%s\"" %
                          (player_uid, player["name"], player["room_name"]))

                input_text = input("\nPlease choose a player UID [%s]: " % first_player_uid) or first_player_uid

                try:
                    selected_player = self.players[input_text]
                except KeyError:
                    print("This player UID does not exist. Please enter the UID in the format "
                          "\"uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\" (without the quotes).")
            elif selected_setting is None:
                first_setting = selected_player["settings"][0]
                print("\nAvailable settings:\n")

                for setting in selected_player["settings"]:
                    print("    Setting \"%s\"" % setting)

                input_text = input(
                    "\nPlease choose a setting you want to subscribe to and/or change [%s]: " % first_setting
                ) or first_setting

                if input_text in selected_player["settings"]:
                    selected_setting = input_text
                else:
                    print("Invalid setting.")
            elif subscription_task_created is None:
                asyncio.create_task(self.subscribe_to_player_setting(selected_player["wamp_uid"], selected_setting))
                subscription_task_created = 1
            else:
                self.current_prompt = "Please set a value for setting \"%s\": " % selected_setting
                await self.prompt_for_setting_and_set(selected_player, selected_setting)

        self.leave()

    async def prompt_for_setting_and_set(self, selected_player, selected_setting):
        sys.stdout.write(self.current_prompt)
        sys.stdout.flush()

        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def response():
            loop.create_task(queue.put(sys.stdin.readline()))

        loop.add_reader(sys.stdin.fileno(), response)
        input_text = (await asyncio.wait_for(queue.get(), timeout=3600)).rstrip()

        if input_text.isnumeric():
            input_text = int(input_text)

        await self.call(
            procedure="com.raumfeld.devices.%s.settings.%s" % (selected_player["wamp_uid"], selected_setting),
            args=["set", input_text]
        )

        loop.remove_reader(sys.stdin.fileno())

    async def subscribe_to_player_setting(self, wamp_uid, setting):
        def on_setting_changed(value):
            print("\n    Received updated setting from the player. New value: %s" % value, flush=True)
            sys.stdout.write(self.current_prompt)

        await self.subscribe(
            on_setting_changed,
            "com.raumfeld.devices.%s.settings.%s" % (wamp_uid, setting)
        )

    async def get_player_info(self):
        rooms = await self.call("com.raumfeld.rooms", args=["get"])

        for room_uid in rooms:
            for player_uid in rooms[room_uid]["players"]:
                player = {
                    "name": rooms[room_uid]["players"][player_uid]["name"],
                    "room_name": rooms[room_uid]["name"],
                    "wamp_uid": re.sub('[^0-9a-zA-Z]+', '_', player_uid),
                    "settings": []
                }

                for setting in Setting:
                    if await self.check_setting_availability(player, setting.value):
                        player["settings"].append(setting.value)

                self.players[player_uid] = player

    async def check_setting_availability(self, player, setting) -> bool:
        try:
            procedure = "com.raumfeld.devices.%s.settings.%s" % (player["wamp_uid"], setting)
            await self.call(procedure, ["get"])
            return True
        except ApplicationError:
            return False

    def onDisconnect(self):
        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    host = input("Please enter the Teufel main host [%s]: " % DEFAULT_HOST) or DEFAULT_HOST
    port = input("Please enter the Teufel WebSocket port [%d]: " % DEFAULT_PORT) or DEFAULT_PORT
    runner = ApplicationRunner("ws://%s:%s" % (host, port), "raumfeld")
    runner.run(Component)
