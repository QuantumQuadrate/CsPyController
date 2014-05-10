import datetime, serial, time, traceback
from numpy import arange
from matplotlib import pyplot as plt
from matplotlib import animation
from matplotlib.dates import AutoDateFormatter,AutoDateLocator

class Scope(object):
    """This defines a matplotlib figure that continuously checks for new data and updates itself"""
    
    def __init__(self, data_source):
        
        self.data_source=data_source.get_data() #create a generator

        #setup file
        self.f = open('arroyotemplog.txt', 'a')

        self.fig, self.ax = plt.subplots()
        self.tdata = []
        self.ydata = []
        self.line, = self.ax.plot(self.tdata,self.ydata)
        #the animation needs to be assigned a name, otherwise it gets garbage collected and stops immediately
        self.anim = animation.FuncAnimation(self.fig, self.update, frames=data_source.get_data, interval=60000)
        plt.show()
    
    #def run(self):
    #    while True:
    #        time.sleep(60)
    #        self.update(self.data_source.next())    
    
    def update(self, y):
        t=datetime.datetime.now()
        print t, y
        with open(r'Z:\Public\AQuA data\BoxTempLog\TiSapphBoxTemp.txt', 'a') as f:
            f.write('{} {}\n'.format(t, y))
        self.tdata.append(t)
        self.ydata.append(y)
    
        if len(self.tdata) == 2:
            loc=AutoDateLocator()
            self.ax.xaxis.set_major_locator(loc)
            self.ax.xaxis.set_major_formatter(AutoDateFormatter(loc))
            
        if len(self.tdata) > 1:
            self.line.set_data(self.tdata, self.ydata)
            r=max(self.ydata)-min(self.ydata) #the range
            self.ax.set_ylim(min(self.ydata)-r*.1, max(self.ydata)+r*.1) #increase the ylim by 20% of the range
            self.ax.set_xlim(self.tdata[0], self.tdata[-1])
            self.fig.autofmt_xdate()
            self.fig.canvas.draw()

class ArroyoSerialPort(serial.Serial):
    '''Encapsulates a serial port for reading data from the Arroyo'''
    
    def __init__(self, port='COM4'):
        super(ArroyoSerialPort, self).__init__(port=port, baudrate=38400, timeout=1, writeTimeout=1)

    #this method is called by the Scope animator
    def get_data(self):
        while True:
            '''Function to read the temp off the Arroyo.'''

            input = 'TEC:T?' #ask for the temperature in return
            try:
                self.write(input + '\r\n')
            except Exception as e:
                print 'Exception while trying serial.write:\n'+str(e)+str(traceback.format_exc())+'\n'
            out=''
            while (out[-2:]!='\r\n'): #wait for end of line
                try:
                    out += self.read(1) #read one more character
                except Exception as e:
                    print 'Exception while trying serial.read:\n'+str(e)+str(traceback.format_exc())+'\n'
                    raise StopIteration
            yield float(out)

    def get_temp(self):
        command = 'TEC:T?'  # ask for the temperature in return
        try:
            self.write(command + '\r\n')
        except Exception as e:
            print 'Exception while trying serial.write:\n'+str(e)+str(traceback.format_exc())+'\n'
            return float('nan')
        out = ''
        while (out[-2:]!='\r\n'):  # wait for end of line
            try:
                out += self.read(1)  # read one more character
            except Exception as e:
                print 'Exception while trying serial.read:\n'+str(e)+str(traceback.format_exc())+'\n'
                return float('nan')
        return float(out)

    def set_temp(self, setpoint):
        command = 'TEC:T {:.2f}'.format(setpoint)  # set the temperature, give hundreths of a degree C
        try:
            self.write(command + '\r\n')
        except Exception as e:
            print 'Exception while trying serial.write:\n'+str(e)+str(traceback.format_exc())+'\n'
            return float('nan')

    def scan_temp(self, target, stepsize, steptime):
        t0 = self.get_temp()
        for t in arange(t0, target, stepsize):
            print t
            self.set_temp(t)
            time.sleep(steptime)  # wait steptime in seconds
        print 'Done.'

if __name__ == '__main__':
    ser = ArroyoSerialPort()
    scope = Scope(ser)

    while True:
        time.sleep(.01) #stay in this loop to keep the animator running
    #ser.close()