"""
Visualisation des sections
"""

import matplotlib.pyplot as plt

from opensection.geometry.section import Section


class SectionPlotter:
    """Tracé de sections"""

    @staticmethod
    def plot_section(section: Section, show_fibers: bool = False):
        """Trace la section"""
        fig, ax = plt.subplots(figsize=(8, 8))

        for contour in section.contours:
            points = contour.to_array()
            ax.plot(points[:, 0], points[:, 1], "b-", linewidth=2)
            ax.fill(
                points[:, 0],
                points[:, 1],
                alpha=0.3,
                facecolor="gray" if not contour.is_hole else "white",
            )

        if show_fibers:
            fibers = section.create_fiber_mesh()
            if len(fibers) > 0:
                ax.scatter(fibers[:, 0], fibers[:, 1], s=1, c="red", alpha=0.5)

        props = section.properties
        ax.plot(props.centroid[0], props.centroid[1], "r+", markersize=15, markeredgewidth=2)

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("y (m)")
        ax.set_ylabel("z (m)")
        ax.set_title("Section transversale")

        return fig, ax
