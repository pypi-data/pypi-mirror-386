# Changelog

All notable changes to the Streamlit Lightweight Charts Pro project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2025-10-22

### Fixed
- **TrendFill Series Line Width Rendering:**
  - Fixed pixel ratio scaling for TrendFill line widths
  - Changed from vertical pixel ratio (`vRatio`) to horizontal pixel ratio (`hRatio`)
  - Now correctly renders `line_width=1` as 1px instead of 2px
  - Affects uptrend, downtrend, and base lines (3 locations in TrendFillPrimitive.ts)
  - Verified Band, Ribbon, and GradientRibbon primitives already use correct `hRatio`

- **React Double-Render Bug:**
  - Fixed critical bug where series were being created twice with different values
  - Root cause: `initializeCharts` was always called with `isInitialRender=true`
  - Solution: Changed to `initializeCharts(isInitializedRef.current === false)`
  - Prevents duplicate series creation and ensures cleanup runs properly
  - Fixes issue where Python custom values were being overwritten by defaults

- **Test Suite Consistency:**
  - Fixed BandPrimitive test property names (`upperFillVisible` → `upperFill`, `lowerFillVisible` → `lowerFill`)
  - Updated Band series JSON structure tests for flattened LineOptions format
  - Fixed 6 test assertions expecting nested structure instead of flat properties
  - All 534 Python unit tests now passing

- **Code Quality:**
  - Fixed 24 unused variable assignments across test files
  - Fixed 2 quote style inconsistencies in Python code
  - Removed all debug `console.log` statements from production code
  - Auto-fixed with Ruff linter

### Added
- **Comprehensive Visual Regression Tests:**
  - Added 13 new visual tests for custom series (total now 94 tests)
  - **Ribbon Series (5 tests):**
    - `ribbon-thin-lines` - Line width validation (1px)
    - `ribbon-thick-lines` - Line width validation (4px)
    - `ribbon-upper-line-hidden` - Upper line visibility toggle
    - `ribbon-lower-line-hidden` - Lower line visibility toggle
    - `ribbon-lines-hidden` - Fill-only rendering
  - **GradientRibbon Series (5 tests):**
    - `gradient-ribbon-thin-lines` - Line width validation (1px)
    - `gradient-ribbon-thick-lines` - Line width validation (4px)
    - `gradient-ribbon-upper-line-hidden` - Upper line visibility
    - `gradient-ribbon-lower-line-hidden` - Lower line visibility
    - `gradient-ribbon-lines-hidden` - Gradient fill-only rendering
  - **Signal Series (3 tests):**
    - `signal-high-opacity` - High opacity color validation (0.5-0.6 alpha)
    - `signal-low-opacity` - Low opacity color validation (0.05 alpha)
    - `signal-monochrome` - Monochrome palette validation

### Changed
- **Code Quality Improvements:**
  - Ran full code review and cleanup of both Python and frontend codebases
  - Applied Ruff formatting to all Python files (1 file reformatted)
  - Applied Prettier formatting to all frontend files (all 175 files already formatted)
  - Zero linting errors across entire codebase

### Technical Details
- **Test Coverage:** 3800+ tests passing (534 Python, 3266+ Frontend)
- **Visual Tests:** 94 comprehensive snapshot tests for all series types
- **Security:** 0 vulnerabilities (npm audit clean)
- **Build:** Production build verified (813.65 kB raw, 221.37 kB gzipped)
- **Code Quality:** 100% linter compliance (Ruff + ESLint + TypeScript)
- **Pixel Ratio Consistency:** All primitives now use `hRatio` for line width scaling

## [0.1.4] - 2025-10-21

