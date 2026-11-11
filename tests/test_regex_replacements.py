"""Tests verifying robustness of regex replacement code."""

import unittest

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from modpkgbuild import gen_new
from modpkgbuild import validate_spec
from modpkgbuild import ReplacementError
from modpkgbuild import SpecError


def cook_spec(spec: str) -> dict:
    d = yaml.load(spec, Loader=SafeLoader)

    return validate_spec(d)


class TestRegexReplacements(unittest.TestCase):
    def test_replace_with_capture(self):
        """Makes one replacement with a backreference to a captured group."""
        old = """\
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )
"""
        expect = """\
b2sums=(
  'c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133'
  '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
)
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_with_capture_after_start(self):
        """Double-checks that the regex doesn't need to be anchored."""
        old = """\
source=("git+$url?signed#tag=v$pkgver")
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )
"""
        expect = """\
source=("git+$url?signed#tag=v$pkgver")
b2sums=(
  'c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133'
  '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
)
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_literal_then_regex(self):
        """Makes a literal replacement, then a regex replacement."""
        old = """\
source=("git+$url?signed#tag=v$pkgver")
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

prepare() {
  cd $pkgname
}
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add source for patches to bubblewrap
    old: |2
      source=("git+$url?signed#tag=v$pkgver")
    new: |2
      source=(
        "git+$url?signed#tag=v$pkgver"
        "$_name-utils-$pkgver.tar.gz::https://codeberg.org/HastD/$_name-utils/archive/v$pkgver.tar.gz"
      )

  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )

  - description: Apply patches
    old: |2
      prepare() {
        cd $pkgname
      }
    new: |2
      prepare() {
        cd $_name
        patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
        patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
      }
"""
        expect = """\
source=(
  "git+$url?signed#tag=v$pkgver"
  "$_name-utils-$pkgver.tar.gz::https://codeberg.org/HastD/$_name-utils/archive/v$pkgver.tar.gz"
)
b2sums=(
  'c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133'
  '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
)
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

prepare() {
  cd $_name
  patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
  patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
}
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_replace_regex_then_literal(self):
        """Makes a regex replacement, then a literal replacement."""
        old = """\
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

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
  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )

  - description: Apply patches
    old: |2
      prepare() {
        cd $pkgname
      }
    new: |2
      prepare() {
        cd $_name
        patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
        patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
      }

  - description: Enable SELinux and rebuild man page
    old: |2
          -D selinux=disabled
        )

        arch-meson $pkgname build "${meson_options[@]}"
    new: |2
          -D selinux=enabled

          -D man=enabled
        )

        arch-meson $_name build "${meson_options[@]}"
"""
        expect = """\
b2sums=(
  'c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133'
  '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
)
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

prepare() {
  cd $_name
  patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
  patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
}

build() {
  local meson_options=(
    # major.minor.0 of linux-lts
    -D assume_kernel=6.18.0

    -D selinux=enabled

    -D man=enabled
  )

  arch-meson $_name build "${meson_options[@]}"
  meson compile -C build
}
"""
        self.assertEqual(gen_new(old, cook_spec(spec)), expect)

    def test_nomatch(self):
        """Raises an exception when there is no match."""
        old = """\
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add checksum for new source
    regex: true
    old: |2
      bsums=\(('.*')\)

    new: |2
      bsums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))

    def test_outoforder_regex_then_literal(self):
        """Raises an exception when the spec is out of order.

        In this test, a regex replacement is followed by an out-of-order
        literal replacement.
        """
        old = """\
source=("git+$url?signed#tag=v$pkgver")
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

prepare() {
  cd $pkgname
}
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )

  - description: Add source for patches to bubblewrap
    old: |2
      source=("git+$url?signed#tag=v$pkgver")
    new: |2
      source=(
        "git+$url?signed#tag=v$pkgver"
        "$_name-utils-$pkgver.tar.gz::https://codeberg.org/HastD/$_name-utils/archive/v$pkgver.tar.gz"
      )

  - description: Apply patches
    old: |2
      prepare() {
        cd $pkgname
      }
    new: |2
      prepare() {
        cd $_name
        patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
        patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
      }
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))

    def test_outoforder_literal_then_regex(self):
        """Raises an exception when the spec is out of order.

        In this test, a literal replacement is followed by an out-of-order
        regex replacement.
        """
        old = """\
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
validpgpkeys=(
  DA98F25C0871C49A59EAFF2C4DE8FF2A63C7CC90 # Simon McVittie <smcv@collabora.com>
  252C6FEA78A69D3BC0AD458A616C5BDC0C29AB04 # Alexander Larsson <alexl@redhat.com>
)

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
  - description: Apply patches
    old: |2
      prepare() {
        cd $pkgname
      }
    new: |2
      prepare() {
        cd $_name
        patch -N -i ../$_name-utils/restricted/bubblewrap.c.patch
        patch -N -i ../$_name-utils/restricted/bwrap.xml.patch
      }

  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*')\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )

  - description: Enable SELinux and rebuild man page
    old: |2
          -D selinux=disabled
        )

        arch-meson $pkgname build "${meson_options[@]}"
    new: |2
          -D selinux=enabled

          -D man=enabled
        )

        arch-meson $_name build "${meson_options[@]}"
"""
        with self.assertRaises(ReplacementError):
            gen_new(old, cook_spec(spec))

    def test_invalid_regex(self):
        old = """\
b2sums=('c7e182d4bb08afcba1bdc4beae77106a6fa75e366f328642f6703ca10299e24ee44ca428f78b00617dfee3e758e68885f889c940c1aa48e7a5c1d3d0baa5c133')
"""
        spec = r"""
repo: https://gitlab.archlinux.org/archlinux/packaging/packages/bubblewrap.git
replacements:
  - description: Add checksum for new source
    regex: true
    old: |2
      b2sums=\(('.*'\)
    new: |2
      b2sums=(
        \1
        '00476dad5836b5143d7f5abf4ab68b458b2e9a59820f0a60b52969b4fa428895ba3d44769ebe8f9b3d3c4ebbe1fdae9f8006229b2189145b48b6161c0259b12f'
      )
"""
        with self.assertRaises(SpecError):
            gen_new(old, cook_spec(spec))


if __name__ == '__main__':
    unittest.main()
