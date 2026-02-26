# import serial
# import time
# from pylsl import StreamInfo, StreamOutlet

# # 1. Setup LSL (8 channels, 256Hz)
# # Matching the Source ID 'gtec_001' is critical for OpenViBE
# info = StreamInfo('gMOBIlab', 'EEG', 8, 256, 'float32', 'gtec_001')
# outlet = StreamOutlet(info)

# def run_bridge():
#     try:
#         print("Connecting to g.MOBILab+ on COM10...")
#         ser = serial.Serial('COM10', baudrate=57600, timeout=1)
#         ser.flushInput()
        
#         # Give the Bluetooth connection a moment to stabilize
#         time.sleep(1)
        
#         print("Sending start command 's'...")
#         ser.write(b's')

#         line_buffer = ""
#         byte_accumulator = []
#         eeg_packet = []

#         print("Bridge active. Searching for data packets...")

#         while True:
#             if ser.in_waiting > 0:
#                 # Read character by character from the text stream
#                 char = ser.read(1).decode('ascii', errors='ignore')
                
#                 if char in [' ', '\n', '\r']:
#                     if line_buffer and "0x" in line_buffer:
#                         try:
#                             # Convert hex string (e.g., '0x07') to integer
#                             val = int(line_buffer, 16)
                            
#                             # 0xf8 (248) is the sync byte; we use it to align
#                             if val == 248:
#                                 # If we hit a sync, reset the partial packet to stay aligned
#                                 byte_accumulator = []
#                                 eeg_packet = []
#                             else:
#                                 byte_accumulator.append(val)
                            
#                             # Combine two 8-bit bytes into one 16-bit value (Little Endian)
#                             if len(byte_accumulator) == 2:
#                                 combined = (byte_accumulator[1] * 256) + byte_accumulator[0]
#                                 eeg_packet.append(float(combined))
#                                 byte_accumulator = []
                            
#                             # Once we have all 8 channels, push the sample to the network
#                             if len(eeg_packet) == 8:
#                                 outlet.push_sample(eeg_packet)
#                                 # Overwrite the same line to show live progress
#                                 # print(f"LSL PUSH: {eeg_packet[0]:.1f} | Chans: {len(eeg_packet)}", end='\r')
#                                 # Change this line in bridge.py
#                                 print(f"LSL PUSH: {eeg_packet} | Time: {time.time()}") # This will scroll continuously
#                                 eeg_packet = []
                                
#                         except ValueError:
#                             pass
#                     line_buffer = ""
#                 else:
#                     line_buffer += char
#             else:
#                 # If the serial buffer is empty, don't hog the CPU
#                 time.sleep(0.001)

#     except Exception as e:
#         print(f"\nCRITICAL ERROR: {e}")
#     finally:
#         if 'ser' in locals():
#             ser.close()
#             print("\nSerial port closed.")

# if __name__ == "__main__":
#     run_bridge()

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
                    for i in range(0, 16, 2):
                        # Combine Low/High bytes into 16-bit
                        val = packet[i] + (packet[i+1] * 256)
                        channels.append(float(val))
                    
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