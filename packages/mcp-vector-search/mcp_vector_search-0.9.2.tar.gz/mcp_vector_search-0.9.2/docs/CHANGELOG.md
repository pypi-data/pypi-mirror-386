# Changelog

All notable changes to MCP Vector Search will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **HTML Language Support**: Full HTML parser implementation
  - Semantic content extraction from HTML tags
  - Intelligent chunking based on heading hierarchy
  - Ignores script and style tag content
  - Extracts text from h1-h6, p, section, article, main, aside, nav, header, footer
  - Preserves class and id attributes for context
  - Supported extensions: `.html`, `.htm`

- **Automatic Version-Based Reindexing**: Smart index updates on tool upgrades
  - Tracks index version in metadata
  - Auto-reindexes on major/minor version changes (skips patch updates)
  - Search-triggered version checks with user-friendly messages
  - Configurable via `auto_reindex_on_upgrade` setting (default: true)
  - Zero user intervention required - seamless upgrade experience
  - New dependency: `packaging>=23.0` for semantic version comparison

### Enhanced
- **Search Performance Optimizations**: 60-85% faster search operations
  - Async file I/O eliminates blocking reads in hot path (+35-40% speed)
  - LRU file content caching reduces repeated disk access (+15-20% speed)
  - Health check throttling (60-second intervals) reduces overhead (+5-7% speed)
  - Connection pooling enabled by default (+13.6% speed)
  - Optimized reranking algorithm with reduced string operations (+8-12% speed)

- **Query Expansion**: Improved semantic search relevance
  - Automatic expansion of common abbreviations (auth → authentication, db → database, etc.)
  - Better matching for programming concepts (class, method, function, etc.)
  - 15-20% improvement in search result relevance
  - Pre-computed expansion dictionaries eliminate runtime overhead (+20-25% speed)

- **Text Parser**: Now supports markdown files (`.md`, `.markdown`) in addition to `.txt`

- **Language Count**: Now supports **8 languages** (up from 7):
  - Python, JavaScript, TypeScript (existing)
  - Dart, PHP, Ruby (v0.5.0)
  - **HTML** (new)
  - Text/Markdown (enhanced)

### Fixed
- Bare exception handlers now use specific exception types for better debugging
- Added comprehensive logging to exception handlers
- Expanded ignore patterns: `.mypy_cache`, `.ruff_cache`, `.claude-mpm`, `.mcp-vector-search`

### Internal
- Extracted magic numbers to project-wide constants for maintainability
- Created parser utilities module to reduce code duplication (potential -800 to -1000 LOC)
- Proper LRU cache implementation with statistics and configurable size

## [0.5.0] - 2025-10-02

### Added
- **PHP Language Support**: Full PHP parser implementation
  - Class, interface, and trait detection
  - Method extraction (public, private, protected, static)
  - Magic methods (__construct, __get, __set, etc.)
  - PHPDoc comment extraction
  - Namespace and use statement handling
  - Laravel framework patterns (Controllers, Models, Eloquent)
  - Supported extensions: `.php`, `.phtml`

