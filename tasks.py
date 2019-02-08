from invoke import task


@task
def test(context):
    """
    Runs tests

    Notes
    -----
    * We utilize `python -m pytest` to ensure that our package is automatically
    appended to `sys.path`. Invoking pytest directly will require the package
    to be added to the path manually
    * Invoke escapes color sequences which will make the output look not ideal.
    This can be circumvented passing in `pty=True` in `run` command but said
    command is not enabled on Windows. If you want colored output during development,
    please invoke the call manually.

    """
    context.run("python -m pytest -v")


@task
def clean(context):
    # Remove caches
    context.run('find -name "__pycache__" -not -path "./.venv/*" | xargs rm -rf')
    format_code(context)
    sort_imports(context)


@task
def sort_imports(context):
    """
    Sort module import orders

    Notes
    -----
    - This works on all Python files rather than working only on a diff as the
    size of this project is tiny. Should that change, we can leverage diff
    or git hooks.

    See Also
    --------
    * https://github.com/timothycrosley/isort

    """
    context.run('find -name "*.py" -not -path "./.venv/*" | xargs isort')


@task
def format_code(context):
    """
    Format all Python files using Black formatter.

    Notes
    -----
    - Black only formats files that are changed or unformatted and
    hence no diffing mechanism is necessary. Additionally, is defaults to
    ignoring commonly ignored paths such as `dist`, `build`, etc

    See Also
    --------
    * https://github.com/ambv/black

    """
    context.run("black .")
