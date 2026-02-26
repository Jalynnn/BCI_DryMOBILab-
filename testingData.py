import pyxdf
import mne
import matplotlib.pyplot as plt
import numpy as np

# 1. LOAD THE DATA
# Replace this with the path to your 20-second recording
file_path = './testData/sub-P001_ses-S001_task-Default_run-002_eeg.xdf'
streams, header = pyxdf.load_xdf(file_path)

# 2. EXTRACT THE EEG STREAM
# We look for the 'gMOBIlab' stream you created in the bridge script
try:
    eeg_stream = [s for s in streams if s['info']['name'][0] == 'gMOBIlab'][0]
    data = eeg_stream['time_series'].T  # Shape must be (channels, samples)
    sfreq = float(eeg_stream['info']['nominal_srate'][0])  # Should be 256
except IndexError:
    print("Error: Could not find 'gMOBIlab' stream in the XDF file.")
    exit()

# 3. CREATE MNE DATA OBJECT
# Using standard 8-channel labels
ch_names = ['Fz', 'Cz', 'P3', 'Pz', 'P4', 'P7', 'Oz', 'P8']
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
raw = mne.io.RawArray(data, info)

# 4. RESEARCH-GRADE CLEANUP (REVISED)
# 1. Notch filter both 60Hz and 120Hz (harmonics often hide in the noise)
print("Applying Notch Filters...")
raw.notch_filter([60, 120], picks='all', filter_length='auto', phase='zero')

# 2. Re-reference to the average (this is huge for dry electrodes)
# It subtracts noise that is common to all sensors (like the 60Hz hum)
print("Applying Common Average Reference...")
raw.set_eeg_reference('average', projection=False)

# 3. Single Bandpass Filter (3-30 Hz)
# We start at 3Hz to aggressively kill that massive DC drift you saw
print("Applying Bandpass Filter (3-30Hz)...")
raw.filter(l_freq=3.0, h_freq=30.0, picks='all', method='fir', phase='zero-double')

# 5. VISUAL VERIFICATION
# Increase scaling to 100uV initially so you don't just see 'black walls'
print("Opening Plot...")
raw.plot(
    duration=5, 
    n_channels=8, 
    scalings={'eeg': 100e-6}, # Start at 100uV, then press '-' in the plot to zoom in
    title="Optimized EEG Verification",
    show=True,
    block=True
)

# 6. FREQUENCY ANALYSIS
# This plot will show you if you have a peak in the 8-12Hz (Alpha) range
raw.compute_psd().plot()
plt.show()