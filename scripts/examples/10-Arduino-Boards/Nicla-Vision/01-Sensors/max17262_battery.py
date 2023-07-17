# Example for Nicla Sense ME Vision Board battery monitoring IC MAX17262

from machine import I2C
from max17262 import MAX17262
from time import sleep_ms

# set your battery parameters here
your_capacity = 340  # mAh
your_termination_current = 50000  # uA

# construct the MAX17262 object and initialize the ic with your battery parameters
battery = MAX17262(I2C(2), your_capacity, your_termination_current)

while True:
    print(f"Charge: {battery.state_of_charge} %")
    print(f"Time to empty: {battery.time_to_empty} s")
    print(f"Voltage: {battery.voltage /1000} V")
    print(f"Current: {battery.current / 1000} mA")
    print(f"Die Temperature: {battery.temperature} °C")
    sleep_ms(2000)
