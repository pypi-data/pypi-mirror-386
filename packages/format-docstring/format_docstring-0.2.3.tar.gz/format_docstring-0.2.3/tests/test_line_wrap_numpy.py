from pathlib import Path

import pytest

from format_docstring.docstring_rewriter import wrap_docstring
from format_docstring.line_wrap_numpy import (
    _fix_colon_spacing,
    _fix_rst_backticks,
    _get_section_heading_title,
    _is_hyphen_underline,
    _is_param_signature,
    _standardize_default_value,
)
from tests.helpers import load_case_from_file, load_cases_from_dir

DATA_DIR: Path = Path(__file__).parent / 'test_data/line_wrap/numpy'


@pytest.mark.parametrize(
    ('name', 'line_length', 'before', 'after'),
    load_cases_from_dir(DATA_DIR),
)
def test_wrap_docstring(
        name: str,  # noqa: ARG001
        line_length: int,
        before: str,
        after: str,
) -> None:
    out = wrap_docstring(
        before, line_length=line_length, docstring_style='numpy'
    )
    # We ignore the leading and trailing newlines here, because we'll check
    # those newlines in test_fix_src_end_to_end() in test_docstring_rewriter.py
    assert out.strip('\n') == after.strip('\n')


def test_wrap_docstring_single_case() -> None:
    """
    A placeholder test for easy debugging. You can replace the file name with
    the test case file that's producing errors.
    """
    _, length, before, after = load_case_from_file(
        DATA_DIR / 'contents_that_are_not_wrapped.txt'
    )
    out = wrap_docstring(
        before,
        line_length=length,
        docstring_style='numpy',
        fix_rst_backticks=False,
    )
    assert out.strip('\n') == after.strip('\n')


@pytest.mark.parametrize(
    ('line', 'expected'),
    [
        ('---', True),
        ('  ----  ', True),
        ('--', True),
        (' - - ', False),
        ('text', False),
        ('', False),
    ],
)
def test_is_hyphen_underline(line: str, *, expected: bool) -> None:
    assert _is_hyphen_underline(line) == expected


@pytest.mark.parametrize(
    ('lines', 'idx', 'expected'),
    [
        (['Parameters', '----------'], 0, 'parameters'),
        (['Returns', '---', 'x'], 0, 'returns'),
        (['Notes', '--', 'free text'], 0, 'notes'),
        (['Only title'], 0, None),
        (['', '----'], 0, None),
    ],
)
def test_get_section_heading_title(
        lines: list[str], idx: int, expected: str | None
) -> None:
    assert _get_section_heading_title(lines, idx) == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('x : int', True),
        ('x: int', True),  # no space before `:` is fine
        ('x           : int', True),  # many space before `:` is also fine
        ('alpha, beta : list[str] | None', True),
        ('data: dict[str, int]', True),  # no space before `:` is fine
        ('abc :', True),
        ('abc:', True),
        ('abc  :', True),  # two spaces before `:` is fine
        ('abc         :', True),  # many spaces before `:` is also fine
        ('  gamma_delta: ', True),
        ('alpha1, _beta2: optional', True),
        ('alpha , beta , gamma : int', True),
        ('*args : Any', True),
        ('**kwargs : dict[str, Any]', True),
        ('*args: tuple[int, ...]', True),
        ('**kwargs_plot : dict[Any, Any]', True),
        ('  *args : Any', True),
        ('*args, **kwargs : Any', True),
        ('data, *args : Any', True),
        ('alpha, *args, **kwargs : Any', True),
        ('1name : int', False),
        ('alpha, beta gamma : int', False),
        ('alpha,,beta: int', False),
        (': int', False),
        (', alpha: int', False),
        ('x', False),
        ('int', False),
        ('    description line', False),
        ('----', False),
        ('   ', False),
        ('***args : Any', False),
        ('*1args : Any', False),
        ('**1kwargs : Any', False),
        ('*, args : Any', False),
        ('** kwargs : Any', False),
    ],
)
def test_is_param_signature(text: str, *, expected: bool) -> None:
    assert _is_param_signature(text) == expected


