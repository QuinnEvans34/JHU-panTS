import numpy as np
import pytest

from scripts.diagnostics.check_case78_coverage import sheet

pytestmark = pytest.mark.unit


def test_contact_sheet_endpoints_and_orientation():
    data=np.arange(24,dtype=np.float32).reshape(2,3,4)
    image,planes=sheet(data,(0,255))
    assert len(planes)==20
    assert planes[0]['index']==0 and planes[9]['index']==3
    assert planes[10]['index']==0 and planes[14]['index']==2
    assert planes[15]['index']==0 and planes[19]['index']==1
    # First axial tile: x reversed (R on left), y reversed (A at top).
    # Two by three pixel tile centered in a 300x280 viewport at y=95.
    assert image.getpixel((149,233))==(20,20,20)
    assert image.getpixel((150,235))==(0,0,0)


def test_window_clips_and_preserves_input():
    data=np.full((2,3,4),500,dtype=np.float32)
    before=data.copy()
    image,_=sheet(data,(-160,240))
    assert image.getpixel((149,233))==(255,255,255)
    assert np.array_equal(data,before)
