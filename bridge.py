import serial
import time
from pylsl import StreamInfo, StreamOutlet

# LSL Setup for NUILab research
info = StreamInfo('gMOBIlab', 'EEG', 8, 256, 'float32', 'gtec_001')
outlet = StreamOutlet(info)

try:
    ser = serial.Serial('COM10', baudrate=57600, timeout=1)
    ser.flushInput()
    
    # The sequence that finally worked!
    print("Sending Binary Handshake...")
    ser.write(b'\x02\x53\x61') 
    
    raw_buffer = bytearray()
    print("--- BINARY STREAM ACTIVE ---")

    while True:
        if ser.in_waiting > 0:
            # Read all available bytes
            raw_buffer.extend(ser.read(ser.in_waiting))
            
            # Packets are 17 bytes: 1 Sync (0x01 or 0xf8) + 16 Data
            while len(raw_buffer) >= 17:
                # The first byte is the sync header
                header = raw_buffer[0]
                
                # Check for standard g.tec binary headers
                if header in [0x01, 0x02, 0xf8]: 
                    packet = raw_buffer[1:17]
                    channels = []
                    # for i in range(0, 16, 2):
                    #     # Combine Low/High bytes into 16-bit
                    #     val = packet[i] + (packet[i+1] * 256)
                    #     channels.append(float(val))
                    # Inside your while loop, update the channel processing:
                    for i in range(0, 16, 2):
                        # Combine Low/High bytes into 16-bit
                        val = packet[i] + (packet[i+1] * 256)
                        
                        # CENTER THE DATA: Subtract the 16-bit midpoint (32768)
                        # This turns 0...65535 into -32768...32767
                        centered_val = float(val - 32768)
                        channels.append(centered_val)
                                        
                    outlet.push_sample(channels)
                    print(f"LSL PUSH: {channels[0]}", end='\r')
                    del raw_buffer[:17]
                else:
                    # Shift until we find a valid header
                    raw_buffer.pop(0)
except Exception as e:
    print(f"\nError: {e}")
finally:
    ser.close()