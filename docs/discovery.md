# Discovery Summary

## 2026-05-12 baseline

- Debian 13 host confirmed.
- BlueZ 5.82 present.
- TP-Link UB500 adapter brought up successfully as `hci0`.
- Adapter supports the roles needed to proceed with A2DP sink work.
- PipeWire and WirePlumber are still missing and are the next installation step.
- Avahi is active, but no `_raop._tcp` services were visible at capture time.
- Android phone is reachable over ADB.
- Home Assistant credentials exist, but the configured server did not answer from this host during discovery.

The committed sanitized report for this pass lives in `artifacts/discovery-20260512T172219Z/`.
