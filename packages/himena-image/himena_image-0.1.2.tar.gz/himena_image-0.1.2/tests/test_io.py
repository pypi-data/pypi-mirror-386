from pathlib import Path
from himena_image.io import read_roi, write_roi

_TEST_PATH = Path(__file__).parent

def test_roi_io(tmpdir):
    tmpdir = Path(tmpdir)
    rois = read_roi(_TEST_PATH / "test-rois.zip")
    write_roi(rois, tmpdir / "test-rois.zip")
