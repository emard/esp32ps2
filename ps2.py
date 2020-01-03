# micropython ESP32
# PS/2 keyboard and mouse emulator

# AUTHOR=EMARD
# LICENSE=BSD

from time import sleep_us
from machine import SPI, Pin
from micropython import const
from uctypes import addressof

class ps2:
  def __init__(self, port=3252):
    print("PS/2 emulator")
    self.led = Pin(5, Pin.OUT)
    self.led.off()
    self.spi_channel = const(-1)
    self.init_pinout() # communicate using SD card pins when SD is inactive
    self.init_pins()
    #self.spi_freq = const(12000)
    #self.ps2=SPI(self.spi_channel, baudrate=self.spi_freq, polarity=0, phase=0, bits=11, firstbit=SPI.MSB, sck=Pin(self.gpio_sck), mosi=Pin(self.gpio_mosi), miso=Pin(self.gpio_miso))
    self.count = 0
    self.count_prev = 0
    self.key_event = Pin(0, Pin.IN, Pin.PULL_UP)
    self.key_event.irq(trigger=Pin.IRQ_FALLING, handler=self.irq_handler)

  @micropython.viper
  def init_pinout(self):
    self.gpio_kbd_clk  = const(14) # sd_clk
    self.gpio_kbd_data = const(15) # sd_cmd

  def init_pins(self):
    self.kbd_clk  = Pin(self.gpio_kbd_clk,  Pin.OUT)
    self.kbd_data = Pin(self.gpio_kbd_data, Pin.OUT)

  @micropython.viper
  def irq_handler(self, pin):
    self.count += const(1)

  @micropython.viper
  def ps2write(self, data):
    p = ptr8(addressof(data))
    l = int(len(data))
    for i in range(l):
      val = p[i]
      parity = 0
      self.kbd_data.off()
      self.kbd_clk.off()
      sleep_us(30)
      self.kbd_clk.on()
      sleep_us(30)
      for nf in range(8):
        if val & 1:
          self.kbd_data.on()
          parity ^= 1
        else:
          self.kbd_data.off()
        val >>= 1
        self.kbd_clk.off()
        sleep_us(30)
        self.kbd_clk.on()
        sleep_us(30)
      if parity:
        self.kbd_data.on()
      else:
        self.kbd_data.off()
      self.kbd_clk.off()
      sleep_us(30)
      self.kbd_clk.on()
      sleep_us(30)
      self.kbd_data.on()
      self.kbd_clk.off()
      sleep_us(30)
      self.kbd_clk.on()
      sleep_us(30)

  #@micropython.viper
  def run(self):
    key_press   = bytearray([0x10])
    key_release = bytearray([0x10 | 0x80])
    while(True):
      if self.count != self.count_prev:
        self.led.on()
        self.ps2write(key_press)
        self.ps2write(key_release)
        self.led.off()
        self.count_prev = self.count
        print("%d" % self.count)
