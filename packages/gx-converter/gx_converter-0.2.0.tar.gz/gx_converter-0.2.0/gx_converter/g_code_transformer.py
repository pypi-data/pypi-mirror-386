from re import sub, RegexFlag, match, search


class GCodeTransformer:
    """Reading and preparation of g-code"""

    BED_TEMPERATURE_COMMAND = "M140"
    NOZZLE_TEMPERATURE_COMMAND = "M104"

    @staticmethod
    def convert(gcode: str) -> str:
        """Modify g-code to match gx format

        Returns:
            Compatible g-code
        """

        gcode = GCodeTransformer._remove_initial_comments(gcode)
        gcode = GCodeTransformer._insert_dimensions(gcode)
        gcode = GCodeTransformer._add_initial_comments(gcode)
        gcode = GCodeTransformer._convert_absolute_positioning(gcode)
        gcode = GCodeTransformer._convert_temperature_commands(
            gcode, GCodeTransformer.BED_TEMPERATURE_COMMAND
        )
        gcode = GCodeTransformer._convert_temperature_commands(
            gcode, GCodeTransformer.NOZZLE_TEMPERATURE_COMMAND
        )
        gcode = GCodeTransformer._add_break_and_continue(gcode)
        # gcode = GCodeTransformer._turn_fans_on_early(gcode)
        gcode = GCodeTransformer._remove_inline_comments(gcode)
        gcode = GCodeTransformer._remove_extra_footer(gcode)

        return gcode

    @staticmethod
    def _turn_fans_on_early(gcode):
        """Turn fans on at the beginning, instead of after the 1st layer

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """
        gcode = sub("^M106.*\n", "", gcode, 1, RegexFlag.MULTILINE)
        gcode = sub("^M107.*", "M106", gcode, 1, RegexFlag.MULTILINE)
        return gcode

    @staticmethod
    def _convert_temperature_commands(gcode, command: str) -> str:
        """Add T0 to end of given command.

        Args:
            gcode: G-code to modify
            command: Command to which T0 should be appended

        Returns:
            Converted g-code
        """

        result = search(f"^{command}.*", gcode, RegexFlag.MULTILINE)
        if not result:
            return gcode

        result = result.group(0)
        result = result.strip() + " T0\n"

        gcode = sub(f"^{command}.*\n", result, gcode, 1, RegexFlag.MULTILINE)
        return gcode

    @staticmethod
    def _add_break_and_continue(gcode):
        """Add Break and Continue statement

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return sub("^G92 E0.*\n^G92 E0.*", "M108 T0", gcode, 1, RegexFlag.MULTILINE)

    @staticmethod
    def _convert_absolute_positioning(gcode):
        """Use compatible absolute positioning

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return sub("^M82.*", "G90", gcode, 1, RegexFlag.MULTILINE)

    @staticmethod
    def _remove_inline_comments(gcode):
        """Commands with inline comments are ignored entirely by the printer.

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return sub(" ;.*", "", gcode, flags=RegexFlag.MULTILINE)

    @staticmethod
    def _remove_initial_comments(gcode):
        """Remove initial Cura comments and add gx_converter comment

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        while match("^;", gcode):
            gcode = sub("^;.*\n", "", gcode)

        return gcode

    @staticmethod
    def _add_initial_comments(gcode):
        """Add gx_converter comment

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return ";created with gx-convert\n;github.com/bkienzle/gx-convert\n" + gcode

    @staticmethod
    def _insert_dimensions(gcode):
        """Add print dimensions.

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return "M118 X10.00 Y10.00 Z10.00 T0\n" + gcode

    @staticmethod
    def _remove_extra_footer(gcode):
        """Remove extra information at EOF. Anything after M18 (Disable steppers) is extraneous.

        Args:
            gcode: G-code to modify

        Returns:
            Converted g-code
        """

        return sub("^M18.*", "M18", gcode, 1, RegexFlag.DOTALL | RegexFlag.MULTILINE)
