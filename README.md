# ESP32->PS/2

Micropython ESP32 code that listens at TCP port and
retransmits received packets using PS/2 protocol.

Intended use is to emulate PS/2 keyboard (and mouse after
a bit of development).

linux uinput python code receives keyboard events,
converts them to "PS/2 SET2" scancodes and
sends over TCP to ESP32.

PS/2 SET2 is standard power-on default scancode setting
for PS/2 keyboards.

Currently this code doesn't support bidirectional PS/2 so
emulated PS/2 keyboard can only send but can't receive commands
from PS/2 to e.g. detect keybard presence, blink keyboard LEDs
or change scancode set.

USAGE: you need to give user "rw" access to "/dev/input/eventX"
device which represents your keyboard:

    lsinput
    chmod a+rw /dev/input/event3

and then you should maybe edit "hostinput.py" to place keyboard name
(you have seen it using "lsinput") and run the host-side input client
as normal user:

    ./hostinput.py
