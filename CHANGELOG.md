# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Breaking: `arun convert` now requires the input file to come before options, and bare conversion without options is not allowed. Use:
  - Correct: `arun convert file.curl --outfile out.yaml`
  - Incorrect: `arun convert --outfile out.yaml file.curl`
- Breaking: OpenAPI conversion moved to a top-level command: `arun convert-openapi ...` (was `arun convert openapi ...`).
- Enhancement: Top-level `arun convert` accepts and forwards `--redact` and `--placeholders` to the underlying importer.
- Fix: Ensure `config.variables` is always a dictionary during conversion (avoid `None` ValidationError).