- **Ruby Language Support**: Full Ruby parser implementation
  - Module and class detection with namespace support (::)
  - Instance and class method extraction
  - Special method names (?, !)
  - Attribute macros (attr_accessor, attr_reader, attr_writer)
  - RDoc comment extraction (# and =begin...=end)
  - Rails framework patterns (ActiveRecord, Controllers)
  - Supported extensions: `.rb`, `.rake`, `.gemspec`

### Fixed
- **MCP Configuration Bug**: Install command now correctly creates `.mcp.json` in project root instead of trying to create `claude-code` directory
- **Configuration Format**: Added required `"type": "stdio"` field for Claude Code compatibility

### Enhanced
- **Language Support**: Now supports **7 languages** total (8 as of next release)
  - Python, JavaScript, TypeScript (existing)
  - Dart/Flutter (v0.4.15)
  - **PHP** (new)
  - **Ruby** (new)
  - Markdown/Text (fallback)

- **Cross-Language Search**: Semantic search now works across all 7 languages
- **Framework Support**: Added specialized support for Laravel (PHP) and Rails (Ruby)

### Technical Details
- Zero new dependencies (uses existing tree-sitter-language-pack)
- Tree-sitter AST parsing with regex fallback for both PHP and Ruby
- Performance: PHP ~2.5ms, Ruby ~4ms per file (sub-5ms target)
- 100% test coverage for new parsers
- Type safety maintained (mypy compliant)

## [0.4.15] - 2025-10-02

### Added
- **Dart Language Support**: Full Dart/Flutter parser implementation
  - Widget detection (StatelessWidget, StatefulWidget)
  - State class parsing (_WidgetNameState pattern)
  - Async function support (Future<T> async)
  - Dartdoc comment extraction (///)
  - Tree-sitter AST parsing with regex fallback
  - Supported extensions: `.dart`
  - 20+ code chunks extracted from comprehensive test files
  - Cross-language semantic search across all 5 languages

- **Enhanced Install Command**: Complete project setup workflow
  - Multi-tool MCP detection (Claude Code, Cursor, Windsurf, VS Code)
  - Interactive MCP configuration with tool selection
  - Rich progress indicators and status updates
  - Automatic indexing after setup (optional)
  - New options:
    - `--no-mcp`: Skip MCP configuration
    - `--no-index`: Skip automatic indexing
    - `--extensions`: Customize file extensions
    - `--mcp-tool`: Specify MCP tool directly

### Enhanced
- **Rich Help System**: Industry-standard CLI help patterns
  - Help panels organized by purpose (Core Operations, Customization, Advanced)
  - Comprehensive examples in all command help text
  - Next-step hints after operations complete
  - Error messages with clear recovery instructions
  - Progressive disclosure pattern (basic → advanced)
  - Emoji indicators for visual hierarchy
  - Follows patterns from git, npm, docker CLIs

- **Language Support**: Now supports 7 languages
  - Python, JavaScript, TypeScript (existing)
  - Dart/Flutter (v0.4.15)
  - PHP, Ruby (v0.5.0)
  - Text/Markdown (fallback)

### Technical Details
- Zero new dependencies (uses existing tree-sitter-language-pack)
- Type safety: 100% mypy compliance maintained
- Test coverage maintained across all new features
- Backward compatible: No breaking changes

## [0.4.14] - 2025-09-23

### Added
- Initial release structure

### Changed
- Version bump preparation

### Fixed
- Build system improvements

## [0.4.1] - 2025-08-18

### 🐛 Critical Bug Fixes
- **BREAKING FIX**: Fixed search functionality returning zero results for all queries
  - Corrected ChromaDB cosine distance to similarity conversion that was producing negative scores
  - Fixed adaptive threshold logic ignoring user-specified threshold values (especially 0.0)
  - Search now properly returns relevant results with accurate similarity percentages

### ✨ Improvements
- Enhanced debug logging for search operations and threshold calculations
- Improved similarity score clamping to ensure values stay within [0, 1] range
- Better CLI output formatting with proper similarity percentage display

### 🧪 Testing & Validation
- Validated search functionality with real-world codebase (claude-mpm project)
- Tested multi-language search across Python, JavaScript, and TypeScript files
- Confirmed performance with 7,723 indexed code chunks from 120 files
- Added comprehensive debugging documentation and analysis

### 📚 Documentation
- Added detailed debugging analysis in `docs/debugging/SEARCH_BUG_ANALYSIS.md`
- Documented ChromaDB distance behavior and similarity calculation methods
- Enhanced troubleshooting guides for search-related issues

### 🎯 Impact
This release fixes the core search functionality that was completely broken in v0.4.0, making MCP Vector Search fully functional and production-ready for real-world use cases.

## [4.0.3] - 2025-01-18

### Added
- Consolidated versioning and build system via comprehensive Makefile
- Unified version management through scripts/version_manager.py
- Automated release workflows with git integration
- Dry-run mode for safe testing of version changes
- **Connection Pooling**: 13.6% performance improvement with automatic connection reuse
- **Semi-Automatic Reindexing**: 5 strategies without daemon processes
  - Search-triggered auto-indexing (built-in)
  - Git hooks integration for development workflows
  - Scheduled tasks (cron/Windows tasks) for production
  - Manual checks via CLI commands
  - Periodic checker for long-running applications
- **Auto-Index CLI Commands**: Complete management of automatic reindexing
- **Performance Testing**: Comprehensive benchmarking and optimization
- **Production Features**: Error handling, monitoring, graceful degradation

### Fixed
- Import error in factory.py (EmbeddingFunction → CodeBERTEmbeddingFunction)
- CLI typer.Choice() AttributeError in auto_index.py
- Missing ConnectionPoolError exception for tests
- Default embedding model updated to valid 'sentence-transformers/all-MiniLM-L6-v2'
- **Critical Bug**: Incremental indexing was creating duplicate chunks
- **Metadata Consistency**: Improved tracking of indexed files

### Changed
- Deprecated old build scripts in favor of unified Makefile workflow
- Version management centralized through single interface
- Build process streamlined with color-coded output
- **Incremental Indexing**: Now properly removes old chunks before adding new ones
- **Search Engine**: Integrated with auto-indexing for seamless updates
- **Database Layer**: Added pooled database option for high-throughput scenarios
- **CLI Interface**: Added auto-index subcommand with comprehensive options

### Deprecated
- scripts/build.sh - Use `make` commands instead
- scripts/dev-build.py - Use `make version-*` commands
- scripts/publish.sh - Use `make publish`

## [Unreleased]

### Added
- 

### Changed
- 

### Fixed
- 

## [0.0.3] - 2024-01-10

### Added
- 🎉 **Initial public alpha release**
- **CLI Interface**: Complete Typer-based command-line tool
  - `init` - Initialize projects for semantic search
  - `index` - Index codebase with smart chunking
  - `search` - Semantic search with similarity scoring
  - `watch` - Real-time file monitoring
  - `status` - Project statistics and health
  - `config` - Configuration management
- **Multi-language Support**: Python, JavaScript, TypeScript parsing
  - AST-aware parsing with Tree-sitter integration
  - Regex fallback for robust parsing
  - Extensible parser registry system
- **Semantic Search**: ChromaDB-powered vector search
  - Sentence transformer embeddings
  - Similarity scoring and ranking
  - Rich terminal output with syntax highlighting
- **Real-time Updates**: File watching with incremental indexing
  - Debounced file change detection
  - Efficient incremental updates
  - Project-aware configuration
- **Developer Experience**:
  - Zero-config project initialization
  - Rich terminal output with progress bars
  - Comprehensive error handling
  - Local-first privacy with on-device processing

### Technical Details
- **Architecture**: Modern async Python with type safety
- **Dependencies**: ChromaDB, Sentence Transformers, Typer, Rich
- **Parsing**: AST-aware with Tree-sitter + regex fallback
- **Database**: Vector database abstraction layer
- **Configuration**: Project-aware settings management
- **Performance**: Sub-second search, ~1000 files/minute indexing

### Documentation
- Comprehensive README with examples
- MIT License for open-source distribution
- Professional project structure
- Development workflow documentation

### Infrastructure
- PyPI package distribution
- GitHub repository with releases
- Pre-commit hooks for code quality
- UV-based dependency management

## [0.0.2] - Internal Testing

### Added
- Core indexing functionality
- Basic search capabilities
- Python parser implementation

### Fixed
- File handling edge cases
- Memory usage optimizations

*Note: This version was used for internal testing and was not publicly released.*

## [0.0.1] - Initial Prototype

### Added
- Basic project structure
- Proof of concept implementation
- Initial CLI framework

*Note: This version was a prototype and was not publicly released.*

---

## Release Notes

### v0.0.3 - "Alpha Launch" 🚀

This is the first public release of MCP Vector Search! We're excited to share this semantic code search tool with the developer community.

**What's Working:**
- ✅ Multi-language code parsing (Python, JS, TS)
- ✅ Semantic search with vector embeddings
- ✅ Real-time file watching and indexing
- ✅ Rich CLI interface with progress indicators
- ✅ Project-aware configuration

**Known Limitations:**
- Tree-sitter integration needs improvement (using regex fallback)
- Search relevance may need tuning for specific codebases
- Limited error handling for edge cases
- Minimal test coverage

**Getting Started:**
```bash
pip install mcp-vector-search
mcp-vector-search init
mcp-vector-search index
mcp-vector-search search "your query here"
```

**Feedback Welcome:**
This is an alpha release - we're actively seeking feedback on search quality, performance, and usability. Please [open an issue](https://github.com/bobmatnyc/mcp-vector-search/issues) or start a [discussion](https://github.com/bobmatnyc/mcp-vector-search/discussions)!

---

## Migration Guides

### Upgrading to Future Versions

*Migration guides will be added here as new versions are released with breaking changes.*

#### From v0.0.x to v0.1.0 (Planned)
- Configuration file format may change
- CLI command options may be refined
- Database schema may be updated (automatic migration planned)

#### From v0.x to v1.0.0 (Planned)
- Stable API guarantees will begin
- MCP server integration will be added
- Plugin system will be introduced

---

## Development History

### Project Milestones

**2024-01-10**: 🎉 First public alpha release (v0.0.3)
- Published to PyPI
- GitHub repository made public
- Documentation and development workflow established

**2024-01-08**: Internal testing phase
- Core functionality implemented
- Multi-language parsing working
- CLI interface polished

**2024-01-05**: Project inception
- Initial concept and architecture design
- Technology stack selection
- Development environment setup

### Key Decisions

**Technology Choices:**
- **Python 3.11+**: Modern async/await, type hints
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: High-quality embeddings
- **Typer**: Modern CLI framework
- **Rich**: Beautiful terminal output
- **UV**: Fast Python package management

**Architecture Decisions:**
- **Local-first**: Complete on-device processing for privacy
- **Async-first**: Non-blocking operations for performance
- **Extensible**: Plugin-ready parser registry system
- **Type-safe**: Comprehensive type hints throughout

**Development Practices:**
- **Three-stage workflow**: Development → Local deployment → PyPI
- **Quality gates**: Linting, formatting, type checking
- **Documentation-first**: Comprehensive docs from day one
- **Community-focused**: Open source with clear contribution guidelines

---

## Statistics

### Release Metrics

**v0.0.3 (Alpha)**:
- **Files**: 39 source files
- **Lines of Code**: 11,718+ lines
- **Languages Supported**: 3 (Python, JavaScript, TypeScript)
- **CLI Commands**: 6 main commands
- **Dependencies**: 100+ (including transitive)
- **Documentation**: 15+ documentation files

### Performance Benchmarks

**Indexing Performance** (typical Python project):
- **Speed**: ~1000 files/minute
- **Memory**: ~50MB baseline + ~1MB per 1000 chunks
- **Storage**: ~1KB per code chunk

**Search Performance**:
- **Latency**: <100ms for most queries
- **Accuracy**: Semantic similarity-based ranking
- **Throughput**: Multiple concurrent searches supported

---

## Future Roadmap

### Short-term (v0.0.x - v0.1.0)
- [ ] Improve Tree-sitter integration
- [ ] Enhanced search relevance tuning
- [ ] Additional language support (Go, Rust, Java)
- [ ] Comprehensive test suite
- [ ] Performance optimizations

### Medium-term (v0.1.0 - v1.0.0)
- [ ] MCP (Model Context Protocol) server implementation
- [ ] Advanced search modes (contextual, similar code)
- [ ] Plugin system for extensibility
- [ ] IDE integrations (VS Code, JetBrains)
- [ ] Team collaboration features

### Long-term (v1.0.0+)
- [ ] Distributed indexing for large codebases
- [ ] Machine learning-powered code understanding
- [ ] Integration with code review tools
- [ ] Enterprise features and support
- [ ] Cloud-hosted option

---

## Contributing to Changelog

When contributing changes, please update this changelog following these guidelines:

1. **Add entries to [Unreleased]** section
2. **Use appropriate categories**: Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write clear, user-focused descriptions**
4. **Include breaking change warnings**
5. **Reference issues/PRs when relevant**

Example entry:
```markdown
### Added
- New `--parallel` flag for faster indexing (#123)

### Fixed
- Handle Unicode characters in file names (#124)

### Changed
- **BREAKING**: Configuration file format updated (see migration guide)
```

The changelog will be updated with each release to move items from [Unreleased] to the appropriate version section.
