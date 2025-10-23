# lobby-ai (npx wrapper)

This is a thin npm wrapper that lets you run the Python-based LOBBY CLI via `npx`:

```bash
npx lobby-ai --help
npx lobby-ai setup
npx lobby-ai request "Build a web scraper"
```

The wrapper tries the following in order:
1. Existing `lobby` binary on your PATH
2. `python3 -m lobby.cli` (if the Python package is installed)
3. `python -m lobby.cli`
4. `pipx run lobby-ai` (ephemeral install)
5. `uvx lobby-ai`

If none are available, it prints clear instructions to install the Python CLI.

## Force a specific Python
```bash
LOBBY_NODE_WRAPPER_PYTHON=python3 npx lobby-ai --help
```

## Publish to npm
```bash
cd npm/lobby-ai
npm publish --access public
```

After publishing, users can run:
```bash
npx lobby-ai setup
```

MIT licensed.
