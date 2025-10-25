# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.9] - 2024-10-24

### Added
- **tiktoken Dependency**: Added `tiktoken>=0.5.0` as core dependency for accurate token counting in HTTP interceptor

### Removed
- **traceloop-sdk**: Removed from optional dependencies to reduce package conflicts and simplify installation

### Fixed
- **Dependency Management**: Ensured all external packages used in ai_monitor are properly declared in requirements

## [1.0.8] - 2024-10-24

### Added
- **Cross-Machine Compatibility**: Enhanced decorator system with force HTTP monitoring setup to ensure consistent behavior across different servers
- **Debug Tools**: Added comprehensive debug utilities including `debug_setup()` function and test scripts
- **Enhanced Logging**: Improved decorator initialization logging with "🔧 [DECORATOR INIT]" messages for better troubleshooting
- **Debug Scripts**: Created `simple_debug.py` and `test_decorator_debug.py` for cross-machine testing
- **One-Liner Tests**: Added quick copy-paste debug commands for rapid server testing
- **Cross-Machine Debug Guide**: Comprehensive troubleshooting documentation in `CROSS_MACHINE_DEBUG.md`

### Fixed
- **Decorator Reliability**: Fixed issues where `@monitor_llm_call()` decorator would work locally but fail on other machines
- **HTTP Monitoring**: Ensured HTTP request patching is properly initialized within decorators
- **Import Order Issues**: Enhanced package initialization to handle various import sequences
- **Silent Failures**: Added extensive debug logging to identify why decorators fail to apply

### Enhanced
- **Decorator System**: Force-enables HTTP monitoring setup on every decorator call for maximum compatibility
- **Error Tracking**: Comprehensive logging throughout the monitoring chain for easier debugging
- **Package Exports**: Added debug utilities to main package exports for easier access

## [1.0.7] - 2024-10-24

### Added
- **Core Dependencies**: Added `httpx>=0.24.0` and `requests>=2.25.0` as required dependencies
- **Enhanced HTTP Monitoring**: Improved HTTPX client monitoring with better error handling

### Fixed
- **Dependency Issues**: Resolved missing httpx dependency causing import errors on clean installations
- **Token Calculation**: Fixed Azure OpenAI token calculation discrepancies

## [1.0.5] - 2024-10-23

### Fixed
- **Version Requirements**: Added + Corrected
Support for other open ai calls 
Calculation/Extraction of tokens

## [1.0.4] - 2024-10-15

### Fixed
- **Version Requirements**: Corrected opentelemetry-exporter-jaeger version requirement to >=1.21.0 (latest available)
- **Installation**: Fixed ai-monitor[all] installation by using correct dependency versions

## [1.0.3] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Removed traceloop-sdk from `ai-monitor[all]` to resolve googleapis-common-protos conflicts
- **Installation Options**: `ai-monitor[all]` now includes tracing, prometheus, and system monitoring without conflicts

### Changed
- Separated traceloop from the all-in-one installation option

## [1.0.2] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Updated OpenTelemetry to v1.22+ for full compatibility with Traceloop SDK
- **googleapis-common-protos**: Resolved protobuf version conflicts in ai-monitor[all] installation

### Changed
- Updated tracing dependencies to OpenTelemetry v1.22.0+ for better compatibility

## [1.0.1] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Resolved OpenTelemetry version conflicts between Jaeger and Traceloop
- **Installation Options**: Separated `tracing` (v1.20+) and `jaeger` (v1.15) optional dependencies
- **Compatibility**: Fixed `ai-monitor[all]` installation issues

### Changed
- Updated OpenTelemetry dependencies to compatible versions
- Added separate `jaeger` optional dependency for legacy Jaeger support

### Installation
```bash
# All features (now works without conflicts)
pip install ai-monitor[all]

# Specific tracing options
pip install ai-monitor[tracing]        # Modern Jaeger (v1.20+)
pip install ai-monitor[jaeger]         # Legacy Jaeger (v1.15)
```
- **Plug & Play Monitoring**: Zero-configuration monitoring for AI agents
- **HTTP Interception**: Automatic monitoring of OpenAI API calls
- **Quality Analysis**: Hallucination detection and drift analysis
- **Prometheus Metrics**: Comprehensive metrics export
- **OpenTelemetry Tracing**: Distributed tracing support
- **Traceloop Integration**: Enterprise-grade observability
- **Decorator API**: Easy-to-use decorators for monitoring
- **Context Managers**: Flexible monitoring contexts
- **Flask Integration**: One-line Flask app monitoring
- **Multi-Agent Support**: Monitor complex agent systems
- **LangChain Integration**: Seamless LangChain monitoring

### Features
- **Zero Source Code Changes**: Drop-in monitoring solution
- **Automatic LLM Detection**: Recognizes OpenAI, Anthropic, and custom APIs
- **Real-time Metrics**: Latency, tokens, costs, and quality scores
- **Comprehensive Tracing**: Request/response tracing with metadata
- **Quality Assurance**: Automated hallucination and drift detection
- **Multiple Export Options**: Prometheus, Jaeger, and Traceloop
- **System Metrics**: CPU, memory, and disk monitoring
- **Alert Integration**: Configurable thresholds and alerts

### Dependencies
- Core: `numpy>=1.20.0`
- Optional: Prometheus, OpenTelemetry, Traceloop SDK, psutil

### Installation
```bash
pip install ai-monitor
# For full features:
pip install ai-monitor[all]
```
