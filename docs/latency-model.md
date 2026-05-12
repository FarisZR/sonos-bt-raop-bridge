# Latency Model

BlueZ `org.bluez.MediaTransport1.Delay` uses `0.1 ms` units.

The intended reported delay is downstream presentation delay from the Debian bridge to audible output at the Sonos speakers. It should not blindly double-count unrelated source-side latency.

Known risks to validate:

- Android may clamp or ignore unusually large remote delay reports.
- PipeWire ownership of the transport may restrict who can write `Delay`.
