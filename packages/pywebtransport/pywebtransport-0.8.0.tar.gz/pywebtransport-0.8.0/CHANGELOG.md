# Changelog

All notable changes to PyWebTransport will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for future release

_(No planned changes for the next release yet.)_

## [0.8.0] - 2025-10-25

This is a major internal refactoring release focused entirely on improving **code health**, **maintainability**, and **testability** across the entire library in preparation for future API stabilization. It addresses significant architectural issues identified in a comprehensive code audit, primarily focusing on eliminating widespread code duplication and resolving complex dependency issues through systematic refactoring and the application of Dependency Injection (DI). While introducing numerous internal improvements and robustness fixes, this release also streamlines the public API surface by removing redundant or unsafe interfaces.

### BREAKING CHANGE

- **API Surface Reduction & Relocation**: Several previously exported components and utility functions have been removed from subpackage `__init__.py` files or the top-level `pywebtransport` namespace as part of the internal refactoring and API cleanup. Key changes include:
  - **Managers (`ConnectionManager`, `SessionManager`, `StreamManager`)** are now exclusively available via `from pywebtransport.manager import ...`.
  - **Pools (`ConnectionPool`, `SessionPool`, `StreamPool`)** are now exclusively available via `from pywebtransport.pool import ...`.
  - **Monitors (`ClientMonitor`, `ServerMonitor`, `DatagramMonitor`)** are now exclusively available via `from pywebtransport.monitor import ...`.
  - The `client` subpackage's `ClientPool` has been **renamed** to `ClientFleet`.
  - The buggy `client.PooledClient` has been **removed** and replaced by the robust `pool.SessionPool`.
  - Internal helper classes (like `StreamBuffer`) and application-level utilities (like `server.utils.create_development_server`, `stream.utils.echo_stream`) are no longer exposed.
  - Low-level types (like `EventType`, `ConnectionState`, etc.) and specific exceptions are no longer exported from the top-level `pywebtransport` namespace and must be imported from their respective modules (e.g., `pywebtransport.types`, `pywebtransport.exceptions`).
- **Configuration API Simplification**: The redundant `ConfigBuilder` class and `merge()` methods on `ClientConfig` and `ServerConfig` have been removed. Use standard `dataclass` initialization, `from_dict()`, or `update()` instead. The generic `.create()` factory methods on config classes have also been removed; use direct initialization or specific `create_for_*()` methods.
- **Diagnostic API Unification**: Multiple disparate methods for fetching statistics and debugging state (e.g., `get_summary()`, `debug_state()`, `diagnose_issues()`, `get_server_stats()`, `monitor_health()`) across core components (`WebTransportConnection`, `WebTransportSession`, `WebTransportStream`, `WebTransportDatagramTransport`, `WebTransportClient`, `WebTransportServer`) have been removed. Use the new unified `.diagnostics` property or `diagnostics()` async method, which return structured `dataclass` objects (`ConnectionDiagnostics`, `SessionDiagnostics`, etc.).
- **Factory Method Removal**: Redundant `.create()` class factory methods have been removed from many utility and higher-level components (`DatagramBroadcaster`, `ServerCluster`, `ConnectionLoadBalancer`, `ReconnectingClient`, `WebTransportBrowser`, etc.). Use direct class instantiation instead.
- **Heartbeat API Change**: `WebTransportDatagramTransport.start_heartbeat()` has been replaced by `enable_heartbeat()` and `disable_heartbeat()` for better lifecycle management.

### Added

- **New Base Classes for Code Reuse**: Introduced internal base classes (`_BaseResourceManager`, `_AsyncObjectPool`, `_BaseMonitor`, `_BaseDataclassSerializer`) to encapsulate common logic for managers, pools, monitors, and serializers respectively, significantly reducing code duplication.
- **New Internal Modules**: Added several new internal modules resulting from architectural refactoring (e.g., `client._proxy`, `protocol._pending_event_manager`, `protocol._session_tracker`, `protocol._stream_tracker`).
- **Unified Diagnostic Data Classes**: Introduced new `dataclasses` (e.g., `ConnectionDiagnostics`, `SessionDiagnostics`, `DatagramTransportDiagnostics`, `ServerDiagnostics`, `ClientDiagnostics`) returned by the unified `.diagnostics` APIs.
- **Robustness Features**:
  - Added mandatory message size limits (`max_message_size`) to `StructuredStream` to prevent DoS attacks.
  - Added validation for unique types in the `registry` for `StructuredStream` and `StructuredDatagramTransport` to prevent configuration errors.

### Changed

