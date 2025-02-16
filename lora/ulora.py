import time
import math


import board
import busio
import digitalio

import adafruit_bus_device.spi_device as spidev

#Constants
FLAGS_ACK = 0x80
BROADCAST_ADDRESS = 255

REG_00_FIFO = 0x00
REG_01_OP_MODE = 0x01
REG_06_FRF_MSB = 0x06
REG_07_FRF_MID = 0x07
REG_08_FRF_LSB = 0x08
REG_0E_FIFO_TX_BASE_ADDR = 0x0e
REG_0F_FIFO_RX_BASE_ADDR = 0x0f
REG_10_FIFO_RX_CURRENT_ADDR = 0x10
REG_12_IRQ_FLAGS = 0x12
REG_13_RX_NB_BYTES = 0x13
REG_1D_MODEM_CONFIG1 = 0x1d
REG_1E_MODEM_CONFIG2 = 0x1e
REG_19_PKT_SNR_VALUE = 0x19
REG_1A_PKT_RSSI_VALUE = 0x1a
REG_20_PREAMBLE_MSB = 0x20
REG_21_PREAMBLE_LSB = 0x21
REG_22_PAYLOAD_LENGTH = 0x22
REG_26_MODEM_CONFIG3 = 0x26

REG_4D_PA_DAC = 0x4d
REG_40_DIO_MAPPING1 = 0x40
REG_0D_FIFO_ADDR_PTR = 0x0d

PA_DAC_ENABLE = 0x07
PA_DAC_DISABLE = 0x04
PA_SELECT = 0x80

CAD_DETECTED_MASK = 0x01
RX_DONE = 0x40
TX_DONE = 0x08
CAD_DONE = 0x04
CAD_DETECTED = 0x01

LONG_RANGE_MODE = 0x80
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RXCONTINUOUS = 0x05
MODE_CAD = 0x07

REG_09_PA_CONFIG = 0x09
FXOSC = 32000000.0
FSTEP = (FXOSC / 524288)

class ModemConfig():
    Bw125Cr45Sf128 = (0x72, 0x74, 0x04) #< Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Default medium range
    Bw500Cr45Sf128 = (0x92, 0x74, 0x04) #< Bw = 500 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Fast+short range
    Bw31_25Cr48Sf512 = (0x48, 0x94, 0x04) #< Bw = 31.25 kHz, Cr = 4/8, Sf = 512chips/symbol, CRC on. Slow+long range
    Bw125Cr48Sf4096 = (0x78, 0xc4, 0x0c) #/< Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, low data rate, CRC on. Slow+long range
    Bw125Cr45Sf2048 = (0x72, 0xb4, 0x04) #< Bw = 125 kHz, Cr = 4/5, Sf = 2048chips/symbol, CRC on. Slow+long range

