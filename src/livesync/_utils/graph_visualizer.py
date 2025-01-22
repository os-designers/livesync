from __future__ import annotations

from typing import Any, Callable, Sequence


class GraphVisualizer:
    """Generic graph visualization utility."""

    BRANCH_COLORS = [
        "\033[95m",  # Magenta
        "\033[92m",  # Green
        "\033[94m",  # Blue
        "\033[96m",  # Cyan
        "\033[93m",  # Yellow
        "\033[91m",  # Red
    ]
    RESET = "\033[0m"

    @staticmethod
    def create_ascii_graph(
        node: Any,
        get_name: Callable[[Any], str],
        get_dependencies: Callable[[Any], Sequence[Any]],
        get_node_type: Callable[[Any], str] | None = None,
        visited: set[str] | None = None,
        prefix: str = "",
        is_right_branch: bool = False,
        color_idx: int = 0,
    ) -> list[str]:
        """
        Create ASCII representation of a graph.

        Parameters
        ----------
        node : Any
            Current node to process
        get_name : Callable[[Any], str]
            Function to get node name
        get_dependencies : Callable[[Any], Sequence[Any]]
            Function to get node dependencies
        get_node_type : Callable[[Any], str] | None
            Optional function to get node type for custom markers
        visited : set[str] | None
            Set of visited node names
        prefix : str
            Current line prefix for drawing
        is_right_branch : bool
            Whether this is a right branch in a merge
        color_idx : int
            Current color index
        """
        if visited is None:
            visited = set()

        node_name = get_name(node)
        if node_name in visited:
            return []

        visited.add(node_name)
        rows: list[str] = []
        current_color = GraphVisualizer.BRANCH_COLORS[color_idx % len(GraphVisualizer.BRANCH_COLORS)]
        reset = GraphVisualizer.RESET

        # Determine node marker
        node_marker = f"{current_color}●{reset}"
        if get_node_type:
            node_type = get_node_type(node)
            if node_type == "input":
                node_marker = f"{current_color}◇{reset}"
            elif node_type == "merge":
                node_marker = f"{current_color}○{reset}"

        # Add current node info
        if is_right_branch:
            rows.append(f"{prefix}{current_color}●{reset}  ({node_name})")
        else:
            rows.append(f"{prefix}{node_marker}  ({node_name})")

        # Process dependencies
        dependencies = list(get_dependencies(node))
        if not dependencies:
            return rows

        if len(dependencies) > 1:  # Merge node
            rows.append(f"{prefix}{current_color}│{reset}")

            # Show strategy instead of repeating the first dependency
            strategy_info = ""
            if hasattr(node, "dependency_strategy"):
                strategy_info = "wait for all streams" if node.dependency_strategy == "all" else "wait for any stream"

            # New color for the right branch
            right_color = GraphVisualizer.BRANCH_COLORS[(color_idx + 1) % len(GraphVisualizer.BRANCH_COLORS)]
            rows.append(f"{prefix}{current_color}○{reset}──{right_color}●{reset}  ({strategy_info})")
            rows.append(f"{prefix}{current_color}│{reset}  {right_color}│{reset}")

            # Process right branch with new color
            right_branch_prefix = f"{prefix}{current_color}│{reset}  "
            sub_rows = GraphVisualizer.create_ascii_graph(
                dependencies[0],
                get_name,
                get_dependencies,
                get_node_type,
                visited.copy(),
                right_branch_prefix,
                True,
                color_idx + 1,
            )
            rows.extend(sub_rows)

            # Process left branch with current color
            rows.append(f"{prefix}{current_color}│{reset}")
            sub_rows = GraphVisualizer.create_ascii_graph(
                dependencies[1], get_name, get_dependencies, get_node_type, visited, prefix, False, color_idx
            )
            rows.extend(sub_rows)

        else:  # Single dependency
            if get_name(dependencies[0]) not in visited:
                rows.append(f"{prefix}{current_color}│{reset}")
                rows.extend(
                    GraphVisualizer.create_ascii_graph(
                        dependencies[0], get_name, get_dependencies, get_node_type, visited, prefix, False, color_idx
                    )
                )

        return rows
