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

# Predetermined paths for audio files
AUDIO_FILES = {
    'A': 'Actuat_LetA.wav',
    'B': 'Actuat_LetB.wav',
    'C': 'Actuat_LetC.wav',
    'D': 'Actuat_LetD.wav',
    'E': 'Actuat_LetE.wav',
    'F': 'Actuat_LetF.wav',
    'G': 'Actuat_LetG.wav',
    'H': 'Actuat_LetH.wav',
    'I': 'Actuat_LetI.wav',
    'J': 'Actuat_LetJ.wav',
    'K': 'Actuat_LetK.wav',
    'L': 'Actuat_LetL.wav',
    'M': 'Actuat_LetM.wav',
    'N': 'Actuat_LetN.wav',
    'O': 'Actuat_LetO.wav',
    'P': 'Actuat_LetP.wav',
    'Q': 'Actuat_LetQ.wav',
    'R': 'Actuat_LetR.wav',
    'S': 'Actuat_LetS.wav',
    'T': 'Actuat_LetT.wav',
    'U': 'Actuat_LetU.wav',
    'V': 'Actuat_LetV.wav',
    'W': 'Actuat_LetW.wav',
    'X': 'Actuat_LetX.wav',
    'Y': 'Actuat_LetY.wav',
    'Z': 'Actuat_LetZ.wav',
    '1': 'Actuat_Num1.wav',
    '2': 'Actuat_Num2.wav',
    '3': 'Actuat_Num3.wav',
    '4': 'Actuat_Num4.wav',
    '5': 'Actuat_Num5.wav',
    '6': 'Actuat_Num6.wav',
    '7': 'Actuat_Num7.wav',
    '8': 'Actuat_Num8.wav',
    '9': 'Actuat_Num9.wav',
    '0': 'Actuat_Num0.wav',
}
# Load the predetermined WAV files
SIGNALS = {}
for key, file_path in AUDIO_FILES.items():
    if os.path.exists(file_path):
        fs, data = wavfile.read(file_path)
        assert data.ndim == 2 and data.shape[1] == 20, "WAV file must have 20 channels"
        SIGNALS[key] = [(data[:, i]).astype('int16') for i in range(20)]
    else:
        print(f"File {file_path} for key {key} does not exist.")
X = 0


def find_device(device_list: sd.DeviceList, api_list: Tuple[Dict]) -> int:
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError


def stream_callback(data: np.ndarray, frames: int, _, __):
    global X, current_signal, playing
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
    out_stream.start()
    while out_stream.active:
        time.sleep(0.1)

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
print("Enter letters or numbers to play the corresponding audio files sequentially, or '*' to stop (Ctrl+C to stop):")

try:
    out_stream = sd.OutputStream(
        samplerate=SPR, blocksize=0, device=device_id, channels=20,
        dtype='int16', latency='low', callback=stream_callback)
    while True:
        user_input = input().strip().upper()
        if user_input == '*':
            break
        for char in user_input:
            if char in SIGNALS:
                play_signal(SIGNALS[char])
            else:
                print(f"No audio signal found for '{char}'")
except KeyboardInterrupt:
    pass
finally:
    if out_stream is not None:
        out_stream.stop()
    print("End of streaming")
