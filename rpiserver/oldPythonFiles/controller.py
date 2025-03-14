from flask import Flask, request, jsonify
import serial.tools.list_ports_linux
from plasds import PlasDS
from autosampler import Autosampler
import serial
import time
from math import floor
from Hamilton import HamiltonDualDispenser
from datetime import datetime, timezone
import threading
import logging
import json
import os


gsc = Flask(__name__)

class GalacticSamplerController:
    def __init__(self,gsc:Flask):
        self.test = 0
        self.gsc = gsc
        self.gsc.add_url_rule('/controller','controller',self.controller, methods=["POST"],provide_automatic_options=False)
        self.gsc.add_url_rule('/controller','corsOptions',self.corsOptions, methods=["OPTIONS"])
        self.path= 'savefiles/'

        self.syringepumps : list[PlasDS | HamiltonDualDispenser ] =[]
        self.autosamplers : list[Autosampler] =[]

        self.runState = {
            'status': 'Not Connected',
            'currentStep': 0,
            'totalSteps': 0,
            'startTime': datetime.now(timezone.utc),
        }
          
    def corsOptions(self):
        print('OPTIONS CALLED')
        response = jsonify({'test':'test'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers','*')
        return response

    def controller(self):
        print('Controller called')
        try:
            data = request.get_json()
            if data['command'] == 'connect':
                self.syringepumps : list[PlasDS | HamiltonDualDispenser ] =[]
                self.autosamplers : list[Autosampler] =[]
                self.devices = list(self.connect())
                print(f'devices={self.devices}')
                response = jsonify({
                    'devices': list(self.devices)
                })                
            if data['command'] == 'initialize':
                print('initialized called')
                result = self.initializeAll()
                response = jsonify({
                    'result' : result
                })
            if data['command'] == 'run':
                print(f'data = {data["data"]}')
                self.setSettings(data['data']['settings'])
                x = threading.Thread(target=self.runRun,args=(data['data']['run'],))
                x.start()
                response = jsonify(
                {
                    'result' : 'started'
                })
            if data['command'] == 'resetHamilton':
                print('RESET HAMILTON')
                self.syringepumps[0].ham.command('!')
                time.sleep(10)
                response = jsonify(
                    {
                        'result' : 'reset'
                    }
                )
            if data['command']== 'settings':
                self.setSettings(data['settings'])
                response = jsonify(
                    {
                        'result' : 'settings set'
                    }
                )
            if data['command'] == 'saveRun':
                if data['data']['overwrite']:
                    self.saveRun(data['data'],True)
                else:
                    self.saveRun(data['data'])
                response = jsonify(
                    {
                        'result' : 'saved'
                    }
                )
            if data['command'] == 'runStatus':
                if self.runState['status'] == 'Error':
                    response = jsonify({
                        'result': 'error',
                        'errorCode' : self.runState['errorCode']
                    })
                response = jsonify(self.runState)
            if data['command'] == 'loadRun':
                with open(f"{self.path}{data['data']['file']['name']}.json",'r') as file:
                    runFile = json.load(file)
                    runFile['result'] = 'loaded'
                    response = jsonify(runFile)
    
            if data['command'] == 'getSaveFiles':
                files = []

                for file in os.listdir(self.path):
                    if file.endswith('.json'):
                        files.append({
                            'name': file.replace('.json',''),
                            'lastModified': os.path.getmtime(self.path + file),
                        })
                response = jsonify({'files': files})
        except Exception as error:
            response = jsonify(
            {
                    'result': 'error',
                    'errorCode' : str(error)
            })
        response.headers.add('Access-Control-Allow-Origin', '*')                
        return response
        
    def initializeAll(self):
        success = True
        for autosampler in self.autosamplers:
            success = success & autosampler.initialize()
        for syringePump in self.syringepumps:
            syringePump.bypass()
            syringePump.waitForBusy()
        for syringePump in self.syringepumps:
            success = success & syringePump.initialize()
            syringePump.bypass()
            syringePump.waitForBusy()            
        return success

    def runRun(self,run):
        try:
            self.runState['status'] = 'Running'
            self.runState['startTime'] = datetime.now(timezone.utc)
            aSampler = self.autosamplers[0]
            ham =  self.syringepumps[0]
            ham.fill()
            tempRunlength = 0
            for rack in run:
                for block in rack:
                    if block['volume'] > 0:
                        tempRunlength += block['endPosition'] - block['startPosition'] + 1
            self.runState['totalSteps'] = tempRunlength

            for rackNumber,rack in enumerate(run):
                print(f'rack length {len(rack)}')
                for block in rack: 
                    #for i in block:
                        #print (f'{i}, {block[i]}')
                    if block['volume'] > 0:
                        for position in range(block['startPosition']-1,block['endPosition']-1):
                            self.runState['currentStep'] += 1

                            if not ham.checkErrors():
                                break    
                            ham.waitForBusy()
                            aSampler.gotoPosition(rackNumber,position)
                            aSampler.commandOut('PMP ON')
                            ham.waitForBusy()
                            ham.dispense(block['volume'])
                            ham.waitForBusy()
                            time.sleep(block['waitSeconds'])
        except Exception as e:
            self.runState['status'] = 'Error'
            self.runState['errorCode'] = str(e)
            return

    def saveRun(self,filedata,overwrite=False):  
        saveFile = open(f"savefiles/{filedata['name']}.json", 'w' if overwrite else 'x')
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
        print(f'Speed set to {speed}')
        self.autosamplers[0].settings['PROBE DEPTH'] = settings['probeDepth']

    def connect(self):
        devices : list[dict] = []
        print('Connecting')
        for port in serial.tools.list_ports_linux.comports():
            print(f'testing port {port}')
            #Test Each port for AutoSampler and PS thru AS
            asTest = Autosampler(port.device)
            if (asTest.query('ver')).startswith('Cetac'):
                self.autosamplers.append(asTest)
                verss = asTest.query('verss')
                if ('520' in verss):
                    devices.append({'device': 'ASX-520'})
                elif ('560' in verss):
                    print('adding 560')
                    devices.append({'device': 'ASX-560'})  
                    continue  
            test = HamiltonDualDispenser(port.device,False)
            identity = test.identify()
            if identity:
                devices.append(identity)
                self.syringepumps.append(test)
                continue    
        print(f'devices {devices}')
        return devices

my_gsc = GalacticSamplerController(gsc)

if __name__ == "__main__":
    gsc.run(host='0.0.0.0',debug=True)