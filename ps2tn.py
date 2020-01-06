# AUTHOR=EMARD
# LICENSE=BSD

import socket
import network
import uos
import gc
from time import sleep_ms, localtime
from micropython import alloc_emergency_exception_buf
import ps2

# constant definitions
_SO_REGISTER_HANDLER = const(20)
_COMMAND_TIMEOUT = const(300)

# Global variables
ps2socket = None
client_list = []
verbose_l = 0
client_busy = False

# ASCII to PS/2 SET2 scancode conversion table
asc2scan = {
'`'         : b'\x0E\xF0\x0E',
'1'         : b'\x16\xF0\x16',
'2'         : b'\x1E\xF0\x1E',
'3'         : b'\x26\xF0\x26',
'4'         : b'\x25\xF0\x25',
'5'         : b'\x2E\xF0\x2E',
'6'         : b'\x36\xF0\x36',
'7'         : b'\x3D\xF0\x3D',
'8'         : b'\x3E\xF0\x3E',
'9'         : b'\x46\xF0\x46',
'0'         : b'\x45\xF0\x45',
'-'         : b'\x4E\xF0\x4E',
'='         : b'\x55\xF0\x55',
'\x7F'      : b'\x66\xF0\x66',# BACKSPACE
'\t'        : b'\x0D\xF0\x0D',# TAB
'q'         : b'\x15\xF0\x15',
'w'         : b'\x1D\xF0\x1D',
'e'         : b'\x24\xF0\x24',
'r'         : b'\x2D\xF0\x2D',
't'         : b'\x2C\xF0\x2C',
'y'         : b'\x35\xF0\x35',
'u'         : b'\x3C\xF0\x3C',
'i'         : b'\x43\xF0\x43',
'o'         : b'\x44\xF0\x44',
'p'         : b'\x4D\xF0\x4D',
'{'         : b'\x54\xF0\x54',
'}'         : b'\x5B\xF0\x5B',
#'CAPSLOCK'  : \x58,
'a'         : b'\x1C\xF0\x1C',
's'         : b'\x1B\xF0\x1B',
'd'         : b'\x23\xF0\x23',
'f'         : b'\x2B\xF0\x2B',
'g'         : b'\x34\xF0\x34',
'h'         : b'\x33\xF0\x33',
'j'         : b'\x3B\xF0\x3B',
'k'         : b'\x42\xF0\x42',
'l'         : b'\x4B\xF0\x4B',
':'         : b'\x4C\xF0\x4C',
'\''        : b'\x52\xF0\x52',
'\r'        : b'\x5A\xF0\x5A',# ENTER
#'LEFTSHIFT' : \x12,
'z'         : b'\x1A\xF0\x1A',
'x'         : b'\x22\xF0\x22',
'c'         : b'\x21\xF0\x21',
'v'         : b'\x2A\xF0\x2A',
'b'         : b'\x32\xF0\x32',
'n'         : b'\x31\xF0\x31',
'm'         : b'\x3A\xF0\x3A',
','         : b'\x41\xF0\x41',
'.'         : b'\x49\xF0\x49',
'/'         : b'\x4A\xF0\x4A',
#'RIGHTSHIFT': \x59,
#'LEFTCTRL'  : \x14,
#'LEFTALT'   : \x11,
' '         : b'\x29\xF0\x29',
#'RIGHTALT'  :(\x11 | \x80),
#'RIGHTCTRL' :(\x14 | \x80),
#'INSERT'    :(\x70 | \x80),
#'DELETE'    :(\x71 | \x80),
#'HOME'      :(\x6C | \x80),
#'END'       :(\x69 | \x80),
#'PAGEUP'    :(\x7D | \x80),
#'PAGEDOWN'  :(\x7A | \x80),
#'UP'        :(\x75 | \x80),
#'DOWN'      :(\x72 | \x80),
#'LEFT'      :(\x6B | \x80),
#'RIGHT'     :(\x74 | \x80),
#'NUMLOCK'   :(\x77 | \x80),
#'KP7'       : \x6C,
#'KP4'       : \x6B,
#'KP1'       : \x69,
#'KPSLASH'   :(\x4A | \x80),
#'KP8'       : \x75,
#'KP5'       : \x73,
#'KP2'       : \x72,
#'KP0'       : \x70,
#'KPASTERISK': \x7C,
#'KP9'       : \x7D,
#'KP6'       : \x74,
#'KP3'       : \x7A,
#'KPPLUS'    : \x79,
#'KPENTER'   :(\x5A | \x80),
'\x1B'       : b'\x76\xF0\x76',# ESC
#'F1'        : \x05,
#'F2'        : \x06,
#'F3'        : \x04,
#'F4'        : \x0C,
#'F5'        : \x03,
#'F6'        : \x0B,
#'F7'        : \x83,
#'F8'        : \x0A,
#'F9'        : \x01,
#'F10'       : \x09,
#'F11'       : \x78,
#'F12'       : \x07,
#'SCROLLLOCK': \x7E,
'\\'         : b'\x5D\xF0\x5D',
'\x01'       : b'\x14\x1C\xF0\x1C\xF0\x14',# Ctrl-A
'\x02'       : b'\x14\x32\xF0\x32\xF0\x14',# Ctrl-B
'\x03'       : b'\x14\x21\xF0\x21\xF0\x14',# Ctrl-C
'\x04'       : b'\x14\x23\xF0\x23\xF0\x14',# Ctrl-D
'\x05'       : b'\x14\x24\xF0\x24\xF0\x14',# Ctrl-E
'\x06'       : b'\x14\x2B\xF0\x2B\xF0\x14',# Ctrl-F
'\x07'       : b'\x14\x34\xF0\x34\xF0\x14',# Ctrl-G
'\x08'       : b'\x14\x33\xF0\x33\xF0\x14',# Ctrl-H
'\x09'       : b'\x14\x43\xF0\x43\xF0\x14',# Ctrl-I
'\x0A'       : b'\x14\x3B\xF0\x3B\xF0\x14',# Ctrl-J
'\x0B'       : b'\x14\x42\xF0\x42\xF0\x14',# Ctrl-K
'\x0C'       : b'\x14\x4B\xF0\x4B\xF0\x14',# Ctrl-L
#'\x0D'       : b'\x14\x3A\xF0\x3A\xF0\x14',# Ctrl-M ENTER
'\x0E'       : b'\x14\x31\xF0\x31\xF0\x14',# Ctrl-N
'\x0F'       : b'\x14\x44\xF0\x44\xF0\x14',# Ctrl-O
'\x10'       : b'\x14\x4D\xF0\x4D\xF0\x14',# Ctrl-P
'\x11'       : b'\x14\x15\xF0\x15\xF0\x14',# Ctrl-Q
'\x12'       : b'\x14\x2D\xF0\x2D\xF0\x14',# Ctrl-R
'\x13'       : b'\x14\x1B\xF0\x1B\xF0\x14',# Ctrl-S
'\x14'       : b'\x14\x2C\xF0\x2C\xF0\x14',# Ctrl-T
'\x15'       : b'\x14\x3C\xF0\x3C\xF0\x14',# Ctrl-U
'\x16'       : b'\x14\x2A\xF0\x2A\xF0\x14',# Ctrl-V
'\x17'       : b'\x14\x1D\xF0\x1D\xF0\x14',# Ctrl-W
'\x18'       : b'\x14\x22\xF0\x22\xF0\x14',# Ctrl-X
'\x19'       : b'\x14\x35\xF0\x35\xF0\x14',# Ctrl-Y
'\x1A'       : b'\x14\x1A\xF0\x1A\xF0\x14',# Ctrl-Z
'A'          : b'\x12\x1C\xF0\x1C\xF0\x12',
'B'          : b'\x12\x32\xF0\x32\xF0\x12',
'C'          : b'\x12\x21\xF0\x21\xF0\x12',
'D'          : b'\x12\x23\xF0\x23\xF0\x12',
'E'          : b'\x12\x24\xF0\x24\xF0\x12',
'F'          : b'\x12\x2B\xF0\x2B\xF0\x12',
'G'          : b'\x12\x34\xF0\x34\xF0\x12',
'H'          : b'\x12\x33\xF0\x33\xF0\x12',
'I'          : b'\x12\x43\xF0\x43\xF0\x12',
'J'          : b'\x12\x3B\xF0\x3B\xF0\x12',
'K'          : b'\x12\x42\xF0\x42\xF0\x12',
'L'          : b'\x12\x4B\xF0\x4B\xF0\x12',
'M'          : b'\x12\x3A\xF0\x3A\xF0\x12',
'N'          : b'\x12\x31\xF0\x31\xF0\x12',
'O'          : b'\x12\x44\xF0\x44\xF0\x12',
'P'          : b'\x12\x4D\xF0\x4D\xF0\x12',
'Q'          : b'\x12\x15\xF0\x15\xF0\x12',
'R'          : b'\x12\x2D\xF0\x2D\xF0\x12',
'S'          : b'\x12\x1B\xF0\x1B\xF0\x12',
'T'          : b'\x12\x2C\xF0\x2C\xF0\x12',
'U'          : b'\x12\x3C\xF0\x3C\xF0\x12',
'V'          : b'\x12\x2A\xF0\x2A\xF0\x12',
'W'          : b'\x12\x1D\xF0\x1D\xF0\x12',
'X'          : b'\x12\x22\xF0\x22\xF0\x12',
'Y'          : b'\x12\x35\xF0\x35\xF0\x12',
'Z'          : b'\x12\x1A\xF0\x1A\xF0\x12',
}


