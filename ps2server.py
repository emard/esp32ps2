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
_CHUNK_SIZE = const(1024)
_SO_REGISTER_HANDLER = const(20)
_COMMAND_TIMEOUT = const(300)
_DATA_TIMEOUT = const(100)
_DATA_PORT = const(13333)

# Global variables
ftpsocket = None
client_list = []
verbose_l = 0
client_busy = False

_month_name = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


class PS2_client:

    def __init__(self, ftpsocket):
        self.command_client, self.remote_addr = ftpsocket.accept()
        self.remote_addr = self.remote_addr[0]
        self.command_client.settimeout(_COMMAND_TIMEOUT)
        log_msg(1, "PS2 Command connection from:", self.remote_addr)
        self.command_client.setsockopt(socket.SOL_SOCKET,
                                       _SO_REGISTER_HANDLER,
                                       self.exec_ftp_command)
        self.command_client.sendall("220 Hello, this is the ULX3S.\r\n")
        self.cwd = '/'
        self.fromname = None
        self.act_data_addr = self.remote_addr
        self.DATA_PORT = 20
        self.active = True

    def exec_ftp_command(self, cl):
        global client_busy
        global my_ip_addr
        global ps2port

        try:
            gc.collect()

            #data = cl.readline().decode("utf-8").rstrip("\r\n")
            data = cl.recv(1024)

            if len(data) <= 0:
                # No data, close
                # This part is NOT CLEAN; there is still a chance that a
                # closing data connection will be signalled as closing
                # command connection
                log_msg(1, "*** No data, assume QUIT")
                close_client(cl)
                return

            if client_busy:  # check if another client is busy
                cl.sendall("400 Device busy.\r\n")  # tell so the remote client
                return  # and quit

            client_busy = True  # now it's my turn
            
            cl.sendall("received %d bytes\r\n" % len(data))
            ps2port.write(data)
            
            client_busy = False
            return
        except Exception as err:
            log_msg(1, "Exception in exec_ftp_command: {}".format(err))


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


def accept_ftp_connect(ftpsocket):
    # Accept new calls for the server
    try:
        client_list.append(PS2_client(ftpsocket))
    except:
        log_msg(1, "Attempt to connect failed")
        # try at least to reject
        try:
            temp_client, temp_addr = ftpsocket.accept()
            temp_client.close()
        except:
            pass


def num_ip(ip):
    items = ip.split(".")
    return (int(items[0]) << 24 | int(items[1]) << 16 |
            int(items[2]) << 8 | int(items[3]))


def stop():
    global ftpsocket
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
    if ftpsocket is not None:
        ftpsocket.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
        ftpsocket.close()
    del ps2port

# start listening for ftp connections on port 21
def start(port=3252, verbose=0, splash=True):
    global ftpsocket
    global verbose_l
    global client_list
    global client_busy
    #global AP_addr, STA_addr
    global ps2port
    
    ps2port=ps2.ps2()

    alloc_emergency_exception_buf(100)
    verbose_l = verbose
    client_list = []
    client_busy = False

    ftpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ftpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ftpsocket.bind(('0.0.0.0', port))
    ftpsocket.listen(0)
    ftpsocket.setsockopt(socket.SOL_SOCKET,
                         _SO_REGISTER_HANDLER, accept_ftp_connect)

def restart(port=21, verbose=0, splash=True):
    stop()
    sleep_ms(200)
    start(port, verbose, splash)


start(splash=True)
