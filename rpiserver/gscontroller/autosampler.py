import serial
import time

import serial.tools
import serial.tools.list_ports_linux
import logging
import random


class Autosampler():
    
    EOL = '\r'
    ENCODER = 'utf-8'
    DEBUG = True # TODO: setup logging

    MAX_MOVETIME_520 = 1 # seconds TODO: Monday measure this
 
    #personality
    PERSONALITY_TYPE = [
        (0,'CETAC Std 520'), 
        (4,'PE 520'),
        (5,'HP/Agilent 520'),
        (6,'Lachat 520'),
        (7,'Lachat 410'),
        (8,'CETAC Std 260'),
        (9,'CETAC Std 130'),
        (14,'CETAC Std 520 HS'),
        (15,'HP/Agilent 520 HS'),
        (16,'PE 520 HS'),
        (17,'Micromass 520'),
        (18,'Thermo AA 520'),
        (20,'Thermo AA 520 HS'),
        (22,'Finnigan Mat 520'),
        (23,'CETAC Std EXR-8'),
        (24,'CETAC Std EXR-8 HS'),
        (25,'PE EXR-8'),
        (26,'PE EXR-8 HS'),
        (27,'Anatel 520'),
        (32,'Micromass 260'),
        (33,'PE 260 Speedy'),
        (37,'Lachat 520 HS'),
        (39,'Lachat EXR-8'),
        (40,'Lachat ASX-260'),
        (41,'Lachat EXR-8 HS'),
    ]

    def getType(self,description):
        for type in self.PERSONALITY_TYPE:
            if (type[1] == description.rstrip()):
                return type
            
    def setType(self,description):
        num=self.getType(description)[0]
        self.commandOut(f'settype={num}')

    def initialize(self):
        self.ver = self.query('ver')
        self.verss = self.query('verss')
        self.personality = self.getType(self.query('gettype'))
        if (self.ver.startswith('Cetac')):
            if '520' in self.ver:
                self.name = 'ASX-520'
            elif '560' in self.ver:
                self.name = 'ASX-560'
            self.isInitialized = True
            self.commandOut('SETZ=1')
            self.commandOut('UP')
            self.home()
            self.commandOut('TRAY=60')#TODO: setup tray size
            self.commandOut('DOWN=40')
            self.commandOut('PMP ON')
            return True
        else:
            return False
    

    def home(self,rinse=False):
        self.commandOut("UP")
        time.sleep(.1)
        z=0
        if rinse:
            z=40    
        self.commandOut(f'ABS=0-0-{z}')
        while True:
            position = self.query('GETPOS')
            try:
                gx, gy, gz = map(int, position.split(','))
                gx, gy, gz = gx // 10, gy // 10, gz // 100
                if gx == 0 and gy == 0 and gz == z:
                    break
            except ValueError as e:
                logging.error(f'ValueError in GETPOS - {e}')
        return True
        
    def gotoPosition(self,rack,position):
        self.goto(rack=rack, x=position//12, y=position%12)

    def goto(self,rack,x,y,z=None,wait=True):
        #TODO ERROR CHECKING ex: Error:035 Tray Not Selected\r
        if z==None:
            z= int(self.settings['PROBE DEPTH'])
        self.oldAlignment = False
        if (self.oldAlignment == True):
            colWidth = 189
            colOffset= 20
            rackWidth = 1098
            rowHeight = 194
            rowOffset = 510
            logging.debug(f'GOTO: x={x} y={y} rack={rack}')
            x = ((rack)*rackWidth) + ((x*colWidth)+colOffset) 
            y = (y * rowHeight) + rowOffset
            self.commandOut(f'ABS={x}-{y}-{z}')
         # TODO Monday test this
            if wait:
                if self.name == 'ASX-520':
                    time.sleep(self.MAX_MOVETIME_520)
                else:
                    while True:
                        position = self.query('GETPOS')
                        try:
                            gx, gy, gz = map(int, position.split(','))
                            gx, gy, gz = gx // 10, gy // 10, gz // 100
                            if gx == x and gy == y and gz == z:
                                break
                        except ValueError as e:
                            logging.debug(f'ValueError in GETPOS - {e}')
        else:
            x = rack*5 + x        
            logging.debug(f'Goto: x={x} y={y} z={z}')
            self.commandOut(f'TUBE={x}-{y}-{z}')
            self.lastPosition = ''
            while True:
                try:
                    currentPos = self.query('GETPOS')
                    logging.debug(f'Current Position: {currentPos} - lastPosition: {self.lastPosition}')
                    if (currentPos == self.lastPosition) and (currentPos != ''):
                        break
                    self.lastPosition = currentPos
                except ValueError as e:
                    logging.error(f'ValueError in GETPOS - {e}')
                
                
    def gotoRinse(self):
        logging.error("GOTORINSE CALLED")
        self.commandOut(f'ABS=0-0-100') 

    def query(self,q):
        qout = q +self.EOL
        if (self.DEBUG):
            logging.debug(f'Writing {qout}')
        self.conn.write(bytes(q + self.EOL,self.ENCODER))
        out = self.conn.read_until(bytes('\r',self.ENCODER)).decode(self.ENCODER)
        if self.DEBUG:
            logging.debug(f'Return:{out}')
        return out.rstrip()

    def commandOut(self,command):
        writeCommand = (command + self.EOL )
        if self.DEBUG:
            logging.debug(f'Writing to {self.name}: {writeCommand}')
        self.conn.write(bytes(writeCommand, self.ENCODER))
        response = self.conn.read_until(bytes(self.EOL, self.ENCODER).decode('utf-8','replace'))
        if self.DEBUG:
            logging.debug(f"{self.name} {response}")


    def setRacks(self,racksize):
        if racksize==60:
            self.rows = 12
            self.cols = 5
            self.racks = 4

    def convertPosition(self,position):
        position=position-1
        if position>=(self.rows*self.cols): 
            position = position + (self.rows*self.cols)
        rack = divmod(position,(self.rows*self.cols))
        rowCol = divmod(rack[1],self.rows)
        return {'rack':rack[0]+1,
                'col':rowCol[0],
                'row':rowCol[1]}
    
    def __init__(self,serConn=None):
        try:
            self.conn = serial.Serial(
                        port = serConn,
                        baudrate = 9600,
                        parity = serial.PARITY_NONE,
                        bytesize = serial.EIGHTBITS,
                        stopbits = serial.STOPBITS_ONE,
                        timeout = 1,
            )
            self.isInitialized = False
            self.setRacks(60)
            self.settings = {
                'PROBE DEPTH': 150
            }
            self.name = ''
        except Exception as error:
            logging.error(f"SERIAL ERROR {error}") #TODO Log errors



if __name__ == "__main__":
    print('Autosampler Terminal')
    
    ports = serial.tools.list_ports_linux.comports()
    for index,port in enumerate(ports):
        print(str(index+1) + " : " + str(port.device) + " - " + str(port.hwid))
    print("-----------------------")
    serialPort = int(input("Select Port:" + str(len(ports)) + "): ")) - 1

    #Open Connection to Autosampler

    my_as = Autosampler(ports[serialPort].device)
    my_as.initialize()
    inp = 1
    while 1:
    # get keyboard input
        inp = input(">> ")
        if inp == 'exit' or inp == 'quit':
            exit()
        else:
            my_as.commandOut(inp)
            