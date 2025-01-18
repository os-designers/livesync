from ..core.nodes import Node


def topological_sort_levels(nodes: list[Node]) -> list[list[Node]]:
    """
    Perform a topological sort and group nodes into execution levels.

    Returns a list of levels, where each level contains nodes that can be
    executed in parallel.

    Raises
    ------
    ValueError
        If the graph contains a cycle or is invalid for DAG processing.
    """
    in_degree = {node.name: len(node.parents) for node in nodes}
    zero_in_degree = [n for n, deg in in_degree.items() if deg == 0]

    levels: list[list[Node]] = []
    current_level: list[Node] = [node for node in nodes if node.name in zero_in_degree]

    while current_level:
        levels.append(current_level)
        next_level: list[Node] = []
        for node in current_level:
            for child in node.children:
                in_degree[child.name] -= 1
                if in_degree[child.name] == 0:
                    next_level.append(child)
        current_level = next_level

    visited_count = sum(len(level) for level in levels)
    if visited_count != len(nodes):
        raise ValueError("Graph contains a cycle or is otherwise invalid for DAG processing.")

    return levels
