# modpkgbuild

## Description

Creates one PKGBUILD from another PKGBUILD by applying a series of changes
specified in a YAML file. Designed to automatically generate alternative
versions of Arch Linux packages (e.g., enabling SELinux support, applying
security-related patches, etc.). This makes it possible to e.g. implement a
CI/CD pipeline that checks for updates to the relevant Arch package,
automatically generates an alternative PKGBUILD when there has been an update,
builds the alternative package in a clean container, and deploys it to a
custom Pacman repo.

The PKGBUILD is written to the current working directory. A diff between the
old PKGBUILD and the new PKGBUILD is written to stderr on success.

## Installation

This script is available on PyPI as `modpkgbuild`:

```
pip install modpkgbuild
```

## modpkgbuild.yml

`modpkgbuild` must be run in the same directory as a `modpkgbuild.yml`. The
`modpkgbuild.yml` must contain the following two fields:

| Key          | Value                         |
| ------------ | -------------------------------
| repo         | The URL to the git repository that contains the PKGBUILD you want to modify |
| replacements | A list of replacement objects |

A replacement object must contain three fields:

| Key         | Value                                                   |
| ----------- | ---------------------------------------------------------
| description | A description of the purpose of the replacement         |
| old         | A literal string you want to replace (may be multiline) |
| new         | A literal string you want to replace `old` with (may be multiline) |

Or, if the optional field `regex` is set to true, the fields mean the
following:

| Key         | Value                                                   |
| ----------- | ---------------------------------------------------------
| description | A description of the purpose of the replacement         |
| old         | A regular expression matching text you want to replace (may be multiline, and may contain captures) |
| new         | A replacement string (may be multiline, may contain backreferences) |

All replacements must be specified **in order**. Any failure to match is
considered an error. `modpkgbuild` is intentionally conservative in these ways
so that it can be relied on in an automated packaging pipeline to not produce
an incorrect PKGBUILD without an error.

Accordingly, the user should use literal strings in `modpkgbuild.yml` whenever
possible. Setting `regex` to true is to be discouraged unless there is a good
reason – for example, you may need to capture part of the match and reference
it in the replacement text.

## Project Status

This project is still in the planning phase and is not ready even for
experimental use.
