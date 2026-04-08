from typing import Tuple, Dict
import sounddevice as sd
import time
import numpy as np
from scipy.io import wavfile
import tkinter as tk
from tkinter import filedialog
import os

# List of devices to connect to
DEVICES = [
    "HSD mk.I",
    "HSD mk.ii",
    "HSD mk.iii",
    "SKINETIC",
]

# List of APIs that can be used
APIS = [
    "Windows WDM-KS",
    "Windows WASAPI",
]

SPR = 48000  # Hz
duration = 60  # seconds
t = np.linspace(0, duration, duration * SPR)
print(t.shape)

# Open a file dialog to select a WAV file
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select a WAV file", filetypes=[("WAV files", "*.wav")]
)

# Dictionary to store audio file path
audio_files = {"selected": file_path}

# Channel processing operations (modify as needed)
CHANNELS = {
    13: ('t1', '-'),
    11: ('t2', '-'),
    9: ('ff1', '-'),
    8: ('ff2', '-'),
    18: ('ff3', '-'),
    5: ('mf1', '-'),
    17: ('mf2', '-'),
    4: ('rf1', '-'),
    7: ('rf2', '-'),
    3: ('p1', '-'),
    6: ('p2', '-'),
    10: ('palm11', '-'),
    1: ('palm12', '-'),
    2: ('palm13', '+'),
    12: ('palm21', '-'),
    0: ('palm22', '+'),
    16: ('palm23', '-'),
    14: ('palm31', '-'),
    15: ('palm32', '-'),
    19: ('palm33', '-')
}

# Prompt user for mono channel assignment
def get_channel_assignment() -> int:
    while True:
        try:
            channel = int(input("Enter the channel number (0-19) to assign mono audio: "))
            if 0 <= channel <= 19:
                return channel
            else:
                print("Invalid input. Please enter a number between 0 and 19.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

mono_channel = get_channel_assignment()

def load_audio_files(audio_files: Dict[str, str], mono_channel: int) -> Dict[str, np.ndarray]:
    signals = {}

    for key, file_path in audio_files.items():
        if os.path.exists(file_path):
            fs, data = wavfile.read(file_path)

            # Ensure data is at least 1D
            if data.ndim == 1:  # If mono, reshape to (N, 1)
                data = data[:, np.newaxis]

            num_channels = data.shape[1]
            if num_channels == 1:  # If the WAV file is mono
                multi_channel_data = np.zeros((data.shape[0], 20), dtype=np.int16)
                multi_channel_data[:, mono_channel] = data[:, 0]  # Assign mono audio to chosen channel
            elif num_channels == 20:  # If already 20 channels
                multi_channel_data = data
            else:
                raise ValueError("WAV file must have 1 or 20 channels")

            # Process the signal
            modified_signal = [multi_channel_data[:, i].astype('int16') for i in range(20)] 

            for channel, (_, operation) in CHANNELS.items():
                if operation == '-':
                    modified_signal[channel] = -2 * np.abs(modified_signal[channel])
                elif operation == '+':
                    modified_signal[channel] = 2 * np.abs(modified_signal[channel])

            signals[key] = modified_signal
        else:
            print(f"File {file_path} for key {key} does not exist.")
    
    return signals

# Load and process the WAV file with user-defined mono channel
SIGNALS = load_audio_files(audio_files, mono_channel)["selected"]
X = 0
print(f"Mono audio assigned to channel {mono_channel}")
print(SIGNALS)

def find_device(device_list: sd.DeviceList, api_list: Tuple[Dict]) -> int:
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError

def stream_callback(data: np.ndarray, frames: int, _, __):
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
        raise sd.CallbackStop  # Stop playback at the end of the file

available_devices = sd.query_devices()
available_apis = sd.query_hostapis()
print("Available devices:")
print(available_devices)
print("\nAvailable APIs:")
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
