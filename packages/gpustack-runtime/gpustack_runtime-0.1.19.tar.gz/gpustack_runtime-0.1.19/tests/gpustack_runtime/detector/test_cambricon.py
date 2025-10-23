import pytest

from gpustack_runtime.detector.cambricon import CambriconDetector


@pytest.mark.skipif(
    not CambriconDetector.is_supported(),
    reason="Cambricon GPU not detected",
)
def test_detect():
    det = CambriconDetector()
    devs = det.detect()
    print(devs)
