import os
from typing import Tuple, Dict
import sounddevice as sd
import time
import numpy as np
from scipy.io import wavfile

# List of devices to connect to
DEVICES = ["HSD mk.I", "HSD mk.ii", "HSD mk.iii", "SKINETIC"]
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
APIS = ["Windows WDM-KS", "Windows WASAPI"]
SPR = 48000  # Hz
SIGNALS = [np.zeros(1, dtype='int16') for _ in range(20)]
X = 0

import os
import numpy as np
from scipy.io import wavfile
from typing import Dict

def load_audio_files(audio_files: Dict[str, str]) -> Dict[str, np.ndarray]:
    signals = {}
    
    for key, file_path in audio_files.items():
        if os.path.exists(file_path):
            fs, data = wavfile.read(file_path)
            
            # Ensure data is at least 1D
            if data.ndim == 1:  # If mono, reshape to (N, 1)
                data = data[:, np.newaxis]

            num_channels = data.shape[1]
            if num_channels == 1:  # If the WAV file is mono
                # Create a 20-channel array with zeros
                multi_channel_data = np.zeros((data.shape[0], 20), dtype=np.int16)
                multi_channel_data[:, 0] = data[:, 0]  # Assign mono audio to the first channel
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



def stream_callback(data: np.ndarray, frames: int, _, __):
    global X, current_signal
    end_reached = False
    r = len(current_signal) - X
    if frames > r:
        data[:r, :] = current_signal[X:X+r, :]  # Assign only the available part
        data[r:, :].fill(0)  # Fill remaining with zeros
        end_reached = True
    else:
        data[:, :] = current_signal[X:X+frames, :]

    X += frames
    if end_reached:
        X = 0
        raise sd.CallbackStop


def find_device(device_list: sd.DeviceList, api_list: Tuple[Dict]) -> int:
    for i, device in enumerate(device_list):
        if api_list[device['hostapi']]['name'] in APIS:
            for d in DEVICES:
                if d in device['name']:
                    return i
    raise OSError

def main():
    global SIGNALS
    available_devices = sd.query_devices()
    available_apis = sd.query_hostapis()

    try:
        device_id = find_device(available_devices, available_apis)
    except OSError:
        print("No compatible device found")
        return

    print("Start streaming on device", device_id)
    print("Enter commands in the format '<channel_key> <file_number>' or 'exit' to quit.")

    out_stream = sd.OutputStream(
        samplerate=SPR, blocksize=0, device=device_id, channels=20, dtype='int16', latency='low', callback=stream_callback
    )
    out_stream.start()

    try:
        while True:
            command = input("Command: ").strip()
            if command.lower() == "exit":
                break
            try:
                channel_key, file_number = command.split()
                file_name = f"Variable/Var_{file_number}.wav"
                channel = next((ch for ch, info in CHANNELS.items() if info[0] == channel_key), None)
                if channel is None:
                    print("Invalid channel key.")
                    continue
                if not os.path.isfile(file_name):
                    print(f"File '{file_name}' not found.")
                    continue
                load_audio_files(channel, file_name)
                print(f"Playing file '{file_name}' on channel {channel}...")
            except ValueError:
                print("Invalid command format. Use '<channel_key> <file_number>'.")
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user.")
    finally:
        out_stream.stop()
        print("End of streaming")

if __name__ == "__main__":
    main()
