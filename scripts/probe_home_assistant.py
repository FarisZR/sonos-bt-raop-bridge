#!/usr/bin/env python3

from sonos_bt_raop_bridge.config import load_config


def main() -> int:
    config = load_config()
    print(config.ha_url or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
