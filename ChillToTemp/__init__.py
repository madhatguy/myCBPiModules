
# -*- coding: iso-8859-1 -*-

"""
A step utilizing A counter-flow chiller with cbpi3
Step is finished (and the pump is turned off) after target temp has been reached or upper time bound was reached.
{License_info}
"""

# Built-in/Generic Imports

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

DEF_SAMPLES = 5


@cbpi.step
class ChillerToTemp(StepBase):
    '''
    Just put the decorator @cbpi.step on top of a method. The class name must be unique in the system
    '''
    # Properties
    temp = Property.Number("Desired Temperature", configurable=True)
    kettle = StepProperty.Kettle("Kettle")
    pump = StepProperty.Actor("Chiller Pump")
    timer = Property.Number("Upper Bound in Minutes", description="The time after which this step will conclude,"
                                                                  " regardless of the current temp", configurable=True)
    # num of times to check target temp has been reached (in order to rule out bad readings)
    Samples = Property.Number("Number of Temp Readings before ShutDown", default_value=DEF_SAMPLES,
                              description="A safety against false positive detection", configurable=True)
    sample_streak = 0

    def init(self):
        '''
        Initialize Step. This method is called once at the beginning of the step
        :return:
        '''
        # set target tep
        self.set_target_temp(self.temp, self.kettle)
        self.start_timer(int(self.timer) * 60)
        # turns pump on
        self.actor_on(int(self.pump))

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
        self.start_timer(int(self.timer) * 60)

    def finish(self):
        self.set_target_temp(0, self.kettle)
        # turns pump off at finish
        self.actor_off(int(self.pump))

    def execute(self):
        '''
        This method is executed in intervals
        :return:
        '''

        # Check if Target Temp has been reached
        if self.get_kettle_temp(self.kettle) <= float(self.temp):
            self.sample_streak += 1
            # Checks if Target Amount of Samples is reached
            if self.sample_streak == self.Samples:
                self.notify("Yeast Pitch Temp Reached!", "Move to fermentation tank", timeout=None)
                # turns pump off at finish
                self.actor_off(int(self.pump))
                self.next()
        else:
            # Nullifies The samples streak
            self.sample_streak = 0
        # Check if timer finished and go to next step
        if self.is_timer_finished():
            self.notify("Step Temp Wasn't Reached!", "Good luck:(", timeout=None)
            # turns pump off at finish
            self.actor_off(int(self.pump))
            self.next()
