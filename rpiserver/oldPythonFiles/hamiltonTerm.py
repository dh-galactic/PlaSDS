import serial
import serial.tools.list_ports_linux
from Hamilton import Hamilton

class HamiltonTerm:
    ports = serial.tools.list_ports_linux.comports()
    print('Select Port')
    for i,port in enumerate(ports):
        print(f'{i+1} - {port.device}')
    print('X - exit')
    inp =int(input('Where is Hamilton:')) - 1
    ham = Hamilton(ports[inp].device,False)
    while 1:
        inp = input('HAMILTON 600 >>')
        match inp:
            case 'exit':
                ham.ser.close()
                exit()
            case 'init':
                if ham.autoAdress():
                    if ham.initialize(leftSpeed=20,rightSpeed=20):
                        if ham.waitForBusy():
                            print('Initialized')
            case 'poll':
                if ham.poll():
                    print('Ready')
            case _:
                ham.command(inp)

app = HamiltonTerm()

if __name__ == "__main__":
    app.run(debug=True)