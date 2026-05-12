# Architecture

The bridge has three paths:

- Audio path: Android A2DP -> BlueZ/PipeWire -> RAOP sink -> Sonos Kitchen pair.
- Control path: CLI -> Home Assistant REST/WebSocket, BlueZ D-Bus, PipeWire tools, ADB.
- Measurement path: generated chirps and Android microphone capture for calibration.

The final system should keep Home Assistant as the Sonos control plane and BlueZ/PipeWire as the transport plane.
