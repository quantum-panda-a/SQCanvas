import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import qcanvas
from qcanvas.components.transmon import TransmonPocket
from qcanvas.designs.design_planar import PlanarDesign
from qcanvas.viewer import display, view


def test_view_top_level_and_module():
    design = PlanarDesign()
    TransmonPocket(design, "Q1")

    fig1 = view(design)
    assert isinstance(fig1, Figure)
    plt.close(fig1)

    fig2 = qcanvas.view(design)
    assert isinstance(fig2, Figure)
    plt.close(fig2)


def test_display():
    design = PlanarDesign()
    TransmonPocket(design, "Q1")

    fig = display(design)
    assert isinstance(fig, Figure)
    plt.close(fig)
