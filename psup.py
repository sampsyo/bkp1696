from __future__ import division
import serial
import glob
import time
import decimal

def _str2num(num, factor=10):
    """Takes a number in the supply's format, which always has one
    decimal place, and returns a decimal number reflecting it.
    """
    return decimal.Decimal(num) / factor
def _num2str(s, length=3, factor=10):
    """Turns a number, which may be a decimal, integer, or float,
    and turns it into a supply-formatted string.
    """
    dec = decimal.Decimal(s)
    return ('%0' + str(length) + 'i') % int(dec * factor)
def _numfields(s, fields, factor=10):
    """Generates numbers of the given lengths in the string.
    """
    pos = 0
    for field in fields:
        yield _str2num(s[pos:pos+field], factor)
        pos += field

class Supply(object):
    def __init__(self, ident=None):
        if not ident:
            # Discover a device.
            devices = glob.glob('/dev/tty.PL*') # Mac OS X
            devices += glob.glob('/dev/ttyUSB*') # Linux
            ident = devices[0]
        self.ser = serial.Serial(ident, 9600, 8, 'N', 1)

    def command(self, code, param='', address='00'):
        # Put this communication in an isolated little transaction.
        self.ser.flushInput()
        self.ser.flushOutput()

        self.ser.write(code + address + param + "\r")
        self.ser.flush()

        out = None
        while True:
            # Read until CR.
            resp = ''
            while True:
                char = self.ser.read()
                resp += char
                if char == '\r':
                    break

            if resp == 'OK\r':
                return out

            if out is not None:
                print 'received more than one line of output without OK!'
                return resp

            out = resp

    def start(self):
        self.command('SESS')
    def close(self):
        self.command('ENDS')
    def voltage(self, volts):
        self.command('VOLT', _num2str(volts))
    def reading(self):
        resp = self.command('GETD')
        volts, amps = _numfields(resp, (4, 4), 1)
        return volts/100, amps/1000
    def maxima(self):
        resp = self.command('GMAX')
        return tuple(_numfields(resp, (3, 3)))
    def settings(self):
        resp = self.command('GETS')
        return tuple(_numfields(resp, (3, 3)))
    def enable(self):
        """Enable output."""
        self.command('SOUT', '0')
    def disable(self):
        """Disable output."""
        self.command('SOUT', '1')

    # Context manager.
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

# Just some tests to show it's working.
if __name__ == '__main__':
    with Supply() as sup:
        time.sleep(0.5)
        sup.voltage(1.3)
        sup.enable()
        time.sleep(0.5)
        print 'Reading', sup.reading()
        print 'Maxima', sup.maxima()
        print 'Settings', sup.settings()
        sup.disable()
        print 'Disabled; reading', sup.reading()
        time.sleep(0.5)
