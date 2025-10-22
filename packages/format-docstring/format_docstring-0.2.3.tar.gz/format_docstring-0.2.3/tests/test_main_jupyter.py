import json
from pathlib import Path
from shutil import copy2

from click.testing import CliRunner

from format_docstring.main_jupyter import main as cli_main_ipynb


def test_integration_cli_ipynb(tmp_path: Path) -> None:
    """Run CLI on a copied .ipynb file and compare to expected output."""
    data_dir = Path(__file__).parent / 'test_data/integration_test/numpy'
    before = data_dir / 'before.ipynb'
    after = data_dir / 'after.ipynb'

    work_file = tmp_path / 'work.ipynb'
    copy2(before, work_file)

    runner = CliRunner()
    res = runner.invoke(cli_main_ipynb, [str(work_file)])
    assert res.exit_code in {0, 1}, res.output

    actual = json.loads(work_file.read_text())
    expected = json.loads(after.read_text())
    assert actual == expected


def test_integration_cli_ipynb_len50(tmp_path: Path) -> None:
    """Run CLI with --line-length 50 on .ipynb and compare to expected."""
    data_dir = Path(__file__).parent / 'test_data/integration_test/numpy'
    before = data_dir / 'before.ipynb'
    after = data_dir / 'after_50.ipynb'

    work_file = tmp_path / 'work.ipynb'
    copy2(before, work_file)

    runner = CliRunner()
    res = runner.invoke(
        cli_main_ipynb, ['--line-length', '50', str(work_file)]
    )
    assert res.exit_code in {0, 1}, res.output

    actual = json.loads(work_file.read_text())
    expected = json.loads(after.read_text())
    assert actual == expected


def test_cli_ipynb_verbose_diff(tmp_path: Path) -> None:
    """Ensure ``--verbose diff`` prints a diff for notebook rewrites."""
    fixture = Path(__file__).parent / 'test_data/jupyter/verbose_before.ipynb'
    work_file = tmp_path / 'work.ipynb'
    copy2(fixture, work_file)

    runner = CliRunner()
    result = runner.invoke(
        cli_main_ipynb, ['--verbose', 'diff', str(work_file)]
    )
    assert result.exit_code in {0, 1}, result.output
    assert '(before)' in result.output
    assert '(after)' in result.output
    assert '@@' in result.output
    assert 'docstring should be rewritten because it is very' in result.output

    # Ensure contents changed.
    original = json.loads(fixture.read_text())
    updated = json.loads(work_file.read_text())
    assert original != updated


def test_cli_ipynb_config_verbose_diff(tmp_path: Path) -> None:
    """Config file enables verbose diff for notebook rewrites."""
    config_file = tmp_path / 'pyproject.toml'
    config_file.write_text('[tool.format_docstring]\nverbose = "diff"\n')

    fixture = Path(__file__).parent / 'test_data/jupyter/verbose_before.ipynb'
    work_file = tmp_path / 'work.ipynb'
    copy2(fixture, work_file)

    runner = CliRunner()
    result = runner.invoke(
        cli_main_ipynb, ['--config', str(config_file), str(work_file)]
    )
    assert result.exit_code in {0, 1}, result.output
    assert '(before)' in result.output
    assert '(after)' in result.output
    assert '@@' in result.output
    assert 'docstring should be rewritten because it is very' in result.output

    # Ensure contents changed after formatting.
    assert json.loads(work_file.read_text()) != json.loads(fixture.read_text())
