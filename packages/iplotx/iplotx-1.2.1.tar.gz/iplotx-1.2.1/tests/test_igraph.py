import unittest
import numpy as np
import importlib
import matplotlib as mpl

mpl.use("agg")
import matplotlib.pyplot as plt
import iplotx as ipx

if importlib.util.find_spec("igraph") is None:
    raise unittest.SkipTest("igraph not found, skipping tests")
else:
    import igraph as ig

from utils import image_comparison


class GraphTestRunner(unittest.TestCase):
    @property
    def layout_small_ring(self):
        coords = [
            [1.015318095035966, 0.03435580194714975],
            [0.29010409851547664, 1.0184451153265959],
            [-0.8699239050738742, 0.6328259400443561],
            [-0.8616466426732888, -0.5895891303732176],
            [0.30349699041342515, -0.9594640169691343],
        ]
        return coords

    @image_comparison(baseline_images=["graph_basic"], remove_text=True)
    def test_basic(self):
        g = ig.Graph.Ring(5)
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(g, ax=ax, layout=self.layout_small_ring)

    @image_comparison(baseline_images=["graph_directed"], remove_text=True)
    def test_directed(self):
        g = ig.Graph.Ring(5, directed=True)
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(g, ax=ax, layout=self.layout_small_ring)

    @image_comparison(baseline_images=["graph_vertexsize"], remove_text=True)
    def test_vertexsize(self):
        g = ig.Graph.Ring(5)
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(
            g,
            ax=ax,
            layout=self.layout_small_ring,
            vertex_size=np.linspace(10, 30, 5),
            margins=0.15,
        )

    @image_comparison(baseline_images=["graph_labels"], remove_text=True)
    def test_labels(self):
        g = ig.Graph.Ring(5)
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(
            network=g,
            ax=ax,
            layout=self.layout_small_ring,
            vertex_labels=["1", "2", "3", "4", "5"],
            style={
                "vertex": {
                    "size": 20,
                    "label": {
                        "color": "white",
                        "size": 10,
                    },
                }
            },
        )

    @image_comparison(baseline_images=["igraph_layout_object"], remove_text=True)
    def test_layout_attribute(self):
        g = ig.Graph.Ring(5)
        layout = g.layout("circle")
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(g, layout=layout, ax=ax)

    @image_comparison(baseline_images=["graph_layout_attribute"], remove_text=True)
    def test_layout_attribute_alt(self):
        g = ig.Graph.Ring(5)
        g["layout"] = ig.Layout([(x, x) for x in range(g.vcount())])
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(g, layout="layout", ax=ax)

    @image_comparison(baseline_images=["graph_directed_curved_loops"], remove_text=True)
    def test_directed_curved_loops(self):
        g = ig.Graph.Ring(5, directed=True)
        g.add_edge(0, 0)
        g.add_edge(0, 0)
        g.add_edge(2, 2)
        fig, ax = plt.subplots(figsize=(4, 4))
        # ax.set_xlim(-1.2, 1.2)
        # ax.set_ylim(-1.2, 1.2)
        ipx.graph(
            g,
            ax=ax,
            layout=self.layout_small_ring,
            style={
                "edge": {
                    "curved": True,
                    "tension": 1.7,
                    "looptension": 5,
                }
            },
            margins=0.05,
        )

    @image_comparison(baseline_images=["graph_squares_directed"], remove_text=True)
    def test_mark_groups_squares(self):
        g = ig.Graph.Ring(5, directed=True)
        fig, ax = plt.subplots(figsize=(3, 3))
        ipx.graph(
            g,
            ax=ax,
            layout=self.layout_small_ring,
            style={
                "vertex": {"marker": "s"},
            },
        )

    @image_comparison(baseline_images=["graph_edit_children"], remove_text=True)
    def test_edit_children(self):
        g = ig.Graph.Ring(5)
        fig, ax = plt.subplots(figsize=(4, 4))
        ipx.graph(
            g,
            ax=ax,
            style={"vertex": {"marker": "o"}},
            layout=self.layout_small_ring,
        )
        graph_artist = ax.get_children()[0]

        dots = graph_artist.get_vertices()
        dots.set_facecolors(["blue"] + list(dots.get_facecolors()[1:]))
        new_sizes = dots.get_sizes()
        new_sizes[1] = 30
        dots.set_sizes(new_sizes)

        lines = graph_artist.get_edges()
        lines.set_edgecolor("green")

    @image_comparison(baseline_images=["graph_with_curved_edges"])
    def test_graph_with_curved_edges(self):
        g = ig.Graph.Ring(24, directed=True, mutual=True)
        fig, ax = plt.subplots()
        lo = g.layout("circle")
        lo.scale(3)
        ipx.graph(
            g,
            ax=ax,
            layout=lo,
            style={
                "vertex": {
                    "size": 15,
                },
                "edge": {
                    "paralleloffset": 8,
                    "curved": True,
                    "tension": 0.5,
                    "arrow": {
                        "height": 5,
                        "width": 5,
                    },
                },
            },
        )
        ax.set_aspect(1.0)

    @image_comparison(baseline_images=["multigraph_with_curved_edges_undirected"])
    def test_graph_with_curved_edges_undirected(self):
        g = ig.Graph.Ring(24, directed=False)
        g.add_edges([(0, 1), (1, 2)])
        fig, ax = plt.subplots()
        lo = g.layout("circle")
        lo.scale(3)
        ipx.graph(
            g,
            ax=ax,
            layout=lo,
            style={
                "vertex": {
                    "size": 15,
                },
                "edge": {
                    "paralleloffset": 8,
                    "curved": True,
                    "tension": 0.5,
                    "arrow": {
                        "height": 5,
                        "width": 5,
                    },
                },
            },
        )
        ax.set_aspect(1.0)

    @image_comparison(baseline_images=["graph_null"])
    def test_null_graph(self):
        g = ig.Graph()
        fig, ax = plt.subplots()
        ipx.graph(g, ax=ax)
        ax.set_aspect(1.0)