class LoRa(object):
    def __init__(self, spi, CS, this_address=0, freq=868.0, tx_power=14,
                 modem_config=ModemConfig.Bw125Cr45Sf128, receive_all=False, acks=False ):
        """
        Lora(spi, CS, this_address, freq=868.0, tx_power=14,
                 modem_config=ModemConfig.Bw125Cr45Sf128, receive_all=False, acks=False)
        spi: The SPI bus connected to the radio.
        CS: The CS pin DigitalInOut connected to the radio.
        this_address: set address for this device [0-254]
        freq: frequency in MHz
        tx_power: transmit power in dBm
        modem_config: Check ModemConfig. Default is compatible with the Radiohead library
        receive_all: if True, don't filter packets on address
        acks: if True, request acknowledgments
        """
        
        self._mode = None
        self._freq = freq
        self._tx_power = tx_power
        self._receive_all = receive_all
        self._acks = acks

        self.last_rssi = None
        self.last_snr = None
        self._this_address = this_address
        self._last_header_id = 0

        self._last_payload = None

        self.send_retries = 2
        self.wait_packet_sent_timeout = 20.0
        self.retry_timeout = 0.2
        
        self._device = spidev.SPIDevice(spi, CS, baudrate=5000000, polarity=0, phase=0)
        
        # set mode
        self._spi_write(REG_01_OP_MODE, MODE_SLEEP | LONG_RANGE_MODE)
        time.sleep(0.1)
        
        # check if mode is set
        assert self._spi_read(REG_01_OP_MODE) == (MODE_SLEEP | LONG_RANGE_MODE), \
            "LoRa initialization failed"

        self._spi_write(REG_0E_FIFO_TX_BASE_ADDR, 0)
        self._spi_write(REG_0F_FIFO_RX_BASE_ADDR, 0)
        
        self.set_mode_idle()

        self.set_modem_config(modem_config)

        # set preamble length (8)
        self._spi_write(REG_20_PREAMBLE_MSB, 0)
        self._spi_write(REG_21_PREAMBLE_LSB, 8)

        # set frequency
        frf = int((self._freq * 1000000.0) / FSTEP)
        self._spi_write(REG_06_FRF_MSB, (frf >> 16) & 0xff)
        self._spi_write(REG_07_FRF_MID, (frf >> 8) & 0xff)
        self._spi_write(REG_08_FRF_LSB, frf & 0xff)
        
        # Set tx power
        if self._tx_power < 5:
            self._tx_power = 5
        if self._tx_power > 23:
            self._tx_power = 23

        if self._tx_power > 20:
            self._spi_write(REG_4D_PA_DAC, PA_DAC_ENABLE)
            self._tx_power -= 3
        else:
            self._spi_write(REG_4D_PA_DAC, PA_DAC_DISABLE)

        self._spi_write(REG_09_PA_CONFIG, PA_SELECT | (self._tx_power - 5))
        

    def set_modem_config(self, modem_config):
        self.set_mode_idle()

        # set modem config
        self._spi_write(REG_1D_MODEM_CONFIG1, modem_config[0])
        self._spi_write(REG_1E_MODEM_CONFIG2, modem_config[1])
        self._spi_write(REG_26_MODEM_CONFIG3, modem_config[2])


    def sleep(self):
        if self._mode != MODE_SLEEP:
            self._spi_write(REG_01_OP_MODE, MODE_SLEEP)
            self._mode = MODE_SLEEP

    def set_mode_tx(self):
        if self._mode != MODE_TX:
            self._spi_write(REG_01_OP_MODE, MODE_TX)
            self._spi_write(REG_40_DIO_MAPPING1, 0x40)  # Interrupt on TxDone
            self._mode = MODE_TX

    def set_mode_rx(self):
        if self._mode != MODE_RXCONTINUOUS:
            self._spi_write(REG_01_OP_MODE, MODE_RXCONTINUOUS)
            self._spi_write(REG_40_DIO_MAPPING1, 0x00)  # Interrupt on RxDone
            self._mode = MODE_RXCONTINUOUS
            
    def set_mode_idle(self):
        if self._mode != MODE_STDBY:
            self._spi_write(REG_01_OP_MODE, MODE_STDBY)
            self._mode = MODE_STDBY

    def broadcast(self, data, header_id=0, header_flags=0):
        return self.send(data, destination=BROADCAST_ADDRESS, header_id=header_id, header_flags=header_flags)
    
    def send(self, data, destination, header_id=0, header_flags=0):
        self.set_mode_idle()

        header = [destination, self._this_address, header_id, header_flags]
        if type(data) == int:
            data = [data]
        elif type(data) == bytes:
            data = [p for p in data]
        elif type(data) == str:
            data = [ord(s) for s in data]

        payload = header + data
        self._spi_write(REG_0D_FIFO_ADDR_PTR, 0)
        self._spi_write(REG_00_FIFO, payload)
        self._spi_write(REG_22_PAYLOAD_LENGTH, len(payload))

        self.set_mode_tx()
        start = time.monotonic()
        msg_sent=False
        while time.monotonic() - start < self.wait_packet_sent_timeout:
            irq_flags = self._spi_read(REG_12_IRQ_FLAGS)
            if (irq_flags & TX_DONE) >> 3:
                msg_sent=True
                break

        self._spi_write(REG_12_IRQ_FLAGS, 0xff)  # Clear all IRQ flags
        self.set_mode_idle()
        return msg_sent

    def receive(self, timeout=5.0, from_id=None):
        self.set_mode_rx()
        start = time.monotonic()
        message=None
        header_from = None
        while time.monotonic() - start < timeout:
            irq_flags = self._spi_read(REG_12_IRQ_FLAGS)

            if (irq_flags & RX_DONE) >> 6:
                self.set_mode_idle()
                packet_len = self._spi_read(REG_13_RX_NB_BYTES)
                self._spi_write(REG_0D_FIFO_ADDR_PTR, self._spi_read(REG_10_FIFO_RX_CURRENT_ADDR))

                packet = self._spi_read(REG_00_FIFO, packet_len)

                snr = self._spi_read(REG_19_PKT_SNR_VALUE) / 4
                rssi = self._spi_read(REG_1A_PKT_RSSI_VALUE)

                if snr < 0:
                    rssi = snr + rssi
                else:
                    rssi = rssi * 16 / 15

                if self._freq >= 779:
                    rssi = round(rssi - 157, 2)
                else:
                    rssi = round(rssi - 164, 2)

                self.last_rssi = rssi
                self.last_snr = snr


                if packet_len >= 4:
                    header_to = packet[0]
                    header_from = packet[1]
                    if (header_to == self._this_address or header_to == BROADCAST_ADDRESS) and (header_from == from_id or from_id is None):
                        header_id = packet[2]
                        header_flags = packet[3]
                        message = bytes(packet[4:]) if packet_len > 4 else b''

                        self.last_msg = message
                break

        self.set_mode_idle()
        self._spi_write(REG_12_IRQ_FLAGS, 0xff)

        if from_id is None:
            return message, header_from
        return message




    def _spi_write(self, register, payload):
        if type(payload) == int:
            payload = [payload]
        elif type(payload) == bytes:
            payload = [p for p in payload]
        elif type(payload) == str:
            payload = [ord(s) for s in payload]

        #print('------------')
        #print(len(payload))
        #'for p in payload: 
        #    print(p)
        #print('------------')
        with self._device as device:
            device.write(bytearray([register | 0x80] + payload))

    def _spi_read(self, register, length=1):
        buf = bytearray(length)

        with self._device as device:
            buf[0] = register & 0x7F
            device.write(buf,end=1)
            device.readinto(buf, end=length)

        if length==1:
            return buf[0]
        else:
            return buf
        

