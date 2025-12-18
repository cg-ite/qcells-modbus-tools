"""
Constants for DTSU666 measurement keys
"""

VOLTAGE_PHASE_AB = 0x2000
VOLTAGE_PHASE_BC = 0x2002
VOLTAGE_PHASE_CA = 0x2004

VOLTAGE_PHASE_A  = 0x2006
VOLTAGE_PHASE_B  = 0x2008
VOLTAGE_PHASE_C  = 0x200A

CURRENT_PHASE_A = 0x200C
CURRENT_PHASE_B = 0x200E
CURRENT_PHASE_C = 0x2010

TOTAL_ACTIVE_POWER   = 0x2012
ACTIVE_POWER_PHASE_A = 0x2014
ACTIVE_POWER_PHASE_B = 0x2016
ACTIVE_POWER_PHASE_C = 0x2018

REACTIVE_POWER_PHASE_A = 0x201C
REACTIVE_POWER_PHASE_B = 0x201E
REACTIVE_POWER_PHASE_C = 0x2020

POWER_FACTOR_PHASE_A = 0x202C
POWER_FACTOR_PHASE_B = 0x202E
POWER_FACTOR_PHASE_C = 0x2030

TOTAL_REACTIVE_POWER = 0x201A
TOTAL_POWER_FACTOR   = 0x202A

FREQUENCY = 0x2044
# the same as address 101E and 1028
TOTAL_IMPORT_ENERGY = 0x401E
TOTAL_EXPORT_ENERGY = 0x4028

# Constants for DTSU666 measurement registers

REGISTERS = {
    0x2000: {"name": "Voltage_Phase_AB", "func": 3, "words": 2, "factor": 0.1},
    0x2002: {"name": "Voltage_Phase_BC", "func": 3, "words": 2, "factor": 0.1},
    0x2004: {"name": "Voltage_Phase_CA", "func": 3, "words": 2, "factor": 0.1},
    0x2006: {"name": "Voltage_Phase_A",  "func": 3, "words": 2, "factor": 0.1},
    0x2008: {"name": "Voltage_Phase_B",  "func": 3, "words": 2, "factor": 0.1},
    0x200A: {"name": "Voltage_Phase_C",  "func": 3, "words": 2, "factor": 0.1},

    0x200C: {"name": "Current_Phase_A", "func": 3, "words": 2, "factor": 0.001},
    0x200E: {"name": "Current_Phase_B", "func": 3, "words": 2, "factor": 0.001},
    0x2010: {"name": "Current_Phase_C", "func": 3, "words": 2, "factor": 0.001},

    0x2014: {"name": "Active_Power_Phase_A", "func": 3, "words": 2, "factor": 0.1},
    0x2016: {"name": "Active_Power_Phase_B", "func": 3, "words": 2, "factor": 0.1},
    0x2018: {"name": "Active_Power_Phase_C", "func": 3, "words": 2, "factor": 0.1},

    0x201C: {"name": "Reactive_Power_Phase_A", "func": 3, "words": 2, "factor": 0.1},
    0x201E: {"name": "Reactive_Power_Phase_B", "func": 3, "words": 2, "factor": 0.1},
    0x2020: {"name": "Reactive_Power_Phase_C", "func": 3, "words": 2, "factor": 0.1},

    0x202C: {"name": "Power_Factor_Phase_A", "func": 3, "words": 2, "factor": 0.001},
    0x202E: {"name": "Power_Factor_Phase_B", "func": 3, "words": 2, "factor": 0.001},
    0x2030: {"name": "Power_Factor_Phase_C", "func": 3, "words": 2, "factor": 0.001},

    0x2012: {"name": "Total_Active_Power",   "func": 3, "words": 2, "factor": 0.1},
    0x201A: {"name": "Total_Reactive_Power", "func": 3, "words": 2, "factor": 0.1},
    0x202A: {"name": "Total_Power_Factor",   "func": 3, "words": 2, "factor": 0.001},

    0x2044: {"name": "Frequency", "func": 3, "words": 2, "factor": 0.01},

    0x401E: {"name": "Total_Import_Energy", "func": 3, "words": 2, "factor": 1},
    0x4028: {"name": "Total_Export_Energy", "func": 3, "words": 2, "factor": 1}
}

# Optional: Liste aller Keys, z.B. für Iterationen
ALL_KEYS = [
    0x2000,  # VOLTAGE_PHASE_AB
    0x2002,  # VOLTAGE_PHASE_BC
    0x2004,  # VOLTAGE_PHASE_CA

    0x2006,  # VOLTAGE_PHASE_A
    0x2008,  # VOLTAGE_PHASE_B
    0x200A,  # VOLTAGE_PHASE_C

    0x200C,  # CURRENT_PHASE_A
    0x200E,  # CURRENT_PHASE_B
    0x2010,  # CURRENT_PHASE_C

    0x2014,  # ACTIVE_POWER_PHASE_A
    0x2016,  # ACTIVE_POWER_PHASE_B
    0x2018,  # ACTIVE_POWER_PHASE_C

    0x201C,  # REACTIVE_POWER_PHASE_A
    0x201E,  # REACTIVE_POWER_PHASE_B
    0x2020,  # REACTIVE_POWER_PHASE_C

    0x202C,  # POWER_FACTOR_PHASE_A
    0x202E,  # POWER_FACTOR_PHASE_B
    0x2030,  # POWER_FACTOR_PHASE_C

    0x2012,  # TOTAL_ACTIVE_POWER
    0x201A,  # TOTAL_REACTIVE_POWER
    0x202A,  # TOTAL_POWER_FACTOR

    0x2044,  # FREQUENCY

    0x401E,  # TOTAL_IMPORT_ENERGY
    0x4028,  # TOTAL_EXPORT_ENERGY
]

FOUR_WIRE_KEYS = [
    0x2006,  # VOLTAGE_PHASE_A
    0x2008,  # VOLTAGE_PHASE_B
    0x200A,  # VOLTAGE_PHASE_C

    0x200C,  # CURRENT_PHASE_A
    0x200E,  # CURRENT_PHASE_B
    0x2010,  # CURRENT_PHASE_C

    0x2014,  # ACTIVE_POWER_PHASE_A
    0x2016,  # ACTIVE_POWER_PHASE_B
    0x2018,  # ACTIVE_POWER_PHASE_C

    0x201C,  # REACTIVE_POWER_PHASE_A
    0x201E,  # REACTIVE_POWER_PHASE_B
    0x2020,  # REACTIVE_POWER_PHASE_C

    0x202C,  # POWER_FACTOR_PHASE_A
    0x202E,  # POWER_FACTOR_PHASE_B
    0x2030,  # POWER_FACTOR_PHASE_C

    0x2012,  # TOTAL_ACTIVE_POWER
    0x201A,  # TOTAL_REACTIVE_POWER
    0x202A,  # TOTAL_POWER_FACTOR

    0x2044,  # FREQUENCY

    0x401E,  # TOTAL_IMPORT_ENERGY
    0x4028,  # TOTAL_EXPORT_ENERGY
]
