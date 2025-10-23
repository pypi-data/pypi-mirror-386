"""
Functions for processing graph slides with nodes and edges.

This module provides functionality to create node/edge graph visualizations
on PowerPoint slides, including validation, positioning, and rendering.
"""

from typing import Callable, Optional

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR_TYPE
from pptx.util import Inches, Pt

from office_templates.templating.core import process_text_recursive

# Standard DPI for converting pixel coordinates to inches
# Frontend graph libraries typically use pixel coordinates at 96 DPI
PIXELS_PER_INCH = 96

# PowerPoint slide dimension limits (in inches)
MAX_SLIDE_DIMENSION = 56  # Maximum dimension allowed by PowerPoint
MIN_SLIDE_DIMENSION = 1  # Minimum dimension allowed by PowerPoint


def _pixels_to_inches(pixels: float) -> float:
    """
    Convert pixel coordinates to inches.

    Args:
        pixels: Position in pixels

    Returns:
        Position in inches
    """
    return pixels / PIXELS_PER_INCH


def process_graph_slide(
    slide,
    graph: dict,
    base_prs,
    global_context: dict,
    check_permissions: Optional[Callable[[object], bool]],
    slide_number: int,
    errors: list[str],
):
    """
    Process a graph slide by creating nodes and edges.

    Args:
        slide: The slide to add graph elements to
        graph: Dict containing 'nodes' and 'edges'
        base_prs: The presentation object (for slide resizing)
        global_context: Global context for template processing
        check_permissions: Permission checking function
        slide_number: Slide number for error reporting
        errors: List to append errors to
    """
    try:
        # Validate graph structure
        if "nodes" not in graph:
            errors.append(f"Slide {slide_number}: Graph missing 'nodes' key")
            return

        if "edges" not in graph:
            errors.append(f"Slide {slide_number}: Graph missing 'edges' key")
            return

        nodes = graph["nodes"]
        edges = graph["edges"]

        # Validate nodes
        if not isinstance(nodes, list):
            errors.append(f"Slide {slide_number}: 'nodes' must be a list")
            return

        if not nodes:
            errors.append(f"Slide {slide_number}: 'nodes' list is empty")
            return

        # Validate edges
        if not isinstance(edges, list):
            errors.append(f"Slide {slide_number}: 'edges' must be a list")
            return

        # Calculate required slide dimensions and scaling factor
        slide_width, slide_height, scale_factor = _calculate_slide_dimensions_and_scale(
            nodes, errors, slide_number
        )

        # Resize the slide
        base_prs.slide_width = Inches(slide_width)
        base_prs.slide_height = Inches(slide_height)

        # Create node shapes and store them for edge connections
        node_shapes = {}
        for node in nodes:
            shape = _create_node_shape(
                slide,
                node,
                global_context,
                check_permissions,
                errors,
                slide_number,
                scale_factor,
            )
            if shape:
                node_shapes[node["id"]] = shape

        # Create edge connectors
        for edge in edges:
            _create_edge_connector(
                slide,
                edge,
                node_shapes,
                global_context,
                check_permissions,
                errors,
                slide_number,
                scale_factor,
            )

    except Exception as e:
        errors.append(f"Slide {slide_number}: Error processing graph: {e}")


