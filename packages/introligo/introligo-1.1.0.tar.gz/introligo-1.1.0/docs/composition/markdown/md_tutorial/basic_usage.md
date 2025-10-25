This section demonstrates the markdown inclusion feature with practical examples.

## Quick Start Checklist

Use this checklist to get started with markdown includes:

.. raw:: html

   <input type="checkbox" checked> Install Introligo and Sphinx<br>
   <input type="checkbox" checked> Create introligo configuration file<br>
   <input type="checkbox"> Identify existing markdown files to include<br>
   <input type="checkbox"> Add <code>markdown_includes</code> to module configuration<br>
   <input type="checkbox"> Run Introligo to generate RST files<br>
   <input type="checkbox"> Build documentation with Sphinx<br>
   <input type="checkbox"> Preview generated documentation

## Including Multiple Markdown Files

Multiple markdown files can be included in module documentation:

```yaml
# Include multiple markdown files
modules:
  my_module:
    title: "My Module"
    description: "Module with markdown documentation"
    module: "myproject.my_module"

    # Include markdown files
    markdown_includes:
      - "docs/user_guide.md"
      - "docs/api_reference.md"
      - "CONTRIBUTING.md"
```

## Single Markdown File

For simpler cases, a single file can be specified:

```yaml
# Include single file (string instead of list)
modules:
  my_module:
    title: "My Module"
    markdown_includes: "README.md"
```

## Relative Paths

All paths are resolved relative to the configuration file:

```yaml
# Config file at: docs/composition/introligo_config.yaml
modules:
  my_module:
    title: "My Module"
    # Include from project root
    markdown_includes:
      - "../../README.md"
      - "../../docs/guides/setup.md"
```

## Advantages of Markdown Includes

### Benefits

- **Reuse existing documentation**: Include README.md and other markdown files directly
- **DRY principle**: Avoid documentation duplication across formats
- **Easy maintenance**: Update once, changes reflect everywhere
- **Version control friendly**: Markdown files are easily reviewed in pull requests
- **Familiar format**: Write in markdown, generate RST documentation automatically

### Recommended Use Cases

- Project overviews and README files
- Detailed user guides and tutorials
- Contributing guidelines
- Changelog and release notes
- FAQ sections
