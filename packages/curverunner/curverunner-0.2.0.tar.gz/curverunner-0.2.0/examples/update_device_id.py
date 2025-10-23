"""Example script to update the CurveRunner device ID via USB serial communication.
"""


from curverunner import Curverunner, CurverunnerCommSerial

new_id = 42

comm = CurverunnerCommSerial()
cr = Curverunner(comm)
print(f"Connected to CurveRunner with ID: {cr.get_device_id()}")

if cr.get_device_id() == new_id:
    print(f"Device ID is already {new_id}, no update needed.")
else:
    cr.set_device_id(new_id)
    print(f"Device ID updated to: {cr.get_device_id()}")

