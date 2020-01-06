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
'`'         : 0x0E,
'1'         : 0x16,
'2'         : 0x1E,
'3'         : 0x26,
'4'         : 0x25,
'5'         : 0x2E,
'6'         : 0x36,
'7'         : 0x3D,
'8'         : 0x3E,
'9'         : 0x46,
'0'         : 0x45,
'-'         : 0x4E,
'='         : 0x55,
'\x7F'      : 0x66, # BACKSPACE
'\t'        : 0x0D, # TAB
'q'         : 0x15,
'w'         : 0x1D,
'e'         : 0x24,
'r'         : 0x2D,
't'         : 0x2C,
'y'         : 0x35,
'u'         : 0x3C,
'i'         : 0x43,
'o'         : 0x44,
'p'         : 0x4D,
'{'         : 0x54,
'}'         : 0x5B,
#'CAPSLOCK'  : 0x58,
'a'         : 0x1C,
's'         : 0x1B,
'd'         : 0x23,
'f'         : 0x2B,
'g'         : 0x34,
'h'         : 0x33,
'j'         : 0x3B,
'k'         : 0x42,
'l'         : 0x4B,
':'         : 0x4C,
'\''        : 0x52,
'\r'        : 0x5A, # ENTER
#'LEFTSHIFT' : 0x12,
'z'         : 0x1A,
'x'         : 0x22,
'c'         : 0x21,
'v'         : 0x2A,
'b'         : 0x32,
'n'         : 0x31,
'm'         : 0x3A,
','         : 0x41,
'.'         : 0x49,
'/'         : 0x4A,
#'RIGHTSHIFT': 0x59,
#'LEFTCTRL'  : 0x14,
#'LEFTALT'   : 0x11,
' '         : 0x29,
#'RIGHTALT'  :(0x11 | 0x80),
#'RIGHTCTRL' :(0x14 | 0x80),
#'INSERT'    :(0x70 | 0x80),
#'DELETE'    :(0x71 | 0x80),
#'HOME'      :(0x6C | 0x80),
#'END'       :(0x69 | 0x80),
#'PAGEUP'    :(0x7D | 0x80),
#'PAGEDOWN'  :(0x7A | 0x80),
#'UP'        :(0x75 | 0x80),
#'DOWN'      :(0x72 | 0x80),
#'LEFT'      :(0x6B | 0x80),
#'RIGHT'     :(0x74 | 0x80),
#'NUMLOCK'   :(0x77 | 0x80),
#'KP7'       : 0x6C,
#'KP4'       : 0x6B,
#'KP1'       : 0x69,
#'KPSLASH'   :(0x4A | 0x80),
#'KP8'       : 0x75,
#'KP5'       : 0x73,
#'KP2'       : 0x72,
#'KP0'       : 0x70,
#'KPASTERISK': 0x7C,
#'KP9'       : 0x7D,
#'KP6'       : 0x74,
#'KP3'       : 0x7A,
#'KPPLUS'    : 0x79,
#'KPENTER'   :(0x5A | 0x80),
'\x1B'       : 0x76, # ESC
#'F1'        : 0x05,
#'F2'        : 0x06,
#'F3'        : 0x04,
#'F4'        : 0x0C,
#'F5'        : 0x03,
#'F6'        : 0x0B,
#'F7'        : 0x83,
#'F8'        : 0x0A,
#'F9'        : 0x01,
#'F10'       : 0x09,
#'F11'       : 0x78,
#'F12'       : 0x07,
#'SCROLLLOCK': 0x7E,
'\\'         : 0x5D,
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
        self.command_client.settimeout(_COMMAND_TIMEOUT)
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
                code = asc2scan[cdata]
                ps2port.write(bytearray([code]))
                #print("scan %02X" % code)
                ps2port.write(bytearray([0xF0, code]))
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
