# Shell commands
- All Python commands should run with uv

# Code style
- Do not reformat for line length in Python or make other changes that ruff can automatically fix
- Avoid using `cast`
- Do not add comments unless the code is extremely unclear without
- We enforce keyword arguments where possible, and mypy will report errors if this is not done

# Workflow
- Be sure to typecheck when you’re done making a series of code changes
- Prefer running the whole test suite rather than one test
- Our test suite requires 100% line and branch coverage, so do not make an `if` statement unless both the if statement and the else will be covered in a test
- To avoid getting stuck in an interactive prompt, do not use `help` in Python. Instead, use import `import inspect; doc = inspect.getdoc(str) ;    print(doc)` for example for `str`
