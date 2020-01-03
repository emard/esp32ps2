# ESP32->PS/2

Micropython ESP32 code that listens at UDP port and
retransmits received packets using PS/2 protocol.

Intended use is to emulate PS/2 keyboard and mouse.

linux uinput python code receives keyboard and mouse
events, converts it to PS/2 scancodes and sends as UDP packets
to ESP32.
