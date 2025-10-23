import pytest

from gpustack_runtime.detector.mthreads import MThreadsDetector


@pytest.mark.skipif(
    not MThreadsDetector.is_supported(),
    reason="MThreads GPU not detected",
)
def test_detect():
    det = MThreadsDetector()
    devs = det.detect()
    print(devs)
