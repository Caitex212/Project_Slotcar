import serial
import time

def record_lap_time(serial_port, count_first):
    counter = 1
    if count_first:
        counter = 0
    with serial.Serial(serial_port, 9600, timeout=1) as ser:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line == '1':
                    if counter <= 0:
                        return time.time()
                    else:
                        counter = counter - 1
                
