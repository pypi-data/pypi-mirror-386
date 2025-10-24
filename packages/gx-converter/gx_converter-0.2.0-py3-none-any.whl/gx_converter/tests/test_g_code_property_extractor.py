"""test_g_code_property_extractor.py

This module contains unit tests for the GCodePropertyExtractor class"""

from g_code_property_extractor import GCodePropertyExtractor


def test_get_hotbed_temperature():
    """happy path"""
    gcode = "a\nM140 S1 T0\na"

    assert GCodePropertyExtractor.get_hotbed_temperature(gcode) == 1


def test__extract_comment_value():
    """happy path"""

    comment = "Layer height"
    code = "a\n;Layer height: 1.1111m\na"

    assert GCodePropertyExtractor._extract_comment_value(comment, code) == 1111
