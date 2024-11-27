# MkDocs Documentation

This document explains how Kagura AI uses MkDocs for documentation.

## Running the Local Server

To preview the documentation locally, use the following command:

```bash
poetry run mkdocs serve
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

## Building the Static Site

To generate the static site, execute:

```bash
poetry run mkdocs build
```

The generated files will be located in the `site/` directory.

## Deploying the Site

To deploy the site to GitHub Pages, use:

```bash
poetry run mkdocs gh-deploy
```

Ensure GitHub Pages is enabled in your repository settings.

## Configuration

The main configuration file is `mkdocs.yml`. Key sections include:

- **`site_name`**: The name of the documentation site.
- **`theme`**: Defines the visual theme (we use `material`).
- **`nav`**: Specifies the structure of the documentation.
- **`plugins`**: Adds functionality, like search and i18n support.

## References

- [MkDocs Official Documentation](https://www.mkdocs.org/)
- [MkDocs Material Theme](https://squidfunk.github.io/mkdocs-material/)
