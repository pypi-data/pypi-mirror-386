# mkdocs-link-cards

Discord-style **link previews** for MkDocs, rendered as **Material** cards at build time.

- ✅ Static HTML output (GitHub Pages friendly)
- ✅ YouTube, arXiv, X/Twitter adapters
- ✅ Generic OpenGraph/Twitter/JSON-LD fallback
- ✅ Cache with TTL, polite UA/timeouts
- ✅ Typed, linted (Ruff), MyPy-clean, tested

![demo](https://user-images.githubusercontent.com/placeholder/demo.gif)

## Install

```bash
poetry add mkdocs-link-cards
# or: pip install mkdocs-link-cards
```

## Configure (`mkdocs.yml`)

```yaml
plugins:
  - search
  - link-cards:
      ttl: 604800      # 7 days
      timeout: 8
      allow_domains: []   # optional safelist
      deny_domains: []    # optional blocklist
```

## Use in Markdown

```md
[[card https://arxiv.org/abs/2501.01234]]
[[card https://www.youtube.com/watch?v=dQw4w9WgXcQ title="Optional override"]]
[[card https://x.com/trydaily/status/1840107...]]
[[card https://example.com/interesting-article]]
```

The plugin outputs Material’s card markup, so your site inherits all theme styles:

```html
<div class="grid cards" markdown>
-   <img ... class="linkcard-img">
    <strong>Title</strong>
    <small>Site</small>
    ---
    Description...

    <a class="md-button" href="...">Open</a>
</div>
```

### Notes

* **Static**: previews update when you rebuild (or when cache TTL expires).
* **Privacy/Robustness**: Icons are data-URIs. Thumbnails are remote (YouTube); others are taken from page metadata if available.
* **CI**: tests mock the network; builds are deterministic.

## Extras

Optional extras (not required):

```bash
poetry add mkdocs-link-cards[oembed]
poetry add mkdocs-link-cards[summarize]
```

## Roadmap

* Provider adapters for GitHub repos, Substack, arXiv PDF direct links
* Async fetch with `httpx` + concurrency controls
* CLI: `mkcards warm docs/` to pre-cache links
* Jinja templates for custom card layouts

## License

MIT © Contributors
