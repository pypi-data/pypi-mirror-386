import os
from time import time, sleep
from random import choice
from collections import OrderedDict
from threading import RLock
from typing import Optional

class EnvRotate:
    def __init__(self, prefix: str, min_interval: int):
        """
        Rotate environment variables (e.g., API keys) with cooldown intervals.

        Args:
            prefix: Environment variable prefix (e.g., "API_X_")
            min_interval: Minimum seconds before a key can be reused
        """
        self.prefix = prefix
        self.min_interval = min_interval
        self._lock = RLock()

        # Load keys from environment
        self._keys = [
            v for k, v in os.environ.items()
            if k.startswith(self.prefix)
        ]
        if not self._keys:
            raise ValueError(f"No env vars found with prefix '{prefix}'")

        # OrderedDict: {key: next_available_timestamp}
        # We'll keep it sorted by timestamp (ascending)
        self._available = OrderedDict((key, time()) for key in self._keys)

    def get(self, random: bool = False, wait: bool = True) -> Optional[str]:
        """
        Get an available key.

        Args:
            random: If True, pick randomly from currently available keys.
                    If False, use the key that became available earliest.
            wait: If True and no key is ready, sleep until the next key is available.

        Returns:
            str: An API key, or None if wait=False and no key is ready.
        """
        now = time()

        with self._lock:
            ready_keys = []
            for key, next_time in self._available.items():
                if next_time <= now:
                    ready_keys.append(key)
                else:
                    break  # EARLY EXIT: rest are unavailable (sorted order guarantee)

            if not ready_keys:
                if not wait:
                    return None
                # Sleep until the first key becomes available
                sleep(next_time - now)
                return self.get(random=random, wait=True)  # retry after sleep

            if random:
                key = choice(ready_keys)
            else:
                # Pick the key that became available earliest (first in ready list)
                key = ready_keys[0]

            # Update its next available time
            self._available[key] = now + self.min_interval

            # Re-sort the OrderedDict by next_available time (ascending)
            self._available = OrderedDict(
                sorted(self._available.items(), key=lambda x: x[1])
            )

            return key