@pytest.mark.parametrize(
    ('line', 'expected'),
    [
        # Basic cases with different spacing
        ('arg1: dict[str, list[str]]', 'arg1 : dict[str, list[str]]'),
        ('arg1 :  dict[str, list[str]]', 'arg1 : dict[str, list[str]]'),
        ('arg1:dict[str, list[str]]', 'arg1 : dict[str, list[str]]'),
        ('arg1  :dict[str, list[str]]', 'arg1 : dict[str, list[str]]'),
        # With indentation
        ('  arg1: dict[str, list[str]]', '  arg1 : dict[str, list[str]]'),
        (
            '    arg1 :  dict[str, list[str]]',
            '    arg1 : dict[str, list[str]]',
        ),
        (
            '        arg1:dict[str, list[str]]',
            '        arg1 : dict[str, list[str]]',
        ),
        # Multiple parameters
        ('alpha, beta: list[str] | None', 'alpha, beta : list[str] | None'),
        ('alpha, beta : list[str] | None', 'alpha, beta : list[str] | None'),
        ('alpha, beta  :  list[str] | None', 'alpha, beta : list[str] | None'),
        # With *args, **kwargs
        ('*args: Any', '*args : Any'),
        ('**kwargs: dict[str, Any]', '**kwargs : dict[str, Any]'),
        ('*args, **kwargs: Any', '*args, **kwargs : Any'),
        # Empty or minimal type annotations
        ('arg:', 'arg : '),
        ('arg :', 'arg : '),
        ('arg  :', 'arg : '),
        # Already correct spacing (should remain unchanged)
        ('arg1 : dict[str, list[str]]', 'arg1 : dict[str, list[str]]'),
    ],
)
def test_fix_colon_spacing(line: str, expected: str) -> None:
    assert _fix_colon_spacing(line) == expected


@pytest.mark.parametrize(
    ('line', 'expected'),
    [
        # Format: ` default XXX`
        ('arg : int default 10', 'arg : int, default=10'),
        ('arg : str default "hello"', 'arg : str, default="hello"'),
        ('arg : bool default True', 'arg : bool, default=True'),
        ('arg : list[int] default []', 'arg : list[int], default=[]'),
        # Format: `, default XXX`
        ('arg : int, default 10', 'arg : int, default=10'),
        ('arg : str, default "hello"', 'arg : str, default="hello"'),
        ('arg : bool, default True', 'arg : bool, default=True'),
        # Format: `, default is XXX`
        ('arg : int, default is 10', 'arg : int, default=10'),
        ('arg : str, default is "hello"', 'arg : str, default="hello"'),
        ('arg : bool, default is True', 'arg : bool, default=True'),
        # Format: ` default is XXX`
        ('arg : int default is 10', 'arg : int, default=10'),
        ('arg : str default is "hello"', 'arg : str, default="hello"'),
        ('arg : bool default is True', 'arg : bool, default=True'),
        # Format: ` default:XXX`
        ('arg : int default:10', 'arg : int, default=10'),
        ('arg : str default:"hello"', 'arg : str, default="hello"'),
        ('arg : bool default:True', 'arg : bool, default=True'),
        # Format: ` default: XXX`
        ('arg : int default: 10', 'arg : int, default=10'),
        ('arg : str default: "hello"', 'arg : str, default="hello"'),
        ('arg : bool default: True', 'arg : bool, default=True'),
        # Format: ` default:    XXX` (multiple spaces after colon)
        ('arg : int default:    10', 'arg : int, default=10'),
        ('arg : str default:    "hello"', 'arg : str, default="hello"'),
        # Format: ` default  :   XXX` (multiple spaces around colon)
        ('arg : int default  :   10', 'arg : int, default=10'),
        ('arg : str default  :   "hello"', 'arg : str, default="hello"'),
        # Format: `, default:XXX`
        ('arg : int, default:10', 'arg : int, default=10'),
        ('arg : str, default:"hello"', 'arg : str, default="hello"'),
        # Format: `, default: XXX`
        ('arg : int, default: 10', 'arg : int, default=10'),
        ('arg : str, default: "hello"', 'arg : str, default="hello"'),
        # Format: `, default:    XXX` (multiple spaces after colon)
        ('arg : int, default:    10', 'arg : int, default=10'),
        ('arg : str, default:    "hello"', 'arg : str, default="hello"'),
        # Format: `, default  :   XXX` (multiple spaces around colon)
        ('arg : int, default  :   10', 'arg : int, default=10'),
        ('arg : str, default  :   "hello"', 'arg : str, default="hello"'),
        # With leading indentation
        ('  arg : int default 10', '  arg : int, default=10'),
        (
            '    arg : str, default is "hello"',
            '    arg : str, default="hello"',
        ),
        (
            '        arg : bool default: True',
            '        arg : bool, default=True',
        ),
        # Complex default values
        (
            'arg : dict[str, int] default {}',
            'arg : dict[str, int], default={}',
        ),
        (
            'arg : list[str] default ["a", "b"]',
            'arg : list[str], default=["a", "b"]',
        ),
        ('arg : float default 3.14159', 'arg : float, default=3.14159'),
        ('arg : str default None', 'arg : str, default=None'),
        # Already in correct format (should remain unchanged)
        ('arg : int, default=10', 'arg : int, default=10'),
        ('arg : str, default="hello"', 'arg : str, default="hello"'),
        # Lines without default (should remain unchanged)
        ('arg : int', 'arg : int'),
        ('arg : str', 'arg : str'),
        ('  arg : bool', '  arg : bool'),
        # Case insensitive "default"
        ('arg : int Default 10', 'arg : int, default=10'),
        ('arg : int DEFAULT 10', 'arg : int, default=10'),
        ('arg : int, Default: 10', 'arg : int, default=10'),
    ],
)
def test_standardize_default_value(line: str, expected: str) -> None:
    assert _standardize_default_value(line) == expected


