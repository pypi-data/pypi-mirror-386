"""
Created on Wed Apr  6 09:47:07 2022.

@author: ooconnor
"""

from pathlib import Path

import pytest

TEST_FOLDER = Path(__file__).parent


def test_rois_script():
    script = TEST_FOLDER.parent / "scripts/segmentation_rois.py"

    inputs_folder = TEST_FOLDER / "data/movie_mothermachine_tif"
    parameters = {
        "config": "Config.default('mothermachine')",
        "inputs_folder": f'Path("{inputs_folder}")',
    }
    _run_script(script, parameters=parameters)


@pytest.mark.parametrize(
    "presets,inputs_folder",
    [
        ("2D", TEST_FOLDER / "data/movie_2D_tif"),
        (
            "mothermachine",
            TEST_FOLDER / "data/movie_mothermachine_tif/cropped_rois",
        ),
    ],
)
def test_segmentation_script(presets, inputs_folder):
    parameters = {
        "config": f'Config.default("{presets}")',
        "inputs_folder": f'Path("{inputs_folder}")',
    }
    _run_script(TEST_FOLDER.parent / "scripts/segmentation.py", parameters=parameters)


@pytest.mark.parametrize(
    "presets,inputs_folder",
    [
        ("2D", TEST_FOLDER / "data/movie_2D_tif"),
        (
            "mothermachine",
            TEST_FOLDER / "data/movie_mothermachine_tif/cropped_rois",
        ),
    ],
)
def test_tracking_script(presets, inputs_folder):
    parameters = {
        "config": f'Config.default("{presets}")',
        "inputs_folder": f'Path("{inputs_folder}")',
    }
    _run_script(TEST_FOLDER.parent / "scripts/tracking.py", parameters=parameters)


def _run_script(scriptfile, parameters):
    """Read script & strip parameters code, set parameters, execute script."""
    # Read script, and replace parameters
    script_lines = []
    for line in Path(scriptfile).read_text(encoding="utf8").splitlines():
        new_line = line
        for k, v in parameters.items():
            if line.startswith(f"{k} = "):
                new_line = f"{k} = {v}"
        script_lines.append(new_line)

    # Run script
    exec("\n".join(script_lines))  # noqa: S102
