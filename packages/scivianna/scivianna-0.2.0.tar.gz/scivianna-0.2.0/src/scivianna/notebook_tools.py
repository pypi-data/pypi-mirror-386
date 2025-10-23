
from typing import Any, Callable
from pathlib import Path
import panel as pn

from scivianna.panel.plot_panel import VisualizationPanel
from scivianna.slave import ComputeSlave
from scivianna.constants import GEOMETRY

"""
    Generic functions for every codes
"""


def _get_panel(panel: VisualizationPanel, title="") -> pn.viewable.Viewable:
    """Generic function to return a displayable panel

    Parameters
    ----------
    panel : VisualizationPanel
        Visualisation panel to display
    title : str, optional
        Panel main frame title, by default ""

    Returns
    -------
    pn.viewable.Viewable
        Displayable panel
    """

    return pn.Column(
        panel.bounds_row,
        panel.main_frame,
        width_policy="max",
        height_policy="max",
    )


def _make_template(panel: VisualizationPanel, title: str = ""):

    custom_css = """
    #main {
        padding: 0 !important;
    }
    #sidebar {
        padding: 0 !important;
    }
    """

    pn.extension("tabulator", 'codeeditor', raw_css=[custom_css])
    return pn.template.BootstrapTemplate(
        main=[
            pn.Column(
                panel.bounds_row,
                panel.main_frame,
                sizing_mode="stretch_both",
                margin=0,
            )
        ],
        sidebar=[panel.side_bar],
        title=title,
    )


def _show_panel(panel: VisualizationPanel, title: str = ""):
    """Display the holoviz panel associated to this compute slave.

    Parameters
    ----------
    panel : VisualizationPanel
        Visualisation panel to display
    """
    _make_template(panel, title=title).show()


def _serve_panel(
    panel:VisualizationPanel = None, get_panel_function: Callable = None, slave_input: Any = None, title: str = ""
):

    """Opens a holoviz panel server associated to this compute slave. The computer IP adress is chosen, and a free port is automatically selected.
    Two use are possible, either the panel is provided, or a function calling it associated to its inputs. In the second case, all multi-user sessions are separated.

    Parameters
    ----------
    panel : VisualizationPanel, optional
        Panel to serve, by default None
    get_panel_function : Callable
        Function returning the visualisation panel to display
    slave_input : Any
        Value provided to the panel, required if get_panel_function is used
    title : str
        Panel title
    """
    import socket

    ip_adress = socket.gethostbyname(socket.gethostname())

    """
        Catching a free port to provide to pn.serve
    """
    sock = socket.socket()
    sock.bind((ip_adress, 0))
    port = sock.getsockname()[1]
    sock.close()


    if panel is not None:
        get_template = _make_template(panel, title=title)
    else:
        assert get_panel_function is not None, "If panel is not provided, get_panel_function must be."
        def get_template():
            return _make_template(get_panel_function(slave_input), title=title)

    pn.serve(
        get_template,
        address=ip_adress,
        websocket_origin=f"{ip_adress}:{port}",
        port=port,
        threaded=True,
    )


"""
    MED functions

"""


def get_med_panel(geo: str, title="") -> VisualizationPanel:
    """Get the visualisation panel for a MEDCoupling .med file path

    Parameters
    ----------
    geo : str
        .med file path
    title : str, optional
        Panel title, by default ""

    Returns
    -------
    VisualizationPanel
        Geometry visualisation panel

    Raises
    ------
    TypeError
        Argument type not implemented
    """
    from scivianna.interface.med_interface import MEDInterface

    slave = ComputeSlave(MEDInterface)
    if geo is None:
        slave.read_file(Path(__file__).parent / "default_jdd" / "power.med", GEOMETRY)
    elif isinstance(geo, str):
        slave.read_file(geo, GEOMETRY)
    else:
        raise TypeError(f"Provided type {type(geo)} not implemented")

    return VisualizationPanel(slave, name=title)


def show_med_geometry(geo, title: str = "MED Field visualizer"):
    """Opens a server on localhost to open in a browser

    Parameters
    ----------
    geo : str
        Geometry to display
    """
    _show_panel(get_med_panel(geo), title=title)


def serve_med_geometry(geo, title: str = "MED Field visualizer"):
    """Opens a server on the machine IP adress to open in a browser on any machine of the network

    Parameters
    ----------
    geo : str
        Geometry to display
    """
    _serve_panel(get_panel_function=get_med_panel, slave_input=geo, title=title)


def get_med_visualizer(geo, title="") -> pn.viewable.Viewable:
    """Returns a panel to displays it in a jupyter notebook

    Parameters
    ----------
    geo : str
        Geometry to display
    """
    return _get_panel(get_med_panel(geo, title=title))