- **Major Architectural Refactoring (DRY & DI)**:
  - **Managers**: Refactored `ConnectionManager`, `SessionManager`, `StreamManager` to inherit from `_BaseResourceManager`, eliminating redundant code. Applied Dependency Injection (DI) to `StreamManager` (using a `stream_factory` callback) to break its circular dependency on `WebTransportSession` and improve testability.
  - **Pools**: Refactored `ConnectionPool` and `StreamPool` to inherit from the new, robust `_AsyncObjectPool` base class, fixing critical concurrency bugs and performance issues. Replaced `client.PooledClient` with a new `pool.SessionPool` based on `_AsyncObjectPool`. Applied DI to `StreamPool` (using `stream_manager`).
  - **Monitors**: Refactored `ClientMonitor`, `ServerMonitor`, `DatagramMonitor` to inherit from `_BaseMonitor`, eliminating redundant code.
  - **Protocol Handler**: Split the monolithic `WebTransportProtocolHandler` ("God Class") into a lean orchestrator and three specialized helper classes (`_ProtocolSessionTracker`, `_ProtocolStreamTracker`, `_PendingEventManager`), dramatically improving modularity, testability, and maintainability.
  - **Serializers**: Refactored `JSONSerializer` and `MsgPackSerializer` to inherit from `_BaseDatagramSerializer`, eliminating redundant dataclass conversion logic.
  - **Utilities**: Restructured utility functions, moving domain-specific helpers into their respective subpackages (e.g., URL parsing to `client.utils`) and removing application-level helpers from core library code (`server.utils`, `stream.utils`, `connection.utils`). The main `utils.py` was significantly streamlined.
  - **Core Components (DI & Testability)**: Applied Dependency Injection extensively to improve testability and reduce coupling in `WebTransportClient` (via `connection/session_factory`), `ReconnectingClient` (inject `WebTransportClient`), `WebTransportBrowser` (inject `WebTransportClient`), `ConnectionLoadBalancer` (via `connection_factory`/`health_checker`), `WebTransportSession` (removing service locator role), `RpcManager` (inject `WebTransportStream`), `PubSubManager` (inject `WebTransportStream`), and `WebTransportDatagramTransport` (via `datagram_sender` callback).
  - **Client Proxy Logic**: Extracted proxy handshake logic from `WebTransportConnection` into a dedicated internal module `client._proxy`.
- **API Unification & Cleanup**:
  - Standardized diagnostic reporting across core components using a unified `.diagnostics` API returning structured data classes.
  - Removed numerous redundant `.create()` class factory methods across the library.
  - Removed redundant or overlapping APIs like `ConfigBuilder`, `merge()`, unsafe `get_*_count()` methods, and unused components like `EventBus`.
  - Streamlined `__init__.py` files for the main package and subpackages to expose a cleaner, more focused public API.
- **Performance Improvements**:
  - Optimized stream data handling in `WebTransportH3Engine` using `collections.deque`.
  - Optimized `WebTransportReceiveStream.readuntil/readline` by avoiding byte-by-byte reading.
- **Robustness Enhancements**:
  - Improved the shutdown logic in `WebTransportSession` and `WebTransportServer` using `TaskGroup` and refined error handling.
  - Made `WebTransportSendStream._teardown` correctly `await` the cancelled writer task.
  - Made the `CONNECTION_LOST` event handling in `WebTransportConnection` more robust and decoupled (delegating close decision to listeners).
  - Improved readability, encapsulation, and resource handling within `ServerApp._handle_session_request`.
  - Improved `ServerApp` session rejection logic to correctly signal HTTP status codes (403/404) via the protocol handler.
  - Enhanced type safety in `ProtobufSerializer` checks and `server.router` path parameter handling.
- **Security Improvement**: Changed the default `ServerConfig.verify_mode` from `ssl.CERT_NONE` to the safer `ssl.CERT_OPTIONAL`.

### Fixed

