"""Creates one PKGBUILD from another by applying changes specified in a YAML file.

Designed to automatically generate alternative versions of Arch Linux packages
(e.g., enabling SELinux support, applying security-related patches, etc.).
Must be run in the same directory as a modpkgbuild.yml. The PKGBUILD is
written to the current working directory. A diff between the old PKGBUILD and
the new PKGBUILD is written to stderr on success.
"""

import argparse
import difflib
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


class ReplacementError(Exception):
    """An error in applying a replacement."""


class SpecError(Exception):
    """An error in modpkgbuild.yml."""


def write_new(new: str) -> None:
    """Writes the new PKGBUILD to `./PKGBUILD`."""
    pkgbuild_path = Path('PKGBUILD')

    if pkgbuild_path.is_file():
        message('warning: PKGBUILD exists. Saving as PKGBUILD.orig...')

        orig_path = Path('PKGBUILD.orig')

        if orig_path.is_file():
            raise FileExistsError('PKGBUILD.orig also exists')
        else:
            pkgbuild_path.rename(orig_path)

    pkgbuild_path.write_text(new)


def gen_new(old: str, spec: dict) -> str:
    """Applies the changes specified in `modpkgbuild.yml`."""
    new = ''
    pos = 0

    for r in spec['replacements']:
        # Save the position of the end of the last match in the old PKGBUILD
        prev_pos = pos

        if not r.get('regex', False):
            # Search for the next match in the old PKGBUILD, starting at the
            # end of the last match, so that the changes specified in
            # modpkgbuild.yml are applied in order. Advance the position
            # tracker to the position of the beginning of the next match. It
            # is an error if a match cannot be found.
            try:
                pos += old[prev_pos:].index(r['old'])
            except ValueError:
                raise ReplacementError(
                    f"substring '{r['old']}' "
                    f"in replacement '{r['description']}' not found"
                )

            # The text between the end of the last match and the start of the
            # next match are the same in the old PKGBUILD and in the new
            # PKGBUILD. Append it to the new PKGBUILD.
            new += old[prev_pos:pos]
            # At this position, append the replacement text to the new
            # PKGBUILD
            new += r['new']
            # Advance the position tracker, which tracks our position in the
            # old PKGBUILD, by the length of the matched and the replaced
            # text
            pos += len(r['old'])
        else:
            try:
                pattern = re.compile(r['old'])
            except re.PatternError as e:
                raise SpecError(
                    f"invalid regex in replacement '{r['description']}': {e}"
                )

            # Search for the next match in the old PKGBUILD, starting at the
            # end of the last match, so that the changes specified in
            # modpkgbuild.yml are applied in order
            match = re.search(pattern, old[prev_pos:])

            # It is an error if a match cannot be found
            if not match:
                raise ReplacementError(
                    f"pattern '{pattern.pattern}' "
                    f"in replacement '{r['description']}' not matched"
                )

            # Advance the position tracker to the position of the beginning of
            # the next match
            pos += match.start()
            # The text between the end of the last match and the start of the
            # next match are the same in the old PKGBUILD and in the new
            # PKGBUILD. Append it to the new PKGBUILD.
            new += old[prev_pos:pos]
            # At this position, append the replacement text to the new
            # PKGBUILD
            new += match.expand(r['new'])
            # Advance the position tracker, which tracks our position in the
            # old PKGBUILD, by the length of the matched and the replaced
            # text
            pos += len(match[0])

    # Append any remaining text in the old PKGBUILD to the new PKGBUILD
    new += old[pos:]
    return new


def read_old(repo: str) -> str:
    """Clones the upstream git repo and reads its PKGBUILD."""
    tmpdir = tempfile.TemporaryDirectory()

    subprocess.run(
        ['git', 'clone', repo, tmpdir.name],
        check=True,
        capture_output=True,
        text=True,
    )

    with open(Path(tmpdir.name) / 'PKGBUILD') as f:
        return f.read()


def parse_spec() -> dict:
    return validate_spec(load_spec())


def load_spec() -> dict:
    """Loads modpkgbuild.yml."""
    with open('./modpkgbuild.yml') as f:
        spec = yaml.load(f.read(), Loader=SafeLoader)

    return spec


def validate_spec(spec: dict) -> dict:
    if not isinstance(spec, dict):
        raise SpecError('expected a YAML mapping')

    try:
        if not isinstance(spec['repo'], str):
            raise SpecError("'repo' must be a string")
        elif not isinstance(spec['replacements'], list):
            raise SpecError("'replacements' must be a list")
    except KeyError as e:
        raise SpecError(f'missing required field {e}')

    for i, r in enumerate(spec['replacements']):
        try:
            if not isinstance(r['description'], str):
                raise SpecError(
                    f"'description' in replacement {i + 1} must be a string"
                )
            elif not isinstance(r['old'], str):
                raise SpecError(
                    f"'old' in replacement '{r['description']}' must be a string"
                )
            elif not isinstance(r['new'], str):
                raise SpecError(
                    f"'new' in replacement '{r['description']}' must be a string"
                )
        except KeyError as e:
            raise SpecError(
                'missing required field {} in replacement {}'.format(
                    e,
                    f"'{r['description']}'" if r.get('description') else i + 1,
                )
            )
            raise

    return spec


def parse_args():
    """Prints help message if necessary."""
    parser = argparse.ArgumentParser(
        description="""
Create one PKGBUILD from another by applying changes specified in a YAML file.
""",
        epilog="""
Must be run in the same directory as a modpkgbuild.yml.
The PKGBUILD is written to the current working directory.
Prints a diff to stderr on success.
""",
    )
    return parser.parse_args()


def message(*args: str, **kwargs):
    print('modpkgbuild.py:', *args, **kwargs, file=sys.stderr)


def main():
    parse_args()

    try:
        spec = parse_spec()
        old = read_old(spec['repo'])
        new = gen_new(old, spec)
        write_new(new)
    except OSError as e:
        message(
            f' {e.filename}:' if e.filename else ' ',
            e.strerror or str(e),
            sep='',
        )
        return 1
    except yaml.YAMLError as e:
        message('failed to parse modpkgbuild.yml:', str(e))
        return 2
    except SpecError as e:
        message('invalid modpkgbuild.yml:', str(e))
        return 2
    except subprocess.CalledProcessError as e:
        message(e.stderr)
        return e.returncode
    except ReplacementError as e:
        message(str(e))
        return 1

    message(
        'new PKGBUILD successfully written to ./PKGBUILD,',
        'with the following changes from the old PKGBUILD:',
    )
    sys.stderr.writelines(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
        )
    )
