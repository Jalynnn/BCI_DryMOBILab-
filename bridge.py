# import serial
# import time
# from pylsl import StreamInfo, StreamOutlet

# # LSL Setup for NUILab research
# info = StreamInfo('gMOBIlab', 'EEG', 8, 256, 'float32', 'gtec_001')
# outlet = StreamOutlet(info)

# try:
#     ser = serial.Serial('COM10', baudrate=57600, timeout=1)
#     ser.flushInput()
    
#     # The sequence that finally worked!
#     print("Sending Binary Handshake...")
#     ser.write(b'\x02\x53\x61') 
    
#     raw_buffer = bytearray()
#     print("--- BINARY STREAM ACTIVE ---")

#     while True:
#         if ser.in_waiting > 0:
#             # Read all available bytes
#             raw_buffer.extend(ser.read(ser.in_waiting))
            
#             # Packets are 17 bytes: 1 Sync (0x01 or 0xf8) + 16 Data
#             while len(raw_buffer) >= 17:
#                 # The first byte is the sync header
#                 header = raw_buffer[0]
                
#                 # Check for standard g.tec binary headers
#                 if header in [0x01, 0x02, 0xf8]: 
#                     packet = raw_buffer[1:17]
#                     channels = []
#                     # for i in range(0, 16, 2):
#                     #     # Combine Low/High bytes into 16-bit
#                     #     val = packet[i] + (packet[i+1] * 256)
#                     #     channels.append(float(val))
#                     # Inside your while loop, update the channel processing:
#                     for i in range(0, 16, 2):
#                         # Combine Low/High bytes into 16-bit
#                         val = packet[i] + (packet[i+1] * 256)
                        
#                         # CENTER THE DATA: Subtract the 16-bit midpoint (32768)
#                         # This turns 0...65535 into -32768...32767
#                         centered_val = float(val - 32768)
#                         channels.append(centered_val)
                                        
#                     outlet.push_sample(channels)
#                     print(f"LSL PUSH: {channels[0]}", end='\r')
#                     del raw_buffer[:17]
#                 else:
#                     # Shift until we find a valid header
#                     raw_buffer.pop(0)
# except Exception as e:
#     print(f"\nError: {e}")
# finally:
#     ser.close()

import serial
import time
from pylsl import StreamInfo, StreamOutlet

PORT = 'COM5'
BAUD = 57600

# Set BYTE_ORDER to 'big' (standard for g.MOBIlab ADC) or 'little' if traces stay jagged
BYTE_ORDER = 'big'

# g.tec g.MOBIlab standard full-scale range: +/- 500 uV over signed 16-bit range (-32768 to 32767)
SCALE_UV = 500.0 / 32768.0

# 8 EEG channels at 256 Hz
info = StreamInfo('gMOBIlab', 'EEG', 8, 256, 'float32', 'gtec_mobilab_001')
outlet = StreamOutlet(info)

ser = None
try:
    print(f"Connecting to {PORT} at {BAUD} baud...")
    ser = serial.Serial(PORT, baudrate=BAUD, timeout=1)
    
    # Allow Bluetooth SPP tunnel to stabilize
    time.sleep(1.2)
    ser.reset_input_buffer()
    
    # Send acquisition start handshake
    print("Initializing g.MOBIlab acquisition mode...")
    ser.write(b'\x02\x53\x61')
    time.sleep(0.1)

    raw_buffer = bytearray()
    print(f"--- STREAMING ACTIVE (Byte Order: {BYTE_ORDER}, Scaling: {SCALE_UV:.6f} uV/count) ---")

    while True:
        waiting = ser.in_waiting
        if waiting > 0:
            raw_buffer.extend(ser.read(waiting))
            
            # Packets are 17 bytes: 1 Sync byte + 16 payload bytes (8 channels * 2 bytes)
            while len(raw_buffer) >= 17:
                header = raw_buffer[0]
                
                # Valid sync header checks
                if header in (0x01, 0x02, 0xF8):
                    packet = raw_buffer[1:17]
                    channels = []
                    
                    for i in range(0, 16, 2):
                        # Decode signed 16-bit integer directly
                        raw_int = int.from_bytes(packet[i:i+2], byteorder=BYTE_ORDER, signed=True)
                        
                        # Scale directly to real microvolts (uV)
                        uv_value = float(raw_int) * SCALE_UV
                        channels.append(uv_value)
                    
                    outlet.push_sample(channels)
                    del raw_buffer[:17]
                else:
                    # Shift forward one byte to re-align sync frame
                    raw_buffer.pop(0)
        else:
            time.sleep(0.001)

except KeyboardInterrupt:
    print("\nStopping acquisition...")
except Exception as e:
    print(f"\nRuntime Error: {e}")
finally:
    if ser and ser.is_open:
        try:
            # Send stop command to put device back into standby
            ser.write(b'\x02\x53\x62')
            time.sleep(0.1)
        except Exception:
            pass
        ser.close()
        print("Serial port closed cleanly.")