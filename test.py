import serial
import time

PORT = "COM9"
BAUD = 115200          # must match FPGA
VALUE = 0x83        # 16-bit value

ser = serial.Serial(
    port=PORT,
    baudrate=BAUD,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

time.sleep(0.1)

# Pack 16-bit value → two bytes (LSB first)
tx_bytes = VALUE.to_bytes(1, byteorder="little")

ser.write(tx_bytes)

print(f"Sent 16-bit value: 0x{VALUE:04X}")
print(f"Bytes: {[hex(b) for b in tx_bytes]}")

ser.close()
