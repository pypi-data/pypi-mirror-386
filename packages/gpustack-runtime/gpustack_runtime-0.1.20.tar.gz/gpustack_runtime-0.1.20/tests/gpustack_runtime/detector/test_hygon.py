import pytest

from gpustack_runtime.detector.hygon import HygonDetector


@pytest.mark.skipif(
    not HygonDetector.is_supported(),
    reason="Hygon GPU not detected",
)
def test_detect():
    det = HygonDetector()
    devs = det.detect()
    print(devs)
