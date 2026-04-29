#scan fire test
#use to send a simple "F:15\n" serial angle test
#15 degrees, will be adapted into computer vision script but just for testing currently
#usage: run and enter 1 in terminal to send command and q to quit


#check com port for arduino and change accordingly

import serial #use "pip install pyserial"
import time
PORT = 'COM5'
ser = serial.Serial(PORT, 9600, timeout = 1)
time.sleep(2)

print("type 1 to test FIRE command (15d). press q to quit")
while True:
    cmd = input(">> ")
    if cmd == '1':
        message = "F:15\n"
        ser.write(message.encode())
        print("Sent:", message.strip())
    elif cmd == 'q':
        break

ser.close()
