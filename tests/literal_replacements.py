"""Tests verifying robustness of literal replacement code."""

import unittest

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from modpkgbuild import gen_new
from modpkgbuild import validate_spec
from modpkgbuild import ReplacementError


def cook_spec(spec: str) -> dict:
    """Turns a string into a validated spec."""
    d = yaml.load(spec, Loader=SafeLoader)

    return validate_spec(d)


class TestLiteralReplacements(unittest.TestCase):
    def test_replace(self):
        """Makes a single literal replacement."""
        old = """\
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
url='https://github.com/containers/bubblewrap'
arch=(x86_64)
license=(LGPL-2.1-or-later)
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: 'A literal replacement'
    old: "pkgdesc='Unprivileged sandboxing tool'"
    new: "pkgdesc='Unprivileged sandboxing tool, with SELinux support and without --cap-add option'"
"""
        expect = """\
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool, with SELinux support and without --cap-add option'
url='https://github.com/containers/bubblewrap'
arch=(x86_64)
license=(LGPL-2.1-or-later)
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_line_with_multiline(self):
        """Replaces one line with a multiline string."""
        old = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: New package name
    old: |2
      pkgname=bubblewrap
    new: |2
      _name=bubblewrap
      pkgname=bubblewrap-restricted
"""
        expect = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

_name=bubblewrap
pkgname=bubblewrap-restricted
pkgver=0.13.1
pkgrel=1
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_multiline_with_multiline(self):
        """Replaces a multiline string with a multiline string."""
        old = """\
license=(LGPL-2.1-or-later)
depends=(
  glibc
  libcap
  libgcc
)
makedepends=(
  bash-completion
  docbook-xsl
  git
  libxslt
  meson
)
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add additional dependency for SELinux support
    old: |2
      depends=(
        glibc
        libcap
        libgcc
      )
    new: |2
      depends=(
        glibc
        libcap
        libselinux
        libgcc
      )
"""
        expect = """\
license=(LGPL-2.1-or-later)
depends=(
  glibc
  libcap
  libselinux
  libgcc
)
makedepends=(
  bash-completion
  docbook-xsl
  git
  libxslt
  meson
)
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_multiple(self):
        """Makes a series of literal replacements."""
        old = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add maintainer tag
    old: |2

    new: |2
      # Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
      #
      # Forked from Arch Linux's bubblewrap package:

  - description: New package name
    old: |2
      pkgname=bubblewrap
    new: |2
      _name=bubblewrap
      pkgname=bubblewrap-restricted

  - description: New description
    old: "pkgdesc='Unprivileged sandboxing tool'"
    new: "pkgdesc='Unprivileged sandboxing tool, with SELinux support and without --cap-add option'"
"""
        expect = """\
# Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
#
# Forked from Arch Linux's bubblewrap package:
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

_name=bubblewrap
pkgname=bubblewrap-restricted
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool, with SELinux support and without --cap-add option'
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_multiple_adjacent(self):
        """Replaces two adjacent strings."""
        old = """\
makedepends=(
  bash-completion
  docbook-xsl
  git
  libxslt
  meson
)
source=("git+$url?signed#tag=v$pkgver")
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Provide and conflict with bubblewrap package
    old: |2
        meson
      )
    new: |2
        meson
      )
      provides=(bubblewrap)
      conflicts=(bubblewrap)

  - description: Add source for patches to bubblewrap
    old: |2
      source=("git+$url?signed#tag=v$pkgver")
    new: |2
      source=(
        "git+$url?signed#tag=v$pkgver"
        "$_name-utils-$pkgver.tar.gz::https://codeberg.org/HastD/$_name-utils/archive/v$pkgver.tar.gz"
      )
"""
        expect = """\
makedepends=(
  bash-completion
  docbook-xsl
  git
  libxslt
  meson
)
provides=(bubblewrap)
conflicts=(bubblewrap)
source=(
  "git+$url?signed#tag=v$pkgver"
  "$_name-utils-$pkgver.tar.gz::https://codeberg.org/HastD/$_name-utils/archive/v$pkgver.tar.gz"
)
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_only_once(self):
        """Replaces only the first match."""
        old = """\
prepare() {
  cd $pkgname
}

build() {
  local meson_options=(
    # major.minor.0 of linux-lts
    -D assume_kernel=6.18.0

    -D selinux=disabled
  )

  arch-meson $pkgname build "${meson_options[@]}"
  meson compile -C build
}
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: 'An inadvisably ambiguous replacement'
    old: '$pkgname'
    new: '$_name'
"""
        expect = """\
prepare() {
  cd $_name
}

build() {
  local meson_options=(
    # major.minor.0 of linux-lts
    -D assume_kernel=6.18.0

    -D selinux=disabled
  )

  arch-meson $pkgname build "${meson_options[@]}"
  meson compile -C build
}
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_only_twice(self):
        """Correctly replaces the same string twice."""
        old = """\