def _calculate_slide_dimensions_and_scale(
    nodes: list[dict], errors: list[str], slide_number: int
) -> tuple[float, float, float]:
    """
    Calculate the required slide dimensions to fit all nodes and scaling factor.

    For very large graphs that would exceed PowerPoint's 56-inch limit, this function
    calculates a scaling factor to fit the graph within the allowed dimensions.

    Args:
        nodes: List of node dictionaries with position in pixels
        errors: List to append errors to
        slide_number: Slide number for error reporting

    Returns:
        Tuple of (width, height, scale_factor) in inches and scale factor
    """
    # Default minimum slide size (standard 16:9)
    min_width = 10
    min_height = 7.5

    # Calculate bounds from node positions (in inches, before scaling)
    max_x = min_width
    max_y = min_height

    # Default node size (will be auto-expanded)
    node_width = 2.5
    node_height = 1.5

    for node in nodes:
        if "position" not in node:
            errors.append(
                f"Slide {slide_number}: Node '{node.get('id', 'unknown')}' missing 'position'"
            )
            continue

        position = node["position"]
        if "x" not in position or "y" not in position:
            errors.append(
                f"Slide {slide_number}: Node '{node.get('id', 'unknown')}' position missing 'x' or 'y'"
            )
            continue

        # Convert pixel positions to inches
        x_inches = _pixels_to_inches(position["x"])
        y_inches = _pixels_to_inches(position["y"])

        # Calculate right and bottom edges of this node
        node_right = x_inches + node_width
        node_bottom = y_inches + node_height

        max_x = max(max_x, node_right + 1)  # Add 1 inch margin
        max_y = max(max_y, node_bottom + 1)

    # Calculate scaling factor if dimensions exceed PowerPoint's limits
    scale_factor = 1.0
    if max_x > MAX_SLIDE_DIMENSION or max_y > MAX_SLIDE_DIMENSION:
        # Scale down to fit within the maximum dimension
        scale_x = MAX_SLIDE_DIMENSION / max_x if max_x > MAX_SLIDE_DIMENSION else 1.0
        scale_y = MAX_SLIDE_DIMENSION / max_y if max_y > MAX_SLIDE_DIMENSION else 1.0
        scale_factor = min(scale_x, scale_y)

        # Apply scaling to dimensions
        max_x = max_x * scale_factor
        max_y = max_y * scale_factor

    return max_x, max_y, scale_factor


def _create_node_shape(
    slide,
    node: dict,
    global_context: dict,
    check_permissions: Optional[Callable[[object], bool]],
    errors: list[str],
    slide_number: int,
    scale_factor: float = 1.0,
):
    """
    Create a node shape on the slide.

    Args:
        slide: The slide to add the shape to
        node: Node dictionary with position and content
        global_context: Global context for template processing
        check_permissions: Permission checking function
        errors: List to append errors to
        slide_number: Slide number for error reporting
        scale_factor: Scaling factor to apply to positions and fonts

    Returns:
        The created shape or None if creation failed
    """
    try:
        # Validate required fields
        if "id" not in node:
            errors.append(f"Slide {slide_number}: Node missing 'id' field")
            return None

        if "name" not in node:
            errors.append(
                f"Slide {slide_number}: Node '{node['id']}' missing 'name' field"
            )
            return None

        if "position" not in node:
            errors.append(
                f"Slide {slide_number}: Node '{node['id']}' missing 'position' field"
            )
            return None

        position = node["position"]
        if "x" not in position or "y" not in position:
            errors.append(
                f"Slide {slide_number}: Node '{node['id']}' position missing 'x' or 'y'"
            )
            return None

        # Process template variables in node name and detail
        name = process_text_recursive(node["name"], global_context, check_permissions)
        detail = ""
        if "detail" in node:
            detail = process_text_recursive(
                node["detail"], global_context, check_permissions
            )

        # Convert pixel positions to inches and apply scaling
        left = Inches(_pixels_to_inches(position["x"]) * scale_factor)
        top = Inches(_pixels_to_inches(position["y"]) * scale_factor)
        width = Inches(2.5 * scale_factor)  # Default width, scaled
        height = Inches(1.5 * scale_factor)  # Default height, will auto-expand, scaled

        shape = slide.shapes.add_shape(1, left, top, width, height)  # MSO_SHAPE.RECTANGLE

        # Configure shape appearance
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(173, 216, 230)  # Light blue
        shape.line.color.rgb = RGBColor(0, 0, 0)  # Black border
        shape.line.width = Pt(1 * scale_factor)

        # Add text to shape
        text_frame = shape.text_frame
        text_frame.clear()  # Clear default paragraph
        text_frame.word_wrap = True

        # Add name (larger font) - font size scales with the graph
        p = text_frame.paragraphs[0]
        p.text = name
        p.font.size = Pt(int(14 * scale_factor))
        p.font.bold = True

        # Add detail if present (smaller font) - font size scales with the graph
        if detail:
            p = text_frame.add_paragraph()
            p.text = detail
            p.font.size = Pt(int(10 * scale_factor))

        # Enable auto-fit
        text_frame.auto_size = 1  # MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

        # Note: Parent functionality is placeholder for now
        # Will be implemented later to resize parent nodes
        if "parent" in node:
            # TODO: Implement parent node resizing logic
            pass

        return shape

    except Exception as e:
        errors.append(
            f"Slide {slide_number}: Error creating node '{node.get('id', 'unknown')}': {e}"
        )
        return None


