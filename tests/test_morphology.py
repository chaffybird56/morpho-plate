import numpy as np

from morphoplate.morphology.pipeline import morphological_pipeline


def test_morphological_pipeline_returns_five_steps():
    roi = np.zeros((40, 120, 3), dtype=np.uint8)
    roi[:, 40:80] = (200, 200, 200)

    steps = morphological_pipeline(roi)
    titles = [s.title for s in steps]

    assert titles == ["Gray", "Blur", "Otsu", "Dilate", "Invert"]
    assert all(step.image.size > 0 for step in steps)


def test_empty_roi_returns_empty_list():
    roi = np.zeros((0, 0, 3), dtype=np.uint8)
    assert morphological_pipeline(roi) == []
