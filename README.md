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

# ESP32 PS/2 pins

this default pinout is recommended for ULX3S, but of course
any other free pins can be used:

    assign ps2_clk  = gp[11]; // wifi_gpio26
    assign ps2_data = gn[11]; // wifi_gpio25

# telnet input

ESP32: upload "ps2tn.py" and "ps2.py"

    import ps2tn

telnet to ESP32 and start typing. "ps2tn" should echo typed chars.

    telnet 192.168.4.1

# linux input

ESP32: upload "ps2recv.py" and "ps2.py"

    import ps2recv

for linux input, you need to give user "rw" access to "/dev/input/eventX"
device which represents your keyboard:

    lsinput
    chmod a+rw /dev/input/event3

and then you should maybe edit "linux_keyboard.py" to place keyboard name
(you have seen it using "lsinput") and run the host-side input client
as normal user:

    ./linux_keyboard.py

# pygame input

ESP32: edit ps2recv.py to set mouse type
(wheel or no wheel), upload "ps2recv.py" and "ps2.py"

    import ps2recv

pygame will open a window that will grab mouse. Press any key to quit.

    ./pygame_mouse.py

# TODO

[x] E0-scancodes
[x] telnet interface
[ ] unify keyboard mouse and joystick, use simple protocol
