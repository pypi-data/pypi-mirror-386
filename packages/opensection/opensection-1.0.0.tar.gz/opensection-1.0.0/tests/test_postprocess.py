"""
Tests for postprocessing modules (report generation and visualization)
"""

import pytest
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from opensection.geometry.section import CircularSection, RectangularSection
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import SteelEC2
from opensection.postprocess.report import ReportGenerator
from opensection.postprocess.visualization import SectionPlotter
from opensection.reinforcement.rebar import RebarGroup
from opensection.solver.section_solver import SectionSolver


class TestReportGenerator:
    """Tests for report generation"""

    @pytest.fixture
    def sample_result(self):
        """Create a sample solver result for testing"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=-0.2, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=0.2, z=0.0, diameter=0.016, n=2)

        solver = SectionSolver(section, concrete, steel, rebars)
        result = solver.solve(N=500, My=0, Mz=100)
        return result

    def test_generate_text_report_basic(self, sample_result):
        """Test basic text report generation"""
        report = ReportGenerator.generate_text_report(sample_result)

        # Check that report is generated
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_contains_convergence_info(self, sample_result):
        """Test that report contains convergence information"""
        report = ReportGenerator.generate_text_report(sample_result)

        assert "Convergence" in report or "CONVERGENCE" in report
        assert "Itérations" in report or "Iterations" in report

    def test_report_contains_deformations(self, sample_result):
        """Test that report contains deformation values"""
        report = ReportGenerator.generate_text_report(sample_result)

        # Check for strain values
        assert "e0" in report or "ε₀" in report or "epsilon" in report
        assert "chi" in report or "χ" in report or "curvature" in report

    def test_report_contains_forces(self, sample_result):
        """Test that report contains force values"""
        report = ReportGenerator.generate_text_report(sample_result)

        # Check for forces
        assert "N" in report
        assert "M" in report or "Moment" in report

    def test_report_contains_stresses(self, sample_result):
        """Test that report contains stress values"""
        report = ReportGenerator.generate_text_report(sample_result)

        # Check for stress values (s_c,max or s_s,max or CONTRAINTES)
        assert "s_c,max" in report or "s_s,max" in report or "CONTRAINTES" in report
        assert "MPa" in report

    def test_report_format_is_readable(self, sample_result):
        """Test that report has proper formatting"""
        report = ReportGenerator.generate_text_report(sample_result)

        # Check for section separators
        assert "=" in report
        lines = report.split("\n")
        assert len(lines) > 10  # Should have multiple lines

    def test_report_with_non_converged_result(self):
        """Test report generation with non-converged result"""
        # Create a difficult case that won't converge
        section = RectangularSection(width=0.1, height=0.1)
        concrete = ConcreteEC2(fck=20)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()

        solver = SectionSolver(section, concrete, steel, rebars)
        # Extreme load that won't converge
        result = solver.solve(N=10000, My=0, Mz=1000)

        report = ReportGenerator.generate_text_report(result)

        # Should still generate report
        assert isinstance(report, str)
        assert len(report) > 0


class TestSectionPlotter:
    """Tests for section visualization"""

    def test_plot_rectangular_section(self):
        """Test plotting a rectangular section"""
        section = RectangularSection(width=0.3, height=0.5)

        fig, ax = SectionPlotter.plot_section(section)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_circular_section(self):
        """Test plotting a circular section"""
        section = CircularSection(diameter=0.4, n_points=24)

        fig, ax = SectionPlotter.plot_section(section)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_section_with_fibers(self):
        """Test plotting section with fiber mesh"""
        section = RectangularSection(width=0.3, height=0.5)

        fig, ax = SectionPlotter.plot_section(section, show_fibers=True)

        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_shows_centroid(self):
        """Test that plot shows centroid marker"""
        section = RectangularSection(width=0.3, height=0.5)

        fig, ax = SectionPlotter.plot_section(section)

        # Check that there are plot elements
        assert len(ax.lines) > 0 or len(ax.collections) > 0

        plt.close(fig)

    def test_plot_has_proper_labels(self):
        """Test that plot has axis labels and title"""
        section = RectangularSection(width=0.3, height=0.5)

        fig, ax = SectionPlotter.plot_section(section)

        # Check for labels
        assert ax.get_xlabel() != ""
        assert ax.get_ylabel() != ""
        assert ax.get_title() != ""

        plt.close(fig)

    def test_plot_aspect_ratio(self):
        """Test that plot has equal aspect ratio"""
        section = RectangularSection(width=0.3, height=0.5)

        fig, ax = SectionPlotter.plot_section(section)

        # Check aspect ratio is equal
        assert ax.get_aspect() in ["equal", 1.0]

        plt.close(fig)

    def test_plot_multiple_sections(self):
        """Test plotting multiple different sections"""
        sections = [
            RectangularSection(width=0.3, height=0.5),
            CircularSection(diameter=0.4, n_points=16),
        ]

        for section in sections:
            fig, ax = SectionPlotter.plot_section(section)
            assert fig is not None
            assert ax is not None
            plt.close(fig)


class TestIntegratedPostprocess:
    """Integration tests for postprocessing workflow"""

    def test_complete_workflow(self):
        """Test complete workflow: solve → report → plot"""
        # 1. Create and solve
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=-0.2, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)
        result = solver.solve(N=500, My=0, Mz=100)

        # 2. Generate report
        report = ReportGenerator.generate_text_report(result)
        assert len(report) > 0

        # 3. Plot section
        fig, ax = SectionPlotter.plot_section(section, show_fibers=True)
        assert fig is not None

        plt.close(fig)

    def test_report_values_match_result(self):
        """Test that report values match actual solver result"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=-0.2, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)
        result = solver.solve(N=500, My=0, Mz=100)

        report = ReportGenerator.generate_text_report(result)

        # Check that key values appear in report
        assert f"{result.N:.2f}" in report or f"{result.N:.1f}" in report
        assert str(result.n_iter) in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

