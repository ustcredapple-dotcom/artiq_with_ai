from moku.instruments import Oscilloscope


MOKU_IP = "192.168.10.100"


instrument = Oscilloscope(MOKU_IP, force_connect=False)
try:
    instrument.set_timebase(-0.001, 0.001)
    data = instrument.get_data()
    print("fields:", sorted(data.keys()))
    print("ch1 points:", len(data.get("ch1", [])))
    print("ch2 points:", len(data.get("ch2", [])))
    print("time points:", len(data.get("time", [])))
finally:
    instrument.relinquish_ownership()
