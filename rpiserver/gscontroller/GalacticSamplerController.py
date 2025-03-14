from flask import Flask, request, jsonify
import serial.tools.list_ports_linux
from .autosampler import Autosampler
import serial
import time
from math import floor
from .Hamilton import HamiltonDualDispenser
from datetime import datetime, timezone
import threading
import logging
import json
import os
import socket
import netifaces


class GalacticSamplerController:
    def __init__(self,gsc:Flask):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Starting Controller V1.0.2')
        self.test = 0
        gsc.add_url_rule('/controller','controller',self.controller, methods=["POST"],provide_automatic_options=False)
        gsc.add_url_rule('/controller','corsOptions',self.corsOptions, methods=["OPTIONS"])
        self.path= 'savefiles/'
        self.filename = 'temp'
        self.logFilePath = 'log/currentRun.json'
        self.keepState = False
        try:
            addrs = netifaces.ifaddresses('eth0')
            logging.debug(f'IP Address - {addrs}')
        except Exception as e:
            logging.error(f'Error getting IP - {e}')
            addrs = {netifaces.AF_INET: [{'addr': '192.168.1.1', 'netmask': '255.255.255.0', 'broadcast': '192.168.1.1'}]}
        
        if not os.path.exists('conf'):
            os.makedirs('conf')
        if not os.path.exists('conf/netSettings.json'):
            with open('conf/netSettings.json','w') as file:
                json.dump({
                    'type': 'static',
                    'dhcp': False,
                    'ip' : self.splitIP(addrs[netifaces.AF_INET][0]['addr']),
                    'netmask' : self.splitIP(addrs[netifaces.AF_INET][0]['netmask']),
                    'gateway' : self.splitIP(addrs[netifaces.AF_INET][0]['broadcast']),
                },file)
        with open('conf/netSettings.json','r') as file:
            self.netSettings = json.load(file)

        if (self.netSettings['ip'] != self.splitIP(addrs[netifaces.AF_INET][0]['addr'])) :
            self.netSettings['ip'] = self.splitIP(addrs[netifaces.AF_INET][0]['addr'])
            self.netSettings['netmask'] = self.splitIP(addrs[netifaces.AF_INET][0]['netmask'])
            self.netSettings['gateway'] = self.splitIP(addrs[netifaces.AF_INET][0]['broadcast'])
        

        try:
            if not os.path.exists('log'):
                os.makedirs('log')
            if not os.path.exists('savefiles'):
                os.makedirs('savefiles')
            if not os.path.exists('log/currentRun.json'):
                self.logFile = open(f'log/currentRun.json', 'w')
                self.logFile.close()
        except Exception as e:
            logging.error(f'Error Opening Log file - {e}')


        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.syringepumps : list[ HamiltonDualDispenser ] =[]
        self.autosamplers : list[Autosampler] =[]

        self.connections = {
                'autosampler': 'Disconnected',
                'hamilton': 'Disconnected'
        }

        self.resetAllRun()

    def splitIP(self,ip):
        return [int(item) for item in ip.split('.')]
    
    def resetAllRun(self):
        self.runState = {
            'status': 'Idle',
            'currentStep': 0,
            'totalSteps': 0,
            'startTime': datetime.now(timezone.utc),
        }
        self.settings = {
            'syringeSize': 10000,
            'speed': 12,
            'probeDepth': 100,
            'numRacks': 4,
            'rackType': {
                'description': "5x12", 
                'col':5,
                'row':12,
            },
            'flushAfter': 1
        }
        self.currentRun = [0][0]
        self.filename = 'temp'

    def corsOptions(self):
        response = jsonify({'test':'test'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers','*')
        return response

    def controller(self):
        try:
            data = request.get_json()
            if data['command'] != 'runState':
                logging.debug(f"Controller called with command = {data['command']}")
            match data['command']:
                case 'connect':
                    self.syringepumps : list[ HamiltonDualDispenser ] =[]
                    self.autosamplers : list[Autosampler] =[]
                    self.devices = list(self.connect())
                    logging.debug(f'Connected to devices - {self.devices}')
                    response = jsonify({
                        'result': 'connected',
                        'runState': self.runState,
                        'devices': list(self.devices),
                    })

                case 'flush':  
                    flushes = data['data']['flushes']
                    self.flush(flushes) 
                    response = jsonify({ 'result': 'flushed' })

                case 'initialize':
                    logging.debug('Initializing all devices')
                    self.initializeAll()
                    response = jsonify({
                        'connections': self.connections,
                    })
                    logging.debug('Initialized all devices')

                case 'run':
                    logging.debug('Starting run')
                    self.settings = data['data']['settings']
                    self.currentRun = data['data']['run']

                    self.setSettings(self.settings)
                    self.thread = threading.Thread(target=self.runRun,args=(self.currentRun,))
                    self.thread.start()
                    response = jsonify({
                        'result' : 'started'
                    })
                
                case 'runFromLog': 
                    logging.debug('Starting run from log')
                    self.logFile = open(f'{self.logFilePath}', 'r')
                    logJSON = json.load(self.logFile)
                    self.currentRun = logJSON['run']
                    self.runState = logJSON['runState']
                    self.logFile.close()
                    self.filename = logJSON['file']
                    self.thread = threading.Thread( target=self.runRun,args=(self.currentRun,logJSON['runState']['currentStep']))
                    self.thread.start()
                    response = jsonify(
                    {
                        'result' : 'started',
                        'filename': self.filename
                    })

                case 'pause':
                    self.runState['status'] = 'Paused'
                    response = jsonify({ 'result' : 'paused'})

                case 'resetHamilton':
                    logging.debug('Reseting Hamilton')
                    self.syringepumps[0].ham.command('!')
                    time.sleep(10)
                    response = jsonify(
                        {
                            'result' : 'reset'
                        }
                    )

                case 'settings':
                    self.setSettings(data['settings'])
                    response = jsonify(
                        {
                            'result' : 'settings set'
                        }
                    )
                
                case'saveRun':
                    if data['data']['overwrite']:
                        self.saveRun(data['data'],True)
                    else:
                        self.saveRun(data['data'])
                    response = jsonify(
                        {
                            'result' : 'saved'
                        }
                    )

                case 'runState':
                    if self.runState['status'] == 'Error':
                        response = jsonify({
                            'result': 'error',
                            'errorCode' : self.runState['errorCode']
                        })
                    response = jsonify(self.runState)

                case 'reloadStatus':
                    if self.runState['status'] == 'Error':
                        response = jsonify({
                            'result': 'error',
                            'errorCode' : self.runState['errorCode']
                        })
                    logJSON = self.checkLog()
                    
                    if 'run' in logJSON:
                        self.currentRun = logJSON['run']
                        self.runState = logJSON['runState']
                        self.filename = logJSON['file']
                        self.settings = logJSON['settings']
                    response = jsonify({
                        'runState': self.runState,
                        'run': self.currentRun,
                        'filename': self.filename,
                        'settings': self.settings,
                        'connections': self.connections
                    })

                case 'clearLog':
                    logFile = open(f'log/currentRun.json', 'w')
                    writeJSON = json.dumps({},default=str)
                    logFile.write(writeJSON)
                    logFile.close()
                    self.resetAllRun()
                    response = jsonify({
                        'result': 'cleared'
                    })

                case 'loadRun':
                    with open(f"{self.path}{data['data']['file']['name']}.json",'r') as file:
                        runFile = json.load(file)
                        runFile['result'] = 'loaded'
                        self.filename = data['data']['file']['name']
                        response = jsonify(runFile)
                case 'trythis':
                    response = jsonify({'result': 'success'})

                case 'getSaveFiles':
                    files = []
                    for file in os.listdir(self.path):
                        if file.endswith('.json'):
                            files.append({
                                'name': file.replace('.json',''),
                                'lastModified': os.path.getmtime(self.path + file),
                            })
                    response = jsonify({'files': files})
                case 'nslookup':
                    response = jsonify(self.netSettings)     

                case 'changeIP':
                    logging.debug('Changing IP to - ' + data['data']['type'])
                    if data['data']['type'] == 'dynamic':
                        os.system(f'sudo ifconfig eth0 down')
                        os.system(f'sudo ifconfig eth0 0.0.0.0 0.0.0.0')
                        os.system(f"sudo dhclient eth0")
                        os.system(f'sudo ifconfig eth0 up')
                        hostname = socket.gethostname()
                        newIP = socket.gethostbyname(hostname)
                    elif data['data']['type'] == 'static':
                        os.system(f'sudo ifconfig eth0 down')
                        os.system(f'sudo killall dhclient')
                        os.system(f"sudo ifconfig eth0 {data['data']['ip']} netmask {data['data']['netmask']} gateway {data['data']['gateway']}")
                        os.system(f'sudo ifconfig eth0 up')
                        hostname = socket.gethostname()
                        newIP = socket.gethostbyname(hostname)
                        if (self.netSettings['dhcp']):
                            os.system('sudo systemctl start dnsmasq')
                        else:
                            os.system('sudo systemctl stop dnsmasq')
                    self.netSettings = data['data']
                    with open('conf/netSettings.json','w') as file:
                        json.dump(self.netSettings,file)
                    response = jsonify({
                                    'result': 'changed',
                                    'ip': newIP,
                                })
        except Exception as error:
            response = jsonify(
            {
                    'result': 'error',
                    'errorCode' : str(error)
            })
            logging.error(f"Error Type- {type(error)}")
            logging.error(f"Error - {error}")
            lo
        if response:
            response.headers.add('Access-Control-Allow-Origin', '*')                
            return response
        else:
            response = jsonify({'result': 'error'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
    
    def flush(self, flushes):
        self.autosamplers[0].initialize()
        for i in range(flushes):
            self.syringepumps[0].flush()
        self.autosamplers[0].commandOut('PMP OFF')

    def statusLog(self):
        try:
            logging.debug("Writing to logfile")
            logFile = open(f'log/currentRun.json', 'w')
            writeJSON = json.dumps({
                'file': self.filename,
                'runState': self.runState,
                'settings': self.settings,
                'run': self.currentRun
            },default=str)
            logging.debug(writeJSON)
            logFile.write(writeJSON)
            logFile.close()
        except Exception as error:
            logging.error(f'Error saving to log file - {error}')


    def initializeAll(self):
        for autosampler in self.autosamplers:
            if (autosampler.initialize()):
                self.connections['autosampler'] = 'Initialized'
        for syringePump in self.syringepumps:
            syringePump.bypass()
            syringePump.waitForBusy()
        for syringePump in self.syringepumps:
            if (syringePump.initialize()):
                self.connections['hamilton'] = 'Initialized'
            else:
                syringePump.checkErrors()
            syringePump.bypass()
            syringePump.waitForBusy()     
        for autosampler in self.autosamplers:
            autosampler.commandOut('PMP OFF')
        

    def checkLog(self) -> dict:
        if (os.path.exists(f'{self.logFilePath}')) & (os.stat(f'{self.logFilePath}').st_size > 0):
            self.logFile = open(f'{self.logFilePath}', 'r')
            logJSON = json.load(self.logFile)
            self.logFile.close()
            return (logJSON)
        return {}
        
    def validateNumber(self, number):
        try:
            return int(number)
        except (ValueError, TypeError):
            return 0
    
    def validateRun(self,run):
        for rack in run:
            for block in rack:
                try:
                    block['startPosition'] = self.validateNumber(block['startPosition'])
                    block['endPosition'] = self.validateNumber(block['endPosition'])
                    block['volume'] = self.validateNumber(block['volume'])
                    if (block['startPosition'] > block['endPosition']):
                        logging.error("Error: End position greater than start position")
                        block['endPosition'] = block['startPosition']
                    if block['volume'] > self.settings['syringeSize']:
                        block['volume'] = self.settings['syringeSize']
                except Exception as e:
                    logging.error(f"Invalid Number in Run - {e}")
        return run
    
    def runRun(self,run,fromStep=0):
        try:
            logging.debug(f'Starting Run {run} from step {fromStep}')
            run = self.validateRun(run)
            self.currentRun = run
            self.runState['status'] = 'Running'
            self.runState['startTime'] = datetime.now(timezone.utc)
            self.runState['currentStep'] = 0
            aSampler = self.autosamplers[0]
            ham =  self.syringepumps[0]

            if ( not self.keepState):
                aSampler.home(rinse=True)
                ham.fill()
            tempRunlength = 0
            for rack in run:
                for block in rack:
                    if block['volume'] > 0:
                        tempRunlength += block['endPosition'] - block['startPosition'] + 1
            self.runState['totalSteps'] = tempRunlength
            for rackNumber,rack in enumerate(run):
                logging.debug(f'Running Rack {rackNumber}')
                for block in rack: 
                    logging.debug(f'Running Block {block}')
                    if block['volume'] > 0: 
                        for position in range(block['startPosition']-1, block['endPosition']):
                            logging.debug(f'Running Position {position}')   
                            self.runState['currentStep'] += 1 
                            logging.debug(f"CurrentStep= {self.runState['currentStep']}")
                            if (self.runState['currentStep'] <= fromStep):
                                continue
                            if not ham.checkErrors():
                                break
                            ham.waitForBusy()
                            aSampler.gotoPosition(rackNumber,position)
                            ham.waitForBusy()
                            ham.dispense(block['volume'])
                            ham.waitForBusy()
                            time.sleep(block['waitSeconds'])
                            self.statusLog()
                            if(self.runState['status'] == 'Paused'):
                                self.keepState = True
                                return False
            aSampler.initialize()
            ham.home()
            logging.debug('Flushing')
            try:
                flushafter = int(self.settings['flushAfter'])
            except Exception as e:
                flushafter = 0
            self.flush(flushafter)
            self.runState['status'] = 'Finished'
            self.statusLog()
            logging.debug('Finished Run')
            return True

        except Exception as e:
            logging.error(f'Error in Run - {e}')
            self.runState['status'] = 'Error'
            self.runState['errorCode'] = str(e)
            return False

    def saveRun(self,filedata,overwrite=False):  
        saveFile = open(f"savefiles/{filedata['name']}.json", 'w' if overwrite else 'x')
        self.filename = filedata['name']
        saveFile.write(json.dumps(filedata))
        saveFile.close()
    
    def setSettings(self,settings):
        logging.debug(f'Setting Set to - {settings}')
        #set speed based on syringe volume and flow rate, speed is in seconds per stroke 

        speed = settings['syringeSize']/settings['speed']
        speed = floor(speed) + 1 if speed % 1 > 0 else floor(speed)
        if speed < 2:
            speed = 2
        self.syringepumps[0].ham.speed = speed
        self.syringepumps[0].ham.syringe = settings['syringeSize']
        logging.debug(f'Speed set to {speed}')

        self.autosamplers[0].settings['PROBE DEPTH'] = settings['probeDepth']

    def connect(self):
        devices : list[dict] = []
        logging.debug('Testing ports for connections')
        for port in serial.tools.list_ports_linux.comports():
            #Test Each port for AutoSampler and PS thru AS
            asTest = Autosampler(port.device)
            if (asTest.query('ver')).startswith('Cetac'):
                self.autosamplers.append(asTest)
                verss = asTest.query('verss')
                if ('520' in verss):
                    devices.append({'device': 'ASX-520'})
                    self.connections['autosampler'] = 'Connected'
                elif ('560' in verss):
                    devices.append({'device': 'ASX-560'})
                    self.connections['autosampler'] = 'Connected'  
                    continue

            test = HamiltonDualDispenser(port.device,False)
            identity = test.identify()
            if identity:
                devices.append(identity)
                self.syringepumps.append(test)
                self.connections['hamilton'] = 'Connected'
                continue
        logging.debug(f'Devices found - {devices}')    
        return devices
