import RPi.GPIO as GPIO
from gpiozero import PWMLED

import multiprocessing
from multiprocessing import Process
import os
import time
import datetime

GPIO.setmode(GPIO.BCM)

# GPIO ports for the 7seg pins
# These are in order from the top segment going all the way around clockwise
# the last two segment pins are the middle segment and the dot, respectfully
segments = (11, 4, 23, 8, 7, 10, 18, 25)
# 7seg_segment_pins (11,7,4,2,1,10,5,3) +  220R

for s in segments:
    GPIO.setup(s, GPIO.OUT)
    GPIO.output(s, 1)

# GPIO ports for the digit 0-3 pins
digits = (22, 27, 17, 24)
# 7seg_digit_pins (12,9,8,6) digits 0-3 respectively

for d in digits:
    GPIO.setup(d, GPIO.OUT)
    GPIO.output(d, 0)


# Taking a segment pin to ground (0) activates that segment
digitSeg = {' ': (1,1,1,1,1,1,1,1),
            '.': (1,1,1,1,1,1,1,0),
            '0': (0,0,0,0,0,0,1,1),
            '1': (1,0,0,1,1,1,1,1),
            '2': (0,0,1,0,0,1,0,1),
            '3': (0,0,0,0,1,1,0,1),
            '4': (1,0,0,1,1,0,0,1),
            '5': (0,1,0,0,1,0,0,1),
            '6': (0,1,0,0,0,0,0,1),
            '7': (0,0,0,1,1,1,1,1),
            '8': (0,0,0,0,0,0,0,1),
            '9': (0,0,0,0,1,0,0,1)}

# alarm:
alarm = 21
enable_alarm = True
GPIO.setup(alarm, GPIO.OUT)
GPIO.output(alarm, 0)

#shutoff for shutting off the alarm
shutoff = 14
GPIO.setup(shutoff, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def shutoff_callback(channel):
    global enable_alarm
    enable_alarm = not enable_alarm
    print("\nToggled alarm! set to ->", enable_alarm)

GPIO.add_event_detect(shutoff, GPIO.RISING, callback=shutoff_callback, bouncetime=300)

# lights
red = PWMLED(5)
green = PWMLED(6)
blue = PWMLED(13)

def displayColor(color='White', brightness=0.8):
    color=color.lower()

    if color == 'white':
        red.on()
        green.on()
        blue.on()
    elif color == 'red':
        red.on()
        green.off()
        blue.off()
    elif color == 'orange':
        green.value = 0.05
        red.value = 1.0

        blue.off()
    elif color == 'yellow':
        green.value = 0.35
        red.value = 1.0

        blue.off()
    elif color == 'green':
        red.off()
        green.on()
        blue.off()

    else:
        red.off()
        green.off()
        blue.off()

    red.value *= brightness
    green.value *= brightness
    blue.value *= brightness


def displayDigit(digit):
    numP = digitSeg[digit]
    for pinLvl, seg in zip(numP, segments):
        GPIO.output(seg, pinLvl)


# Displays up to a 3-digit number
# Bringing these low will turn on the digits 0-3 (from left to right):
# [22] [27] [17] [24]
def displayNum(number):
    number = str(number) # ensuring string
    numDigits = len(number)

    print("Displaying number:", number)
    dif = 4-numDigits

    # This function should only be run as a subprocess
    while True:
        for i, digit in enumerate(number):
            # Turning on the right digits:
            try:
                GPIO.output(digits[i+dif], 1)
                # Displaying the digit:
                displayDigit(digit)
            except:
                print("error when turning on digit")

            time.sleep(0.000001)
            GPIO.output(digits[i+dif], 0)


def debugDisplay(speed=None):
    while True:
        for segment in segments:
            x = 0
            for digit in digits:
                print("GPIOPins:")
                print("\tDigit:", digit, "(number", str(x) + ")")
                print("\tSegment:", segment)

                GPIO.output(digit, 1)
                GPIO.output(segment, 0)

                if speed==None:
                    input()
                else:
                    time.sleep(speed)

                GPIO.output(digit, 0)
                GPIO.output(segment, 1)
                x += 1


def main(): 
    print("\n Start Time:", time.strftime("%d %b %H:%M:%S", time.localtime()))
    vid_delta, vid_title = int(datetime.timedelta().total_seconds()/60), "some video title" #TODO: replace with call to API
    currTime = time.localtime()
    prevCheckTime = currTime

    # only care if the video is within 30 mins of uploading
    num_to_display = vid_delta if vid_delta < 30 else ' ' 
    print("latest video '{}' uploaded '{}' minutes ago".format(vid_title, num_to_display))

    # Starts a subprocess to render the number on the 7-segment display
    renderNumber = Process(target=displayNum, args=(str(num_to_display),))
    renderNumber.start()

    while True:
        currTime = time.localtime()

        # Turns off during the night:
        if currTime.tm_hour >= 22 or currTime.tm_hour < 6:
            displayColor(color='None')
            if renderNumber.is_alive():
                print("Terminating")
                renderNumber.terminate()
                renderNumber.join()
                print("Alive status:", renderNumber.is_alive())

                # Reseting the pins:
                displayDigit(' ')

        else:
            # Checks video in 2 min intervals
            if (currTime.tm_min != prevCheckTime.tm_min and
                    currTime.tm_min % 2 == 0):
                print("\n", time.strftime("%d %b %H:%M:%S", time.localtime()))
                vid_delta, vid_title = int(datetime.timedelta().total_seconds()/60), "some video title" #TODO: replace with call to API

                prevCheckTime = currTime
                
                # only care if the video is within 30 mins of uploading
                num_to_display = vid_delta if vid_delta < 30 else ' ' 
                print("\t'{}' \n\tuploaded '{}' minutes ago".format(vid_title, num_to_display))
                

                # Terminates old process and starts a new one with the updated number:
                renderNumber.terminate()
                renderNumber.join()
                
                renderNumber = Process(target=displayNum, args=(str(num_to_display),))
                renderNumber.start()

                global enable_alarm
                # Updating color and making noise depending on how long ago it was uploaded
                if vid_delta < 5:
                    if enable_alarm:
                        # Set off alarm for 30 seconds 
                        GPIO.output(alarm, 1)
                        time.sleep(1) # TODO: change this to 30s later...
                        GPIO.output(alarm, 0)

                    # For a minute flash Green
                    for x in range(60):
                        displayColor(color='Green', brightness=1.0)
                        time.sleep(0.5)
                        displayColor(color='None')
                        time.sleep(0.5)

                    displayColor('Green')
                elif vid_delta < 10:
                    # Just flash green
                    # For a minute flash Green
                    for x in range(60):
                        displayColor(color='Green', brightness=1.0)
                        time.sleep(0.5)
                        displayColor(color='None')
                        time.sleep(0.5)
                    displayColor('Green')

                    # Reenabling alarm for next time
                    enable_alarm = True

                elif vid_delta < 20:
                    # display green
                    displayColor('Green')
                elif vid_delta < 30:
                    # display yellow
                    displayColor('Yellow')
                elif vid_delta < 60:
                    displayColor('Red')
                else:
                    displayColor() # displaying nothing



# try:
#     # main()
#     # print("testing numbers")
#     # debugDisplay()
# finally:
#     # Termination sequence:
#     GPIO.cleanup()
#     for process in multiprocessing.active_children():
#         process.terminate()
#         process.join()