def _create_edge_connector(
    slide,
    edge: dict,
    node_shapes: dict,
    global_context: dict,
    check_permissions: Optional[Callable[[object], bool]],
    errors: list[str],
    slide_number: int,
    scale_factor: float = 1.0,
):
    """
    Create an edge connector between two nodes.

    Args:
        slide: The slide to add the connector to
        edge: Edge dictionary with from/to node IDs
        node_shapes: Dictionary of node shapes by ID
        global_context: Global context for template processing
        check_permissions: Permission checking function
        errors: List to append errors to
        slide_number: Slide number for error reporting
        scale_factor: Scaling factor to apply to line widths and fonts

    Returns:
        The created connector or None if creation failed
    """
    try:
        # Validate required fields
        if "from" not in edge:
            errors.append(f"Slide {slide_number}: Edge missing 'from' field")
            return None

        if "to" not in edge:
            errors.append(f"Slide {slide_number}: Edge missing 'to' field")
            return None

        from_id = edge["from"]
        to_id = edge["to"]

        # Check if nodes exist
        if from_id not in node_shapes:
            errors.append(
                f"Slide {slide_number}: Edge references unknown source node '{from_id}'"
            )
            return None

        if to_id not in node_shapes:
            errors.append(
                f"Slide {slide_number}: Edge references unknown target node '{to_id}'"
            )
            return None

        from_shape = node_shapes[from_id]
        to_shape = node_shapes[to_id]

        # Create elbow connector (right angles)
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.ELBOW,
            from_shape.left + from_shape.width,  # Right edge of source
            from_shape.top + from_shape.height // 2,  # Middle of source
            to_shape.left,  # Left edge of target
            to_shape.top + to_shape.height // 2,  # Middle of target
        )

        # Connect to shapes
        connector.begin_connect(from_shape, 3)  # Right connection point
        connector.end_connect(to_shape, 1)  # Left connection point

        # Style the connector - line width scales with the graph
        connector.line.color.rgb = RGBColor(0, 0, 0)  # Black line
        connector.line.width = Pt(1.5 * scale_factor)

        # Add label if present
        if "label" in edge and edge["label"]:
            label_text = process_text_recursive(
                edge["label"], global_context, check_permissions
            )

            # Add text box for label near the middle of the connector
            mid_x = (connector.begin_x + connector.end_x) // 2
            mid_y = (connector.begin_y + connector.end_y) // 2

            # Label box dimensions scale with the graph
            label_box = slide.shapes.add_textbox(
                mid_x - Inches(0.5 * scale_factor),
                mid_y - Inches(0.25 * scale_factor),
                Inches(1 * scale_factor),
                Inches(0.5 * scale_factor),
            )

            label_box.text_frame.text = label_text
            label_box.text_frame.paragraphs[0].font.size = Pt(int(9 * scale_factor))
            label_box.fill.solid()
            label_box.fill.fore_color.rgb = RGBColor(255, 255, 255)  # White background

        return connector

    except Exception as e:
        errors.append(f"Slide {slide_number}: Error creating edge: {e}")
        return None
