"""
@file cartography.py
@brief Cartography utilities for retrieving and processing OpenStreetMap data.

This module provides functions to download and process street network data
from OpenStreetMap using OSMnx, with support for graph simplification and
standardization of attributes.
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox


def get_cartography(
    place_name: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    network_type: str = "drive",
    consolidate_intersections: bool | float = 10,
    dead_ends: bool = False,
    infer_speeds: bool = False,
    return_type: str = "gdfs",
) -> tuple | nx.DiGraph:
    """
    Retrieves and processes cartography data for a specified place using OpenStreetMap data.

    This function downloads a street network graph for the given place or bounding box, optionally consolidates
    intersections to simplify the graph, removes edges with zero length, self-loops and isolated nodes,
    and standardizes the attribute names in the graph. Can return either GeoDataFrames or the graph itself.

    Args:
        place_name (str): The name of the place (e.g., city, neighborhood) to retrieve cartography for.
        bbox (tuple, optional): A tuple specifying the bounding box (north, south, east, west)
            to retrieve cartography for.
        network_type (str, optional): The type of network to retrieve. Common values include "drive",
            "walk", "bike". Defaults to "drive".
        consolidate_intersections (bool | float, optional): If True, consolidates intersections using
            a default tolerance. If a float, uses that value as the tolerance for consolidation.
            Set to False to skip consolidation. Defaults to 10.
        dead_ends (bool, optional): Whether to include dead ends when consolidating intersections.
            Only relevant if consolidate_intersections is enabled. Defaults to False.
        infer_speeds (bool, optional): Whether to infer edge speeds based on road types. Defaults to False.
            If True, calls ox.routing.add_edge_speeds using np.nanmedian as aggregation function.
            Finally, the "maxspeed" attribute is replaced with the inferred "speed_kph", and the "travel_time" attribute is computed.
        return_type (str, optional): Type of return value. Options are "gdfs" (GeoDataFrames) or
            "graph" (NetworkX DiGraph). Defaults to "gdfs".

    Returns:
        tuple | nx.DiGraph: If return_type is "gdfs", returns a tuple containing two GeoDataFrames:
            - gdf_edges: GeoDataFrame with processed edge data, including columns like 'source',
              'target', 'nlanes', 'type', 'name', 'id', and 'geometry'.
            - gdf_nodes: GeoDataFrame with processed node data, including columns like 'id', 'type',
              and 'geometry'.
            If return_type is "graph", returns the NetworkX DiGraph with standardized attributes.
    """
    if bbox is None and place_name is None:
        raise ValueError("Either place_name or bbox must be provided.")

    if consolidate_intersections and isinstance(consolidate_intersections, bool):
        consolidate_intersections = 10  # Default tolerance value

    # Retrieve the graph using OSMnx
    if place_name is not None:
        G = ox.graph_from_place(place_name, network_type=network_type, simplify=False)
    elif bbox is not None:
        G = ox.graph_from_bbox(
            bbox, network_type=network_type, simplify=False, truncate_by_edge=True
        )
    else:
        raise ValueError("Either place_name or bbox must be provided.")

    # Simplify the graph without removing rings
    G = ox.simplify_graph(G, remove_rings=False)

    if consolidate_intersections:
        G = ox.consolidate_intersections(
            ox.project_graph(G),
            tolerance=consolidate_intersections,
            rebuild_graph=True,
            dead_ends=dead_ends,
        )
        # Convert back to lat/long
        G = ox.project_graph(G, to_latlong=True)
    # Remove all edges with length 0 because the ox.convert.to_digraph will keep the duplicates with minimal length
    G.remove_edges_from(
        [
            (u, v, k)
            for u, v, k, data in G.edges(keys=True, data=True)
            if data.get("length", 0) == 0
        ]
    )
    # Remove self-loops
    G.remove_edges_from([(u, v, k) for u, v, k in G.edges(keys=True) if u == v])
    # Remove also isolated nodes
    G.remove_nodes_from(list(nx.isolates(G)))

    if infer_speeds:
        G = ox.routing.add_edge_speeds(G, agg=np.nanmedian)
        G = ox.routing.add_edge_travel_times(G)
        # Replace "maxspeed" with "speed_kph"
        for u, v, data in G.edges(data=True):
            if "speed_kph" in data:
                data["maxspeed"] = data["speed_kph"]
                del data["speed_kph"]

    # Convert to Directed Graph
    G = ox.convert.to_digraph(G)

    # Standardize edge attributes in the graph
    edges_to_update = []
    for u, v, data in G.edges(data=True):
        edge_updates = {}

        # Standardize lanes
        if "lanes" in data:
            lanes_value = data["lanes"]
            if isinstance(lanes_value, list):
                edge_updates["nlanes"] = min(lanes_value)
            else:
                edge_updates["nlanes"] = lanes_value
            edge_updates["_remove_lanes"] = True
        else:
            edge_updates["nlanes"] = 1

        # Standardize highway -> type
        if "highway" in data:
            edge_updates["type"] = data["highway"]
            edge_updates["_remove_highway"] = True

        # Standardize name
        if "name" in data:
            name_value = data["name"]
            if isinstance(name_value, list):
                name_value = ",".join(name_value)
            edge_updates["name"] = str(name_value).lower().replace(" ", "_")
        else:
            edge_updates["name"] = "unknown"

        # Remove unnecessary attributes
        for attr in [
            "bridge",
            "tunnel",
            "access",
            "service",
            "ref",
            "reversed",
            "junction",
            "osmid",
        ]:
            if attr in data:
                edge_updates[f"_remove_{attr}"] = True

        if consolidate_intersections:
            for attr in ["u_original", "v_original"]:
                if attr in data:
                    edge_updates[f"_remove_{attr}"] = True

        edges_to_update.append((u, v, edge_updates))

    # Apply edge updates
    for u, v, updates in edges_to_update:
        for key, value in updates.items():
            if key.startswith("_remove_"):
                attr_name = key.replace("_remove_", "")
                if attr_name in G[u][v]:
                    del G[u][v][attr_name]
            else:
                G[u][v][key] = value
    # Add id to edges and rename u/v to source/target
    for i, (u, v) in enumerate(G.edges()):
        G[u][v]["id"] = i
        G[u][v]["source"] = u
        G[u][v]["target"] = v

    # Standardize node attributes in the graph
    nodes_to_update = []
    for node, data in G.nodes(data=True):
        node_updates = {}

        # Standardize osmid -> id (keep both for compatibility with ox.graph_to_gdfs)
        if "osmid" in data:
            node_updates["id"] = data["osmid"]

        # Standardize highway -> type
        if "highway" in data:
            node_updates["type"] = data["highway"]
            node_updates["_remove_highway"] = True
        else:
            # Set type to "N/A" if not present
            node_updates["type"] = "N/A"

        # Remove unnecessary attributes
        for attr in ["street_count", "ref", "cluster", "junction"]:
            if attr in data:
                node_updates[f"_remove_{attr}"] = True

        if consolidate_intersections and "osmid_original" in data:
            node_updates["_remove_osmid_original"] = True

        nodes_to_update.append((node, node_updates))

    # Apply node updates
    for node, updates in nodes_to_update:
        for key, value in updates.items():
            if key.startswith("_remove_"):
                attr_name = key.replace("_remove_", "")
                if attr_name in G.nodes[node]:
                    del G.nodes[node][attr_name]
            else:
                G.nodes[node][key] = value

    # Fill NaN values in node type attribute
    for node in G.nodes():
        if (
            "type" not in G.nodes[node]
            or G.nodes[node]["type"] is None
            or (
                isinstance(G.nodes[node]["type"], float)
                and G.nodes[node]["type"] != G.nodes[node]["type"]
            )
        ):  # Check for NaN
            G.nodes[node]["type"] = "N/A"

    # Return graph or GeoDataFrames based on return_type
    if return_type == "graph":
        return G
    elif return_type == "gdfs":
        # Convert back to MultiDiGraph temporarily for ox.graph_to_gdfs compatibility
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(nx.MultiDiGraph(G))

        # Reset index and drop unnecessary columns (id, source, target already exist from graph)
        gdf_edges.reset_index(inplace=True)
        # Move the "id" column to the beginning
        id_col = gdf_edges.pop("id")
        gdf_edges.insert(0, "id", id_col)

        # Ensure length is float
        gdf_edges["length"] = gdf_edges["length"].astype(float)

        gdf_edges.drop(columns=["u", "v", "key"], inplace=True, errors="ignore")

        # Reset index for nodes
        gdf_nodes.reset_index(inplace=True)
        gdf_nodes.drop(columns=["y", "x"], inplace=True, errors="ignore")
        gdf_nodes.rename(columns={"osmid": "id"}, inplace=True)

        return gdf_edges, gdf_nodes
    else:
        raise ValueError("Invalid return_type. Choose 'gdfs' or 'graph'.")


def graph_from_gdfs(
    gdf_edges: gpd.GeoDataFrame,
    gdf_nodes: gpd.GeoDataFrame,
) -> nx.DiGraph:
    """
    Constructs a NetworkX DiGraph from given GeoDataFrames of edges and nodes.
    The supported GeoDataFrame are the ones returned by get_cartography with return_type="gdfs".

    Args:
        gdf_edges (GeoDataFrame): GeoDataFrame containing edge data.
        gdf_nodes (GeoDataFrame): GeoDataFrame containing node properties data.

    Returns:
        nx.DiGraph: The constructed DiGraph with standardized attributes.
    """

    # Cast node IDs to int for consistency
    gdf_edges["source"] = gdf_edges["source"].astype(np.uint64)
    gdf_edges["target"] = gdf_edges["target"].astype(np.uint64)
    gdf_nodes["id"] = gdf_nodes["id"].astype(np.uint64)

    G = nx.from_pandas_edgelist(
        gdf_edges,
        edge_key="id",
        source="source",
        target="target",
        edge_attr=True,
        create_using=nx.DiGraph,
    )
    for node, data in gdf_nodes.set_index("id").to_dict(orient="index").items():
        G.nodes[node].update(data)
    return G


def graph_to_gdfs(
    G: nx.DiGraph,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Converts a NetworkX DiGraph to GeoDataFrames of edges and nodes.
    The returned GeoDataFrames are compatible with those returned by get_cartography with return_type="gdfs".

    Args:
        G (nx.DiGraph): The input DiGraph.

    Returns:
        tuple: A tuple containing two GeoDataFrames:
            - gdf_edges: GeoDataFrame with edge data.
            - gdf_nodes: GeoDataFrame with node properties data.
    """
    # Convert back to MultiDiGraph temporarily for ox.graph_to_gdfs compatibility
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(nx.MultiDiGraph(G))

    # Reset index and drop unnecessary columns (id, source, target already exist from graph)
    gdf_edges.reset_index(inplace=True)
    # Move the "id" column to the beginning
    id_col = gdf_edges.pop("id")
    gdf_edges.insert(0, "id", id_col)

    # Ensure length is float
    gdf_edges["length"] = gdf_edges["length"].astype(float)

    gdf_edges.drop(columns=["u", "v", "key"], inplace=True, errors="ignore")

    # Reset index for nodes
    gdf_nodes.reset_index(inplace=True)
    gdf_nodes.drop(columns=["y", "x"], inplace=True, errors="ignore")
    gdf_nodes.rename(columns={"osmid": "id"}, inplace=True)

    return gdf_edges, gdf_nodes


# if __name__ == "__main__":
#     # Produce data for tests
#     edges, nodes = get_cartography(
#         "Postua, Piedmont, Italy", consolidate_intersections=False, infer_speeds=True
#     )
#     edges.to_csv("../../../test/data/postua_edges.csv", index=False, sep=";")
#     edges.to_file(
#         "../../../test/data/postua_edges.geojson", index=False, driver="GeoJSON"
#     )
#     nodes.to_csv("../../../test/data/postua_nodes.csv", index=False, sep=";")
#     edges, nodes = get_cartography("Forlì, Emilia-Romagna, Italy", infer_speeds=True)
#     edges.to_csv("../../../test/data/forlì_edges.csv", index=False, sep=";")
#     nodes.to_csv("../../../test/data/forlì_nodes.csv", index=False, sep=";")
