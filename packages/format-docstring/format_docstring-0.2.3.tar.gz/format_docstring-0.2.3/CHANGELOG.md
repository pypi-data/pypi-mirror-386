# Change Log

All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-10-22

- Added
  - A lot more linters
  - Formatters for TOML and INI config files
- Changed
  - A lot of code changes to pass the linter checks
- Removed
  - Unnecessary pre-commit hooks
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.2.2...0.2.3

## [0.2.2] - 2025-10-20

- Added
  - Formatting support for type hints and default values in class docstrings
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.2.1...0.2.2

## [0.2.1] - 2025-10-20

- Fixed
  - A bug where raised exceptions in docstrings are incorrectly changed
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.2.0...0.2.1

## [0.2.0] - 2025-10-20

- Added
  - AST-driven synchronization of NumPy `Parameters` and `Returns` signature
    lines with the function signature, including tuple element expansion for
    multi-line return blocks
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.9...0.2.0

## [0.1.9] - 2025-10-16

- Added
  - A "`# no-format-docstring`" directive to ignore certain docstring
  - Verbose diff output via `--verbose diff` and
    `[tool.format_docstring] verbose`
  - Normalize NumPy section headings that include trailing colons (e.g.,
    `Parameters:`); also, fix Google-style "Arg" header into "Parameters"
- Changed
  - Added "self format" pre-commit hook to format docstrings within this repo
    with its own formatting logic
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.8...0.1.9

## [0.1.8] - 2025-10-14

- Fixed
  - Bug in `_fix_rst_backticks()` where backtick pairs spanning multiple lines
    (e.g., multi-line external links) were incorrectly processed
  - Added `(?!_)` lookahead to regex pattern to prevent matching trailing
    backticks from cross-references (e.g., `` `text`_ ``)
- Changed
  - Moved backtick fixing from line-by-line processing to whole-docstring
    processing to correctly handle multi-line constructs
  - REPL lines (starting with `>>> ` or `... `) are now protected with
    placeholders during backtick fixing to preserve backticks in Python
    examples
- Added
  - Test cases for multi-line external links in
    `test_fix_rst_backticks_cases()`
  - Test cases for REPL lines with backticks in
    `test_fix_rst_backticks_cases()`
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.7...0.1.8

## [0.1.7] - 2025-10-14

- Fixed
  - Backtick fixing logic to properly distinguish between inline literals and
    external links (e.g., `` `Python <https://example.org>`_ ``)
  - Refactored `_fix_rst_backticks()` to use pre-compiled regex pattern for
    better performance
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.6...0.1.7

## [0.1.6] - 2025-10-13

- Added
  - New `--fix-rst-backticks` option to automatically convert single backticks
    to double backticks per rST syntax
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.5...0.1.6

## [0.1.5] - 2025-10-13

- Added
  - Support for `... ` (continuation of REPL lines) in the Examples section
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.4...0.1.5

## [0.1.4] - 2025-10-12

- Added
  - Support for detecting misspelled section title: "Example"
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.3...0.1.4

## [0.1.3] - 2025-10-12

- Fixed
  - A bug in counting line length for single-line docstrings
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.2...0.1.3

## [0.1.2] - 2025-10-08

- Added
  - Support for 1 blank line after `::`
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.1...0.1.2

## [0.1.1] - 2025-10-06

- Fixed
  - A bug where single-line docstrings exceeding length limit aren't handled
- Full diff
  - https://github.com/jsh9/format-docstring/compare/0.1.0...0.1.1

## [0.1.0] - 2025-10-06

- Added
  - Initial release of format-docstring
  - Support for NumPy-style docstring formatting
  - Limited support for Google-style docstrings
  - CLI tools: `format-docstring` and `format-docstring-jupyter`
  - Configuration via `pyproject.toml` with `[tool.format_docstring]` section
  - Options for line length, docstring style, and file exclusion patterns
  - Pre-commit hooks for Python files and Jupyter notebooks
  - Comprehensive test suite with pytest
  - Type checking with mypy
  - Support for Python 3.10-3.12
- Full diff
  - N/A
