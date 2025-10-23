# Contributing to `fleetmaster`

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/eelcovv/fleetmaster/issues>

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

### Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

fleetmaster could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at <https://github.com/eelcovv/fleetmaster/issues>.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started

Ready to contribute? Here's how to set up `fleetmaster` for local development.
Please note this documentation assumes you already have `uv` and `Git` installed and ready to go.

1. Fork the `fleetmaster` repo on GitHub.

2. Clone your fork locally:

   ```bash
   cd <directory_in_which_repo_should_be_created>
   git clone git@github.com:YOUR_NAME/fleetmaster.git
   ```

3. Now we need to install the environment. Navigate into the directory

   ```bash
   cd fleetmaster
   ```

   Then, install and activate the environment with:

   ```bash
   uv sync
   ```

4. Install pre-commit to run linters/formatters at commit time:

   ```bash
   uv run pre-commit install
   ```

5. Create a branch for local development:

   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```

   Now you can make your changes locally.

6. Don't forget to add test cases for your added functionality to the `tests` directory.

7. When you're done making changes, check that your changes pass the formatting tests.

   ```bash
   just check
   ```

8. Now, validate that all unit tests are passing:

   ```bash
   just test
   ```

9. Before raising a pull request you should also run tox.
   This will run the tests across different versions of Python:

   ```bash
   tox
   ```

   This requires you to have multiple versions of python installed.
   This step is also triggered in the CI/CD pipeline, so you could also choose to skip this step locally.

10. Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

11. Submit a pull request through the GitHub website.

Done!

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.

## Developers tips and tricks

### vscode

In case you want to add a quick launcher under `.vscode/launcher.json`, an example is:

```json
    "configurations": [
              {
            "name": "fleetmaster draf 1m",
            "type": "debugpy",
            "request": "launch",
            "module": "fleetmaster.cli",
            "console": "integratedTerminal",
            "args": ["-v", "run", "examples/defraction_box_1m.stl"],
            "justMyCode": true
        },
    ]
```

### direnv

If you are only using a Python virtual environment (without Nix), you can use `direnv` to activate it automatically.
Create a `.envrc` file with the following content:

```shell
# Load the Python virtual environment if it exists
if [ -d .venv ]; then
  layout python .venv
fi
```

### linux

To install in linux

### nixos

To run the this packagine in a nix os environment, use the flake below to activate your environment.:

```nix
{
  description = "Development environment for the fleetmaster project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # Python en package manager
            python312
            uv

            # Core dependencies voor de GUI
            vtk
            qt6.full

            # Essentiële libraries voor rendering en windowing
            mesa
            libglvnd
            wayland
            libxkbcommon
            xorg.libX11
            xorg.libXcursor
            xorg.libXrandr
            xorg.libXi
            fontconfig
            freetype
            harfbuzz
          ];
        };
      });
}
```

Activate the flake with

```
use flake flake.nix
```
