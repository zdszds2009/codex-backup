## Summary

Describe the change in one or two sentences.

## Validation

- [ ] `python -m unittest discover -s tests -p "test_*.py"`
- [ ] `python -m py_compile .\scripts\build_restore_package.py .\scripts\restore_package.py`

## Risk review

- [ ] This change affects package contents
- [ ] This change affects restore behavior
- [ ] This change affects privacy or file-collection boundaries
- [ ] README or docs were updated when behavior changed
