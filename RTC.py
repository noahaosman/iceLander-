from machine import I2C, Pin
from urtc import DS3231
import utime

i2c_rtc = I2C(0,scl = Pin(17),sda = Pin(16),freq = 400000)
result = I2C.scan(i2c_rtc)
rtc = DS3231(i2c_rtc)

def LeadZero(int_in):
    return ('00' + str(int_in))[-2:]

def DateTime():
    (year,month,date,day,hour,minute,second,p1)=rtc.datetime()
    return [str(year)+"-"+LeadZero(month)+"-"+LeadZero(date) , LeadZero(hour)+":"+LeadZero(minute)+":"+LeadZero(second)]
    