class PS2_client:

    def __init__(self, ps2socket):
        self.command_client, self.remote_addr = ps2socket.accept()
        self.command_client.setblocking(False)
        self.command_client.sendall(bytes([255, 252, 34])) # dont allow line mode
        self.command_client.sendall(bytes([255, 251,  1])) # turn off local echo
        self.command_client.recv(32) # drain junk
        sleep_ms(20)
        self.command_client.recv(32) # drain junk
        self.remote_addr = self.remote_addr[0]
        #self.command_client.settimeout(_COMMAND_TIMEOUT)
        log_msg(1, "PS2 Command connection from:", self.remote_addr)
        self.command_client.setsockopt(socket.SOL_SOCKET,
                                       _SO_REGISTER_HANDLER,
                                       self.exec_ps2_command)
        self.act_data_addr = self.remote_addr
        self.active = True

    def exec_ps2_command(self, cl):
        global client_busy
        global my_ip_addr
        global ps2port

        #try:
        if True:
            gc.collect()

            data = cl.recv(32)

            if len(data) <= 0:
                # No data, close
                log_msg(1, "*** No data, assume QUIT")
                close_client(cl)
                return

            if client_busy:  # check if another client is busy
                #cl.sendall("400 Device busy.\r\n")  # tell so the remote client
                return  # and quit

            client_busy = True  # now it's my turn
            sdata = str(data, "utf-8")
            #print(sdata)
            for cdata in sdata:
              if cdata in asc2scan:
                code = bytearray(asc2scan[cdata])
                for scancode in code:
                  ps2port.write(bytearray([scancode]))
            client_busy = False
            return

        #except Exception as err:
        #    log_msg(1, "Exception in exec_ps2_command: {}".format(err))


