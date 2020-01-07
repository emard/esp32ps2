# micropython ESP32
# PS/2 protocol emulator (keyboard and mouse, transmit-only)

# AUTHOR=EMARD
# LICENSE=BSD

from time import sleep_us
from machine import Pin
from micropython import const
from uctypes import addressof

class ps2:
  def __init__(self, clk=26, data=25, qbit_ms=16, byte_ms=20000):
    self.gpio_ps2_clk  = clk
    self.gpio_ps2_data = data
    self.init_pins()
    self.qdelay = qbit_ms # quarter-bit delay
    self.cdelay = byte_ms # byte-to-byte delay

  def init_pins(self):
    #self.ps2_clk  = Pin(self.gpio_ps2_clk,  Pin.OPEN_DRAIN, Pin.PULL_UP)
    #self.ps2_data = Pin(self.gpio_ps2_data, Pin.OPEN_DRAIN, Pin.PULL_UP)
    self.ps2_clk  = Pin(self.gpio_ps2_clk,  Pin.OUT)
    self.ps2_data = Pin(self.gpio_ps2_data, Pin.OUT)
    self.ps2_clk.on()
    self.ps2_data.on()

  @micropython.viper
  def write(self, data):
    qdelay = int(self.qdelay)
    p = ptr8(addressof(data))
    l = int(len(data))
    for i in range(l):
      val = p[i]
      parity = 1
      self.ps2_data.off()
      sleep_us(qdelay)
      self.ps2_clk.off()
      sleep_us(qdelay+qdelay)
      self.ps2_clk.on()
      sleep_us(qdelay)
      for nf in range(8):
        if val & 1:
          self.ps2_data.on()
          parity ^= 1
        else:
          self.ps2_data.off()
          parity ^= 0 # keep timing the same as above
        sleep_us(qdelay)
        self.ps2_clk.off()
        val >>= 1
        sleep_us(qdelay+qdelay)
        self.ps2_clk.on()
        sleep_us(qdelay)
      if parity:
        self.ps2_data.on()
      else:
        self.ps2_data.off()
      sleep_us(qdelay)
      self.ps2_clk.off()
      sleep_us(qdelay+qdelay)
      self.ps2_clk.on()
      sleep_us(qdelay)
      self.ps2_data.on()
      sleep_us(qdelay)
      self.ps2_clk.off()
      sleep_us(qdelay+qdelay)
      self.ps2_clk.on()
      sleep_us(self.cdelay)