@pytest.mark.parametrize(
    ('src', 'expected'),
    [
        # --- should fix (inline literals) ---
        ('Use `foo` to do something', 'Use ``foo`` to do something'),
        ('Edge punctuation: `x`.', 'Edge punctuation: ``x``.'),
        (
            'Multiple inline literals: `a` and `b`.',
            'Multiple inline literals: ``a`` and ``b``.',
        ),
        (
            'Underscores inside literal are fine: `foo_bar`.',
            'Underscores inside literal are fine: ``foo_bar``.',
        ),
        (
            'Adjacent to parentheses: (`call_me`) and `ok`',
            'Adjacent to parentheses: (``call_me``) and ``ok``',
        ),
        # Edge cases: literals that contain special characters -> should fix
        ('`>>> `', '``>>> ``'),
        ('`... `', '``... ``'),
        # --- should not fix (roles) ---
        (':emphasis:`word`', ':emphasis:`word`'),
        (':strong:`bold`', ':strong:`bold`'),
        (':sup:`2`', ':sup:`2`'),
        (
            ':title-reference:`The Great Book`',
            ':title-reference:`The Great Book`',
        ),
        # --- should not fix (cross-references & links) ---
        ('See `Section`_ for details', 'See `Section`_ for details'),
        (
            'See `Docs`__ for the anonymous reference',
            'See `Docs`__ for the anonymous reference',
        ),
        (
            '`Python <https://www.python.org>`_',
            '`Python <https://www.python.org>`_',
        ),
        # --- should not fix (already correct literals) ---
        (
            'Already has ``double`` backticks',
            'Already has ``double`` backticks',
        ),
        # --- should not fix (explicit hyperlink target) ---
        (
            '.. _`Special Target`: https://example.com/special',
            '.. _`Special Target`: https://example.com/special',
        ),
        # --- should not fix (multi-line external links) ---
        (
            "Here's another example where long URLs"
            ' extend to the next line `Here is perhaps\n'
            'the Link <https://www.this-is-a-url-that-is-long.com>`_'
            ' and `Another One\n'
            '<https://www.this-is-another-url-that-is-long.com>`_.',
            "Here's another example where long URLs extend to"
            ' the next line `Here is perhaps\n'
            'the Link <https://www.this-is-a-url-that-is-long.com>`_'
            ' and `Another One\n'
            '<https://www.this-is-another-url-that-is-long.com>`_.',
        ),
        # --- should not fix (REPL lines with backticks) ---
        (
            '>>> # Use `config` parameter to customize `mode`\n'
            '... # and set the `threshold` value',
            '>>> # Use `config` parameter to customize `mode`\n'
            '... # and set the `threshold` value',
        ),
    ],
)
def test_fix_rst_backticks_cases(src: str, expected: str) -> None:
    assert _fix_rst_backticks(src) == expected


@pytest.mark.parametrize(
    ('fix_rst_backticks', 'input_docstring', 'expected_docstring'),
    [
        (
            True,
            '\nThis is a `string`!\n',
            '\nThis is a ``string``!\n',
        ),
        (
            False,
            '\nThis is a `string`!\n',
            '\nThis is a `string`!\n',
        ),
    ],
)
def test_fix_rst_backticks_option_on_and_off(
        *,
        fix_rst_backticks: bool,
        input_docstring: str,
        expected_docstring: str,
) -> None:
    """
    Verify the ``fix_rst_backticks`` option can be correctly turned on/off
    """
    result = wrap_docstring(
        input_docstring,
        line_length=79,
        docstring_style='numpy',
        fix_rst_backticks=fix_rst_backticks,
    )
    assert result == expected_docstring