prepare() {
  cd $pkgname
}

build() {
  local meson_options=(
    # major.minor.0 of linux-lts
    -D assume_kernel=6.18.0

    -D selinux=disabled
  )

  arch-meson $pkgname build "${meson_options[@]}"
  meson compile -C build
}
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: 'An inadvisably ambiguous replacement'
    old: '$pkgname'
    new: '$_name'

  - description: 'AGAIN an inadvisably ambiguous replacement'
    old: '$pkgname'
    new: '$_name'
"""
        expect = """\
prepare() {
  cd $_name
}

build() {
  local meson_options=(
    # major.minor.0 of linux-lts
    -D assume_kernel=6.18.0

    -D selinux=disabled
  )

  arch-meson $_name build "${meson_options[@]}"
  meson compile -C build
}
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_with_query_only_once(self):
        """Correctly replaces only once when replacement contains query."""
        old = """\
pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
url='https://github.com/containers/bubblewrap'
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: 'An inadvisably ambiguous replacement'
    old: 'bubblewrap'
    new: 'bubblewrap-restricted'
"""
        expect = """\
pkgname=bubblewrap-restricted
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
url='https://github.com/containers/bubblewrap'
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_with_query_only_twice(self):
        """Correctly replaces twice when replacement contains query."""
        old = """\
pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
url='https://github.com/containers/bubblewrap'
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: 'An inadvisably ambiguous replacement'
    old: 'bubblewrap'
    new: 'bubblewrap-restricted'

  - description: 'AGAIN an inadvisably ambiguous replacement'
    old: 'bubblewrap'
    new: 'bubblewrap-restricted'
"""
        expect = """\
pkgname=bubblewrap-restricted
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
url='https://github.com/containers/bubblewrap-restricted'
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_prepend_line(self):
        """Prepends a line to the PKGBUILD."""
        old = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add maintainer tag
    old: |2

    new: |2
      # Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
      #
      # Forked from Arch Linux's bubblewrap package:
"""
        expect = """\
# Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
#
# Forked from Arch Linux's bubblewrap package:
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_insert_line(self):
        """Inserts a line into the PKGBUILD."""
        old = """\
makedepends=(
  bash-completion
  docbook-xsl
  git
  libxslt
  meson
)
source=("git+$url?signed#tag=v$pkgver")
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add unnecessary dependency for the sake of testing
    old: |2
      makedepends=(
        bash-completion
        docbook-xsl
        git
        libxslt
        meson
      )
    new: |2
      makedepends=(
        bash-completion
        docbook-xsl
        git
        libselinux
        libxslt
        meson
      )

  - description: Provide and conflict with bubblewrap package
    old: |2

    new: |2
      provides=(bubblewrap)
      conflicts=(bubblewrap)
"""
        expect = """\
makedepends=(
  bash-completion
  docbook-xsl
  git
  libselinux
  libxslt
  meson
)
provides=(bubblewrap)
conflicts=(bubblewrap)
source=("git+$url?signed#tag=v$pkgver")
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_nomatch(self):
        """Raises an exception when there is no match."""
        old = """\
pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: No match
    old: 'Blah'
    new: 'Blah blah'
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))

    def test_outoforder(self):
        """Raises an exception when the spec is out of order."""
        old = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add maintainer tag
    old: |2

    new: |2
      # Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
      #
      # Forked from Arch Linux's bubblewrap package:

  - description: New description
    old: "pkgdesc='Unprivileged sandboxing tool'"
    new: "pkgdesc='Unprivileged sandboxing tool, with SELinux support and without --cap-add option'"

  - description: New package name
    old: |2
      pkgname=bubblewrap
    new: |2
      _name=bubblewrap
      pkgname=bubblewrap-restricted
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))

    def test_overlapping(self):
        """Raises an exception when one search text contains the next."""
        old = """\
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
# Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
# Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

pkgname=bubblewrap
pkgver=0.13.1
pkgrel=1
pkgdesc='Unprivileged sandboxing tool'
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add maintainer tag
    old: |2
      # Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
      # Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
      # Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

      pkgname=bubblewrap
    new: |2
      # Maintainer: Russell Wright Helder <rwh[at]russellhelder[dot]net>
      #
      # Forked from Arch Linux's bubblewrap package:
      # Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>
      # Maintainer: Levente Polyak <anthraxx[at]archlinux[dot]org>
      # Contributor: Bartłomiej Piotrowski <bpiotrowski@archlinux.org>

      _name=bubblewrap
      pkgname=bubblewrap-restricted

  - description: New package name
    old: |2
      pkgname=bubblewrap
    new: |2
      _name=bubblewrap
      pkgname=bubblewrap-restricted
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))


if __name__ == '__main__':
    unittest.main()
