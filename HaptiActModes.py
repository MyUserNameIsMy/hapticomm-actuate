
from typing import Tuple, Dict
import sounddevice as sd
import time
import numpy as np
from scipy.io import wavfile
import os

# List of devices to connect to
DEVICES = [
    "HSD mk.I",
    "HSD mk.ii",
    "SKINETIC",
]

# List of API that can be used
APIS = [
    "Windows WDM-KS",
    "Windows WASAPI",
]

SPR = 48000  # Hz
duration = 60  # seconds

# Predetermined paths for audio files in different modes
MODES = {
    
    "default": "",
    "pop": "pop/",
    "reverse": "reverse/",
    "check": "Check/",
    "var": "Variable/"
}

# Actuator channels mapping with hardcoded + or - signs
CHANNELS = {
    13: ('t1', '-'),
    11: ('t2', '-'),
    9: ('ff1', '-'),
    8: ('ff2', '-'),
    18: ('ff3', '-'),
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

# Function to create the AUDIO_FILES dictionary based on the chosen mode
def create_audio_files_dict(mode: str) -> Dict[str, str]:
    prefix = MODES.get(mode, "")
    return {
        'A': os.path.join(prefix, 'Actuat_LetA.wav'),
        'B': os.path.join(prefix, 'Actuat_LetB.wav'),
        'C': os.path.join(prefix, 'Actuat_LetC.wav'),
        'D': os.path.join(prefix, 'Actuat_LetD.wav'),
        'E': os.path.join(prefix, 'Actuat_LetE.wav'),
        'F': os.path.join(prefix, 'Actuat_LetF.wav'),
        'G': os.path.join(prefix, 'Actuat_LetG.wav'),
        'H': os.path.join(prefix, 'Actuat_LetH.wav'),
        'I': os.path.join(prefix, 'Actuat_LetI.wav'),
        'J': os.path.join(prefix, 'Actuat_LetJ.wav'),
        'K': os.path.join(prefix, 'Actuat_LetK.wav'),
        'L': os.path.join(prefix, 'Actuat_LetL.wav'),
        'M': os.path.join(prefix, 'Actuat_LetM.wav'),
        'N': os.path.join(prefix, 'Actuat_LetN.wav'),
        'O': os.path.join(prefix, 'Actuat_LetO.wav'),
        'P': os.path.join(prefix, 'Actuat_LetP.wav'),
        'Q': os.path.join(prefix, 'Actuat_LetQ.wav'),
        'R': os.path.join(prefix, 'Actuat_LetR.wav'),
        'S': os.path.join(prefix, 'Actuat_LetS.wav'),
        'T': os.path.join(prefix, 'Actuat_LetT.wav'),
        'U': os.path.join(prefix, 'Actuat_LetU.wav'),
        'V': os.path.join(prefix, 'Actuat_LetV.wav'),
        'W': os.path.join(prefix, 'Actuat_LetW.wav'),
        'X': os.path.join(prefix, 'Actuat_LetX.wav'),
        'Y': os.path.join(prefix, 'Actuat_LetY.wav'),
        'Z': os.path.join(prefix, 'Actuat_LetZ.wav'),
        '1': os.path.join(prefix, 'Actuat_Num1.wav'),
        '2': os.path.join(prefix, 'Actuat_Num2.wav'),
        '3': os.path.join(prefix, 'Actuat_Num3.wav'),
        '4': os.path.join(prefix, 'Actuat_Num4.wav'),
        '5': os.path.join(prefix, 'Actuat_Num5.wav'),
        '6': os.path.join(prefix, 'Actuat_Num6.wav'),
        '7': os.path.join(prefix, 'Actuat_Num7.wav'),
        '8': os.path.join(prefix, 'Actuat_Num8.wav'),
        '9': os.path.join(prefix, 'Actuat_Num9.wav'),
        '0': os.path.join(prefix, 'Actuat_Num0.wav'),
        '10': os.path.join(prefix, 'Actuat_Num10.wav'),
        ' ': os.path.join(prefix, 'Actuat_Space.wav'), 
    }

# Function to load WAV files based on the AUDIO_FILES dictionary and apply channel modifications
def load_audio_files(audio_files: Dict[str, str]) -> Dict[str, np.ndarray]:
    signals = {}
    for key, file_path in audio_files.items():
        if os.path.exists(file_path):
            fs, data = wavfile.read(file_path)
            assert data.ndim == 2 and data.shape[1] == 20, "WAV file must have 20 channels"
            modified_signal = [(data[:, i]).astype('int16') for i in range(20)]
            for channel, (_, operation) in CHANNELS.items():
                if operation == '-':
                    modified_signal[channel] = -1*np.abs(modified_signal[channel])
                elif operation == '+':
                    modified_signal[channel] = np.abs(modified_signal[channel])
            signals[key] = modified_signal
        else:
            print(f"File {file_path} for key {key} does not exist.")
    return signals

X = 0

def find_device(device_list: sd.DeviceList, api_list: Tuple[Dict]) -> int:
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError

def stream_callback(data: np.ndarray, frames: int, _, __):
    global X, current_signal
    end_reached = False
    for c in range(data.shape[1]):
        r = len(current_signal[c]) - X
        if frames > r:
            data[0:r, c] = current_signal[c][X:X+r]
            data[r:, c].fill(0)
            end_reached = True
        else:
            data[:, c] = current_signal[c][X:X+frames]
    X += frames
    if end_reached:
        X = 0
        raise sd.CallbackStop

def play_signal(signal):
    global current_signal, X
    current_signal = signal
    X = 0
    if out_stream.active:
        out_stream.stop()
    out_stream.start()
    while out_stream.active:
        time.sleep(0.3)
    out_stream.stop()

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

# Get the mode from the user
mode = input("Enter mode (default, print_on_palm, reverse): ").strip().lower()
if mode not in MODES:
    print("Invalid mode. Using default mode.")
    mode = "default"

# Create the AUDIO_FILES dictionary based on the chosen mode
AUDIO_FILES = create_audio_files_dict(mode)


# Load the audio files and apply channel modifications
SIGNALS = load_audio_files(AUDIO_FILES)
out_stream = None 
print("Start streaming on device", device_id)
print("Enter letters or numbers to play the corresponding audio files sequentially, or '*' to stop (Ctrl+C to stop):")

try:
    out_stream = sd.OutputStream(
        samplerate=SPR, blocksize=0, device=device_id, channels=20,
        dtype='int16', latency='low', callback=stream_callback)
    while True:
        out_stream.stop()
        user_input = input().strip().upper()
        if user_input == '*':
            out_stream.stop()
            break
        for char in user_input:
            if char in SIGNALS:
                out_stream.stop()
                play_signal(SIGNALS[char])
                time.sleep(0.05)
                out_stream.stop()
            else:
                print(f"Ignored character '{char}' - no audio signal found")
except KeyboardInterrupt:
    pass
finally:
    if out_stream is not None:
        out_stream.stop()
    print("End of streaming")


