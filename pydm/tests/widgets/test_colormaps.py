# Unit Tests for the Frame Widget


import pytest

import numpy as np

from ...widgets.colormaps import PyDMColorMap, _magma_data, _inferno_data, _plasma_data, _viridis_data, _jet_data, \
    _monochrome_data, _hot_data, cmaps, magma, inferno, plasma, viridis, jet, monochrome, hot, cmap_names


# --------------------
# POSITIVE TEST CASES
# --------------------

def test_construct(qtbot):
    """
    Test the construction of the ColorMap widget, and the creations of auxiliary helper objects.

    Expecations:
    The default values are assigned to the attributes correctly.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    pydm_colormap = PyDMColorMap()
    qtbot.addWidget(pydm_colormap)

    for (name, data) in ((PyDMColorMap.Magma, np.array(_magma_data)),
                         (PyDMColorMap.Inferno, np.array(_inferno_data)),
                         (PyDMColorMap.Plasma, np.array(_plasma_data)),
                         (PyDMColorMap.Viridis, np.array(_viridis_data)),
                         (PyDMColorMap.Jet, np.array(_jet_data)),
                         (PyDMColorMap.Monochrome, np.array(_monochrome_data)),
                         (PyDMColorMap.Hot, np.array(_hot_data))):
        assert np.array_equal(cmaps[name], data)

    assert np.array_equal(magma, cmaps[PyDMColorMap.Magma])
    assert np.array_equal(inferno, cmaps[PyDMColorMap.Inferno])
    assert np.array_equal(plasma, cmaps[PyDMColorMap.Plasma])
    assert np.array_equal(viridis, cmaps[PyDMColorMap.Viridis])
    assert np.array_equal(jet, cmaps[PyDMColorMap.Jet])
    assert np.array_equal(monochrome, cmaps[PyDMColorMap.Monochrome])
    assert np.array_equal(hot, cmaps[PyDMColorMap.Hot])

    assert cmap_names[PyDMColorMap.Magma] == "Magma"
    assert cmap_names[PyDMColorMap.Inferno] == "Inferno"
    assert cmap_names[PyDMColorMap.Plasma] == "Plasma"
    assert cmap_names[PyDMColorMap.Viridis] == "Viridis"
    assert cmap_names[PyDMColorMap.Jet] == "Jet"
    assert cmap_names[PyDMColorMap.Monochrome] == "Monochrome"
    assert cmap_names[PyDMColorMap.Hot] == "Hot"
