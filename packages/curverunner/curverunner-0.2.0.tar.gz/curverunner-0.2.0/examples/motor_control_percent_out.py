"""Example of controlling closed loop motor using percent output mode."""

from curverunner import Curverunner, CurverunnerCommSerial, CurverunnerMotor
import time


# Create a CurveRunner instance using USB serial communication
# When no argument is given, the first available CurveRunner device is used
# I2C is recommended for usage with Raspberry Pi
comm = CurverunnerCommSerial()
# Create a CurveRunner instance using the communication interface
cr = Curverunner(comm)
print(f"Connected to CurveRunner with ID: {cr.get_device_id()}")

# Initialize motors with closed loop BDC mode and set slew rate
cr.motor1.set_motor_type(CurverunnerMotor.MOTOR_TYPE_CLOSED_LOOP_BDC)
cr.motor1.set_slew_rate(1.0)
cr.motor2.set_motor_type(CurverunnerMotor.MOTOR_TYPE_CLOSED_LOOP_BDC)
cr.motor2.set_slew_rate(1.0)

print("Setting motor1 to -50 percent and motor 2 to 50 percent output")
cr.motor1.set_percent_out(-0.5)
cr.motor2.set_percent_out(0.5)

# Sleep to allow motors to reach speed
time.sleep(1)
print("Motor 1 velocity (rads/s):", cr.motor1.get_velocity_rads())
print("Motor 2 velocity (rads/s):", cr.motor2.get_velocity_rads())

time.sleep(2)
print("Stopping motors")
cr.motor1.set_percent_out(0)
cr.motor2.set_percent_out(0)
