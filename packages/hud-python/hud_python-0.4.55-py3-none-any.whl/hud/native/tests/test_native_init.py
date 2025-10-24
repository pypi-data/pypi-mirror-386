"""Tests for hud.native.__init__ module."""

from __future__ import annotations


class TestNativeInit:
    """Tests for the native package initialization."""

    def test_comparator_server_import(self):
        """Test that comparator server can be imported."""
        from hud.native.comparator import comparator
        from hud.server import MCPServer

        # Verify comparator is an MCPServer instance
        assert isinstance(comparator, MCPServer)
        assert comparator.name == "comparator"

    def test_all_exports(self):
        """Test that __all__ is properly defined."""
        import hud.native.comparator

        expected_exports = ["comparator"]

        # Check __all__ exists and contains expected exports
        assert hasattr(hud.native.comparator, "__all__")
        assert hud.native.comparator.__all__ == expected_exports

        # Verify all items in __all__ are actually available
        for item in hud.native.comparator.__all__:
            assert hasattr(hud.native.comparator, item)

    def test_comparator_tools_registered(self):
        """Test that comparator server has tools registered."""
        from hud.native.comparator import comparator

        # The server should have tools registered
        # We can check that the tool manager has tools
        tool_names = [t.name for t in comparator._tool_manager._tools.values()]

        # Should have the main compare tool
        assert "compare" in tool_names

        # Should have the submit tool
        assert "response" in tool_names

        # Should have all the alias tools
        expected_aliases = [
            "compare_exact",
            "compare_text",
            "compare_string",
            "compare_numeric",
            "compare_float",
            "compare_int",
            "compare_json",
            "compare_boolean",
            "compare_list",
        ]

        for alias in expected_aliases:
            assert alias in tool_names, f"Expected alias {alias} not found"

        # Total should be 1 (submit) + 1 (compare) + 9 (aliases) = 11 tools
        assert len(tool_names) == 11

    def test_comparator_tool_functionality(self):
        """Test that we can get the CompareTool from the comparator."""
        from hud.native.comparator import comparator

        # Get the compare tool
        compare_tool = None
        for tool in comparator._tool_manager._tools.values():
            if tool.name == "compare":
                compare_tool = tool
                break

        assert compare_tool is not None
        # FastMCP wraps tools as FunctionTool instances
        assert hasattr(compare_tool, "name")
        assert compare_tool.name == "compare"
        # FunctionTool has a 'fn' attribute for the callable
        assert hasattr(compare_tool, "fn") or hasattr(compare_tool, "__call__")
