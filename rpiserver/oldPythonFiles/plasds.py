import serial
import time
from dataclasses import dataclass

class PlasDS():

    DEBUG=True

    initSpeed = 3
    conn = None

    #Constants
    EOL = '\r'
    HEADER_IN = '/0'
    HEADER_OUT = '\\/1' #1 Pump
    ENCODER = 'utf-8'
    TOTAL_STEPS = 3000


    # ERROR CODES in Hex
    ERROR_CODES = [
        'OK',                       # 0
        'Initialization Error',     # 1
        'Invalid Command',          # 2
        'Invalid Operand',          # 3
        'Invalid Command Sequence', # 4
        'Unknown Error',            # 5
        'Unknown Error',            # 6
        'Device Not Initialized',   # 7
        'Internal Failure',         # 8
        'Plunger Overload',         # 9
        'Valve Overload',           # A
        'Plunger Move Not Allowed', # B
        'Unknown Error',            # C
        'Unknown Error',            # D
        'Unknown Error',            # E
        'Command Overflow',         # F
    ]

    def commandOut(self, command):
        self.conn.reset_input_buffer()
        self.conn.reset_output_buffer()
        writeCommand = (self.HEADER_OUT + command + 'R' + self.EOL )
        
        if self.DEBUG:
            print(f"writing {writeCommand}")
        self.conn.write(bytes(writeCommand, self.ENCODER))
        time.sleep(.3)
        readReturn = self.conn.read_until(bytes(self.EOL,self.ENCODER)).hex()
        if self.DEBUG:
            print(f'return={readReturn}')  
            
    def query(self,q):
        self.conn.reset_input_buffer()
        writeCommand = (self.HEADER_OUT + q + self.EOL)
        if self.DEBUG:
            print("writing :" + writeCommand)
        self.conn.write(bytes(writeCommand, self.ENCODER))
        time.sleep(.1)
        qRead = self.conn.read_until(bytes(self.EOL,self.ENCODER))
        i = qRead.find(b'\x2f\x30')
        if (i>=0):
            qRead = qRead[i+3:]
            return qRead.decode(self.ENCODER,'replace').rstrip('\r\n'+u'\x03')
        else:
            print ("NO HEADER")
            return ''

    def initialize(self, inputValveLeft=True,wait=True):
        initCommand = 'Y'
        if (inputValveLeft):
            initCommand = 'Z'
        self.commandOut((initCommand + str(self.initSpeed)))
        if(wait):
            if (self.waitForBusy()):
                self.isInitialized = True
                return True
            else:
                return False
        
        return True

    def waitForBusy(self):
        statusByte=''
        self.conn.reset_output_buffer()
        while (statusByte == '' or statusByte == '4'):
            self.conn.reset_input_buffer()
            writeCommand = (self.HEADER_OUT + 'Q' + self.EOL)
            self.conn.write(bytes(writeCommand, self.ENCODER))
            time.sleep(.1)
            qRead = self.conn.read_until(bytes(self.EOL,self.ENCODER)).hex()
            i = qRead.find('2f30')
            if (i>=0):
                if len(qRead) > i+5:
                    statusByte=qRead[i+4]
                    errorByte=int(qRead[i+5],16)
                    if(errorByte!=0):
                        print(f'ERROR:{self.ERROR_CODES[errorByte]}')
            else:
                statusByte =''
        if self.DEBUG:
            print(f"Wait For Busy Done Last return:{qRead}")
        time.sleep(.1)
        return True

    def empty(self,io='O',wait=True):
        self.waitForBusy()
        try:
            dispenseVolume = int(self.query('?'))
        except ValueError:
            dispenseVolume = 0
        if(dispenseVolume>0):
            self.commandOut(f"{io}S{self.outputSpeed}D{dispenseVolume}")
            if wait:
                self.waitForBusy()
                    
    def getDiagnostics(self):
         self.firmware = self.query('&')
         self.lostvalvesteps = self.query('$')
         self.voltage = self.query("*")
         if self.DEBUG:
             print(f'firmware-{self.firmware}')

    def inputVolume(self,volume, speed = None):
        self.waitForBusy()
        if speed == None:
            speed = self.inputSpeed
        self.commandOut(f"IS{speed}P{self.getSteps(volume)}")
        
    def outputVolume(self,volume, speed = None):
        self.waitForBusy()
        if speed == None:
            speed = self.outputSpeed
        self.commandOut(f"OS{speed}P{self.getSteps(volume)}")    

    def setSyringe(self,size):
        self.syringe = size

    def __init__(self,serConn=None,thruAS=True):
        self.conn = serial.Serial(
                    port = serConn,
                    baudrate = 9600,
                    parity = serial.PARITY_NONE,
                    bytesize = serial.EIGHTBITS,
                    stopbits = serial.STOPBITS_ONE,
                    timeout = 1,
        )
        
        self.isInitialized = False
        #default settings
        if thruAS==False:
            self.HEADER_OUT = '/1'
        self.inputSpeed = 15
        self.outputSpeed = 11
        self.syringe = 5000

    def getSteps(self,volumeInMicroliters):
        return int(3000 * (volumeInMicroliters/(self.syringe)))
    def bypass(self):
        self.commandOut('B')
    
    def volumeLeft(self):
        absolutePosition = int(self.query('?'))
        if absolutePosition > 0:
            return (self.syringe - ((absolutePosition/3000)  * self.syringe))
        else:
            return 0
    def fill(self):
        self.commandOut(f'IS{self.inputSpeed}A{self.TOTAL_STEPS}')
    def identify(self):
        if self.query('&').startswith('73'):
            return {'device':'PlaSDS'}
        return None
    
class DualPlasDS():
    def __init__(self,pdsleft:PlasDS,pdsright: PlasDS):
        self.pdsleft = pdsleft
        self.pdsright = pdsright
        self.pickup = pdsleft
        self.dispensing = pdsright
    
    def initialize(self):
        self.pdsleft.bypass()
        self.pdsright.initialize()
        self.pdsright.waitForBusy()
        self.pdsright.bypass()
        self.pdsleft.initialize()
        self.pdsleft.bypass()

    def fill(self):
        self.dispensing.fill()
    
    def switch(self):
        temppds = self.dispensing
        self.dispensing = self.pickup
        self.pickup = temppds

    def dispense(self,volume):
        steps = self.dispensing.getSteps(volumeInMicroliters=volume)
        try:
            stepsLeft = int(self.dispensing.query('?'))
        except ValueError:
            print('int error')
            stepsLeft = 0
        if steps > stepsLeft:
            self.switch()
            try:
                stepsLeft = int(self.dispensing.query('?'))
            except ValueError:
                stepsLeft =0
            if steps>stepsLeft:
                self.dispensing.fill()
        self.dispensing.outputVolume(volume)
        self.pickup.inputVolume(volume)


    def waitForBusy(self):
        return self.dispensing.waitForBusy() and self.pickup.waitForBusy()

    def bypass(self):
        self.dispensing.bypass()
        self.pickup.bypass()

    