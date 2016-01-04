import graphlab as gl
from graphlab import SGraph, Vertex, Edge, degree_counting, connected_components
import cPickle as pickle
from math import sqrt

def build_weighted_graph(ing_comp_dict):
    """
    builds the weighted undirected graph that is the flavor network
    :param ing_comp_dict: ingredient:compound dictionary
    :return: SGraph that represents the flavor network
    """
    flav_network = SGraph()
    vert_list = []
    edge_list = []
    ingrds_not_seen = ing_comp_dict.keys()
    for node_1_ingr, compounds in ing_comp_dict.iteritems():
        ingrds_not_seen.remove(node_1_ingr)
        vert_list.append(Vertex(node_1_ingr, attr={'deg': 0}))
        for node_2_ingr in ingrds_not_seen:
            weight = len(set(ing_comp_dict[node_2_ingr]).intersection(set(compounds)))
            if weight > 0:
                edge_list.append(Edge(node_1_ingr, node_2_ingr, attr={'weight': weight}))
        vert_list.append(Vertex(node_1_ingr))

    flav_network = flav_network.add_vertices(vert_list)
    flav_network = flav_network.add_edges(edge_list)
    return flav_network

def extract_backbone(flavor_network):
    """
    return a new graph with only the edges that meet the requirement for statistical significance
    :param ing_comp_graph: full flavor ingredient network
    :return: the pruned SGraph
    """
    def degree_count_fn(src, edge, dst):
        """
        increments the degree of the nodes on this edge
        :param src:
        :param edge:
        :param dst:
        :return:
        """
        src['deg'] += 1
        dst['deg'] += 1
        return src, edge, dst

    def compute_node_moments(node):
        k = float(node.attr.values()[0])
        mean = 2*k/(k+1)
        sigma = sqrt(k**2*((20 + 4*k)/((k + 1)(k + 2)(k + 3)) - 4/(k + 1)**2))
        return mean, sigma

    def test_for_significance(edge, alpha):
        y_obs = edge.attr.values()[0]
        node1 = edge.dst_vid
        node2 = edge.src.vid
        m1, sig1 = compute_node_moments(node1)
        m2, sig2 = compute_node_moments(node2)

        return y_obs > (m1 + alpha*sig1) or y_obs > (m2 + alpha*sig2)

    flav_net_w_deg = SGraph()
    edge_list = flavor_network.get_edges()
    new_node_list = flavor_network.vertices.fillna('deg', 0)
    flav_net_w_deg = flav_net_w_deg.add_vertices(new_node_list).add_edges(edge_list)
    flav_net_w_deg = flav_net_w_deg.triple_apply(degree_count_fn, mutated_fields=['deg'])

    significant_edges = []
    # for edge in flav_net_w_deg.get_edges():
    #     if test_for_significance(edge, 1):
    #         significant_edges.append(edge)
    return flav_net_w_deg

if __name__ == '__main__':
    with open('../../notebooks/data/first_ing_comp_dict.pkl', 'r') as f:
        ing_comp_dict = pickle.load(f)
    fnet = extract_backbone(build_weighted_graph(ing_comp_dict))