def log_msg(level, *args):
    global verbose_l
    if verbose_l >= level:
        print(*args)


# close client and remove it from the list
def close_client(cl):
    cl.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
    cl.close()
    for i, client in enumerate(client_list):
        if client.command_client == cl:
            del client_list[i]
            break


def accept_ps2_connect(ps2socket):
    # Accept new calls for the server
    try:
        client_list.append(PS2_client(ps2socket))
    except:
        log_msg(1, "Attempt to connect failed")
        # try at least to reject
        try:
            temp_client, temp_addr = ps2socket.accept()
            temp_client.close()
        except:
            pass


def stop():
    global ps2socket
    global client_list
    global client_busy
    global ps2port

    for client in client_list:
        client.command_client.setsockopt(socket.SOL_SOCKET,
                                         _SO_REGISTER_HANDLER, None)
        client.command_client.close()
    del client_list
    client_list = []
    client_busy = False
    if ps2socket is not None:
        ps2socket.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
        ps2socket.close()
    del ps2port


# start listening for ftp connections on port 21
def start(port=23, verbose=0, splash=True):
    global ps2socket
    global verbose_l
    global client_list
    global client_busy
    global ps2port
    
    ps2port=ps2.ps2()

    alloc_emergency_exception_buf(100)
    verbose_l = verbose
    client_list = []
    client_busy = False

    ps2socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ps2socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ps2socket.bind(('0.0.0.0', port))
    ps2socket.listen(0)
    ps2socket.setsockopt(socket.SOL_SOCKET,
                         _SO_REGISTER_HANDLER, accept_ps2_connect)


def restart(port=23, verbose=0, splash=True):
    stop()
    sleep_ms(200)
    start(port, verbose, splash)


start(splash=True)
