# Unit Tests for the Color Map


import numpy as np

from pydm.widgets.colormaps import (
    PyDMColorMap,
    cmaps,
    magma,
    inferno,
    plasma,
    viridis,
    jet,
    monochrome,
    hot,
    cmap_names,
)


# --------------------
# POSITIVE TEST CASES
# --------------------


def test_construct():
    """
    Test the construction of the ColorMaps, and the creations of auxiliary helper objects.

    Expectations:
    The default values are assigned to the attributes correctly.
    """

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
