# AUTHOR=EMARD
# LICENSE=BSD

# PS/2 receiver converts from TCP to PS/2
# use linux_keyboard.py or pygame_mouse.py on host side
# edit ps2port (see below)

import socket
import network
import uos
import gc
from time import sleep_us
from struct import unpack
from micropython import alloc_emergency_exception_buf
from micropython import const
from uctypes import addressof
import ps2

# keyboard
ps2port=ps2.ps2(qbit_us=16,byte_us=150)

# 3-byte mouse (PS/2 legacy, no wheel)
#ps2port=ps2.ps2(qbit_us=16,byte_us=150,f0_us=0,n=3,n_us=1000)

# 4-byte mouse (PS/2 with wheel)
#ps2port=ps2.ps2(qbit_us=16,byte_us=150,f0_us=0,n=4,n_us=1000)

# constant definitions
_SO_REGISTER_HANDLER = const(20)
_COMMAND_TIMEOUT = const(300)

# Global variables
ps2socket = None
client_list = []
verbose_l = 0
client_busy = False


class PS2_client:

    def __init__(self, ps2socket):
        self.command_client, self.remote_addr = ps2socket.accept()
        self.remote_addr = self.remote_addr[0]
        self.command_client.settimeout(_COMMAND_TIMEOUT)
        log_msg(1, "PS2 Command connection from:", self.remote_addr)
        self.command_client.setsockopt(socket.SOL_SOCKET,
                                       _SO_REGISTER_HANDLER,
                                       self.exec_ps2_command)
        # simple PS/2 packet parser state
        self.state = 0
        self.length = 0
        self.index = 0
        self.wait = 0 # 0 sending, 1 waiting
        self.mouse = 0 # 0 keyboard 1 mouse
        self.packet = bytearray(256)

    def packet_parser(self, data):
        for val in data:
            if self.state == 0: # K/M/W
                if val == 75: # K
                    #print("K")
                    if self.mouse != 0:
                        self.mouse = 0
                        ps2port.keyboard()
                    self.state = 1
                if val == 77: # M
                    #print("M")
                    if self.mouse != 1:
                        self.mouse = 1
                        ps2port.mouse()
                    self.state = 1
                if val == 87: # W
                    #print("W")
                    self.wait = 1
                    self.state = 1
                continue
            if self.state == 1: # length
                self.length = val
                self.index = 0
                self.state = 2
                continue
            if self.state == 2: # packet data
                self.packet[self.index] = val
                #print(val, self.index, self.length)
                self.index += 1
                if self.index >= self.length:
                  if self.wait:
                    sleep_us(unpack("<H", self.packet[0:2])[0])
                    #print("Wait %d" % (unpack("<H", self.packet[0:2])[0]))
                    self.wait = 0
                  else:
                    ps2port.write(self.packet[0:self.length])
                    #print(self.packet[0:self.length])
                  self.state = 0
                continue


    def exec_ps2_command(self, cl):
        global client_busy
        global my_ip_addr
        global ps2port

        #try:
        if True:
            #gc.collect()

            data = cl.recv(32)

            if len(data) <= 0:
                # No data, close
                log_msg(1, "*** No data, assume QUIT")
                close_client(cl)
                return

            if client_busy:  # check if another client is busy
                return  # and quit

            client_busy = True  # now it's my turn
            #ps2port.write(data)
            self.packet_parser(data)
            client_busy = False
            return
#        except Exception as err:
#            log_msg(1, "Exception in exec_ps2_command: {}".format(err))


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
def start(port=3252, verbose=0, splash=True):
    global ps2socket
    global verbose_l
    global client_list
    global client_busy
    global ps2port
    

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


def restart(port=3252, verbose=0, splash=True):
    stop()
    sleep_us(200000)
    start(port, verbose, splash)


start(splash=True)
