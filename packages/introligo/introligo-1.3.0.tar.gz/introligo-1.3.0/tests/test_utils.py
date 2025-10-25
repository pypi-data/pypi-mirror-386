"""Tests for utility functions (slugify and count_display_width)."""

from introligo.utils import count_display_width, slugify


class TestSlugify:
    """Test cases for the slugify function."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello_world"

    def test_slugify_special_characters(self):
        """Test slugify with special characters."""
        assert slugify("Hello@World#2024!") == "helloworld2024"

    def test_slugify_unicode(self):
        """Test slugify with unicode characters."""
        assert slugify("Café") == "cafe"
        assert slugify("naïve") == "naive"

    def test_slugify_multiple_spaces(self):
        """Test slugify with multiple spaces."""
        assert slugify("Hello   World") == "hello_world"

    def test_slugify_leading_trailing_spaces(self):
        """Test slugify with leading/trailing spaces."""
        assert slugify("  Hello World  ") == "hello_world"

    def test_slugify_hyphens(self):
        """Test slugify with hyphens."""
        assert slugify("Hello-World-Test") == "hello_world_test"

    def test_slugify_underscores(self):
        """Test slugify preserves underscores."""
        assert slugify("Hello_World") == "hello_world"

    def test_slugify_mixed(self):
        """Test slugify with mixed characters."""
        assert slugify("My-Module 2.0 (beta)") == "my_module_20_beta"

    def test_slugify_empty(self):
        """Test slugify with empty string."""
        assert slugify("") == "unnamed"

    def test_slugify_only_special_chars(self):
        """Test slugify with only special characters."""
        assert slugify("@#$%^&*()") == "unnamed"

    def test_slugify_numbers(self):
        """Test slugify with numbers."""
        assert slugify("Module123") == "module123"

    def test_slugify_consecutive_underscores(self):
        """Test slugify removes consecutive underscores."""
        assert slugify("Hello___World") == "hello_world"


class TestCountDisplayWidth:
    """Test cases for the count_display_width function."""

    def test_count_display_width_basic(self):
        """Test basic display width counting."""
        assert count_display_width("Hello") == 5

    def test_count_display_width_with_emoji(self):
        """Test display width with emojis."""
        # Emoji should add extra width
        text = "Hello 🎉"
        width = count_display_width(text)
        assert width > len(text)

    def test_count_display_width_multiple_emojis(self):
        """Test display width with multiple emojis."""
        text = "🚀 Rocket 🎉 Party"
        width = count_display_width(text)
        # Two emojis should add 2 to the length
        assert width == len(text) + 2

    def test_count_display_width_no_emoji(self):
        """Test display width without emojis."""
        text = "Regular Text 123"
        assert count_display_width(text) == len(text)

    def test_count_display_width_empty(self):
        """Test display width with empty string."""
        assert count_display_width("") == 0

    def test_count_display_width_special_emoji(self):
        """Test display width with various emoji types."""
        # Sparkles
        assert count_display_width("✨") == 2
        # Check mark
        assert count_display_width("✅") == 2
        # Star
        assert count_display_width("⭐") == 2

    def test_count_display_width_mixed_content(self):
        """Test display width with mixed content."""
        text = "API Documentation ✅"
        width = count_display_width(text)
        assert width > len(text)
