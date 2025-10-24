import os
from typing import Dict
import streamlit.components.v1 as components
from .widget import GraphWidget

# re-exports
from .label_style import *
from .layout.layout import *
from .node_style import *
from .edge_style import *

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component("Streamlit_Graph_Widget", url='http://localhost:5173')
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component("Streamlit_Graph_Widget", path=build_dir)

class StreamlitGraphWidget(GraphWidget):
    def __init__(self, nodes=None, edges=None):
        super().__init__()
        if nodes is not None and edges is not None:
            self.nodes = nodes
            self.edges = edges

    @classmethod
    def from_graph(cls, graph):
        instance = cls()
        instance.import_graph(graph)
        return instance

    def show(self,
             directed=True,
             graph_layout=Layout.ORGANIC,
             sync_selection=False,
             sidebar={'enabled': False},
             neighborhood={'max_distance': 1, 'selected_nodes': []},
             overview=True,
             key=None):
        """Create a new instance of "StreamlitGraphWidget".

        Parameters
        ----------
        directed: bool
            A boolean whether the edges show a direction indicator. By default, `True`.
        graph_layout: Layout
            An optional argument specifying the starting layout
        sync_selection: bool
            Whether the component returns the lists of interactively selected nodes and edges. Enabling this may require caching the component to avoid excessive rerendering.
        sidebar: Dict
            The sidebar starting configuration
        neighborhood: Dict
            The neighborhood tab starting configuration
        overview: bool
            Whether the overview is expanded
        key: str or None
            An optional key that uniquely identifies this component. If this is
            None, and the component's arguments are changed, the component will
            be re-mounted in the Streamlit frontend and lose its current state.

        Returns
        -------
        [selected_nodes, selected_edges]
             Returns a reference to the interactively selected node- or edge-dicts iff `sync_selection` is set to `True`.

        """
        self._directed = directed
        self._mapper.apply_mappings()
        self.set_graph_layout(graph_layout)
        graph_layout = self.get_graph_layout()

        widget_overview = {'enabled': overview, 'overview_set': True}

        component_value = _component_func(nodes=self.nodes, edges=self.edges, directed=directed, graph_layout=graph_layout,
                                          _sidebar=sidebar, _neighborhood=neighborhood, _overview=widget_overview,
                                          sync_selection=sync_selection, key=key)

        selected_nodes = component_value[0] if component_value is not None else []
        selected_edges = component_value[1] if component_value is not None else []
        return selected_nodes, selected_edges

