"""
Helper functions for reinforcement placement with automatic cover
"""

from typing import List, Tuple

import numpy as np


class CoverHelper:
    """Helper class for automatic cover calculation"""

    @staticmethod
    def rectangular_position_with_cover(
        position: str, width: float, height: float, diameter: float, cover: float
    ) -> Tuple[float, float]:
        """
        Calculate rebar position with automatic cover for rectangular section

        Args:
            position: "top", "bottom", "left", "right", "top-left", etc.
            width: Section width (m)
            height: Section height (m)
            diameter: Rebar diameter (m)
            cover: Concrete cover (m)

        Returns:
            (y, z) coordinates in section local axes

        Examples:
            >>> y, z = CoverHelper.rectangular_position_with_cover(
            ...     "top", width=0.3, height=0.5, diameter=0.016, cover=0.03
            ... )
            >>> # Returns y = 0.232, z = 0.0 (top position with 3cm cover)
        """
        radius = diameter / 2

        # Calculate distances from center
        half_width = width / 2
        half_height = height / 2

        # Distance from edge to rebar center
        distance_from_edge = cover + radius

        position = position.lower()

        # Vertical positions (y-axis)
        if "top" in position:
            y = half_height - distance_from_edge
        elif "bottom" in position:
            y = -half_height + distance_from_edge
        else:
            y = 0.0

        # Horizontal positions (z-axis)
        if "left" in position:
            z = -half_width + distance_from_edge
        elif "right" in position:
            z = half_width - distance_from_edge
        else:
            z = 0.0

        return y, z

    @staticmethod
    def circular_position_with_cover(
        angle_degrees: float, diameter_section: float, diameter_rebar: float, cover: float
    ) -> Tuple[float, float]:
        """
        Calculate rebar position on circular section with automatic cover

        Args:
            angle_degrees: Angle in degrees (0° = right, 90° = top)
            diameter_section: Section diameter (m)
            diameter_rebar: Rebar diameter (m)
            cover: Concrete cover (m)

        Returns:
            (y, z) coordinates in section local axes

        Examples:
            >>> y, z = CoverHelper.circular_position_with_cover(
            ...     90, diameter_section=0.5, diameter_rebar=0.016, cover=0.03
            ... )
            >>> # Returns position at top of circle with 3cm cover
        """
        radius_section = diameter_section / 2
        radius_rebar = diameter_rebar / 2

        # Radius to rebar center
        radius_to_center = radius_section - cover - radius_rebar

        # Convert to radians
        angle_rad = np.deg2rad(angle_degrees)

        # Calculate coordinates (y = vertical, z = horizontal)
        z = radius_to_center * np.cos(angle_rad)
        y = radius_to_center * np.sin(angle_rad)

        return y, z

    @staticmethod
    def circular_array_with_cover(
        n_bars: int,
        diameter_section: float,
        diameter_rebar: float,
        cover: float,
        start_angle: float = 0.0,
    ) -> List[Tuple[float, float]]:
        """
        Create circular array of rebars with automatic cover

        Args:
            n_bars: Number of bars
            diameter_section: Section diameter (m)
            diameter_rebar: Rebar diameter (m)
            cover: Concrete cover (m)
            start_angle: Starting angle in degrees (default 0°)

        Returns:
            List of (y, z) coordinates

        Examples:
            >>> positions = CoverHelper.circular_array_with_cover(
            ...     n_bars=8, diameter_section=0.5, diameter_rebar=0.016, cover=0.03
            ... )
            >>> # Returns 8 positions equally spaced around circle
        """
        positions = []
        angle_step = 360.0 / n_bars

        for i in range(n_bars):
            angle = start_angle + i * angle_step
            y, z = CoverHelper.circular_position_with_cover(
                angle, diameter_section, diameter_rebar, cover
            )
            positions.append((y, z))

        return positions

    @staticmethod
    def layer_positions_with_cover(
        position: str,
        width: float,
        height: float,
        n_bars: int,
        diameter: float,
        cover: float,
        spacing: float = None,
    ) -> List[Tuple[float, float]]:
        """
        Create a layer of rebars with automatic cover

        Args:
            position: "top" or "bottom"
            width: Section width (m)
            height: Section height (m)
            n_bars: Number of bars in layer
            diameter: Rebar diameter (m)
            cover: Concrete cover (m)
            spacing: Spacing between bars (if None, auto-calculated)

        Returns:
            List of (y, z) coordinates

        Examples:
            >>> positions = CoverHelper.layer_positions_with_cover(
            ...     "top", width=0.3, height=0.5, n_bars=3,
            ...     diameter=0.016, cover=0.03
            ... )
            >>> # Returns 3 positions spaced along top
        """
        # Get y position
        y, _ = CoverHelper.rectangular_position_with_cover(position, width, height, diameter, cover)

        # Calculate z positions
        radius = diameter / 2
        half_width = width / 2

        # Available width for spacing
        available_width = width - 2 * (cover + radius)

        if n_bars == 1:
            z_positions = [0.0]
        elif n_bars == 2:
            edge_distance = cover + radius
            z_positions = [-half_width + edge_distance, half_width - edge_distance]
        else:
            # Multiple bars - distribute evenly
            if spacing is None:
                spacing = available_width / (n_bars - 1)

            z_start = -half_width + cover + radius
            z_positions = [z_start + i * spacing for i in range(n_bars)]

        return [(y, z) for z in z_positions]
