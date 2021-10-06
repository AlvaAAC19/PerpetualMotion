# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO 
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus
from threading import Thread


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port = 0, speed = INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////

s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                 steps_per_unit=200, speed = 2)

class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40

    ramp_speed_slider = ObjectProperty(None)
    staircase_speed_slider = ObjectProperty(None)

    servoPosition = 0
    state = 0
    cyprus.set_pwm_values(1, period_value=100000, compare_value=state, compare_mode=cyprus.LESS_THAN_OR_EQUAL)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        #if self.servoPosition == 0:
        cyprus.set_servo_position(2, 0.5)
        sleep(2)
        cyprus.set_servo_position(2, 0)
            #self.servoPosition = 0.5
        #else:
            #cyprus.set_servo_position(2, 0)
            #self.servoPosition = 0
        print("Open and Close gate here")

    def toggleStaircase(self):
        if self.state == 0:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=60000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.state = 60000
        else:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.state = 0
        print("Turn on and off staircase here")

    def thread_toggleRamp(self):
        Thread(target=self.toggleRamp).start()

    def toggleRamp(self):
        while s0.get_position_in_units() < 28:
            if (cyprus.read_gpio() & 0b0010) == 0:  # binary bitwise AND of the value returned from read.gpio()
                sleep(0.1)
                if (cyprus.read_gpio() & 0b0010) == 0:
                    print("GPIO on port P7 is activated")
                    s0.start_relative_move(28)
                    sleep(0.1)
            # elif (cyprus.read_gpio() & 0b0001) == 0:
            #     print("GPIO on port P6 is activated")
            #     s0.go_until_press(0, 64000)
            #     sleep(0.1)
            # else:
            #     s0.start_relative_move(0)
        s0.softStop()
        s0.go_until_press(0, 64000)
        print("Move ramp up and down here")
        
    def auto(self):
        while True:
            while s0.get_position_in_units() < 28:
                if (cyprus.read_gpio() & 0b0010) == 0:  # binary bitwise AND of the value returned from read.gpio()
                    sleep(0.1)
                    if (cyprus.read_gpio() & 0b0010) == 0:
                        cyprus.set_servo_position(2, 0)
                        s0.start_relative_move(28)
                        sleep(0.1)
            s0.softStop()
            cyprus.set_pwm_values(1, period_value=100000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            s0.go_until_press(0, 64000)
            sleep(13)
            cyprus.set_servo_position(2, 0.5)
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)

        print("Run through one cycle of the perpetual motion machine")
        
    def setRampSpeed(self, value):
        #self.ramp_speed_slider
        s0.set_speed(self.ramp_speed_slider.value)
        print("Set the ramp speed and update slider text")
        
    def setStaircaseSpeed(self, speed):
        #self.staircase_speed_slider
        cyprus.set_pwm_values(1, period_value=100000, compare_value=speed, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        print("Set the staircase speed and update slider text")
        
    def initialize(self):
        cyprus.initialize()
        cyprus.set_servo_position(2, 0)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        s0.go_until_press(0, 64000)
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
