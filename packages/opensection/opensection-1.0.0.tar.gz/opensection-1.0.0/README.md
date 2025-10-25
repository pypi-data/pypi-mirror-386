# opensection - Professional Concrete Section Analysis

<div align="center">

**A Python library for structural concrete section analysis according to Eurocodes**

[![PyPI version](https://img.shields.io/pypi/v/opensection.svg)](https://pypi.org/project/opensection/)
[![Python versions](https://img.shields.io/pypi/pyversions/opensection.svg)](https://pypi.org/project/opensection/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/Pavlishenku/opensection/workflows/CI/badge.svg)](https://github.com/Pavlishenku/opensection/actions)
[![codecov](https://codecov.io/gh/Pavlishenku/opensection/branch/main/graph/badge.svg)](https://codecov.io/gh/Pavlishenku/opensection)
[![Documentation Status](https://readthedocs.org/projects/opensection/badge/?version=latest)](https://opensection.readthedocs.io/en/latest/?badge=latest)

[English](README.md) | [Français](README_FR.md)

</div>

---

## ✨ Features

- **Eurocode-compliant**: Full support for EN 1992 (Eurocode 2) for concrete structures
- **Fiber-based analysis**: Advanced section analysis using fiber discretization
- **Material models**: Comprehensive constitutive laws for concrete and reinforcing steel
- **Interaction diagrams**: Generate N-M interaction diagrams for sections
- **Flexible geometry**: Support for rectangular, circular, T-sections, and custom polygons
- **Visualization**: Built-in tools for plotting sections and results
- **Fast**: Optimized NumPy-based computations
- **Extensible**: Clean API for advanced users and researchers

## 📦 Installation

### From PyPI (recommended)

```bash
pip install opensection
```

### From source

```bash
git clone https://github.com/Pavlishenku/opensection.git
cd opensection
pip install -e .
```

### Development installation

```bash
git clone https://github.com/Pavlishenku/opensection.git
cd opensection
pip install -e ".[dev]"
```

## 🚀 Quick Start

```python
import opensection as ops

# Define a rectangular concrete section
section = ops.RectangularSection(width=0.3, height=0.5)

# Define materials (Eurocode 2)
concrete = ops.ConcreteEC2(fck=30)  # C30/37
steel = ops.SteelEC2(fyk=500)       # B500B

# Add reinforcement
rebars = ops.RebarGroup()
rebars.add_rebar(y=0.0, z=-0.20, diameter=0.020, n=3)  # 3Ø20 bottom
rebars.add_rebar(y=0.0, z=0.20, diameter=0.016, n=2)   # 2Ø16 top

# Create solver and analyze
solver = ops.SectionSolver(section, concrete, steel, rebars)
result = solver.solve(N=500, My=0, Mz=100)  # N in kN, M in kN·m

# Check results
print(f"Converged: {result.converged}")
print(f"Max concrete stress: {result.sigma_c_max:.2f} MPa")
print(f"Max steel stress: {result.sigma_s_max:.2f} MPa")

# Verify according to EC2
checks = ops.EC2Verification.check_ULS(result, concrete.fcd, steel.fyd)
print(f"Concrete check: {'OK' if checks['concrete_stress']['ok'] else 'FAIL'}")
print(f"Steel check: {'OK' if checks['steel_stress']['ok'] else 'FAIL'}")
```

## 📚 Documentation

Full documentation is available at [opensection.readthedocs.io](https://opensection.readthedocs.io)

- [User Guide](https://opensection.readthedocs.io/en/latest/user_guide/index.html)
- [API Reference](https://opensection.readthedocs.io/en/latest/api/index.html)
- [Examples](https://opensection.readthedocs.io/en/latest/examples/index.html)
- [Theory](https://opensection.readthedocs.io/en/latest/theory/index.html)

## 💡 Examples

Check out the [examples](examples/) directory for more detailed use cases:

- [Basic section analysis](examples/example_basic.py)
- [Interaction diagrams](examples/example_interaction_diagram.py)
- [Custom sections](examples/example_custom_sections.py)
- [Biaxial bending](examples/example_biaxial_bending.py)
- [Circular columns](examples/example_circular_column.py)
- [T-beam design](examples/example_t_beam_design.py)

## 🛠️ Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/Pavlishenku/opensection.git
cd opensection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opensection --cov-report=html

# Run specific test file
pytest tests/test_geometry.py
```

### Code quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Code of conduct
- Development process
- Submitting pull requests
- Coding standards
- Testing requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for open-source structural design tools
- Based on Eurocode 2 (EN 1992-1-1) specifications
- Built with NumPy and Matplotlib

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/Pavlishenku/opensection/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Pavlishenku/opensection/discussions)

## 🗺️ Roadmap

- [x] Basic section analysis (EC2)
- [x] Interaction diagrams
- [ ] Support for ACI 318 (US code)
- [ ] Support for GB 50010 (Chinese code)
- [ ] Time-dependent effects (creep, shrinkage)
- [ ] Crack width calculations
- [ ] Deflection analysis
- [ ] Web interface
- [ ] CAD integration (DXF import/export)

## 📖 Citation

If you use opensection in academic work, please cite:

```bibtex
@software{opensection2025,
  author = {opensection Contributors},
  title = {opensection: Professional Concrete Section Analysis},
  year = {2025},
  url = {https://github.com/Pavlishenku/opensection},
  version = {1.0.0}
}
```

---

<div align="center">

**Made with ❤️ by the opensection community**

[⭐ Star us on GitHub](https://github.com/Pavlishenku/opensection) | [📖 Read the docs](https://opensection.readthedocs.io) | [💬 Join the discussion](https://github.com/Pavlishenku/opensection/discussions)

</div>
