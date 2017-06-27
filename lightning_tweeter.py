#!/usr/bin/env python
# -*- coding: utf-8 -*-
from RPi_AS3935 import RPi_AS3935
import RPi.GPIO as GPIO
import thread
import time
from datetime import datetime
import tweepy

# Initialize Twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

# Initialize GPIO
GPIO.setmode(GPIO.BCM)

# pin used for interrupts
pin = 17
# Rev. 1 Raspberry Pis should leave bus set at 0, while rev. 2 Pis should set
# bus equal to 1. The address should be changed to match the address of the
# sensor.
sensor = RPi_AS3935(address=0x03, bus=1)
# Indoors = more sensitive (can miss very strong lightnings)
# Outdoors = less sensitive (can miss far away lightnings)
sensor.set_indoors(False)
sensor.set_noise_floor(1)
# Change this value to the tuning value for your sensor
sensor.calibrate(tun_cap=0x01)

last_alert = datetime.min
strikes_since_last_alert = 0


# We use a function to send tweet so that we can run it in a different thread and avoid spending too much time in the
# interrupt handle
def send_tweet(tweet):
    api.update_status(tweet)


# Interrupt handler
def handle_interrupt(channel):
    global last_alert
    global strikes_since_last_alert
    global sensor
    current_timestamp = datetime.now()
    time.sleep(0.003)
    reason = sensor.get_interrupt()
    if reason == 0x01:
        print("Noise level too high - adjusting")
        sensor.raise_noise_floor()
    elif reason == 0x04:
        print("Disturber detected. Masking subsequent disturbers")
        sensor.set_mask_disturber(True)
    elif reason == 0x08:
        print("We sensed lightning! (%s)" % current_timestamp.strftime('%H:%M:%S - %Y/%m/%d'))
        if (current_timestamp - last_alert).seconds < 300:
            print("Last strike is too recent, incrementing counter since last alert.")
            strikes_since_last_alert += 1
            return
        distance = sensor.get_distance()
        energy = sensor.get_energy()
        print("Energy: " + str(energy) + " - distance: " + str(distance) + "km")
        # Yes, it tweets in French. Baguette.
        if strikes_since_last_alert == 0:
            thread.start_new_thread(send_tweet, (
                "Eclair détecté ! Puissance : {0} - distance du front de tempête : {1}km".format(energy, distance),))
        else:
            thread.start_new_thread(send_tweet, (
                "/!\ {2} éclairs détectés ces {3} dernières minutes. Puissance dernier éclair : {0} - distance du front de tempête : {1}km".format(
                    energy, distance, strikes_since_last_alert + 1, (current_timestamp - last_alert).seconds / 60),))
            strikes_since_last_alert = 0
        last_alert = current_timestamp
    # If no strike has been detected for the last hour, reset the strikes_since_last_alert (consider storm finished)
    if (current_timestamp - last_alert).seconds > 1800 and last_alert != datetime.min:
        thread.start_new_thread(send_tweet, (
                "\o/ Orage terminé. Aucun nouvel éclair détecté depuis 1 heure.",))
        strikes_since_last_alert = 0
        last_alert = datetime.min


# Use a software Pull-Down on interrupt pin
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
sensor.set_mask_disturber(False)
GPIO.add_event_detect(pin, GPIO.RISING, callback=handle_interrupt)

print("Waiting for lightning - or at least something that looks like it")

try:
    while True:
        # Read/clear the sensor data every 10s in case we missed an interrupt (interrupts happening too fast ?)
        time.sleep(10)
        handle_interrupt(pin)
finally:
    # cleanup used pins... just because we like cleaning up after us
    GPIO.cleanup()
