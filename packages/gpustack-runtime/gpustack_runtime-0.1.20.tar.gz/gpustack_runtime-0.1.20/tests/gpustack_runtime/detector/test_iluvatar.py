import pytest

from gpustack_runtime.detector.iluvatar import IluvatarDetector


@pytest.mark.skipif(
    not IluvatarDetector.is_supported(),
    reason="Iluvatar GPU not detected",
)
def test_detect():
    det = IluvatarDetector()
    devs = det.detect()
    print(devs)
