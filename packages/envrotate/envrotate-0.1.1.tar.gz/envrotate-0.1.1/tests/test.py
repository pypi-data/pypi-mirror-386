import os
import time
import pytest
from envrotate import EnvRotate

def test_basic_rotation():
    os.environ["TEST_API_1"] = "key1"
    os.environ["TEST_API_2"] = "key2"
    rotator = EnvRotate(prefix="TEST_API_", min_interval=1)

    # Round-robin
    assert rotator.get(random=False) == "key1"
    assert rotator.get(random=False) == "key2"

    # Random (should return either key after cooldown)
    time.sleep(1.1)
    key = rotator.get(random=True)
    assert key in ["key1", "key2"]


def test_wait_behavior():
    os.environ["WAIT_TEST_1"] = "keyA"
    rotator = EnvRotate(prefix="WAIT_TEST_", min_interval=2)

    rotator.get()  # Use keyA
    assert rotator.get(wait=False) is None  # Not available yet

    start = time.time()
    key = rotator.get(wait=True)  # Should wait ~2s
    assert key == "keyA"
    assert time.time() - start >= 1.9  # Allow minor timing variance