# Changelog

All notable changes to MDemon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-25

### Added
- **Extended XYZ Reader**: Complete implementation of Extended XYZ format reader
  - Support for GPUMD and ASE Extended XYZ format
  - Automatic lattice type detection (orthogonal/triclinic)
  - Flexible Properties parsing (species, pos, mass, charge, vel, group)
  - Automatic element identification and mass lookup
  - XYZWriter for exporting data
- **Comprehensive Documentation**:
  - File Reading Architecture Guide (`docs/file_reading_architecture.md`)
  - XYZ Reader Usage Guide (`docs/xyz_reader_guide.md`)
  - Detailed architecture explanation with examples
- **Examples**:
  - XYZ reader example script (`examples/xyz_reader_example.py`)
  - Complete test suite for XYZ reader

### Changed
- Updated README with XYZ format support information
- Improved code formatting with black and isort
- Enhanced reader module structure

### Technical Details
- Automatic reader registration via metaclass
- Seamless integration with existing Database system
- Support for both orthogonal and triclinic lattices
- Intelligent default values for optional properties

## [0.1.1] - 2024-XX-XX

### Added
- Initial release with LAMMPS and REAXFF readers
- RDF (Radial Distribution Function) analysis
- Angular distribution analysis
- Coordination number analysis
- Constants library (physics, chemistry, materials)
- Irradiation analysis tools (Waligorski-Zhang calculator)
- Cython-optimized distance calculations

### Features
- Support for LAMMPS DATA format
- Support for REAXFF bond format
- Physical and chemical constants database
- Unit conversion utilities
- Parallel computing support
- Material properties database

---

## Version Numbering

MDemon follows semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

[0.2.0]: https://github.com/IMPNanoLabMDTeam/MDemon/releases/tag/v0.2.0
[0.1.1]: https://github.com/IMPNanoLabMDTeam/MDemon/releases/tag/v0.1.1

