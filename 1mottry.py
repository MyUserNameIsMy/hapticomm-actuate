from typing import Dict
import sounddevice as sd
import time
import numpy as np
from scipy.io import wavfile
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

audio_files = {}
variable_folder = "./Variable"

# Load WAV files Var_1.wav to Var_9.wav
digits = range(1, 10)
for i in digits:
    file_path = os.path.join(variable_folder, f"Var_{i}.wav")
    if os.path.exists(file_path):
        audio_files[f"Var_{i}"] = file_path
    else:
        print(f"Warning: {file_path} not found.")

# Channel processing operations (modify as needed)
CHANNELS = {
    13: ('t1', '-'),
    11: ('t2', '-'),
    9: ('ff1', '-'),
    8: ('ff2', '-'),
    18: ('ff3', '+'),
    5: ('mf1', '+'),
    17: ('mf2', '+'),
    4: ('rf1', '+'),
    7: ('rf2', '+'),
    3: ('p1', '-'),
    6: ('p2', '+'),
    10: ('palm11', '-'),
    1: ('palm12', '+'),
    2: ('palm13', '-'),
    12: ('palm21', '-'),
    0: ('palm22', '-'),
    16: ('palm23', '-'),
    14: ('palm31', '+'),
    15: ('palm32', '+'),
    19: ('palm33', '+')
}

def load_audio_files(audio_files: Dict[str, str], file_key: str, channel_number: int) -> Dict[str, np.ndarray]:
    file_path = audio_files[file_key]
    fs, data = wavfile.read(file_path)
    
    if data.ndim == 1:
        data = data[:, np.newaxis]
    
    num_channels = data.shape[1]
    if num_channels == 1:
        multi_channel_data = np.zeros((data.shape[0], 20), dtype=np.int16)
        multi_channel_data[:, channel_number] = data[:, 0]  # Assign to chosen channel
    elif num_channels == 20:
        multi_channel_data = data
    else:
        raise ValueError("WAV file must have 1 or 20 channels")
    
    modified_signal = [multi_channel_data[:, i].astype('int16') for i in range(20)] 

    for channel, (_, operation) in CHANNELS.items():
        if operation == '-':
            modified_signal[channel] = -1 * np.abs(modified_signal[channel])
        elif operation == '+':
            modified_signal[channel] = np.abs(modified_signal[channel])
    
    return modified_signal

def find_device(device_list: sd.DeviceList, api_list):
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError

def stream_callback(data: np.ndarray, frames: int, _, __):
    global X, repeat_count
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
        repeat_count -= 1
        if repeat_count > 0:
            time.sleep(delay_seconds)
        if repeat_count <= 0:
            raise sd.CallbackStop

available_devices = sd.query_devices()
available_apis = sd.query_hostapis()

try:
    device_id = find_device(available_devices, available_apis)
except OSError:
    print("No compatible device found.")
    quit()

print("Start streaming on device", device_id)

while True:
    user_input = input("Enter the channel name, file number, repeat count, and delay (e.g., 't1 2 3 1.5') or type 'exit' to quit: ")
    if user_input.lower() == 'exit':
        break
    
    try:
        channel_name, file_number, repeat_count, delay_seconds = user_input.split()
        repeat_count = int(repeat_count)
        delay_seconds = float(delay_seconds)
        file_key = f"Var_{file_number}"
        channel_number = next((k for k, v in CHANNELS.items() if v[0] == channel_name), None)
        if channel_number is None or file_key not in audio_files or repeat_count < 1:
            print("Invalid input. Try again.")
            continue
    except ValueError:
        print("Invalid input format. Use 'channel_name file_number repeat_count delay_seconds'.")
        continue
    
    SIGNALS = load_audio_files(audio_files, file_key, channel_number)
    X = 0
    
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
        print("End of Stimuli")
