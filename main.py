import RPi.GPIO as GPIO
from gpiozero import PWMLED

import multiprocessing
from multiprocessing import Process
import os
import time

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

red = PWMLED(5)
green = PWMLED(6)
blue = PWMLED(13)

def displayColor(color='White', brightness=0.8):
    if color == 'White':
        red.on()
        green.on()
        blue.on()
    elif color == 'Red':
        red.on()
        green.off()
        blue.off()
    elif color == 'Orange':
        green.value = 0.05
        red.value = 1.0

        blue.off()
    elif color == 'Yellow':
        green.value = 0.35
        red.value = 1.0

        blue.off()
    elif color == 'Green':
        red.off()
        green.on()
        blue.off()

    elif color == 'None':
        red.off()
        green.off()
        blue.off()

    else:
        print("\nERROR: THAT IS NOT A COLOR\n")

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

            time.sleep(0.00001)
            GPIO.output(digits[i+dif], 0)


def debugDisplay(speed=1):
    while True:
        for segment in segments:
            x = 0
            for digit in digits:
                print("GPIOPins:")
                print("\tDigit:", digit, "(number", str(x) + ")")
                print("\tSegment:", segment)

                GPIO.output(digit, 1)
                GPIO.output(segment, 0)

                time.sleep(speed)
                GPIO.output(digit, 0)
                GPIO.output(segment, 1)
                x += 1


def main():
    print("started")
    # print("\n", time.strftime("%d %b %H:%M:%S", time.localtime()))
    # communityStatus, activeCases = getData()
    # currTime = time.localtime()
    # prevCheckTime = currTime
    # prevActiveCases = activeCases

    # # Starts a subprocess to render the number on the 7-segment display
    # renderNumber = Process(target=displayNum, args=(str(activeCases),))
    # renderNumber.start()
    # displayColor(color=communityStatus)

    # while True:
    #     currTime = time.localtime()

    #     # Turns off during the night:
    #     if currTime.tm_hour >= 22 or currTime.tm_hour < 6:
    #         displayColor(color='None')
    #         if renderNumber.is_alive():
    #             print("Terminating")
    #             renderNumber.terminate()
    #             renderNumber.join()
    #             print("Alive status:", renderNumber.is_alive())

    #             # Reseting the pins:
    #             displayDigit(' ')

    #     else:
    #         # Checks the cases every 15 min
    #         if (currTime.tm_min != prevCheckTime.tm_min and
    #                 currTime.tm_min % 15 == 0):

    #             print("\n", time.strftime("%d %b %H:%M:%S", time.localtime()))
    #             communityStatus, activeCases = getData()
    #             prevCheckTime = currTime

    #             # Only terminates if the new number is different
    #             if (prevActiveCases != activeCases or
    #                  not renderNumber.is_alive()):
    #                 prevActiveCases = activeCases

    #                 # Terminates old process and starts a new one with the updated number:
    #                 renderNumber.terminate()
    #                 renderNumber.join()

    #                 renderNumber = Process(target=displayNum, args=(str(activeCases),))
    #                 renderNumber.start()

    #                 # Flashes the color to show that the number has been updated
    #                 for x in range(60):
    #                     displayColor(color='White', brightness=1.0)
    #                     time.sleep(0.5)
    #                     displayColor(color='None')
    #                     time.sleep(0.5)

    #             # Updates the color:
    #             displayColor(color=communityStatus)


try:
    main()
    print("testing numbers")
    debugDisplay(0.25)
finally:
    # Termination sequence:
    GPIO.cleanup()
    for process in multiprocessing.active_children():
        process.terminate()
        process.join()
