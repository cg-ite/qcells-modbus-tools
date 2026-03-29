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

# Constants for DTSU666 measurement registers and mqtt topics
# names has to be unique, because they are the mqtt
# object_id, value_template, state_topic
REGISTERS = {
    0x2000: {"name": "Voltage_Phase_AB", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x2002: {"name": "Voltage_Phase_BC", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x2004: {"name": "Voltage_Phase_CA", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},

    0x2006: {"name": "Voltage_Phase_A", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x2008: {"name": "Voltage_Phase_B", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x200A: {"name": "Voltage_Phase_C", "device_class": "voltage", "unit": "V", "words": 2, "factor": 0.1,
             "state_class": "measurement"},

    0x200C: {"name": "Current_Phase_A", "device_class": "current", "unit": "A", "words": 2, "factor": 0.001,
             "state_class": "measurement"},
    0x200E: {"name": "Current_Phase_B", "device_class": "current", "unit": "A", "words": 2, "factor": 0.001,
             "state_class": "measurement"},
    0x2010: {"name": "Current_Phase_C", "device_class": "current", "unit": "A", "words": 2, "factor": 0.001,
             "state_class": "measurement"},

    0x2014: {"name": "Active_Power_Phase_A", "device_class": "power", "unit": "kW", "force_update": True, "words": 2,
             "factor": 0.1, "state_class": "measurement"},
    0x2016: {"name": "Active_Power_Phase_B", "device_class": "power", "unit": "kW", "force_update": True, "words": 2,
             "factor": 0.1, "state_class": "measurement"},
    0x2018: {"name": "Active_Power_Phase_C", "device_class": "power", "unit": "kW", "force_update": True, "words": 2,
             "factor": 0.1, "state_class": "measurement"},

    0x201C: {"name": "Reactive_Power_Phase_A", "device_class": "reactive_power", "unit": "kvar", "words": 2,
             "factor": 0.1, "state_class": "measurement"},
    0x201E: {"name": "Reactive_Power_Phase_B", "device_class": "reactive_power", "unit": "kvar", "words": 2,
             "factor": 0.1, "state_class": "measurement"},
    0x2020: {"name": "Reactive_Power_Phase_C", "device_class": "reactive_power", "unit": "kvar", "words": 2,
             "factor": 0.1, "state_class": "measurement"},

    0x202C: {"name": "Power_Factor_Phase_A", "device_class": "power_factor", "words": 2, "factor": 0.001,
             "state_class": "measurement"},
    0x202E: {"name": "Power_Factor_Phase_B", "device_class": "power_factor", "words": 2, "factor": 0.001,
             "state_class": "measurement"},
    0x2030: {"name": "Power_Factor_Phase_C", "device_class": "power_factor", "words": 2, "factor": 0.001,
             "state_class": "measurement"},

    0x2012: {"name": "Total_Active_Power", "device_class": "power", "unit": "W", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x201A: {"name": "Total_Reactive_Power", "device_class": "power", "unit": "W", "words": 2, "factor": 0.1,
             "state_class": "measurement"},
    0x202A: {"name": "Total_Power_Factor", "device_class": "power_factor", "words": 2, "factor": 0.001,
             "state_class": "measurement"},

    0x2044: {"name": "Frequency", "device_class": "frequency", "unit": "Hz", "words": 2, "factor": 0.01,
             "state_class": "measurement"},

    0x401E: {"name": "Total_Import_Energy", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x4020: {"name": "Import_Energy_A", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x4022: {"name": "Import_Energy_B", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x4024: {"name": "Import_Energy_C", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x4026: {"name": "Total_Net_Import_Energy", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},

    0x4028: {"name": "Total_Export_Energy", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x402A: {"name": "Export_Energy_A", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x402C: {"name": "Export_Energy_B", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x402E: {"name": "Export_Energy_C", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
    0x4030: {"name": "Total_Net_Export_Energy", "device_class": "energy", "unit": "kWh", "words": 2, "factor": 1,
             "state_class": "total_increasing"},
}

# list of address-ranges which can read in blocks
BLOCK_STATS = [
    {"address": 0x2000, "count": 34},
    {"address": 0x202A, "count": 8},
    {"address": 0x2044, "count": 2},
    {"address": 0x401E, "count": 20},
]

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

    0x2012,  # TOTAL_ACTIVE_POWER
    0x2014,  # ACTIVE_POWER_PHASE_A
    0x2016,  # ACTIVE_POWER_PHASE_B
    0x2018,  # ACTIVE_POWER_PHASE_C

    0x201A,  # TOTAL_REACTIVE_POWER
    0x201C,  # REACTIVE_POWER_PHASE_A
    0x201E,  # REACTIVE_POWER_PHASE_B
    0x2020,  # REACTIVE_POWER_PHASE_C

    0x202A,  # TOTAL_POWER_FACTOR
    0x202C,  # POWER_FACTOR_PHASE_A
    0x202E,  # POWER_FACTOR_PHASE_B
    0x2030,  # POWER_FACTOR_PHASE_C

    0x2044,  # FREQUENCY

    0x401E,  # TOTAL_IMPORT_ENERGY
    0x4020,
    0x4022,
    0x4024,
    0x4026,
    0x4028,  # TOTAL_EXPORT_ENERGY
    0x402A,
    0x402C,
    0x402E,
    0x4030,
]

FOUR_WIRE_KEYS = [
    0x2006,  # VOLTAGE_PHASE_A
    0x2008,  # VOLTAGE_PHASE_B
    0x200A,  # VOLTAGE_PHASE_C

    0x200C,  # CURRENT_PHASE_A
    0x200E,  # CURRENT_PHASE_B
    0x2010,  # CURRENT_PHASE_C

    0x2012,  # TOTAL_ACTIVE_POWER
    0x2014,  # ACTIVE_POWER_PHASE_A
    0x2016,  # ACTIVE_POWER_PHASE_B
    0x2018,  # ACTIVE_POWER_PHASE_C

    0x201A,  # TOTAL_REACTIVE_POWER
    0x201C,  # REACTIVE_POWER_PHASE_A
    0x201E,  # REACTIVE_POWER_PHASE_B
    0x2020,  # REACTIVE_POWER_PHASE_C

    0x202A,  # TOTAL_POWER_FACTOR
    0x202C,  # POWER_FACTOR_PHASE_A
    0x202E,  # POWER_FACTOR_PHASE_B
    0x2030,  # POWER_FACTOR_PHASE_C

    0x2044,  # FREQUENCY

    0x401E,  # TOTAL_IMPORT_ENERGY
    0x4020,
    0x4022,
    0x4024,
    0x4026,
    0x4028,  # TOTAL_EXPORT_ENERGY
    0x402A,
    0x402C,
    0x402E,
    0x4030,
]
# only this keys will
MQTT_TOPICS = [
    0x2006,  # VOLTAGE_PHASE_A
    0x2008,  # VOLTAGE_PHASE_B
    0x200A,  # VOLTAGE_PHASE_C

    0x200C,  # CURRENT_PHASE_A
    0x200E,  # CURRENT_PHASE_B
    0x2010,  # CURRENT_PHASE_C

    0x2012,  # TOTAL_ACTIVE_POWER
    0x2014,  # ACTIVE_POWER_PHASE_A
    0x2016,  # ACTIVE_POWER_PHASE_B
    0x2018,  # ACTIVE_POWER_PHASE_C

    0x201A,  # TOTAL_REACTIVE_POWER
    0x201C,  # REACTIVE_POWER_PHASE_A
    0x201E,  # REACTIVE_POWER_PHASE_B
    0x2020,  # REACTIVE_POWER_PHASE_C

    0x202A,  # TOTAL_POWER_FACTOR
    0x202C,  # POWER_FACTOR_PHASE_A
    0x202E,  # POWER_FACTOR_PHASE_B
    0x2030,  # POWER_FACTOR_PHASE_C

    0x2044,  # FREQUENCY

    0x401E,  # TOTAL_IMPORT_ENERGY
    0x4020,
    0x4022,
    0x4024,
    0x4026,
    0x4028,  # TOTAL_EXPORT_ENERGY
    0x402A,
    0x402C,
    0x402E,
    0x4030,
]
