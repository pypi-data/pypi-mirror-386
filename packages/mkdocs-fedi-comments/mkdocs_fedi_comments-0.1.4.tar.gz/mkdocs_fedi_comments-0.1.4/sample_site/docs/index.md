---
description: mkdocs_fedi_comment allows commenting from the Fediverse on mkdocs generated sites.
---

# Comments for mkdocs generated static sites

## Usage

This package does not enable comments for a mkdocs site by
itself. It requires a few things:

* A running [cattle_grid](https://bovine.codeberg.page/cattle_grid/) installation, including RabbitMQ and Postgresql
* A running [comments](https://helge.codeberg.page/comments/) installation linked to cattle_grid
* You probably must use [mkdocs-material](https://squidfunk.github.io/mkdocs-material/)

Once you have this you can use this plugin.

!!! tip
    You could replace these parts with equivalent implementations, as
    long as these satisfy what is described in [FEP-136c](https://helge.codeberg.page/comments/136c/fep-136c/)

### Installation

Currently, this plugin needs to be installed from git

```bash
pip install git+https://codeberg.org/helge/mkdocs_fedi_comments.git
```

### Configuration

Include the following in your mkdocs configuration file with
`base_path` replaced by the appropriate path.

```yaml title="mkdocs.yml"
plugins:
  - fedi-comments:
      base_path: https://comments.bovine.social/
```