- **Fixed Critical Concurrency Bugs**: Eliminated race conditions in all pooling mechanisms (`ConnectionPool`, `StreamPool`, replaced `PooledClient` with `SessionPool`) by migrating to the robust `_AsyncObjectPool` base class.
- **Fixed Critical Architectural Flaw**: Corrected `DatagramReliabilityLayer`'s violation of encapsulation by removing its dependency on private methods of `WebTransportDatagramTransport` and internalizing the framing logic.
- **Fixed Debuggability Issue**: Implemented correct `__repr__` methods for all custom exception classes.
- **Fixed Type Annotations**: Corrected inaccurate type hints (e.g., `EventHandler`).
- **Fixed Silent Failures**: Added validation to prevent silent failures in structured messaging registry configuration and unknown event type strings.
- **Fixed potential task leaks in `ServerApp`**: Ensured session handler tasks are explicitly tracked and cancelled during application shutdown.
- **Fixed potential `AssertionError` during connection closure**: Updated the required `aioquic` dependency to >= 1.3.0, incorporating an upstream fix for a race condition (`aioquic` issue #597) that could cause noisy errors (`cannot call reset() more than once`) in server logs.

### Removed

- **Removed Redundant Components**: Deleted `client/pooled.py` (replaced by `pool/SessionPool`), `server/utils.py`, `stream/utils.py`, `connection/utils.py`. Moved logic from `connection/manager.py`, `session/manager.py`, `stream/manager.py` to the new `manager/` package. Moved logic from `connection/pool.py`, `stream/pool.py` to the new `pool/` package. Moved logic from `client/monitor.py`, `server/monitor.py`, `datagram/monitor.py` to the new `monitor/` package.
- **Removed Redundant APIs**: Deleted `ConfigBuilder`, `merge()`, generic `.create()` factories, multiple old diagnostic methods, unsafe `get_*_count()` methods, `EventBus`, `event_handler`, `create_event_emitter`, `connection._transmit`, `datagram._receive/send_framed_data`, and various other internal or unused functions/methods identified during the audit.
- **Removed Dead Code**: Deleted numerous unused constants from `constants.py`.

## [0.7.1] - 2025-09-27

This is a hardening release focused on improving the stability and robustness of the RPC framework. It introduces a critical concurrency limiting feature and fixes a major bug in the request handling loop to enhance observability and prevent server overload.

### Added

- **Added a configurable concurrency limit to the RPC framework.** The new `rpc_concurrency_limit` option in `ClientConfig` and `ServerConfig` allows applications to control the maximum number of simultaneous incoming RPC requests, enhancing server stability and providing essential back-pressure against high request loads.

### Fixed

- **Fixed a critical bug in the RPC ingress loop** where all exceptions were silently swallowed. This ensures that unexpected errors are now correctly propagated and logged, significantly improving the framework's observability and robustness.

## [0.7.0] - 2025-09-26

This is a major feature release that introduces a high-level application protocol layer with built-in RPC and Publish/Subscribe frameworks. It also unifies the client-side proxy configuration to create a more consistent and powerful API. This version includes significant, repository-wide improvements to code style, type hint consistency, and test suite reliability.

### Added

- **Implemented a built-in RPC Framework** for high-performance, request-response communication. It features a JSON-RPC 2.0-like protocol over a dedicated bidirectional stream and a simple `session.rpc.call()` API.
- **Implemented a built-in Publish/Subscribe Framework** for efficient, channel-based messaging. It uses a simple text-based protocol over a dedicated stream and offers a Pythonic API with `async with` for subscriptions and `async for` for message consumption.
- **Added End-to-End Tests and API Documentation** for the new RPC and Pub/Sub frameworks.
- **Introduced a `.codecov.yml` configuration** to enforce code coverage thresholds.

### Changed

- **Unified the Client-Side Proxy Configuration**. The proxy settings are now integrated directly into `ClientConfig`, providing a single, consistent API. The old, separate `WebTransportProxy` component has been removed.
- **Enhanced Reliability of All Core Managers**. Refactored `ConnectionManager`, `SessionManager`, `StreamManager` with a "supervisor" pattern to ensure they shut down safely if a background task fails unexpectedly, preventing resource leaks and improving the stability of long-running applications.
- **Modernized Codebase with Python Best Practices**:
  - Standardized all module docstrings to the single-line format (PEP 257).
  - Enforced `-> None` return type annotation on all `__init__` methods (PEP 484).
  - Replaced legacy `typing.Type` with the modern built-in `type` generic (PEP 585).
  - Standardized the instantiation of all custom exception classes to use keyword arguments.
- **Improved Test Suite Rigor**. Enabled `strict` mode for `pytest-asyncio` to enforce explicit `@pytest.mark.asyncio` markers for all asynchronous tests and fixtures, eliminating ambiguity.

## [0.6.1] - 2025-09-20

This is a quality and hardening release focused on improving the core protocol handler's stability, refining the developer experience through documentation alignment, and ensuring the reliability of the CI/CD pipeline.

### Changed

- **Refined API Documentation and Examples**: Aligned all documentation (`README.md`, `quickstart.md`) and code examples to use the simplified top-level import path for `ConnectionError` and `SessionError`, improving usability and consistency.
- **Improved CI/CD Reliability**: Added necessary dependencies (`git`, `curl`, `gpg`) to the continuous integration workflow to harden the Codecov coverage reporting step and prevent intermittent failures.

### Fixed

- **Fixed Critical Resource Leak in Protocol Handler**: Resolved a major stability issue where a `StreamReset` on a data stream would not be properly cleaned up, preventing state and memory leaks in long-running applications.
- **Hardened Protocol Parsing**: The protocol handler now safely decodes `CLOSE_SESSION` reason strings containing invalid UTF-8 and uses a side-effect-free pattern for internal state checks, improving overall robustness.
- **Improved API Consistency**: Enhanced the `WebTransportDatagramTransport` by adding fail-fast initialization checks and wrapping unexpected internal errors in the documented `DatagramError` exception, creating a more predictable API.

## [0.6.0] - 2025-09-18

This is a critical protocol conformance release that aligns the library strictly with the `draft-ietf-webtrans-http3-13` standard. It resolves core interoperability issues with major WebTransport implementations and introduces essential mechanisms for production-grade reliability, such as session-level flow control and robust termination logic.

### BREAKING CHANGE

- **The entire datagrams API has been refactored for conceptual clarity.** The primary class `WebTransportDatagramDuplexStream` is renamed to `WebTransportDatagramTransport`. All related components (`DatagramBroadcaster`, `DatagramMonitor`, `DatagramReliabilityLayer`, `StructuredDatagramTransport`) and methods have been updated to use the "Transport" terminology, improving API consistency.

### Added

- **Implemented a complete, spec-compliant session-level flow control system.** This includes not only enforcing data and stream limits but also a **reactive credit management** mechanism that automatically issues `MAX_DATA` and `MAX_STREAMS` updates to prevent deadlocks, ensuring robust communication even with conservative initial settings.
- **Added a resource-limited buffering mechanism for out-of-order datagrams and streams** that arrive before their session is fully established, significantly improving connection reliability on complex networks.
- **Implemented the protocol-mandated mapping of 32-bit application error codes** to the reserved HTTP/3 error code space, enabling more granular and interoperable error signaling.

### Changed

- **Protocol Negotiation Mechanism**: Updated the HTTP/3 `SETTINGS` frame exchange to use the standardized `SETTINGS_WT_MAX_SESSIONS` parameter, replacing the obsolete `SETTINGS_ENABLE_WEBTRANSPORT`. This is the cornerstone for interoperability with modern clients and servers.
- **Session Termination**: `WebTransportSession.close()` now sends a `CLOSE_WEBTRANSPORT_SESSION` capsule for graceful shutdown, as required by the protocol, instead of relying on a simple stream reset.

### Fixed

- **Stream Reset Logic**: Ensured that upon session closure, all associated data streams are correctly reset with the `WT_SESSION_GONE` error code, fulfilling a key protocol requirement for clean resource teardown.
- **Test Suite Configuration**: Updated all relevant test clients (unit, integration, E2E, and performance) with the necessary flow control configurations. This corrects a fundamental flaw where tests would be improperly throttled, ensuring that all test results are now valid and accurate.

## [0.5.1] - 2025-09-11

This is a maintenance and quality-focused release that enhances the library's internal robustness and aligns the codebase with modern Python 3.11+ best practices. The primary enhancement is a comprehensive refactoring of `asyncio` event loop handling to use the more reliable `get_running_loop()` API, improving stability for production use cases.

### Changed

- **Modernized Asyncio Usage**: Systematically replaced all internal calls to the legacy `asyncio.get_event_loop()` with the modern `asyncio.get_running_loop()`. This change spans core components (`connection`, `utils`) and the test suite, hardening the library against potential concurrency issues and providing fail-fast behavior.
- **Improved Tooling and CI Configuration**:
  - Refined the `pytest` configuration in `pyproject.toml` to correctly execute the main E2E test suite while excluding individual, numbered test case files.
  - Removed the `isort` exclusion for `__init__.py` files to enforce a uniform import sorting style across the entire project.
  - Updated the Python 3.13 patch version in `.python-version` to align the CI environment with the latest security and bug fixes.

## [0.5.0] - 2025-09-10

This is a major feature release that significantly enhances the library's usability, performance, and resilience. It introduces three major new capabilities: a pluggable structured message layer for transmitting typed Python objects, a configurable client-side auto-reconnect strategy with exponential backoff, and selectable congestion control algorithms for performance tuning. This release also includes a comprehensive API standardization to enforce keyword-only arguments across the entire library, improving robustness and developer experience.

### BREAKING CHANGE

- **The entire public API of the library has been refactored to enforce keyword-only arguments.** Positional arguments in constructors and method calls are no longer supported and will raise a `TypeError`. All user code must be updated to use keyword arguments.
- **The `MiddlewareProtocol` has been changed from a session processor that returns a session to a boolean validator.** Existing middleware implementations must be updated to conform to this new, simpler interface.
- **The `WebTransportConstants` class in the `constants.py` module has been removed.** All constants are now defined at the module level and must be imported directly (e.g., `from pywebtransport.constants import SOME_CONSTANT`).

### Added

- **Implemented a Structured Message Layer** for transmitting typed Python objects, which includes:
  - A pluggable `Serializer` abstraction with out-of-the-box support for **JSON**, **MsgPack**, and **Protobuf**.
  - `StructuredStream` and `StructuredDatagramStream` wrappers that add object-level `send()` and `receive()` capabilities.
  - New `WebTransportSession.create_structured_stream()` and `create_structured_datagram_stream()` factory methods for easy access.
- **Implemented a configurable client-side auto-reconnect strategy.** The client can now automatically recover from transient network failures using an exponential backoff policy, controlled via new `ClientConfig` parameters.
- **Implemented a congestion control algorithm selection.** Users can now choose the desired algorithm (e.g., 'cubic', 'reno') in `ClientConfig` and `ServerConfig` for performance tuning.

### Changed

- **Standardized the entire public API to enforce keyword-only arguments**, improving clarity and preventing common errors from incorrect argument order.
- **Refactored `WebTransportClient.create` into a factory method** that transparently returns a specialized `ReconnectingClient` when auto-reconnect is enabled, simplifying the user experience.
- **Refactored the `ReconnectingClient`** to be fully driven by `ClientConfig`, improving its lifecycle management and robustness.
- **Simplified the server-side `MiddlewareProtocol`** to be a boolean validator, making middleware implementation more straightforward.
- **Refactored the `constants` module** to use a flattened, module-level namespace for simpler and more direct imports.

## [0.4.1] - 2025-09-01

This is a critical stability and quality release focused on hardening the library for production use. It addresses deep-seated concurrency flaws in all pooling mechanisms, improves the robustness of the core protocol engine, enhances error handling and diagnostics, and continues the systematic modernization of the codebase.

### Added

- **Enhanced Error Diagnostics**: Added several specific H3 and QPACK error codes to the `ErrorCodes` enum, allowing for more granular and precise protocol-level error reporting.
- **Improved Test Coverage**: Significantly increased overall test coverage from 91% to 96%, enhancing the reliability and correctness of the entire library.

### Changed

- **Modernized Codebase Style**: Systematically modernized type hint imports across the entire codebase (including `app`, `events`, `middleware`, `session`, `stream`, `types`, and `utils` modules) by migrating from the `typing` module to `collections.abc` in accordance with Python 3.11+ best practices.

### Fixed

- **Fixed Critical Concurrency Flaws in All Pooling Mechanisms**:
  - Re-architected `client.PooledClient`, `connection.ConnectionPool`, and `stream.StreamPool` to use a robust **`asyncio.Condition`**-based pattern. This resolves fundamental correctness issues, properly enforces resource limits (`pool_size`/`max_size`), and eliminates performance bottlenecks caused by "thundering herd" problems in previous implementations.
- **Improved Robustness of the Core Protocol Engine**:
  - Fixed multiple correctness and robustness issues in the `WebTransportH3Engine`, including correctly handling the non-fatal `pylsqpack.StreamBlocked` signal, improving the logical flow of unidirectional stream parsing, and propagating more specific error codes.
- **Improved Error Handling Consistency and Usability**:
  - Fixed an issue in `ServerCluster` where exceptions during `stop_all` and `get_cluster_stats` were silently ignored; they are now correctly propagated as an `ExceptionGroup`.
  - Changed the string representation of all `WebTransportError` exceptions to display error codes in hexadecimal format for better readability and alignment with protocol specifications.
- **Fixed Silent Failure in `DatagramQueue`**:
  - The `clear()` method on an uninitialized `DatagramQueue` no longer fails silently and now correctly raises a `DatagramError`, ensuring consistent fail-fast behavior across the component's API.

## [0.4.0] - 2025-08-26

This is a major architectural release that marks a significant milestone in the library's maturity. The core of this update is the complete re-architecture of the protocol layer, replacing the generic, `aioquic`-derived H3 component with a specialized, in-house `WebTransportH3Engine`. This change dramatically improves maintainability, reduces complexity, and perfectly aligns the protocol implementation with the specific needs of WebTransport, solidifying the library's foundation as a truly independent and production-grade solution.

**Note on Versioning:** While originally slated as a patch release (`v0.3.2`), the complete re-architecture of the core protocol engine represents a major architectural milestone for the library. To accurately reflect the significance and value of this change, it has been designated as `v0.4.0`.

### Added

- **Exposed `StreamId` and `SessionId` in the Public API**:
  - The `StreamId` and `SessionId` type aliases are now available for direct import from the top-level `pywebtransport` package. This improves the developer experience for users employing type hinting in their applications.
- **Added Comprehensive Unit Tests for the New Protocol Engine**:
  - Implemented a robust and highly-structured test suite for the new `WebTransportH3Engine` and its associated events. The tests utilize extensive mocking and parametrization to ensure correctness, protocol compliance, and resilience against errors.

### Changed

- **Re-architected the Core Protocol Engine**:
  - Replaced the general-purpose `H3Connection` with `WebTransportH3Engine`, a new, purpose-built protocol engine exclusively designed for WebTransport-over-H3. This change removes all unnecessary HTTP/3 features (like Server Push), resulting in a simpler, more efficient, and highly maintainable codebase.
  - Decoupled the protocol layer from underlying `aioquic` types by introducing a dedicated internal event system (`pywebtransport.protocol.events`). The engine now emits library-native, structured events, creating a clean and stable abstraction boundary.
  - Improved internal API ergonomics by transitioning header representation from `list[tuple[bytes, bytes]]` to the more Pythonic `dict[str, str]`, simplifying the logic in the `WebTransportProtocolHandler`.

### Fixed

- **Improved Code Consistency in the Test Suite**:
  - Updated the test suites for `WebTransportProtocolHandler`, `WebTransportStream`, and `StreamManager` to align with the new protocol engine APIs and the newly exposed public types, ensuring the entire codebase follows a consistent and modern approach.

## [0.3.1] - 2025-08-25

This is a landmark release focused on solidifying the library's architecture for production use. It addresses deep-seated concurrency flaws, enhances performance across the entire stack, and systematically modernizes the codebase to align with the latest asynchronous best practices.

### Added

- **Enhanced Testing Capability** by adding the `pytest-repeat` dependency, a powerful tool for identifying and fixing non-deterministic, flaky tests in complex asynchronous code.

### Changed

- **Refined CI/CD and Quality Assurance Infrastructure**:
  - Migrated the test coverage reporting and Codecov upload functionality from GitLab CI to GitHub Actions to consolidate quality checks for community contributions.
- **Modernized Concurrency Model across the Entire Library**:
  - Systematically refactored all concurrent operations (lifecycle management, cleanup, batch processing) in all high-level components to use the more robust **`asyncio.TaskGroup`** (Python 3.11+).
  - Re-architected the `WebTransportSendStream` to use a robust **producer-consumer pattern** with proper locking and events for writing data and handling backpressure.
- **Vastly Improved Concurrency Performance**:
  - Re-architected `ConnectionPool` and `PooledClient` from a single global lock to a highly concurrent **per-key locking mechanism**, eliminating a major performance bottleneck when handling multiple endpoints.
  - Drastically improved the performance of all manager classes (`ConnectionManager`, `SessionManager`, `StreamManager`) by making their periodic cleanup operations **atomic and efficient** with a single-lock strategy.
  - Optimized the `ConnectionLoadBalancer`'s health checks and the `StreamPool`'s filling mechanism by making them **fully concurrent**.
  - Made the `DatagramReliabilityLayer`'s retry mechanism concurrent for faster recovery from packet loss.
- **Modernized Codebase Style**:
  - Upgraded all `Enum` classes to **`StrEnum`** and simplified all dependent code by removing redundant `.value` calls, improving ergonomics.
  - Modernized conditional logic throughout the codebase to use **`match-case`** syntax for improved clarity and readability.
- **Updated Test Suites and Documentation**:
  - Comprehensively updated the entire test suite (unit, integration, E2E) and API documentation to align with the extensive architectural refactoring and ensure full coverage of the new concurrency models and fixed behaviors.

### Fixed

- **Fixed Critical Race Conditions in Core Protocol Handling**:
  - Eliminated a major stability issue in the low-level QUIC event processing loop (for both client and server) by implementing a robust, ordered **`asyncio.Queue`-based pipeline**, which replaced a fragile "fire-and-forget" task creation model. This change ensures strict event ordering, which, after performance evaluation, was proven to be more stable and performant than a parallelized model for this specific workload.
  - Fixed a race condition in the protocol handler's `StreamReset` processing by ensuring it is handled synchronously before other events.
  - Resolved a race condition where data on a new stream could be discarded. The protocol handler now reliably associates new streams by **correctly using the parent session context already provided in H3 protocol events**.
- **Fixed Critical Concurrency Bugs in High-Level Components**:
  - Resolved a severe **"thundering herd"** problem in `ConnectionLoadBalancer`, `ConnectionPool`, and `PooledClient` that caused redundant, wasteful resource creation under concurrent demand.
  - Fixed a critical concurrency flaw in the `DatagramReliabilityLayer` by adding proper `asyncio.Lock` protection for all shared state.
- **Fixed Major Resource and Stability Issues**:
  - Fixed a critical stability issue in `StreamBuffer` by replacing a fragile recursive implementation with a robust iterative one, preventing potential `RecursionError` crashes.
  - Fixed major bugs in the bidirectional `WebTransportStream` implementation that caused resource leaks and incomplete initialization.
  - Fixed a potential resource leak in `ServerCluster` by ensuring server instances are cleaned up correctly if startup fails.

## [0.3.0] - 2025-08-18

This is a major release focused on production-readiness, significantly enhancing the library's robustness, resource management, performance, and configurability.

**Note on Versioning:**
While building the performance test suite for v0.2.2, we discovered a series of deep-seated resource management and robustness defects. As ensuring the library's stability in production environments is paramount, we decided to prioritize addressing these issues over the originally planned functional refactoring and release the fixes as version v0.3.0.

### BREAKING CHANGE

- **The `StreamManager` now fails immediately if the stream limit is reached.** Previously, an attempt to create a stream beyond the configured limit would block indefinitely. It now raises a `StreamError`, making resource exhaustion explicit and allowing applications to handle it gracefully.
- **`WebTransportSession.close()` now closes the underlying `WebTransportConnection` by default.** This provides a more intuitive default behavior. To close only the session without terminating the connection, use `session.close(close_connection=False)`.

### Added

- **Implemented a server-side idle connection timeout.** The server can now be configured to automatically close connections that have been inactive for a specified duration, a critical feature for production environments.
- **Introduced a performance-oriented "fire-and-forget" write mode.** The `WebTransportSendStream.write()` method now accepts a `wait_flush=False` parameter to allow high-throughput applications to buffer data without waiting for network I/O on every call.
- **Added a new `CONNECTION_CLOSED` event** to distinguish graceful connection closures from unexpected losses (`CONNECTION_LOST`), enabling more precise lifecycle management.
- **Added a comprehensive integration test suite** to validate the end-to-end behavior of the client, server, and application framework.
- **Added a new performance test suite** to measure and benchmark key metrics like connection latency, stream throughput, and resource usage.

### Changed

- **Overhauled the resource management architecture to be event-driven.** Managers (`ConnectionManager`, `SessionManager`) now use event listeners and `weakref` to clean up closed resources almost instantaneously, replacing the less efficient polling mechanism and improving responsiveness.
- **Enhanced the entire configuration system.** The `ClientConfig` and `ServerConfig` objects now include a wide range of new, fully validated parameters. This configuration is now correctly propagated from the top-level client/server down to every new session and stream.
- **Refactored background task management.** Responsibility for periodic cleanup and idle checks has been delegated from the main `WebTransportServer` to the specialized `ConnectionManager` and `SessionManager` components, improving architectural separation of concerns.
- **Updated API documentation** for 13 core components to reflect the new features, lifecycle behaviors, and configuration options.

### Fixed

- **Fixed a critical memory leak** in the protocol handler caused by a circular reference between the `WebTransportConnection` and `WebTransportProtocolHandler` objects.
- **Fixed a severe resource leak** in the `StreamManager` where the `asyncio.Semaphore` controlling the stream limit was not released upon shutdown, which could lead to deadlocks.
- **Eliminated "zombie sessions"** by correctly linking the `WebTransportSession` lifecycle to its parent `WebTransportConnection`. Sessions are now automatically cleaned up when the underlying connection is lost or closed.
- **Fixed a bug in the CI/CD pipeline** that caused inaccurate code coverage reporting for parallel test jobs.
- **Fixed bugs in the client and server application layers** where configuration values from `ClientConfig` and `ServerConfig` were not being correctly applied to new connections and sessions.

## [0.2.1] - 2025-08-07

This is a patch release focused on improving the reliability of the protocol handler and the CI/CD pipeline.

### Changed

- **Hardened the CI/CD pipeline** by fixing parallel coverage reporting, resolving Codecov repository detection issues, and ensuring the GitHub sync step is more robust.
- **Refined development dependencies** by removing `pre-commit` from the core dev setup and updated the `dev-requirements.txt` lock file.
- **Improved package metadata** in `pyproject.toml` for better discoverability on PyPI.

### Fixed

- **Eliminated race condition warnings during session shutdown.** A race condition that occurred during rapid connection teardown would cause false positive warnings for late-arriving packets (both datagrams and streams). The handler now correctly and silently drops these packets, aligning with best practices and improving log clarity.

## [0.2.0] - 2025-08-06

This is a major release focused on enhancing runtime safety and modernizing the library for Python 3.11 and newer. It introduces significant, backward-incompatible changes to the asynchronous object lifecycle.

### BREAKING CHANGE

- Core components (e.g., Streams, Managers, Pools) now require activation via an `async with` block or a dedicated factory. Direct instantiation and use without proper initialization will raise a runtime error. This change is fundamental to ensuring runtime safety and event loop independence.

### Added

- Integrated `pip-tools` to manage and lock development dependencies, ensuring fully reproducible environments.

### Changed

- **Upgraded the minimum required Python version from 3.8 to 3.11.**
- Modernized the entire codebase to use modern type hint syntax (`X | Y`, built-in generics, `typing.Self`) available in Python 3.11+.
- Refactored all core components to defer the initialization of `asyncio` primitives until runtime, decoupling object instantiation from a running event loop.
- Introduced an `initialize()` pattern for resource-like objects (Streams, Sessions) to restore a convenient "get-and-use" API while maintaining runtime safety.
- Updated project documentation, including user guides, the API reference (`docs/`), and the contributor guide (`CONTRIBUTING.md`), to reflect the new asynchronous object lifecycle and initialization patterns.
- Overhauled the unit test suite to use asynchronous fixtures, aligning with the new component lifecycle contracts.
- Refactored CI/CD pipelines to use the locked `dev-requirements.txt` for improved reliability and efficiency.
- Consolidated development tool configurations (e.g., from `tox.ini`) into `pyproject.toml`.

### Fixed

- Eliminated a critical race condition by atomically delivering the first data payload with the stream opening event, preventing data loss.
- Resolved a lifecycle violation in the server application framework where sessions were not being properly initialized.
- Replaced the deprecated `datetime.utcnow()` with the timezone-aware `datetime.now(timezone.utc)`.
- Corrected improper `await` usage for asynchronous properties throughout the test suite.

## [0.1.2] - 2025-07-30

### Added

- Introduced a `DeprecationWarning` for Python versions below 3.11, signaling the planned removal of support in v0.2.0.
- Integrated `tox` and `pyenv` configurations to streamline the development and testing workflow for contributors.

### Changed

- Refactored internal module imports to use absolute paths, improving code structure and maintainability.
- Enhanced code quality by resolving all MyPy warnings within the test suite.

### Fixed

- Corrected an issue in the CI pipeline that prevented code coverage reports from being displayed correctly.

## [0.1.1] - 2025-07-28

### Added

- A robust, end-to-end CI/CD pipeline for automated testing, coverage reporting, and deployment.
- A public-facing CI workflow on GitHub Actions for pull request validation and build status badges.

### Changed

- Refactored unit tests to be independent of hardcoded version strings, improving maintainability.

## [0.1.0] - 2025-07-27

### Added

- Implemented the core WebTransport protocol over HTTP/3 and QUIC.
- Added a high-level `ServerApp` with path-based routing and middleware capabilities.
- Added a high-level asynchronous `WebTransportClient` for establishing and managing connections.
- Implemented a robust `WebTransportSession` class to encapsulate stream and datagram operations.
- Added support for bidirectional (`WebTransportStream`) and unidirectional (`WebTransportSendStream`, `WebTransportReceiveStream`) streams.
- Added support for sending and receiving unreliable datagrams for low-latency communication.
- Implemented connection pooling utilities, available via `pywebtransport.client.ClientPool`.
- Implemented a connection load balancer, available via `pywebtransport.connection.ConnectionLoadBalancer`.
- Introduced a flexible configuration system with `ClientConfig` and `ServerConfig`.
- Added built-in utilities for SSL/TLS certificate handling and generation of self-signed certificates.
- Implemented performance statistics collection for client and server monitoring.
- Provided a comprehensive logging infrastructure for debugging purposes.
- Ensured full `async/await` API support with complete type annotations.
- Established cross-platform compatibility for Python 3.8 and newer.

### Dependencies

- aioquic (>=1.2.0,<2.0.0) for QUIC protocol support
- cryptography (>=45.0.4,<46.0.0) for SSL/TLS operations
- typing-extensions (>=4.14.0,<5.0.0) for Python <3.10 support

[Unreleased]: https://github.com/lemonsterfy/pywebtransport/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/lemonsterfy/pywebtransport/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/lemonsterfy/pywebtransport/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/lemonsterfy/pywebtransport/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/lemonsterfy/pywebtransport/releases/tag/v0.1.0
