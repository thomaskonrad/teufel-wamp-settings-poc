# Proof of Concept: Control Teufel Audio Settings via the Network

This is a proof of concept that lets you control some settings of your Teufel audio system through the network.
It uses the WAMP protocol which is usually exposed on port 55555 on your Teufel main host.


## Set and Subscribe To Settings

The script lets you write settings.
Also, the script automatically subscribes to changes of the selected setting on your Teufel system.
So you will always get the current setting value, even if you set the value through your infrared remote.


## Sample Output

Here's a sample output:

```
$ python3 main.py
Please enter the Teufel main host [10.0.0.21]: 
Please enter the Teufel WebSocket port [55555]: 

Available players:

    [UID "uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"] "Speaker Mobiler Lautsprecher" in room "Mobiler Lautsprecher"
    [UID "uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"] "Speaker Soundbar Wohnzimmer" in room "Soundbar Wohnzimmer"

Please choose a player UID [uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx]: uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Available settings:

    Setting "audio_input_source"
    Setting "sound_mode"
    Setting "display_max_brightness"
    Setting "led_brightness"
    Setting "auto_standby_delay"

Please choose a setting you want to subscribe to and/or change [audio_input_source]: audio_input_source
Please set a value for setting "audio_input_source": 3
Please set a value for setting "audio_input_source": 
    Received updated setting from the player. New value: 3
Please set a value for setting "audio_input_source": 2
Please set a value for setting "audio_input_source": 
    Received updated setting from the player. New value: 2
```
