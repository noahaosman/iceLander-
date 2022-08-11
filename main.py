import machine
import time
import uos
import RTC
from machine import Pin, SPI
import sdcard
import os


spi=SPI(1,baudrate=40000000,sck=Pin(10),mosi=Pin(11),miso=Pin(12))
sd=sdcard.SDCard(spi,Pin(9))
# Create a instance of MicroPython Unix-like Virtual File System (VFS),
vfs=os.VfsFat(sd)
 
# Mount the SD card
os.mount(sd,'/sd')

### Define Constants
ADC_CF = 3.3/(65536)
AUX_BATT_DIV_RATIO = 14.8/2.426 #R1 = 5.1kOhm; R2 = 1kOhm
MELT_2BATT_DIV_RATIO = 50.4/2.185 # R1 = 100kOhm; R2 = 4.11kOhm?

### Setup ouputs
stat_led = machine.Pin(25, machine.Pin.OUT)
melt_ssr = machine.Pin(0, machine.Pin.OUT)
thrust_relay = machine.Pin(1, machine.Pin.OUT)

### setup thruster control
thrust_relay.on()
thrust_on = 1
pwm = machine.PWM(machine.Pin(5))
pwm_freq = 200
pwm.freq(pwm_freq)
def thrust(thrust_bool):
    if thrust_bool == 1:
        frac = 0.6
    else:
        frac = 0.0
    pwm.duty_u16(int( pwm_freq*(0.000001)*(1500+frac*400)*(65535) ))
thrust(0)

### setup Inputs
reed_sw_on = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
reed_sw_off = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)

### Setup Analog pins
analog_adc_0 = machine.ADC(26) # melt battery pin
analog_adc_1 = machine.ADC(27) # aux battery pin

#setup default outputs 
stat_led.off()
melt_ssr.off()
melt_tip_state = 0
tim = machine.Timer()
low_aux_battery = False
low_melt_battery = False
start_time=0
    
def heartbeat(timer):
    global stat_led
    global low_aux_battery
    global low_melt_battery
    
    if not low_aux_battery and not low_melt_battery:
        stat_led.toggle()
    else:
        for i in range(1,5):
            stat_led.on()
            time.sleep_ms(50)
            stat_led.off()
            time.sleep_ms(50)
        
def read_adc(p):
    res = p.read_u16()
    return res*ADC_CF
    
def reed_sw_on_callback(p):
    global melt_tip_state
    global start_time
    global low_aux_battery
    global low_melt_battery
    
    time.sleep_ms(10)
    if reed_sw_on.value() == 0:
        if not low_aux_battery and not low_melt_battery:
            if melt_tip_state == 0: #if melt stake is currently OFF
                print("")
                print("Initializing melt tip")
                thrust(thrust_on)
                print("    - Thruster ON")
#                 print("    - Waiting five seconds ... ", end =" ")
#                 for i in range(1,8):
#                     time.sleep_ms(500)
#                     time.sleep_ms(500)
#                     if i < 8:
#                         print(i, end =" ")
#                     else:
#                         print(8)
                start_time = time.time()
                melt_ssr.on() # turn on melt tip
                print("    - Melt tip ON")  
                check_battery_voltage()
                melt_tip_state = 1
            

def reed_sw_off_callback(p):
    global melt_tip_state
    global start_time
    
    time.sleep_ms(10)
    if reed_sw_off.value() == 0:
        time.sleep_ms(100)
        if melt_tip_state == 1: # if melt stake is currently ON
            print("")
            print("Deactivating melt tip")
            melt_ssr.off() # turn off melt tip
            print("    - Melt tip OFF")
            thrust(0)
            print("    - Thruster OFF")
            print("    - time on: ", time.time()-start_time," seconds")
            melt_tip_state = 0
    
def check_battery_voltage():
    global melt_tip_state
    global imon_offset
    global low_aux_battery
    global low_melt_battery
    
    # Read battery voltages
    aux_batt_v = read_adc(analog_adc_1)*AUX_BATT_DIV_RATIO
    print("\rAuxiliary battery voltage =", aux_batt_v, "V    |    ", end='')
    melt_batt_V = read_adc(analog_adc_0)*MELT_2BATT_DIV_RATIO
    print("Melt battery voltage =", melt_batt_V, "V    ", end='')
        
    # if aux battery is low, shut things down
    if aux_batt_v > 13.5 - (1.5*float(melt_tip_state)):
        low_aux_battery = False
    else:
        low_aux_battery = True
        print("!!!! LOW VOLTAGE -- recharge auxiliary battery !!!!", end='')
        if melt_tip_state == 1:
            print("turning thruster & melt tip OFF")
            reed_sw_off_callback(1)
            
    # if melt battery is low, shut things down
    if melt_batt_V>41.0:
        low_melt_battery = False
        print("                                                   ", end='')
    else:
        low_melt_battery = True
        print("!!!! LOW VOLTAGE -- recharge melt tip battery !!!! ", end='')
        if melt_tip_state == 1:
            print("turning thruster & melt tip OFF")
            reed_sw_off_callback(1)
    
    #save date to file
    if melt_tip_state == 1:
        current_time = RTC.DateTime()
        file = open("/sd/"+current_time[0]+".txt","a")
        file.write(current_time[1]+" "+"AUX BATT="+str(aux_batt_v)+"V; " + "MELT BATT="+str(melt_batt_V)+ "V\r\n")
        file.close()
            
reed_sw_on.irq(trigger=machine.Pin.IRQ_FALLING, handler=reed_sw_on_callback)

reed_sw_off.irq(trigger=machine.Pin.IRQ_FALLING, handler=reed_sw_off_callback)

tim.init(freq=1, mode=machine.Timer.PERIODIC, callback=heartbeat)

while True:
    #if not low_aux_battery and not low_melt_battery:
    check_battery_voltage()
#     print("----")
#     print(reed_sw_off.value())
#     print(reed_sw_on.value())
    time.sleep_ms(1000)