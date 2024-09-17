# Contributing to imxInsights

First off ❤️ ️ ️thanks for taking the time to contribute! 

All types of contributions are encouraged and valued!!! Please make sure to read the relevant section before making your contribution.
It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions.



## Development

### Setup environment

We use [Hatch](https://hatch.pypa.io/latest/install/) to manage the development environment and production build. Ensure it's installed on your system.

```bash
hatch build env
```

#### Local environments
[Hatch configuration](https://hatch.pypa.io/1.0/config/hatch/):
>
> Configuration for Hatch itself is stored in a `config.toml` file located by default in one of the following platform-specific directories.
>
> | Platform | Path |
> | --- | --- |
> | macOS | `~/Library/Application Support/hatch` |
> | Windows | `%USERPROFILE%\AppData\Local\hatch` |
> | Unix | `$XDG_CONFIG_HOME/hatch` (the [XDG_CONFIG_HOME](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables) environment variable default is `~/.config`) |
>
> If you wanted to store virtual environments in a .venv directory within your home directory, you could specify the following in the `config.toml`:
>
> ```toml
> [dirs.env]
> virtual = ".venv"
> ```

### Run unit tests

You can run all the tests with:

```bash
hatch run test
```

### Format the code

Execute the following command to apply linting and check typing:

```bash
hatch run lint
```

### Publish a new version

You can bump the version, create a commit and associated tag with one command:

```bash
hatch version patch
```

```bash
hatch version minor
```

```bash
hatch version major
```

Your default Git text editor will open so you can add information about the release.

When you push the tag on GitHub, the workflow will automatically publish it on PyPi and a GitHub release will be created as draft.

## Serve the documentation

You can serve the Mkdocs documentation with:

```bash
hatch run docs-serve
```

It'll automatically watch for changes in your code.


## Styleguides

Todo

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji: [https://gitmoji.dev/](https://gitmoji.dev/)

## Code of Conduct

This project and everyone participating in it is governed by the
[Code of Conduct](https://xxxxxx).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <>.

## init project started with
frankie coociecutter hipster stuff
https://github.com/frankie567/cookiecutter-hipster-pypackage
