from pathlib import Path

from morphoplate.config import Settings


def test_settings_defaults():
    settings = Settings(video_path=Path("data/test.mp4"))
    assert settings.detector_model.endswith("license-plate-end2end")
    assert settings.show_window is True
    assert settings.thumb_width == 80
