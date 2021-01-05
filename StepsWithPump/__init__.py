# -*- coding: iso-8859-1 -*-

"""
Heating steps activating a pump at set intervals
{License_info}
"""

# Built-in/Generic Imports
import time

# Libs
from modules.core.props import Property, StepProperty
from modules.core.step import StepBase
from modules import cbpi

# Own modules


__author__ = 'madhatguy'


# __copyright__ = 'Copyright {2020}, {project_name}'
# __credits__ = ['{credit_list}']
# __license__ = '{license}'
# __version__ = '{mayor}.{minor}.{rel}'
# __maintainer__ = '{maintainer}'
# __email__ = '{contact_email}'
# __status__ = '{dev_status}'

@cbpi.step
class PumpMash(StepBase):
    '''
    A step replacing the default mash step. Adds the functionality of temp overshoot and pump activation.
    '''
    # Properties
    temp = Property.Number("Temperature", configurable=True, description="Target Temperature of Mash Step")
    kettle = StepProperty.Kettle("Kettle", description="Kettle in which the mashing takes place")
    pump = StepProperty.Actor("Pump", description="Please select the agitator")
    timer = Property.Number("Timer in Minutes", configurable=True,
                            description="Timer is started when the target temperature is reached")
    # the diff in celsius degrees from mash temp to desired strike temp
    overshoot = Property.Number("Overshoot Temperature Difference", configurable=True, default_value=1,
                                description="The difference between the initial heating temp and the mash temp."
                                            "Reset doesn't use overshoot")
    pump_work_time = Property.Number("Mash pump work time", True, 600,
                                     description="Rest the pump after this many seconds during the mash.")
    pump_rest_time = Property.Number("Mash pump rest time", True, 60,
                                     description="Rest the pump for this many seconds every rest interval.")
    # the temp above which the pump starts its working cycles
    pump_min_temp = Property.Number("The Min Temperature", True, 40,
                                    description="The temperature in which the pump starts working.")
    pump_on = False  # current state of the pump
    last_toggle_time = None
    pump_cycle = None

    def init(self):
        '''
        Initialize Step. This method is called once at the beginning of the step
        :return:
        '''
        self.pump_cycle = {True: float(self.pump_work_time), False: float(self.pump_rest_time)}
        self.actor_off(int(self.pump))
        self.last_toggle_time = time.time()

        # set target temp
        self.set_target_temp(float(self.temp) + float(self.overshoot), self.kettle)

    @cbpi.action("Start Timer Now")
    def start(self):
        '''
        Custom Action which can be execute form the brewing dashboard.
        All method with decorator @cbpi.action("YOUR CUSTOM NAME") will be available in the user interface
        :return:
        '''
        if self.is_timer_finished() is None:
            self.start_timer(int(self.timer) * 60)

    def reset(self):
        self.stop_timer()
        self.set_target_temp(self.temp, self.kettle)

    def finish(self):
        self.set_target_temp(0, self.kettle)
        self.actor_off(int(self.pump))  # turns pump off

    def toggle_pump(self):
        '''
        Toggles between pump states (on/off)
        '''
        if self.pump_on:
            self.pump_on = False
            self.actor_off(int(self.pump))
        else:
            self.pump_on = True
            self.actor_on(int(self.pump))
        self.last_toggle_time = time.time()

    def execute(self):
        '''
        This method is execute in an interval
        :return:
        '''
        # Pump action
        if self.get_kettle_temp(self.kettle) >= float(self.pump_min_temp) and time.time() >= self.last_toggle_time + \
                self.pump_cycle[self.pump_on]:
            self.toggle_pump()
        # Check if Target Temp is reached
        if self.get_kettle_temp(self.kettle) >= float(self.temp) + float(self.overshoot):
            # Check if Timer is Running
            if self.is_timer_finished() is None:
                self.start_timer(int(self.timer) * 60)
                # sets target temp to mash temp
                self.set_target_temp(self.temp, self.kettle)
                self.notify("Mash Temp Reached!", "Insert Grain", timeout=None)
        # Check if timer finished and go to next step
        if self.is_timer_finished():
            self.actor_off(int(self.pump))  # turns pump off
            self.notify("Mash Step Completed!", "Starting the next step", timeout=None)
            self.next()


