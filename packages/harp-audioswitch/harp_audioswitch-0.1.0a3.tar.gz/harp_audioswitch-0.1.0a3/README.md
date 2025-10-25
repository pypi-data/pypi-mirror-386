# harp.audioswitch

[![PyPI](https://img.shields.io/pypi/v/harp.audioswitch)](https://pypi.org/project/harp.audioswitch/)

This is a generated Harp device Python interface that interacts with the Harp protocol.

- **Github repository**: <https://github.com/fchampalimaud/harp.devices/>
- **Bug Tracker**: <https://github.com/fchampalimaud/harp.devices/issues>
- **Documentation**: <https://fchampalimaud.github.io/pyharp/harp.audioswitch/>

# Installation
You can install the package using `uv` or `pip`:

```bash
uv add harp.audioswitch
```
or

```bash
pip install harp.audioswitch
```

# Usage example

```python
from harp.protocol import OperationMode
from harp.devices.audioswitch import AudioSwitch

# Example usage of the AudioSwitch device
with AudioSwitch("/dev/ttyUSB0") as device: # For Windows, use "COM8" or similar
    device.info()

    # Set the device to active mode
    device.set_mode(OperationMode.ACTIVE)

    # Get the events
    try:
        while True:
            for event in device.get_events():
                # Do what you need with the event
                print(event.payload)
    except KeyboardInterrupt:
        # Capture Ctrl+C to exit gracefully
        print("Exiting...")
    finally:
        # Do what you need to do to clean up. Disconnect is automatically called with the "with" statement.
        pass
```