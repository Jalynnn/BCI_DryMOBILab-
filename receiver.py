from pylsl import StreamInlet, resolve_byprop

print("Searching for gMOBIlab stream on the network...")

# Search for a stream where the 'name' property is 'gMOBIlab'
# The 1 is the minimum number of streams to find, and 5 is the timeout in seconds
streams = resolve_byprop('name', 'gMOBIlab', minimum=1, timeout=5.0)

if not streams:
    print("Error: Could not find gMOBIlab stream. Is bridge.py running?")
else:
    inlet = StreamInlet(streams[0])
    print(f"Stream found! Host: {streams[0].hostname()}")
    print("Receiving data samples...")

    while True:
        # Pull a sample and its timestamp
        sample, timestamp = inlet.pull_sample()
        if sample:
            print(f"Sample: {sample} | TS: {timestamp:.3f}")