### Fixed
- **Series Settings Dialog:**
  - Fixed tab rendering issues in SeriesSettingsDialog
  - Tabs now display properly as clickable buttons instead of plain text
  - Added CSS `!important` flags to ensure proper tab styling
  - Fixed tab colors: gray (#787b86) for inactive, dark (#131722) for active
  - Fixed active tab indicator with blue underline (#2962ff)
  - Improved tab hover effects and transitions

- **Property Consistency:**
  - Fixed Python ↔ Frontend property flow for all series types
  - Ensured all SeriesOptionsCommon properties are correctly passed from Python to Frontend
  - Fixed `visible`, `displayName`, and other standard properties for Signal series
  - Added hidden properties (zIndex, priceLineSource, etc.) to STANDARD_SERIES_PROPERTIES
  - Fixed property preservation during dialog updates

- **Code Quality:**
  - Fixed 10 Python linting errors with Ruff
  - Reformatted Python codebase for consistency
  - Fixed CSS duplicate rules in seriesConfigDialog.css
  - Cleaned up all ESLint warnings and auto-fixed issues

### Changed
- **UI Improvements:**
  - Removed "Defaults" button from Series Settings Dialog footer
  - Simplified dialog footer layout (buttons now right-aligned)
  - Cleaner, more streamlined dialog interface
  - Reduced bundle size by 0.89 kB (804.74 kB → 218.85 kB gzipped)

- **Documentation:**
  - Consolidated `.cursor/rules` from 20 files to 7 organized files (65% reduction)
  - All rule files now use `.mdc` extension
  - Removed `_archive/` directory for cleaner structure
  - Created comprehensive navigation with `00-README.mdc`
  - Added full Python ↔ Frontend property consistency guide (26KB in `01-PYTHON-DEVELOPMENT.mdc`)

- **Build & Deployment:**
  - Production build optimized and verified
  - All code formatted with Prettier and ESLint

### Technical Details
- **Frontend Bundle:** 804.74 kB raw, 218.85 kB gzipped
- **Modules Transformed:** 246
- **Code Quality:** ESLint + Prettier + Ruff formatting applied
- **Documentation:** 7 consolidated rule files in `.cursor/rules/`

## [0.1.2] - 2025-10-15

### Added
- **React 19 Migration:**
  - Upgraded to React 19.1.1 with full concurrent features support
  - Implemented useTransition for smooth non-blocking chart updates
  - Added useOptimistic hook for instant UI feedback with server rollback
  - Integrated useActionState for advanced form state management
  - Enhanced ref patterns with automatic cleanup to prevent memory leaks
  - Added Form Actions with server integration and progressive enhancement
  - Implemented Document Metadata management for SEO optimization
  - Created comprehensive performance monitoring for React 19 concurrent features
  - Built progressive loading strategies with priority queues and asset management
  - Enhanced Suspense integration with lazy loading optimization

- **Advanced Chart Features:**
  - Multi-pane charts with integrated legends and range switchers
  - Dynamic legend functionality with real-time value updates
  - Enhanced range switcher with data timespan filtering
  - Session state management for persistent chart configurations
  - Automatic key generation for improved component lifecycle management
  - Gradient ribbon series with advanced rendering
  - Enhanced signal series implementation with improved visuals

- **Testing Infrastructure:**
  - Added Playwright E2E testing framework with visual regression tests
  - Implemented comprehensive visual testing with node-canvas
  - Created 119 visual regression tests for all series types
  - Added 108 E2E tests with browser automation
  - Enhanced test utilities with centralized mock factories
  - Added test data generators for deterministic testing
  - Implemented visual diff generation for failed tests

- **Developer Experience:**
  - Added ESLint configuration with comprehensive rules
  - Implemented pre-commit hooks for code quality enforcement
  - Created code quality scripts for automated checks
  - Enhanced documentation with architecture guides
  - Added performance monitoring and profiling tools
  - Implemented intelligent caching for chart data
  - Created background task scheduler with priority queues

- **New Components & Utilities:**
  - ChartProfiler with DevTools integration
  - ChartSuspenseWrapper for better loading states
  - ProgressiveChartLoader with priority-based loading
  - ChartFormActions with server-integrated forms
  - react19PerformanceMonitor for comprehensive tracking
  - Asset loader for intelligent resource management
  - Chart scheduler for background task processing

### Fixed
- **Test Suite Improvements:**
  - Fixed 46+ test implementation bugs across frontend test suite
  - Improved test pass rate from ~504 tests to 736/782 passing (94% pass rate)
  - Fixed color case sensitivity test expectations (lowercase hex colors)
  - Fixed logger console method spies (debug/info/warn/error)
  - Fixed React19 performance monitor console spy expectations
  - Added console.debug polyfill for Node.js test environment
  - Fixed ResizeObserverManager test environment (added jsdom pragma)
  - Fixed Jest-DOM integration for Vitest compatibility
  - Fixed Streamlit API mock lifecycle and stability
  - Fixed SeriesSettingsDialog hook mocks (added missing methods)

- **Critical Bug Fixes:**
  - Fixed padding issue causing constant chart re-rendering
  - Fixed pane collapse functionality with widget-based approach
  - Resolved chart re-initialization issues with session state
  - Fixed gradient ribbon rendering logic
  - Improved error handling and validation messages for data types
  - Fixed TypeScript compatibility issues with React 19
  - Resolved ESLint warnings for production-ready code quality

### Changed
- **Code Quality:**
  - Updated frontend test imports to use explicit Vitest imports
  - Improved mock management to preserve stable references between tests
  - Enhanced test documentation and error messages
  - Refactored series systems for better maintainability
  - Streamlined codebase by removing obsolete files
  - Improved error messages for better debugging experience
  - Enhanced TypeScript type safety across components

- **Build & Configuration:**
  - Updated Vite configuration for optimal UMD bundling
  - Enhanced package.json with new scripts and dependencies
  - Updated build configuration for Streamlit compatibility
  - Improved pre-commit workflow for better user experience
  - Optimized frontend build process with code splitting

### Removed
- Removed obsolete TrendFillRenderer and test files
- Cleaned up temporary ribbon series test harness
- Removed debug console files from production builds
- Eliminated gradient band support in favor of gradient ribbon
- Removed deprecated component implementations

## [0.1.0] - 2024-01-15

### Added
- Initial release of Streamlit Lightweight Charts Pro
- Professional-grade financial charting for Streamlit applications
- Built on TradingView's lightweight-charts library
- **Core Features:**
  - Interactive financial charts (candlestick, line, area, bar, histogram, baseline)
  - Fluent API with method chaining for intuitive chart creation
  - Multi-pane synchronized charts with multiple series
  - Advanced trade visualization with markers and P&L display
  - Comprehensive annotation system with text, arrows, and shapes
  - Responsive design with auto-sizing capabilities
- **Advanced Features:**
  - Price-volume chart combinations
  - Professional time range switchers (1D, 1W, 1M, 3M, 6M, 1Y, ALL)
  - Custom styling and theming support
  - Seamless pandas DataFrame integration
- **Developer Experience:**
  - Type-safe API with comprehensive type hints
  - 450+ unit tests with 95%+ coverage
  - Professional logging and error handling
  - CLI tools for development and deployment
  - Production-ready build system with frontend asset management
- **Performance Optimizations:**
  - Optimized React frontend with ResizeObserver
  - Efficient data serialization for large datasets
  - Bundle optimization and code splitting
- **Documentation:**
  - Comprehensive API documentation
  - Multiple usage examples and tutorials
  - Installation and setup guides

### Technical Details
- **Python Compatibility:** 3.7+
- **Dependencies:** Streamlit ≥1.0, pandas ≥1.0, numpy ≥1.19
- **Frontend:** React 18, TypeScript, TradingView Lightweight Charts 5.0
- **Build System:** Modern Python packaging with automated frontend builds
- **Testing:** pytest with comprehensive test coverage
- **Code Quality:** Black formatting, type hints, and linting compliance

### Architecture
- Bi-directional Streamlit component with Python API and React frontend
- Proper component lifecycle management and cleanup
- Theme-aware styling for light/dark mode compatibility
- Advanced height reporting with loop prevention
- Comprehensive error boundaries and logging

[0.1.4]: https://github.com/nandkapadia/streamlit-lightweight-charts-pro/releases/tag/v0.1.4
[0.1.0]: https://github.com/nandkapadia/streamlit-lightweight-charts-pro/releases/tag/v0.1.0
