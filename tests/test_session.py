"""Session and style-preset round-trips.

Reproducibility is the whole point of the ``.birds`` file: a session
that comes back subtly different is worse than no session at all.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.detection_limits import scan_and_convert
from birds.plot_style import GroupStyle, PlotStyle


@pytest.fixture
def window(qapp):
    from birds.main_window import BirdsMainWindow
    return BirdsMainWindow()


@pytest.fixture
def loaded_window(window, majors_df):
    raw = majors_df.copy()
    raw["Nb"] = ["<0.5"] + ["3.2"] * (len(raw) - 1)
    conv, mask, report = scan_and_convert(raw, "half")
    window.data.df = conv
    window.data.bdl_masks = {"main": mask}
    window.data.bdl_limits = {"main": report.limits}
    window.data.bdl_policy = "half"
    window.style.group_columns = ["Group"]
    window.style.groups = [GroupStyle(name="A"), GroupStyle(name="B")]
    window.on_dataset_replaced()
    return window


class TestSessionRoundTrip:
    def test_data_survives(self, loaded_window, tmp_path, qapp):
        from birds.main_window import BirdsMainWindow
        path = tmp_path / "s.birds"
        loaded_window._session_path = path
        loaded_window.on_save_session()
        assert path.exists()

        reloaded = BirdsMainWindow()
        reloaded._load_session_path(path)
        assert len(reloaded.data.df) == len(loaded_window.data.df)
        assert list(reloaded.data.df.columns) == \
            list(loaded_window.data.df.columns)

    def test_detection_limits_survive(self, loaded_window, tmp_path, qapp):
        """Without the limits the policy can never be changed again."""
        from birds.main_window import BirdsMainWindow
        path = tmp_path / "s.birds"
        loaded_window._session_path = path
        loaded_window.on_save_session()

        reloaded = BirdsMainWindow()
        reloaded._load_session_path(path)
        assert "main" in reloaded.data.bdl_masks
        assert "main" in reloaded.data.bdl_limits
        assert reloaded.data.bdl_limits["main"]["Nb"].notna().any()

    def test_policy_still_changeable_after_reload(self, loaded_window,
                                                  tmp_path, qapp):
        from birds.dialogs.detection_limits_dialog import (
            DetectionLimitsDialog,
        )
        from birds.main_window import BirdsMainWindow
        path = tmp_path / "s.birds"
        loaded_window._session_path = path
        loaded_window.on_save_session()

        reloaded = BirdsMainWindow()
        reloaded._load_session_path(path)
        dialog = DetectionLimitsDialog(reloaded.data)
        index = dialog.policy_combo.findData("nan")
        dialog.policy_combo.setCurrentIndex(index)
        dialog._apply()
        assert dialog.n_changed >= 1

    def test_group_styling_survives(self, loaded_window, tmp_path, qapp):
        from birds.main_window import BirdsMainWindow
        path = tmp_path / "s.birds"
        loaded_window._session_path = path
        loaded_window.on_save_session()

        reloaded = BirdsMainWindow()
        reloaded._load_session_path(path)
        assert reloaded.style.group_columns == ["Group"]
        assert [g.name for g in reloaded.style.groups] == ["A", "B"]


class TestStylePresets:
    def test_round_trip(self, tmp_path):
        from birds.style_presets import load_preset, save_preset
        style = PlotStyle()
        style.group_columns = ["Rock_type"]
        style.groups = [GroupStyle(name="basalt"), GroupStyle(name="dacite")]
        style.point_size = 42.0
        path = save_preset(tmp_path / "mine.birdstyle", style, "mine")

        restored, name = load_preset(path)
        assert name == "mine"
        assert restored.group_columns == ["Rock_type"]
        assert restored.point_size == pytest.approx(42.0)
        assert [g.name for g in restored.groups] == ["basalt", "dacite"]

    def test_missing_file_raises_preset_error(self, tmp_path):
        from birds.style_presets import StylePresetError, load_preset
        with pytest.raises(StylePresetError):
            load_preset(tmp_path / "absent.birdstyle")

    def test_corrupt_file_raises_preset_error(self, tmp_path):
        from birds.style_presets import StylePresetError, load_preset
        bad = tmp_path / "bad.birdstyle"
        bad.write_text("{not json", encoding="utf-8")
        with pytest.raises(StylePresetError):
            load_preset(bad)

    def test_foreign_json_is_rejected(self, tmp_path):
        """A .birdstyle that is not ours must not be applied silently."""
        from birds.style_presets import StylePresetError, load_preset
        alien = tmp_path / "alien.birdstyle"
        alien.write_text('{"format": "something-else"}', encoding="utf-8")
        with pytest.raises(StylePresetError):
            load_preset(alien)

    def test_apply_keeps_grouping_columns_when_asked(self):
        from birds.style_presets import apply_preset
        target = PlotStyle()
        target.group_columns = ["Group"]
        target.groups = [GroupStyle(name="mine-1"), GroupStyle(name="mine-2")]
        preset = PlotStyle()
        preset.group_columns = ["Other"]
        preset.groups = [GroupStyle(name="theirs-1"),
                         GroupStyle(name="theirs-2")]
        apply_preset(target, preset, keep_group_columns=True)
        assert target.group_columns == ["Group"]
        assert [g.name for g in target.groups][:2] == ["mine-1", "mine-2"]
