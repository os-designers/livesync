# CHANGELOG


## v0.3.9 (2025-01-30)

### Bug Fixes

- Safely changed to terminate the run
  ([`d2faa97`](https://github.com/os-designers/livesync/commit/d2faa97a1efac27523e3bdad94e55a2cf274a61b))

- Safely changed to terminate the run
  ([`18815a4`](https://github.com/os-designers/livesync/commit/18815a410dee5ae8c52d3ed29ef61b726afae0d9))

- Safely changed to terminate the run
  ([`48fe808`](https://github.com/os-designers/livesync/commit/48fe808b7984b5955810a39255c45637209ddfba))

- Safely changed to terminate the run
  ([`632c2d9`](https://github.com/os-designers/livesync/commit/632c2d937c3a8c11c0f04ddffa94e7b2b4cf7f42))

- Safely changed to terminate the run
  ([`d8cf86e`](https://github.com/os-designers/livesync/commit/d8cf86e2750298f34a66d1cc476adfcd73f587f8))


## v0.3.8 (2025-01-29)

### Bug Fixes

- Change protobuf version
  ([`3b0c812`](https://github.com/os-designers/livesync/commit/3b0c812062b93df9beb138c12115d2482d0a5620))


## v0.3.7 (2025-01-28)

### Bug Fixes

- Add async init and replace remote layer with it
  ([`01f5d0c`](https://github.com/os-designers/livesync/commit/01f5d0ca7ddff4bf80b6083b971a035b90041742))

- Add async init and replace remote layer with it
  ([`3aa9915`](https://github.com/os-designers/livesync/commit/3aa99156bdc5967414a066f9b3e4835db3b54bc2))

### Chores

- Install beam
  ([`0f77ae1`](https://github.com/os-designers/livesync/commit/0f77ae139685dac50e5b6f4abaac0653e84b234a))

### Continuous Integration

- Add trigger for ci
  ([`29df264`](https://github.com/os-designers/livesync/commit/29df264f3f31f1a5aea4463dd20450f1b1c85361))

- Add trigger for ci
  ([`31cf517`](https://github.com/os-designers/livesync/commit/31cf517146fdd35c059e0ed5d05688cd3fc9b920))


## v0.3.6 (2025-01-28)

### Bug Fixes

- Remove initialization logging in remote layer
  ([`80d35e3`](https://github.com/os-designers/livesync/commit/80d35e3cd2bf94b8cc2ffc555d0120f9a4866c66))


## v0.3.5 (2025-01-27)

### Bug Fixes

- Improved initialization process to avoid repeated calls during frame processing in remote layer
  ([`d89d7ee`](https://github.com/os-designers/livesync/commit/d89d7eedc6581481b5d36311e39922d4ca39f677))


## v0.3.4 (2025-01-27)

### Bug Fixes

- Change media sync name
  ([`356d76f`](https://github.com/os-designers/livesync/commit/356d76feafef027273043b9e29f42ce5e5c0f5c6))

### Continuous Integration

- Add step for publising to PyPI
  ([`0549c04`](https://github.com/os-designers/livesync/commit/0549c04a9e6eb423774d551ee74f03dbcf6e84eb))


## v0.3.3 (2025-01-27)

### Bug Fixes

- Replace resolution control with video quality control
  ([`ec1be84`](https://github.com/os-designers/livesync/commit/ec1be84ebcf9ccd76014b469a25fc66c9ed9ae69))

### Chores

- Apply fix:ruff
  ([`afc285d`](https://github.com/os-designers/livesync/commit/afc285d3f92695745a4bd926b403ecb5db450996))

### Refactoring

- Replace resolution control with video quality control
  ([`ab88f60`](https://github.com/os-designers/livesync/commit/ab88f60d37f18fefbed1b9a9d5be5b6e7fb674ec))

- Update dashboard example to use video quality settings instead of fixed resolution - Rename
  ResolutionControlLayer to VideoQualityControlLayer - Modify UI to support broader range of quality
  presets - Update workflow and app to use new quality parameter - Remove deprecated
  resolution_control.py file


## v0.3.2 (2025-01-27)

### Bug Fixes

- Resolve type and sync issues in recorder layers
  ([`7c4d4fc`](https://github.com/os-designers/livesync/commit/7c4d4fc4395c87c1804c15d999723b18db401405))

### Chores

- Update release process with semantic-release and modify fps changes in docs and README.md
  ([`f928b58`](https://github.com/os-designers/livesync/commit/f928b58f9d9f5915c337a4cebdce059d62ec3ab6))

- Update release process with semantic-release and modify fps changes in docs and README.md
  ([`bb63e56`](https://github.com/os-designers/livesync/commit/bb63e5688f969080ceb08900980717d16b9bef71))

### Continuous Integration

- Change installment of semantic release
  ([`66035e5`](https://github.com/os-designers/livesync/commit/66035e54af0bbe4a9758984baefd2a3e0bb43028))

- Install rye before release
  ([`5c80934`](https://github.com/os-designers/livesync/commit/5c80934531fb7ccd0838af3adb1caa26cc409e20))

- Revery rye install for release
  ([`b98c41e`](https://github.com/os-designers/livesync/commit/b98c41e4ebdbf44da73927dd04c325ca3223fea8))

- Temporarily disable auto publishing
  ([`31f47ea`](https://github.com/os-designers/livesync/commit/31f47ea48d642cf377cd3ffca406d6cc9224d402))


## v0.3.1 (2025-01-23)

### Bug Fixes

- Remove unused pages
  ([`fad6d07`](https://github.com/os-designers/livesync/commit/fad6d07a7f8db310afe9cab5e7719e6fc5555568))

### Chores

- Bump version to 0.3.1
  ([`70cc6be`](https://github.com/os-designers/livesync/commit/70cc6beda928120779c176bc891f0b72c5644c0b))

### Refactoring

- Improve code readability and update protobuf definitions
  ([`becc852`](https://github.com/os-designers/livesync/commit/becc85203cd6daef72e530390a6c5654131e03ff))

- Enhance formatting in README.md for better clarity. - Refactor frame handling in remote server
  examples to improve readability. - Update protobuf DataType enum to include a NONE value and
  adjust related code for consistency. - Modify MediaStreamRecorderLayer to improve audio frame
  conversion. - Refactor RemoteLayer and RemoteLayerServicer to use BytesableType for better type
  handling. - Improve error handling and logging in remote layer processing.

These changes enhance the maintainability and clarity of the codebase while ensuring better type
  safety in remote processing.

- Update remote server handling and protobuf integration
  ([`0e668b5`](https://github.com/os-designers/livesync/commit/0e668b52524a943e282aa14a91fbc602a81eb488))

- Change the `on_call` function signature in remote server examples to accept `VideoFrame` directly
  instead of bytes. - Remove the `main_window.py` file and update imports in the dashboard
  application to use the new `ui` module. - Enhance the `CallRequest` and `CallResponse` messages in
  the protobuf definition to include a `DataType` field for better type handling. - Update the
  `RemoteLayerServicer` to process different data types based on the new protobuf structure,
  improving the handling of various media types. - Introduce structured error handling and logging
  in the remote layer processing.

This refactor improves the clarity and functionality of the remote processing architecture.


## v0.3.0 (2025-01-22)

### Chores

- Bump version to 0.3.0
  ([`0ac5d0a`](https://github.com/os-designers/livesync/commit/0ac5d0ad6010717869d35e063f4419323279ac10))

### Refactoring

- Consolidate protobuf file paths and update tooling configs
  ([`be4854b`](https://github.com/os-designers/livesync/commit/be4854bea94423a96dfd134afb7e4df9ce1a0d7a))

- migrate protobuf paths to src/livesync/_protos directory - update exclusion paths in mypy, pyright
  configurations - add new linter rules for generated proto files and stubs

- Migrate to layer-based architecture with stream processing
  ([`47250ee`](https://github.com/os-designers/livesync/commit/47250eea3d96694e57c26a398d3378fddba50952))

- replace node-based system with new layer architecture for better composability - implement stream
  synchronization and processing pipeline - add remote processing capabilities with gRPC - improve
  media handling with FFmpeg integration - restructure project layout and documentation

BREAKING CHANGE: Complete API redesign from node-based to layer-based architecture - Removed
  nodes.md, graphs.md, frames.md and related implementation files - New layer system requires
  different pipeline construction - Updated all examples to use new layer-based approach - Remote
  processing now uses RemoteLayer instead of RemoteNode

Key additions: - Stream-based processing with async support - Layer system (InputLayer,
  CallableLayer, Lambda, Merge, etc.) - Media synchronization capabilities - Configurable remote
  processing - Enhanced documentation and examples

### BREAKING CHANGES

- Complete API redesign from node-based to layer-based architecture


## v0.2.1 (2025-01-19)

### Bug Fixes

- Add system dependencies for workflows
  ([`f264d62`](https://github.com/os-designers/livesync/commit/f264d62ef12fffe0c054a3a5f4c0996ee786f2ac))

- Change README.md
  ([`ef53052`](https://github.com/os-designers/livesync/commit/ef530529e31e9ae10308dc510c91277f683100a4))

### Chores

- Bump version to 0.2.1
  ([`f293088`](https://github.com/os-designers/livesync/commit/f293088c1086e3e33fe6ce46eea7a1b3e4cd0575))

### Refactoring

- **proto**: Restructure protobuf compilation and imports
  ([`a03552c`](https://github.com/os-designers/livesync/commit/a03552c887d0602e04aa18b13a97661415e0acb1))

- move generated proto files to centralized _protos directory - update proto compilation script to
  handle multiple proto files - adjust import paths across remote node implementations - upgrade
  protobuf dependency to 5.29.3

BREAKING CHANGE: proto file locations and import paths have changed

### BREAKING CHANGES

- **proto**: Proto file locations and import paths have changed


## v0.2.0 (2025-01-18)

### Bug Fixes

- Version.py typo
  ([`b648c7a`](https://github.com/os-designers/livesync/commit/b648c7ab4f6cc396733edf723f9b305a410aefdf))

### Chores

- Bump version to 0.2.0
  ([`36d301b`](https://github.com/os-designers/livesync/commit/36d301b03413ae3febf8df968540256f56e9d013))

### Features

- Refactor all files and add mkdocs documentation
  ([`5203def`](https://github.com/os-designers/livesync/commit/5203def0668bece4ec5ab019e44ddd4a5cb80f83))


## v0.1.2 (2025-01-14)

### Chores

- Add an additional usage example for the basic server
  ([`0d2cd64`](https://github.com/os-designers/livesync/commit/0d2cd6466467e52ccc1b13f0f8b49ea32c0c058a))

- Bump version to 0.1.2
  ([`8f153ce`](https://github.com/os-designers/livesync/commit/8f153ce050186f28122b26fb091ee24c32d4138d))

- Cleanup unused bumpversion file
  ([`5bba250`](https://github.com/os-designers/livesync/commit/5bba2504ac9c78d8d9dc02c82a7ab78929889bfe))

### Refactoring

- Implement node replacement and improve dashboard UI
  ([`750adc7`](https://github.com/os-designers/livesync/commit/750adc7cbbf686375a29d46298b147d0e38db4e6))

- add Graph.replace_node method with connection preservation - refactor MainWindow UI initialization
  for better organization - add toggle button for switching between local/remote frame rate nodes -
  improve code structure and error handling in graph view - remove typing_extensions dependency and
  @override decorators - rename service readiness flag for clarity (_is_service_ready -> _is_ready)

BREAKING CHANGE: Graph.replace_node may throw ValueError for invalid nodes

- Remove unused RoundRobinSelector class and improve logging setup
  ([`55e76e1`](https://github.com/os-designers/livesync/commit/55e76e10d44c9a58f6c63d3df1246c4cc326dd98))

- Removed the unused RoundRobinSelector class from livesync_remote_node.py. - Integrated
  RoundRobinSelector into RemoteNode class in remote_node.py. - Cleaned up logging configuration in
  basic_client.py by removing an unnecessary blank line.

### BREAKING CHANGES

- Graph.replace_node may throw ValueError for invalid nodes


## v0.1.1 (2025-01-13)

### Bug Fixes

- Add pytest command to pyproject.toml
  ([`0fe1983`](https://github.com/os-designers/livesync/commit/0fe1983a65c2afe5318dbe5d1f61ad6bb99848e3))

- Align license field in pyproject.toml with MIT license
  ([`eb44386`](https://github.com/os-designers/livesync/commit/eb443867edb2fd33cbb196e1d76be4bf98ff4c4c))

- Change basic example for clarity
  ([`6f01466`](https://github.com/os-designers/livesync/commit/6f01466650b748ad02ba13d7924a41d1d79df6c5))

- Change condition for creating releases
  ([`fbd72ea`](https://github.com/os-designers/livesync/commit/fbd72ea3516bde305c14db58fe61dabe837881a3))

- Change pakcage name in pypi
  ([`b4c8615`](https://github.com/os-designers/livesync/commit/b4c86152f238e4151f9558f7a04b33d791f5aaca))

- Change publishing ci
  ([`c93d60a`](https://github.com/os-designers/livesync/commit/c93d60a4ee56ca1e6c9de7d8087e4c909c402c17))

- Change rye install url
  ([`1dd12db`](https://github.com/os-designers/livesync/commit/1dd12db5bbc7d4681752cfcad297cdad8b050427))

- Change rye install url
  ([`b12be7e`](https://github.com/os-designers/livesync/commit/b12be7e593ec4c00af09e0aba5538c6ed4aa07e3))

- Change rye install url
  ([`33be4fa`](https://github.com/os-designers/livesync/commit/33be4fa2918b316fd651409ba3bdb2178b9f2324))

- Ci.yml
  ([`a188373`](https://github.com/os-designers/livesync/commit/a188373a6db5891023e34b48e04f5a5e39c79573))

- Install PyYAML first before installing rye
  ([`bec4afa`](https://github.com/os-designers/livesync/commit/bec4afa4e2275e5d5e72e1ffc58f181de9eb0f12))

- Install rye before ci
  ([`95a52a9`](https://github.com/os-designers/livesync/commit/95a52a941def4ce5414a555d3834a48829a9ad3e))

- Make scripts executable
  ([`4321721`](https://github.com/os-designers/livesync/commit/4321721c909864090fc35aee75f52cd7bad75c2d))

- Patch importlib-metadata version
  ([`88552e1`](https://github.com/os-designers/livesync/commit/88552e17e606a1c170712fab2bc4d91a164cf41e))

- Replace github token with PAT
  ([`7bc7c2e`](https://github.com/os-designers/livesync/commit/7bc7c2ea45a7285bf9fb9a6cb1fa9408bbcccba0))

- Reset all existing tags
  ([`ae1d2b5`](https://github.com/os-designers/livesync/commit/ae1d2b56f89273cb81b8219e241e7116e46991ea))

- Sync all version files
  ([`164cbc6`](https://github.com/os-designers/livesync/commit/164cbc6e60c46ced1c39d1b913aeb3c5684cb51f))

- Update license field format in pyproject.toml
  ([`7820ee8`](https://github.com/os-designers/livesync/commit/7820ee8d4820300e7fcc2dab9fbd331846b5af6f))

### Chores

- Bump version to 0.1.1
  ([`83dfd23`](https://github.com/os-designers/livesync/commit/83dfd2337938a1473a409fca7bc4465da38ef82b))

- Bump version to 0.1.1
  ([`acb4580`](https://github.com/os-designers/livesync/commit/acb4580cea19b432347c89431df18d179d1cb856))

- Downgrade Python version from 3.12.8 to 3.12.2
  ([`b3c5cff`](https://github.com/os-designers/livesync/commit/b3c5cff0c9167e761c2d01be0d410022c63e94be))

- Initial commit
  ([`40b88a8`](https://github.com/os-designers/livesync/commit/40b88a841865220020d35332154f47397df076df))

- Reset version to 0.1.0
  ([`c1f4da0`](https://github.com/os-designers/livesync/commit/c1f4da0a3b742652095dfc50cd7001523dcb886a))

- Reset version to 0.1.0
  ([`04bab3d`](https://github.com/os-designers/livesync/commit/04bab3d01dbc7cdc92c50cb56bce4e8656562977))

### Features

- Add release command
  ([`7a6fc2c`](https://github.com/os-designers/livesync/commit/7a6fc2c1388d1b9362417cd88c7ac551de5abdaf))

- Add release command
  ([`03a6a49`](https://github.com/os-designers/livesync/commit/03a6a4985884fed18e0573f7563751a0b43a2e5b))

- Add release command
  ([`dcf3b03`](https://github.com/os-designers/livesync/commit/dcf3b03d6f6d30433aebdac37d7bf8c0b0296bb7))
