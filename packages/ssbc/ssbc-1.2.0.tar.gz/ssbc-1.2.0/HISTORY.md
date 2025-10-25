# History

## 1.2.0 (2025-01-27)

### Code Quality & Type Safety
- **Fixed all type checking issues** - Reduced from 47 to 0 type errors
- **Enhanced type annotations** across all modules for better IDE support and code reliability
- **Improved test coverage** with proper type assertions and error handling
- **Fixed CLI parameter validation** with proper type checking for mode parameters
- **Updated return type annotations** in LOO uncertainty quantification functions
- **Enhanced test robustness** with proper DataFrame vs tuple handling in conformal tests
- **Fixed import paths** in example notebooks for better compatibility
- **Improved error handling** in examples with proper null checks
- **Updated MCP test server** with proper type annotations and arithmetic operations

### Technical Improvements
- Added comprehensive type checking with `ty` tool integration
- Enhanced code quality with proper type hints throughout codebase
- Improved test reliability with type-safe assertions
- Better error handling and validation across all modules
- Enhanced developer experience with better IDE support
- Fixed CI import sorting issues for robust continuous integration

## 1.1.2 (2025-01-27)

### Documentation Infrastructure
- Fixed ReadTheDocs build configuration and output directory
- Resolved MyST parser and theme dependency issues
- Added comprehensive API documentation with organized module sections
- Enabled full markdown support for installation, usage, and theory guides
- Professional ReadTheDocs theme with complete navigation

## 1.1.1 (2025-01-27)

### Documentation Improvements
- Fixed ReadTheDocs package index generation
- Added proper Sphinx autodoc configuration
- Organized API reference with logical module groupings
- Enabled comprehensive documentation for all 14 modules

## 1.1.0 (2025-10-15)

### Major Features

* Added **bootstrap calibration uncertainty analysis** for understanding recalibration variability
* Added **cross-conformal validation** (K-fold) for finite-sample diagnostics
* Added **validation module** for empirical PAC bounds verification
* Added **unified workflow** via `generate_rigorous_pac_report()` integrating all uncertainty analyses

### API Changes (BREAKING)

* Removed deprecated `sla.py` module and old operational bounds API:
  - Removed `compute_mondrian_operational_bounds()`
  - Removed `compute_marginal_operational_bounds()`
  - Removed `OperationalRateBounds` and `OperationalRateBoundsResult`
* Replaced with rigorous PAC-controlled operational bounds via `generate_rigorous_pac_report()`
* New bounds use LOO-CV + Clopper-Pearson for proper estimation uncertainty

### Internal Improvements

* Removed dead code modules: `coverage_distribution.py` (1,400 lines), `blakers_confidence_interval.py` (388 lines)
* Added comprehensive test suite: 90+ new tests across 6 new test files
* Test coverage improved from ~45% to 77%
* All code now passes ruff linting and ty type checking
* Examples directory cleaned and fully integrated into linting workflow

### Migration Guide

```python
# OLD (v1.0.0 and earlier)
from ssbc import compute_mondrian_operational_bounds, compute_marginal_operational_bounds
bounds = compute_mondrian_operational_bounds(cal_result, labels, probs)

# NEW (v1.1.0)
from ssbc import generate_rigorous_pac_report
report = generate_rigorous_pac_report(labels, probs, alpha_target=0.10, delta=0.10)
pac_bounds = report['pac_bounds_class_0']
```

## 1.0.0 (2025-10-10)

* First stable release on PyPI.

## 0.1.0 (2025-10-10)

* Initial development release.
