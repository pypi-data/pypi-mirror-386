"""test_g_code_transformer.py

Unit tests for GCodeTransformer"""

from g_code_transformer import GCodeTransformer


def test__remove_extra_footer():
    """happy path"""

    footer = "a\nM18\na"

    assert GCodeTransformer._remove_extra_footer(footer) == "a\nM18"


def test__modify_initial_comments():
    """happy path"""

    code = ";a\na\n;a"
    expected_result = "a\n;a"

    assert GCodeTransformer._remove_initial_comments(code) == expected_result
