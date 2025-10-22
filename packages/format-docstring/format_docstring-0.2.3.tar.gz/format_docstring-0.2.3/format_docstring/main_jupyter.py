from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from jupyter_notebook_parser import (
    JupyterNotebookParser,
    JupyterNotebookRewriter,
    SourceCodeContainer,
    reconstruct_source,
)

import format_docstring.docstring_rewriter as doc_rewriter
from format_docstring import __version__
from format_docstring.base_fixer import BaseFixer
from format_docstring.config import inject_config_from_file


@click.command()
@click.version_option(version=__version__)
@click.argument('paths', nargs=-1, type=click.Path())
@click.option(
    '--config',
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    is_eager=True,
    callback=inject_config_from_file,
    default='pyproject.toml',
    help=(
        'Path to a pyproject.toml config file. '
        'If not specified, searches for pyproject.toml in parent directories. '
        'Command-line options take precedence over config file settings.'
    ),
)
@click.option(
    '--exclude',
    type=str,
    default=r'\.git|\.tox|\.pytest_cache',
    help='Regex pattern to exclude files/directories',
)
@click.option(
    '--line-length',
    type=int,
    default=79,
    show_default=True,
    help='Maximum line length for wrapping docstrings',
)
@click.option(
    '--docstring-style',
    type=click.Choice(['numpy', 'google'], case_sensitive=False),
    default='numpy',
    show_default=True,
    help='Docstring style to target',
)
@click.option(
    '--fix-rst-backticks',
    default=True,
    show_default=True,
    help='Fix single backticks to double backticks per rST syntax',
)
@click.option(
    '--verbose',
    type=click.Choice(['default', 'diff'], case_sensitive=False),
    default='default',
    show_default=True,
    help='Increase logging detail; "diff" prints unified diffs for rewrites',
)
def main(
        paths: tuple[str, ...],
        config: str | None,  # noqa: ARG001 (used by Click callback)
        *,
        exclude: str,
        line_length: int,
        docstring_style: str,
        fix_rst_backticks: bool,
        verbose: str,
) -> None:
    """Format .ipynb files."""
    ret = 0
    for path in paths:
        fixer = JupyterNotebookFixer(
            path=path,
            exclude_pattern=exclude,
            line_length=line_length,
            fix_rst_backticks=fix_rst_backticks,
            verbose=verbose.lower(),
        )
        fixer.docstring_style = docstring_style
        ret |= fixer.fix_one_directory_or_one_file()

    if ret != 0:
        raise SystemExit(ret)


class JupyterNotebookFixer(BaseFixer):
    """Fixer for Jupyter notebook files."""

    def __init__(
            self,
            path: str,
            exclude_pattern: str = r'\.git|\.tox|\.pytest_cache',
            line_length: int = 79,
            *,
            fix_rst_backticks: bool = True,
            verbose: str = 'default',
    ) -> None:
        super().__init__(
            path=path,
            exclude_pattern=exclude_pattern,
            verbose=verbose.lower(),
        )
        self.line_length = line_length
        self.fix_rst_backticks = fix_rst_backticks
        self.docstring_style: str = 'numpy'

    def fix_one_directory_or_one_file(self) -> int:
        """Fix formatting in a file or all .ipynb files in a directory."""
        path_obj = Path(self.path)

        if path_obj.is_file():
            return self.fix_one_file(path_obj.as_posix())

        # Process .ipynb files instead of .py files for Jupyter notebooks
        filenames = self._get_files_to_process(path_obj, '*.ipynb')
        all_status = set()
        for filename in filenames:
            status = self.fix_one_file(str(filename))
            all_status.add(status)

        return 0 if not all_status or all_status == {0} else 1

    def fix_one_file(self, filename: str) -> int:
        """Fix formatting in a single Jupyter notebook file."""
        file_path = Path(filename)
        if not file_path.is_file():
            msg = f'{filename} is not a file (skipping)'
            print(msg, file=sys.stderr)
            return 0

        original_text = file_path.read_text(encoding='utf-8')

        try:
            parsed: JupyterNotebookParser = JupyterNotebookParser(filename)
            rewriter: JupyterNotebookRewriter = JupyterNotebookRewriter(
                parsed_notebook=parsed
            )
            code_cells: list[dict[str, Any]] = parsed.get_code_cells()
            code_cell_indices: list[int] = parsed.get_code_cell_indices()
            code_cell_sources: list[SourceCodeContainer] = (
                parsed.get_code_cell_sources()
            )
        except OSError as exc:
            print(f'Error reading {filename}: {exc!s}', file=sys.stderr)
            return 1
        else:
            ret_val = 0
            assert len(code_cells) == len(code_cell_indices)
            assert len(code_cells) == len(code_cell_sources)

            for i in range(len(code_cells)):
                index: int = code_cell_indices[i]
                source: SourceCodeContainer = code_cell_sources[i]
                source_without_magic: str = source.source_without_magic
                magics: dict[str, str] = source.magics
                fixed: str = doc_rewriter.fix_src(
                    source_code=source_without_magic,
                    line_length=self.line_length,
                    docstring_style=self.docstring_style,
                    fix_rst_backticks=self.fix_rst_backticks,
                )

                if fixed != source_without_magic:
                    ret_val = 1
                    fixed_with_magics = reconstruct_source(fixed, magics)
                    rewriter.replace_source_in_code_cell(
                        index=index,
                        new_source=fixed_with_magics,
                    )

            if ret_val == 1:
                new_text = json.dumps(parsed.notebook_content, indent=1) + '\n'
                print(f'Rewriting {filename}', file=sys.stderr)
                self.print_diff(filename, original_text, new_text)
                with Path(filename).open('w', encoding='utf-8') as fp:
                    fp.write(new_text)

            return ret_val


if __name__ == '__main__':
    raise SystemExit(main())
