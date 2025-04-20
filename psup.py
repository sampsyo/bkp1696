
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
    def __init__(self, ident=None,timeout=0.0,verbose=False):
        if not ident:
            # Discover a device.
            devices = glob.glob('/dev/tty.PL*') # Mac OS X
            devices += glob.glob('/dev/ttyUSB*') # Linux
            ident = devices[0]
        self.verbose=verbose
        if self.verbose:
            print("Serial Port: ",ident)
        self.ser = serial.Serial(port=ident, baudrate=9600, bytesize=8, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,timeout=timeout)

    def command(self, code, param='', address='00'):
        # Put this communication in an isolated little transaction.
        self.ser.flushInput()
        self.ser.flushOutput()

        command_string = code + address + param + "\r"
        if self.verbose:
            print("Send", command_string)
        command_bytes = command_string.encode('utf-8')  # Encode the string to bytes using UTF-8
        self.ser.write(command_bytes)
        self.ser.flush()

        out = None
        while True:
            # Read until CR.
            resp = ''
            while True:
                char = self.ser.read()
                if char == b'':
                    break
                resp += char.decode('ascii')
                if char == b'\r':
                    break

            if resp == '':
                if self.verbose:
                    print('Received no data in timeout period')
                return None

            if resp == 'OK\r':
#                print(f"Got OK {out}")
                if out is None:
                    return ""
                else:
                    return out

            if out is None:
                out = resp
            else:
                out += resp

    def start(self):
        return self.command('SESS')

    def close(self):
        return self.command('ENDS')

    def current(self, amps):
        return self.command('CURR', _num2str(amps,factor=100))

    def voltage(self, volts):
        return self.command('VOLT', _num2str(volts))

    def reading(self):
        resp = self.command('GETD')
        if resp is not None:
            volts, amps = _numfields(resp, (4, 4), 1)
            return volts/100, amps/1000
        else:
            return None

    def maxima(self):
        resp = self.command('GMAX')
        if resp is not None:
            return tuple(_numfields(resp, (3, 3)))
        else:
            return None

    def memory(self):
        mem=self.command('GETM')
        mem_split=mem.split()
        mem_list=[]
        for line in mem_split:
            volts,amps = tuple(_numfields(line, (3, 3)))
            amps=amps/10
            mem_list.append([float(volts),float(amps)])
        return (mem_list)

    def program(self):
        mem=self.command('GETP')
        mem_split=mem.split()
        mem_list=[]
        for line in mem_split:
            volts,amps, minutes,seconds = tuple(_numfields(line, (3, 3, 2, 2),1))
            volts=volts/10
            amps=amps/100
            mem_list.append([float(volts),float(amps),int(minutes),int(seconds)])
        return (mem_list)


    def program_set_step(self,step,voltage,amps,minute,seconds):
        params=""
        params+=_num2str(step,length=2,factor=1)
        params+=_num2str(voltage,length=3,factor=10)
        params+=_num2str(amps,length=3,factor=100)
        params+=_num2str(minute,length=2,factor=1)
        params+=_num2str(seconds,length=2,factor=1)
        self.command('PROP',params)

        pass


    def program_get_step(self,step):
        step=f'{step:02}'

        mem=self.command('GETP',param=step)
        volts,amps, minutes,seconds = tuple(_numfields(mem, (3, 3, 2, 2),1))
        volts=volts/10
        amps=amps/100
        return ([float(volts),float(amps),int(minutes),int(seconds)])

    def program_run(self,cycles):
        cycles=f'{cycles:04d}'
        mem=self.command('RUNP',param=cycles)
        return

    def program_stop(self):
        mem=self.command('STOP')
        return



    def screen(self):
        resp = self.command('GPAL')
        if resp is not None:
            timer=resp[35]=="0"
            fault=resp[64]=="0"
            Output_On=resp[65]=="0"
            Output_Off=resp[66]=="0"
            return timer,fault,Output_On,Output_Off
        else:
            return None

    def settings(self):
        resp = self.command('GETS')
        if resp is not None:
            return tuple(_numfields(resp, (3, 3)))
        else:
            return None

    def enable(self):
        """Enable output."""
        return self.command('SOUT', '0')
    def disable(self):
        """Disable output."""
        return self.command('SOUT', '1')

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
        sup.voltage(12.3)
        sup.enable()
        time.sleep(0.5)
        print('Reading', sup.reading())
        print('Maxima', sup.maxima())
        print('Settings', sup.settings())
        sup.disable()
        time.sleep(0.5)
        print('Disabled; reading', sup.reading())
