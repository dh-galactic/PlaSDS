import serial
import serial.tools.list_ports_linux
import logging

SYRINGE_ERROR ={
    'P': 'Syringe does not exist',
    'H': 'Initialization Error',
    'D': 'Stroke too large',
    'B': 'Overload Error',
    'A': 'Not initialized',
}
VALVE_ERROR = {
    'P': 'Valve does not exist',
    'D': 'Overload Error',
    'B': 'Initialization Error',
    'A': 'Not initialized',
}
class Hamilton:
    EOL_OUT = '\r'
    ENCODER = 'utf-8'
    TOTAL_STEPS = 48000

    
    def __init__(self, port, thruAS:bool) -> None:
        logging.basicConfig(level=logging.WARNING)
        self.ser = serial.Serial(
            port = port,
            baudrate = 9600,
            parity = serial.PARITY_ODD,
            bytesize= serial.SEVENBITS,
            stopbits = serial.STOPBITS_ONE,
            timeout = 1
        )
        self.syringe = 10000 
        self.address='a'
        self.speed = 12
        self.thruAS = thruAS
        if thruAS:
            self.address='\\/a'
        #TODO Set defualt speed and backoff stpes based on syringe

        
    # BASIC COMMS
    def query(self,query : str):
        queryOut = f'{self.address}{query}{self.EOL_OUT}'
        self.ser.write(bytes(queryOut,self.ENCODER))
        logging.debug(f'Command Out:{queryOut}')
        response = self.ser.read_until(bytes(self.EOL_OUT,self.ENCODER))
        responseHex = response.hex()
        responseText = response.decode('utf-8','replace')
        logging.debug(f'Response: {response}')
        #check for ACK or NAK
        if responseHex[0:2] == '06':
            responseText = responseText.strip('\n\r\x06')
            return responseText
        elif responseHex[0:2] == '21':
            logging.warning('QUERY NOT ACKNOLEDGED')
        else:
            logging.debug('Missing initial return')

    def command(self, command: str):
        commandOut = f'{self.address}{command}R{self.EOL_OUT}'
        logging.debug(f'Command Out:{commandOut}')
        self.ser.write(bytes(commandOut,self.ENCODER))
        response = self.ser.read_until(bytes(self.EOL_OUT,self.ENCODER)).hex()
        logging.debug(f'Response: {response}')
        #check for ACK or NAK
        if response[0:2] == '06':
            logging.debug('Command Succesful')
            return True
        elif response[0:2] == '21':
            logging.warning('COMMAND NOT ACKNOWLEDGED')
            return False
        else:
            logging.debug('Missing initial return')
            return False
    
    # Poll Hamilton to see if syringe is busy or errors
    def waitForBusy(self): #TODO add Error Checking
        response='*'
        while True:
            response = self.query('F')
            if response == 'Y':
                break
            
    def poll(self,waitForProbe=False):
        while True:
            response = self.query('Q') 
            print(f'poll response-{response}')
            if response != '*':
                if waitForProbe:
                    if response == 'Y':
                        break
                else:
                    break
        return True
    
    #INITIALIZE
    def autoAdress(self):
        queryOut = f'1a{self.EOL_OUT}'
        if self.thruAS:
            queryOut = f'\\1a'
        self.ser.write(bytes(queryOut,self.ENCODER))
        logging.debug(f'Command Out:{queryOut}')
        response = self.ser.read_until(bytes(self.EOL_OUT,self.ENCODER))
        logging.debug(f'Response: {response.hex()}')
        
        #check for ACK or NAK
        fixedResponse = response.strip(b'\x0d').decode('utf-8','replace')
        logging.debug(f'Response: {fixedResponse}')
        if fixedResponse=='1b':
            return True
        elif fixedResponse=='1a':
            return True
        else:
            logging.debug('WRONG AUTOADDRESS')
            return False

    def initialize(self,leftSpeed=None,rightSpeed=None):
        ls = ''
        rs = ''
        if (leftSpeed):
            ls = f'S{leftSpeed}'
        if (rightSpeed):
            rs = f'S{rightSpeed}'
        initCommand = f'BX{ls}CX{rs}'
        self.command(initCommand)
        return True
        
    #COMMANDS

    #UTILS
    def getSteps(self,microliterVolume):
        return int((microliterVolume / self.syringe)*self.TOTAL_STEPS)

class HamiltonDualDispenser:
    def __init__(self,port,thruAS:bool):
        self.dispensing = 'C'
        self.pickup = 'B'
        self.ham = Hamilton(port,thruAS)

    def initialize(self):
        if self.ham.autoAdress():
            self.ham.command('LST19')
            print("Setting Continuous dispenser")
            if self.ham.initialize(leftSpeed=26,rightSpeed=26): #TODO setup init speed and syringe setting
                self.ham.syringe = 10000
                self.ham.waitForBusy()
                self.ham.waitForBusy()
                if self.checkErrors():
                    return True
                return False

    def fill(self):
        self.ham.command(f'{self.dispensing}LP02P{self.ham.TOTAL_STEPS}')
    
    def switch(self):
        if self.dispensing == "C":
            self.pickup='C'
            self.dispensing ='B'
        else:
            self.dispensing = 'C'
            self.pickup='B'
        #MAYBE SWITCH VALVES HERE

    def dispense(self,volume):
        steps = self.ham.getSteps(volume)
        try:
            stepsLeft = int(self.ham.query(f'{self.dispensing}YQP'))
        except ValueError:
            print('int error')
            stepsLeft = 0
        if steps>stepsLeft:
            print('Switching')
            self.switch()
            try:
                stepsLeft = int(self.ham.query(f'{self.dispensing}YQP'))
            except ValueError:
                print('int error')
                stepsLeft = 0
            if steps>stepsLeft:
                logging.debug('FILLING BUT SHOULDNT BE')
                self.fill()

        logging.debug(f'Dispensing {volume} with {steps} steps')
        self.ham.command(f'{self.dispensing}OD{steps}S{self.ham.speed}{self.pickup}IP{steps}S{self.ham.speed}')

    def changeSyringes(self):
        if self.ham.poll():
            print('here')
            self.ham.command('BM40000CM40000')
        print ('and here')
    def identify(self):
        if not self.ham.autoAdress():
            return None
        self.ham.waitForBusy()
        self.device = { 'device': 'Hamilton 600' }
        query= self.ham.query('H')
        if query == 'Y':
            self.device['config'] = 'Dual'
        elif query =='N':
            self.device['config'] = 'Single'
        return self.device

    def waitForBusy(self):
        return self.ham.waitForBusy()
    
    def bypass(self):
        pass

    def getConfig(self):
        return self.ham.query('LQT')    

    def checkErrors(self):
        response = self.ham.query('E2')
        print (f'errorcheck {response}')
        print(f'errorcheck LSyringe-{response[0:1]} LValve-{response[1:2]} RSyringe-{response[2:3]} RValve-{response[3:4]}')
        if response == '@@@@':
           return True
        error = ''
        try:
            if not response[0:1] == '@':
                error += 'Left Syringe Error - ' + SYRINGE_ERROR[response[0:1]]
            if not response[2:3] == '@':
                error += 'Right Syringe Error - ' + SYRINGE_ERROR[response[2:3]]
            if not response[1:2] == '@':
                error += 'Left Valve Error - ' + VALVE_ERROR[response[0:1]]
            if not response[3:4] == '@':
                error += 'Right Valve Error - ' + VALVE_ERROR[response[2:3]]
            if not error == '':
                raise Exception(error)
        except IndexError:         
            logging.error(f'Hamilton Error - {response}')
            return False
    
        
