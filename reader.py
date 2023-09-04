import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import serial

import time 

from rich.live import Live
from rich.table import Table

# TC conversion ratio
tc_ratio = 50

# Create a Modbus RTU master
master = modbus_rtu.RtuMaster(
    serial.Serial(port='/dev/ttyUSB0', 
                    baudrate=9600, 
                    bytesize=8, 
                    parity='N', 
                    stopbits=1, 
                    xonxoff=0
    )
)
master.set_timeout(1.0)
master.set_verbose(True)

# Connect to the Modbus slave
master.open()

# Define the slave ID
slave_id = 1

# Define the starting address of the holding registers
start_address = 0x280

# Define the number of words to read in each reading
num_words = 12

def modbus_request():
    # Perform four consecutive readings
    for i in range(4):
        # Read the holding registers
        registers = master.execute(slave_id, 
                                cst.READ_HOLDING_REGISTERS, 
                                start_address+2*num_words*i, 
                                num_words)

        # Save each word in a different variable
        for j in range(num_words):
            variable_name = f'register_{i * num_words + j}'
            globals()[variable_name] = registers[j]

    # Close the Modbus connection
    master.close()

def pfFilter(pf):
        neg = pf >> 7
        pf = pf & 0x7f
        if neg:
            pf *= -1
        return pf

def generate_table() -> Table:
    # RTU requests
    modbus_request()

    # Parse data
    VL1_N = register_0/10 
    AL1 = register_1*tc_ratio/1000
    WL1 = register_2*tc_ratio/10 

    VL2_N = register_3/10 
    AL2 = register_4*tc_ratio/1000
    WL2 = register_5*tc_ratio/10 

    VL3_N = register_6/10 
    AL3 = register_7*tc_ratio/1000
    WL3 = register_8*tc_ratio/10 

    VA_L1 = register_16*tc_ratio/10 
    VA_L2 = register_17*tc_ratio/10 
    VA_L3 = register_18*tc_ratio/10 

    VAR_L1 = register_20*tc_ratio/10 
    VAR_L2 = register_21*tc_ratio/10 
    VAR_L3 = register_22*tc_ratio/10 

    PF_L1 = pfFilter(register_30 and 0xff)/100
    PF_L2 = pfFilter(register_30 >> 8)/100
    PF_L3 = pfFilter(register_31 and 0xff)/100
    PF_S  = pfFilter(register_31 >> 8)/100

    # Create the table
    table = Table(title="Analyzer Measurements")
    table.add_column("Phase", justify="left")
    table.add_column("L1", justify="center")
    table.add_column("L2", justify="center")
    table.add_column("L3", justify="center")
    
    # Add the rows to the table
    table.add_row("Phase volt", f"{VL1_N} V", f"{VL2_N} V", f"{VL3_N} V")
    table.add_row("Current", f"{AL1} A", f"{AL2} A", f"{AL3} A")
    table.add_row("Power", f"{WL1} W", f"{WL2} W", f"{WL3} W")
    table.add_row("Apparent", f"{VA_L1} VA", f"{VA_L2} VA", f"{VA_L3} VA")
    table.add_row("Reactive", f"{VAR_L1} VAR", f"{VAR_L2} VAR", f"{VAR_L3} VAR")
    table.add_row("PF", f"{PF_L1:.2f}", f"{PF_L2:.2f}", f"{PF_L3:.2f}")

    return table

with Live(generate_table(), refresh_per_second=0.2) as live:
    for _ in range(40):
        time.sleep(1)
        live.update(generate_table())

