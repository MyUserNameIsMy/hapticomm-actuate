from typing import Tuple, Dict
import sounddevice as sd
import time
import numpy
from scipy.io import wavfile
from scipy import signal
import tkinter as tk
from tkinter import filedialog

# List of devices to connect to
# The actual device name cannot be predicted, but it should at least contain the
# specified string
DEVICES = [
    "HSD mk.I",
    "HSD mk.ii",
    "HSD mk.iii",
    "SKINETIC",
]

# List of API that can be used
APIS = [
    "Windows WDM-KS",
    "Windows WASAPI",
]

SPR = 48000  # Hz
duration = 60  # second
t = numpy.linspace(0, duration, duration * SPR)
print(t.shape)

# Open a file dialog to select a WAV file
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select a WAV file", filetypes=[("WAV files", "*.wav")]
)

# Load the selected WAV file
fs, data = wavfile.read(file_path)
assert data.ndim == 2 and data.shape[1] == 20, "WAV file must have 20 channels"
SIGNALS = [(data[:, i]).astype('int16') for i in range(20)]
X = 0
print(SIGNALS)


def find_device(device_list: sd.DeviceList, api_list: Tuple[Dict]) -> int:
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError


def stream_callback(data: numpy.ndarray, frames: int, _, __):
    global X
    end_reached = False
    for c in range(data.shape[1]):
        r = len(SIGNALS[c]) - X
        if frames > r:
            data[0:r, c] = SIGNALS[c][X:X+r]
            data[r:, c].fill(0)
            end_reached = True
        else:
            data[:, c] = SIGNALS[c][X:X+frames]
    X += frames
    if end_reached:
        X = 0
        # To play in loop forever, comment the next line.
        raise sd.CallbackStop


available_devices = sd.query_devices()
available_apis = sd.query_hostapis()
print("Available devices:")
print(available_devices)
print()
print("Available APIs:")
for api in available_apis:
    print(api['name'], ": Devices", api['devices'])
print()

try:
    device_id = find_device(available_devices, available_apis)
except OSError:
    print("No compatible device found")
    print("If your device is listed above, add the appropriate entries to the "
          "lists 'DEVICES' and 'APIS' to allow connection")
    print("Otherwise, check wiring and power supply and try again")
    quit()
print("Start streaming on device", device_id)
print("Ctrl+C to stop")
try:
    out_stream = sd.OutputStream(
        samplerate=SPR, blocksize=0, device=device_id, channels=20,
        dtype='int16', latency='low', callback=stream_callback)
    out_stream.start()
    while out_stream.active:
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    out_stream.stop()
    print("End of streaming")
