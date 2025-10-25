"""Tests for markdown link conversion to RST format."""

from introligo.markdown_converter import (
    convert_markdown_links_to_rst,
    convert_markdown_table_to_rst,
    convert_markdown_to_rst,
)


class TestMarkdownLinkConversion:
    """Test markdown link conversion to reStructuredText."""

    def test_external_link_conversion(self):
        """Test external HTTP/HTTPS links are converted correctly."""
        # Test external link conversion
        markdown = "[Documentation](https://example.com/docs)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == "`Documentation <https://example.com/docs>`_"

        # Test HTTPS link
        markdown = "[Secure Site](https://secure.example.com)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == "`Secure Site <https://secure.example.com>`_"

    def test_internal_document_link_conversion(self):
        """Test internal .md links are converted to :doc: references."""
        # Test .md file link
        markdown = "[Setup Guide](./setup.md)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == ":doc:`Setup Guide <setup>`"

        # Test relative path with .md (preserves directory structure)
        markdown = "[Config](../config/settings.md)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == ":doc:`Config <../config/settings>`"

    def test_anchor_link_conversion(self):
        """Test anchor links are converted to :ref: references."""
        # Test anchor link
        markdown = "[Jump to section](#installation)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == ":ref:`installation`"

    def test_image_conversion(self):
        """Test image markdown is converted to RST image directive."""
        # Test image conversion
        markdown = "![Logo](./assets/logo.png)"
        result = convert_markdown_links_to_rst(markdown)
        assert ".. image:: ./assets/logo.png" in result
        assert ":alt: Logo" in result

    def test_mixed_links_in_line(self):
        """Test multiple different link types in one line."""
        # Test multiple links
        markdown = "See [docs](https://example.com) and [Setup Guide](./setup.md)"
        result = convert_markdown_links_to_rst(markdown)
        assert "`docs <https://example.com>`_" in result
        assert ":doc:`Setup Guide <setup>`" in result

    def test_full_markdown_to_rst_conversion(self):
        """Test complete markdown conversion including links."""
        markdown = """## Getting Started

For more information, see [Documentation](https://example.com/docs) and [Setup Guide](./setup.md).

- [External link](https://github.com/example)
- [Internal doc](./guide.md)
- [Anchor](#section)
"""

        result = convert_markdown_to_rst(markdown)

        # Check header conversion (demoted by default: ## -> H3)
        assert "Getting Started" in result
        assert "~~~~~~~~~~~~~~~" in result  # H3 underline (demoted from ##)

        # Check link conversions
        assert "`Documentation <https://example.com/docs>`_" in result
        assert ":doc:`Setup Guide <setup>`" in result
        assert "`External link <https://github.com/example>`_" in result
        assert ":doc:`Internal doc <guide>`" in result
        assert ":ref:`section`" in result

    def test_rst_file_link_conversion(self):
        """Test .rst file links are also converted."""
        # Test .rst file link
        markdown = "[API Reference](./api.rst)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == ":doc:`API Reference <api>`"

    def test_internal_link_with_anchor(self):
        """Test internal document links with anchors are converted correctly."""
        # Test .md file link with anchor
        markdown = "[Running Code in Devcontainer](./devcontainer_usage.md#prerequisites)"
        result = convert_markdown_links_to_rst(markdown)
        # Should convert to doc link with section info in the text
        assert ":doc:`" in result
        assert "devcontainer_usage" in result
        assert "Prerequisites" in result or "prerequisites" in result.lower()

        # Test with different anchor format
        markdown = "[Setup Guide](./setup.md#installation-steps)"
        result = convert_markdown_links_to_rst(markdown)
        assert ":doc:`" in result
        assert "setup" in result
        # Should include the section name in some form
        assert "Installation" in result or "Steps" in result

    def test_external_link_with_anchor(self):
        """Test external links with anchors are preserved correctly."""
        # External link with anchor should preserve the anchor
        markdown = "[Docker Installation](https://docs.docker.com/get-docker#linux)"
        result = convert_markdown_links_to_rst(markdown)
        assert result == "`Docker Installation <https://docs.docker.com/get-docker#linux>`_"

    def test_preserves_code_blocks(self):
        """Test that links inside code blocks are NOT converted."""
        markdown = """```python
# This [link](https://example.com) should not be converted
print("hello")
```"""

        result = convert_markdown_to_rst(markdown)

        # Link should remain unchanged inside code block
        assert "[link](https://example.com)" in result
        assert ".. code-block:: python" in result

    def test_table_conversion(self):
        """Test markdown table to RST list-table conversion."""
        markdown = """## Features

| Feature | Status | Notes |
|---------|--------|-------|
| Links | ✅ Yes | All types |
| Images | ✅ Yes | With alt |
| Tables | ✅ Yes | List-table |

End of table."""

        result = convert_markdown_to_rst(markdown)

        # Check for list-table directive
        assert ".. list-table::" in result
        assert ":header-rows: 1" in result
        assert ":widths: auto" in result

        # Check for table content
        assert "Feature" in result
        assert "Status" in result
        assert "Links" in result
        assert "✅ Yes" in result
        assert "List-table" in result

        # Check structure
        assert "* -" in result  # List-table row marker

    def test_link_with_parent_directory_path(self):
        """Test links with ../ parent directory paths are handled correctly."""
        # Test ../ path with anchor (lines 1093-1095)
        # The elif branch is only in the anchor handling function
        markdown = "[Parent Doc](../parent/document.md#section)"
        result = convert_markdown_links_to_rst(markdown)
        assert ":doc:`" in result
        assert "../parent/document" in result

    def test_link_text_contains_section_name(self):
        """Test when link text already contains the section name (line 1105)."""
        # Link where text already mentions the section
        markdown = "[Prerequisites Section](./setup.md#prerequisites)"
        result = convert_markdown_links_to_rst(markdown)
        # Should not duplicate "Prerequisites" in the text
        assert ":doc:`Prerequisites Section <setup>`" in result
        assert result.count("Prerequisites") == 1

    def test_table_with_insufficient_lines(self):
        """Test table parsing with insufficient lines (lines 1178, 1194)."""
        # Test line 1178: Call table parser directly with only 1 line
        lines = ["|  |"]
        rst_table, end_idx = convert_markdown_table_to_rst(lines, 0)
        assert rst_table == []  # Should return empty list
        assert end_idx == 0  # Should return start index

        # Test line 1194: Table lines that produce no valid rows after filtering
        # Lines with only a single pipe have no cells after filtering
        lines = ["|", "|"]  # Two lines but produce 0 rows after filtering
        rst_table, end_idx = convert_markdown_table_to_rst(lines, 0)
        # After filtering, all cells are empty, so rows < 2
        assert rst_table == []
        assert end_idx == 0
