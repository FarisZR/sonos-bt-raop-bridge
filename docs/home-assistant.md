# Home Assistant

Home Assistant is used as the Sonos control plane.

The implementation will:

- probe API health
- list `media_player` entities
- select only the Kitchen/Küche/Kueche target
- stop playback
- unjoin if needed
- set safe volume
- trigger direct test playback
