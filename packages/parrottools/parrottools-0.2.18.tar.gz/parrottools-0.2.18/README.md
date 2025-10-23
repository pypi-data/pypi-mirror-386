# Parrot tools


## Modules

[Logging](docs/logging.md)


## Development

Install dependencies

```bash
make install
```

Install pre-commit hook to avoid commiting invalid code:

```bash
make pre-commit-install
```

## Tests

Run all tests:

```bash
make test
```


## Release process

Branch `main` is published to Test PyPI.

Tags are published to PyPI. To create a new release execute:

```
gh release create <version>
```

in the terminal or create a release in the GitHub UI.