class ClusteringTestRunner(unittest.TestCase):
    @property
    def layout_small_ring(self):
        coords = [
            [1.015318095035966, 0.03435580194714975],
            [0.29010409851547664, 1.0184451153265959],
            [-0.8699239050738742, 0.6328259400443561],
            [-0.8616466426732888, -0.5895891303732176],
            [0.30349699041342515, -0.9594640169691343],
        ]
        return coords

    @property
    def layout_large_ring(self):
        coords = [
            (2.5, 0.0),
            (2.4802867532861947, 0.31333308391076065),
            (2.4214579028215777, 0.621724717912137),
            (2.324441214720628, 0.9203113817116949),
            (2.190766700109659, 1.2043841852542883),
            (2.0225424859373686, 1.469463130731183),
            (1.822421568553529, 1.7113677648217218),
            (1.5935599743717241, 1.926283106939473),
            (1.3395669874474914, 2.110819813755038),
            (1.0644482289126818, 2.262067631165049),
            (0.7725424859373686, 2.3776412907378837),
            (0.4684532864643113, 2.4557181268217216),
            (0.15697629882328326, 2.495066821070679),
            (-0.1569762988232835, 2.495066821070679),
            (-0.46845328646431206, 2.4557181268217216),
            (-0.7725424859373689, 2.3776412907378837),
            (-1.0644482289126818, 2.2620676311650487),
            (-1.3395669874474923, 2.1108198137550374),
            (-1.5935599743717244, 1.926283106939473),
            (-1.8224215685535292, 1.7113677648217211),
            (-2.022542485937368, 1.4694631307311832),
            (-2.190766700109659, 1.204384185254288),
            (-2.3244412147206286, 0.9203113817116944),
            (-2.4214579028215777, 0.621724717912137),
            (-2.4802867532861947, 0.3133330839107602),
            (-2.5, -8.040613248383183e-16),
            (-2.4802867532861947, -0.3133330839107607),
            (-2.4214579028215777, -0.6217247179121376),
            (-2.324441214720628, -0.9203113817116958),
            (-2.1907667001096587, -1.2043841852542885),
            (-2.022542485937368, -1.4694631307311834),
            (-1.822421568553529, -1.7113677648217218),
            (-1.5935599743717237, -1.9262831069394735),
            (-1.339566987447491, -2.1108198137550382),
            (-1.0644482289126804, -2.2620676311650496),
            (-0.7725424859373689, -2.3776412907378837),
            (-0.46845328646431156, -2.4557181268217216),
            (-0.156976298823283, -2.495066821070679),
            (0.1569762988232843, -2.495066821070679),
            (0.46845328646431283, -2.4557181268217216),
            (0.7725424859373681, -2.377641290737884),
            (1.0644482289126815, -2.262067631165049),
            (1.3395669874474918, -2.1108198137550374),
            (1.593559974371725, -1.9262831069394726),
            (1.8224215685535297, -1.7113677648217207),
            (2.0225424859373695, -1.4694631307311814),
            (2.190766700109659, -1.2043841852542883),
            (2.3244412147206286, -0.9203113817116947),
            (2.421457902821578, -0.6217247179121362),
            (2.4802867532861947, -0.3133330839107595),
        ]
        return coords

    @image_comparison(baseline_images=["clustering_directed"], remove_text=True)
    def test_clustering_directed_small(self):
        g = ig.Graph.Ring(5, directed=True)
        clu = ig.VertexClustering(g, [0] * 5)
        fig, ax = plt.subplots()
        ipx.graph(g, grouping=clu, ax=ax, layout=self.layout_small_ring)

    @image_comparison(baseline_images=["clustering_directed_large"], remove_text=True)
    def test_clustering_directed_large(self):
        g = ig.Graph.Ring(50, directed=True)
        clu = ig.VertexClustering(g, [0] * 3 + [1] * 17 + [2] * 30)
        fig, ax = plt.subplots()
        ipx.graph(
            g,
            grouping=clu,
            style={
                "vertex": {
                    "size": 15,
                },
                "edge": {
                    "arrow": {
                        "width": 5,
                        "height": 5,
                    },
                },
                "grouping": {
                    "vertexpadding": 9,
                },
            },
            layout=self.layout_large_ring,
            ax=ax,
            aspect=1.0,
        )


def suite():
    return unittest.TestSuite(
        [
            unittest.defaultTestLoader.loadTestsFromTestCase(GraphTestRunner),
            unittest.defaultTestLoader.loadTestsFromTestCase(ClusteringTestRunner),
        ]
    )


def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())


if __name__ == "__main__":
    test()
