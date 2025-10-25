
# NaluConfigs

This repository houses all board configuration files (both register files and clock files).


## Installation

Generally you don't have to install this repository unless you plan to change anything.

If you do however want to install this package, the best way is to use our PyPI package:

```sh
pip install naluconfigs
```

### Developer Installation

To install this reposity for development the best way is to clone and install as an editable package.

First clone this repository to a suitable location:

```sh
git clone https://github.com/NaluScientific/naluconfigs.git
```

Then install the package into your Anaconda environment:

```sh
cd naluconfigs
pip install -e .
```

## Usage

In addition to the default board configuration files and clock files, the `naluconfigs` package
also contains functions to load or copy these files. Check out the package to see what you can do!

## Developers
Install this package as editable, and with development extras:
```
cd naluconfigs
pip install -e .[dev]
```

Make sure to read the `YAML HELP.md` file if you're new, or haven't kept up with NaluConfigs.

This project follows a X.Y.Z version scheme according to the following:

- Add/remove register files, increment X
- register adds / remove, increment Y
- register edits and/or value edits increment Z


### Pre-commit

This project uses pre-commit hooks to make sure the code is following the style guide.
To install the pre-commit hooks, run the following command:

```
    pre-commit install
```

The hooks will run automatically when you commit changes to the repository.

The code MUST run the pre-commit hooks before commiting. If the hooks fail, the commit will be rejected.

### Tests
The tests are located under the `naluconfigs/tests/` directory, and use [pytest](https://github.com/pytest-dev/pytest).
To run the tests, run `naluconfigs/run_tests.bat`. This will run the tests and also generate a coverage report to
`naluconfigs/coverage.xml`.

Make sure to keep the test coverage at 100%. This is doable, since NaluConfigs is a relatively simple package.
The [Coverage Gutters](https://marketplace.visualstudio.com/items?itemName=ryanluker.vscode-coverage-gutters)
extension is highly recommended to monitor test coverage.