@cbpi.step
class PumpBoil(StepBase):
    '''
    A step replacing the default boil step. Adds the functionality of pump activation.
    '''
    # Properties
    temp = Property.Number("Temperature", configurable=True, default_value=100,
                           description="Target temperature for boiling")
    kettle = StepProperty.Kettle("Kettle", description="Kettle in which the boiling step takes place")
    pump = StepProperty.Actor("Pump", description="Please select the agitator")
    timer = Property.Number("Timer in Minutes", configurable=True, default_value=90,
                            description="Timer is started when target temperature is reached")
    hop_1 = Property.Number("Hop 1 Addition", configurable=True, description="Fist Hop alert")
    hop_1_added = Property.Number("", default_value=None)
    hop_2 = Property.Number("Hop 2 Addition", configurable=True, description="Second Hop alert")
    hop_2_added = Property.Number("", default_value=None)
    hop_3 = Property.Number("Hop 3 Addition", configurable=True)
    hop_3_added = Property.Number("", default_value=None, description="Third Hop alert")
    hop_4 = Property.Number("Hop 4 Addition", configurable=True)
    hop_4_added = Property.Number("", default_value=None, description="Fourth Hop alert")
    hop_5 = Property.Number("Hop 5 Addition", configurable=True)
    hop_5_added = Property.Number("", default_value=None, description="Fives Hop alert")

    pump_work_time = Property.Number("Mash pump work time", True, 200,
                                     description="Rest the pump after this many seconds during the mash.")
    pump_rest_time = Property.Number("Mash pump rest time", True, 100,
                                     description="Rest the pump for this many seconds every rest interval.")
    # the pump above which the pump stops working
    pump_max_temp = Property.Number("The Max Temperature", True, 100,
                                    description="The temperature in which the pump stops its cycles.")
    pump_on = False  # the current state of the pump
    pump_time = None
    pump_cycle = None

    def init(self):
        '''
        Initialize Step. This method is called once at the beginning of the step
        :return:
        '''
        # set target tep
        self.set_target_temp(self.temp, self.kettle)
        self.pump_cycle = {True: int(self.pump_work_time), False: int(self.pump_rest_time)}
        self.pump_time = time.time()
        self.actor_off(int(self.pump))

    @cbpi.action("Start Timer Now")
    def start(self):
        '''
        Custom Action which can be execute form the brewing dashboard.
        All method with decorator @cbpi.action("YOUR CUSTOM NAME") will be available in the user interface
        :return:
        '''
        if self.is_timer_finished() is None:
            self.start_timer(int(self.timer) * 60)

    def reset(self):
        self.stop_timer()
        self.set_target_temp(self.temp, self.kettle)

    def finish(self):
        self.set_target_temp(0, self.kettle)
        self.actor_off(int(self.pump))

    def check_hop_timer(self, number, value):

        if self.__getattribute__("hop_%s_added" % number) is not True and time.time() > (
                self.timer_end - (int(self.timer) * 60 - int(value) * 60)):
            self.__setattr__("hop_%s_added" % number, True)
            self.notify("Hop Alert", "Please add Hop %s" % number, timeout=None)

    def toggle_pump(self):
        """
        Toggles between pump states (on/off)
        """
        if self.pump_on:
            self.pump_on = False
            self.actor_off(int(self.pump))
        else:
            self.pump_on = True
            self.actor_on(int(self.pump))
        self.pump_time = time.time()

    def execute(self):
        '''
        This method is execute in an interval
        :return:
        '''
        # Pump action
        if self.get_kettle_temp(self.kettle) > float(self.pump_max_temp):
            self.actor_off(int(self.pump))
        elif time.time() >= self.pump_time + self.pump_cycle[self.pump_on]:
            self.toggle_pump()
        # Check if Target Temp is reached
        if self.get_kettle_temp(self.kettle) >= float(self.temp):
            # Check if Timer is Running
            if self.is_timer_finished() is None:
                self.start_timer(int(self.timer) * 60)
            else:
                self.check_hop_timer(1, self.hop_1)
                self.check_hop_timer(2, self.hop_2)
                self.check_hop_timer(3, self.hop_3)
                self.check_hop_timer(4, self.hop_4)
                self.check_hop_timer(5, self.hop_5)
        # Check if timer finished and go to next step
        if self.is_timer_finished():
            self.actor_off(int(self.pump))  # turns pump off
            self.notify("Boil Step Completed!", "Starting the next step", timeout=None)
            self.next()
