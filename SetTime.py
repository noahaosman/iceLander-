from machine import I2C, Pin
from urtc import DS3231
import utime

# go to tools --> manage packages... --> search & download package "urtc"
# This program should only need to be ran one time as an initialization step for a new RTC module

i2c = I2C(0,scl = Pin(17),sda = Pin(16),freq = 400000)
rtc = DS3231(i2c)

year = int(input("Year : "))
month = int(input("month (Jan --> 1 , Dec --> 12): "))
date = int(input("date : "))
day = int(input("day (1 --> monday , 2 --> Tuesday ... 0 --> Sunday): "))
hour = int(input("hour (24 Hour format): "))
minute = int(input("minute : "))
second = int(input("second : "))

now = (year,month,date,day,hour,minute,second,0)
rtc.datetime(now)

while True:
    (year,month,date,day,hour,minute,second,p1)=rtc.datetime()
    utime.sleep(1)
    print(rtc.datetime())