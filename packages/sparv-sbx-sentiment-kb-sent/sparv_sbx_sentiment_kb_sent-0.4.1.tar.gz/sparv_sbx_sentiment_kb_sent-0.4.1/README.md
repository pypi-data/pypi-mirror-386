# sparv-sbx-sentiment-kb-sent

[![PyPI version](https://img.shields.io/pypi/v/sparv-sbx-sentiment-kb-sent/0.4.1.svg)](https://pypi.org/project/sparv-sbx-sentiment-kb-sent/)
[![PyPI license](https://img.shields.io/pypi/l/sparv-sbx-sentiment-kb-sent/0.4.1.svg)](https://pypi.org/project/sparv-sbx-sentiment-kb-sent/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/sparv-sbx-sentiment-kb-sent/0.4.1.svg)](https://pypi.org/project/sparv-sbx-sentiment-kb-sent)

[![Maturity badge - level 2](https://img.shields.io/badge/Maturity-Level%202%20--%20First%20Release-yellowgreen.svg)](https://github.com/spraakbanken/getting-started/blob/main/scorecard.md)
[![Stage](https://img.shields.io/pypi/status/sparv-sbx-sentiment-kb-sent/0.4.1.svg)](https://pypi.org/project/sparv-sbx-sentiment-kb-sent/)

[![CI(check)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/check.yml/badge.svg)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/check.yml)
[![CI(test)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/test.yml/badge.svg)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/test.yml)
[![CI(scheduled)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/scheduled.yml/badge.svg)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/scheduled.yml)
[![CI(release)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/release-sentence-sentiment-kb-sent.yml/badge.svg)](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/actions/workflows/release-sentence-sentiment-kb-sent.yml)
[![Codecov](https://codecov.io/gh/spraakbanken/sparv-sbx-sentiment-kb-sent/coverage.svg)](https://codecov.io/gh/spraakbanken/sparv-sbx-sentiment-kb-sent)

Plugin for computing sentiment as a [Sparv](https://github.com/spraakbanken/sparv) annotation.

## Install

### With [pipx](https://pipx.pypa.io/latest/)

First, install Sparv as suggested:

```bash
pipx install sparv
```

Then install `sparv-sbx-sentiment-kb-sent` with

```bash
sparv plugins install sparv-sbx-sentiment-kb-sent
```

or, you can also install `sparv-sbx-sentiment-kb-sent` with

```bash
pipx inject sparv sparv-sbx-sentiment-kb-sent
```

### With [uv-pipx](https://github.com/pytgaen/uv-pipx)

First, install Sparv as recommended:

```shell
uvpipx install sparv
```

Then install `sparv-sbx-sentiment-kb-sent` with

```bash
sparv plugins install sparv-sbx-sentiment-kb-sent
```

or, you can also install `sparv-sbx-sentiment-kb-sent` with

```shell
uvpipx install sparv-sbx-sentiment-kb-sent --inject sparv
```

## Usage

Depending on how many explicit exports of annotations you have you can decide to use this
annotation exclusively by adding it as the only annotation to export under `xml_export`:

```yaml
xml_export:
  annotations:
    - <sentence>:sbx_sentiment_kb_sent.sentiment--kb-sent
```

To use it together with other annotations you might add it under `export`:

```yaml
export:
    annotations:
        - <sentence>:sbx_sentiment_kb_sent.sentiment--kb-sent
        ...
```

### Configuration

You can configure this plugin in the following way.

#### Number of Decimals

The number of decimals defaults to `3` but can be configured in `config.yaml`:

```yaml
sbx_sentiment_kb_sent:
  num_decimals: 3
```

> [!NOTE] This also controls the cut-off, so all values where the score round to 0.000 (or the number of decimals) is discarded.

### Metadata

#### Model

| Type      | HuggingFace Model                                                                                                     | Revision                                 |
| --------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Model     | [`KBLab/robust-swedish-sentiment-multiclass`](https://huggingface.co/KBLab/robust-swedish-sentiment-multiclass)       | b0ec32dca56aa6182a6955c8f12129bbcbc7fdbd |
| Tokenizer | [`KBLab/megatron-bert-large-swedish-cased-165k`](https://huggingface.co/KBLab/megatron-bert-large-swedish-cased-165k) | 90c57ab49e27b820bd85308a488409dfea25600d |

## Supported Python versions

This library thrives to support a Python version to End-Of-Life, and will at
least bump the minor version when support for a Python version is dropped.

The following versions of this library supports these Python versions:

- v0.4: Python 3.11
- v0.3: Python 3.11
- v0.2: Python 3.8

## Changelog

This project keeps a [changelog](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/blob/0.4.1/CHANGELOG.md).

## License

This repository is licensed under the [MIT](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/blob/0.4.1/LICENSE) license.

## Development

### Development prerequisites

- [`uv`](https://docs.astral.sh/uv/)
- [`pre-commit`](https://pre-commit.org)

For starting to develop on this repository:

- Clone the repo (in one of the ways below): (in one of the ways below):
  - `git clone git@github.com:spraakbanken/sparv-sbx-sentiment-kb-sent.git`
  - `git clone https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent.git`
- Setup environment: `make dev`
- Install `pre-commit` hooks: `pre-commit install`

Do your work.

Tasks to do:

- Test the code with `make test` or `make test-w-coverage`.
- Lint the code with `make lint`.
- Check formatting with `make check-fmt`.
- Format the code with `make fmt`.
- Type-check the code with `make type-check`.
- Test the examples with:
  - `make test-example-small-txt`
  - `make test-example-issue-10`

This repo uses [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).

### Release a new version

#### sparv-sbx-sentiment-kb-sent

- Prepare the CHANGELOG: `make prepare-release`.
- Edit `CHANGELOG.md` to your liking.
- Add to git: `git add --update`
- Commit with `git commit -m 'chore(release): prepare release'` or `cog commit chore 'prepare release' release`.
- Bump version (depends on [`bump-my-version](https://callowayproject.github.io/bump-my-version/))
  - Major: `make bumpversion part=major`
  - Minor: `make bumpversion part=minor`
  - Patch: `make bumpversion part=patch` or `make bumpversion`
- Push `main` and tags to GitHub: `git push main --tags` or `make publish`
  - [GitHub Actions workflow](https://github.com/spraakbanken/sparv-sbx-sentiment-kb-sent/blob/0.4.1/.github/workflows/release-sentence-sentiment-kb-sent.yaml) will build, test and publish the package to [PyPi](https://pypi.prg).
- Add metadata for [Språkbanken's resource](https://spraakbanken.gu.se/resurser)
  - Generate metadata: `make generate-metadata`
  - Upload the files from `assets/metadata/export/sbx_metadata/analysis` to <https://github.com/spraakbanken/metadata/tree/main/yaml/analysis>.
