"""
ToL constants
"""
from __future__ import absolute_import
import math
from revolve.build.sdf import PID

MAX_HIDDEN_NEURONS = 10
""" Maximum number of hidden neurons """

MAX_SERVO_TORQUE = 0.1 * (1.8 * 9.81) / 100
""" Expressed in Newton*m from kg-cm = ((kg-cm)*g)/100 """

MAX_SERVO_TORQUE_ROTATIONAL = 0.1 * (4 * 9.81) / 100
""" Expressed in Newton*m from kg-cm = ((kg-cm)*g)/100 """

MAX_SERVO_VELOCITY = (50.0/60.0) * 2 * math.pi
""" Maximum rotational velocity of a servo, in radians / second """

SERVO_LIMIT = math.radians(45)
""" Upper and lower limit """

CARDAN_LIMIT = math.radians(45)
""" Upper and lower limit of each axis of rotation """

# We're using small values for the default PIDs, since they actually
# overshoot quite rapidly.
SERVO_VELOCITY_PID = PID(
    proportional_gain=1e-2,
    derivative_gain=1e-2,

    # Can apply up to 1/10th of total force as integral error
    integral_gain=0.1,
    integral_max=MAX_SERVO_TORQUE_ROTATIONAL
)
""" Default servo velocity PID """

SERVO_POSITION_PID = PID(
    proportional_gain=5e-4,
    derivative_gain=8e-5,

    # Can apply up to 1/10th of total force as integral error
    integral_gain=5e-5,
    integral_max=MAX_SERVO_TORQUE
)
""" Default servo position PID. """
