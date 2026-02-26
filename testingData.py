import pyxdf
import mne
import matplotlib.pyplot as plt
import numpy as np

# 1. LOAD THE DATA
# Replace this with the path to your recording
file_path = './testData/sub-P001_ses-S001_task-Default_run-004_eeg.xdf'
streams, header = pyxdf.load_xdf(file_path)

# 2. EXTRACT THE EEG STREAM
try:
    eeg_stream = [s for s in streams if s['info']['name'][0] == 'gMOBIlab'][0]
    data = eeg_stream['time_series'].T  # Shape: (channels, samples)
    sfreq = float(eeg_stream['info']['nominal_srate'][0])  # Should be 256
except IndexError:
    print("Error: Could not find 'gMOBIlab' stream in the XDF file.")
    exit()

# 3. CREATE MNE DATA OBJECT (Revised with Scaling)
# Standard 8-channel labels for your setup
ch_names = ['Fz', 'Cz', 'P3', 'Pz', 'P4', 'P7', 'Oz', 'P8']
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')

# SCALING FIX: MNE expects data in Volts.
# 1. Your data is already centered (-32768 to 32767) from bridge.py.
# 2. Multiply by 0.5 to get microvolts (Standard g.MOBIlab+ resolution).
# 3. Multiply by 1e-6 to convert microvolts to Volts for MNE.
volt_data = data * 0.5 * 1e-6

raw = mne.io.RawArray(volt_data, info)

# 4. RESEARCH-GRADE CLEANUP
# Apply Notch filter for 60Hz and 120Hz harmonics
print("Applying Notch Filters...")
raw.notch_filter([60, 120], picks='all', filter_length='auto', phase='zero')

# Re-reference to the average to remove shared environmental noise
print("Applying Common Average Reference...")
raw.set_eeg_reference('average', projection=False)

# Bandpass Filter (3-30 Hz)
# Starting at 3Hz is aggressive but helps stabilize dry electrode drift
print("Applying Bandpass Filter (3-30Hz)...")
raw.filter(l_freq=3.0, h_freq=30.0, picks='all', method='fir', phase='zero-double')

# 5. VISUAL VERIFICATION
# Scaling is now set to 100uV; if the signal looks too small, press '-' in the plot window.
print("Opening Plot...")
raw.plot(
    duration=5, 
    n_channels=8, 
    scalings={'eeg': 100e-6}, 
    title="Scaled & Cleaned EEG Verification",
    show=True,
    block=True
)

# 6. FREQUENCY ANALYSIS
# Look for the Alpha peak (8-12Hz) in the Oz/Pz channels
print("Generating Power Spectral Density Plot...")
raw.compute_psd().plot()
plt.show()