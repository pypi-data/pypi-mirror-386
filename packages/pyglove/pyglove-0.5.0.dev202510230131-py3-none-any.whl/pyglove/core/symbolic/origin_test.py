# Copyright 2022 The PyGlove Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for pyglove.symbolic.Origin."""

import unittest

from pyglove.core.symbolic import flags
from pyglove.core.symbolic.dict import Dict
from pyglove.core.symbolic.origin import Origin


class OriginTest(unittest.TestCase):
  """Tests for `pg.symbolic.Origin`."""

  def test_basics(self):
    a = Dict(a=1)
    o = Origin(a, '__init__')
    self.assertIs(o.source, a)
    self.assertEqual(o.tag, '__init__')
    self.assertIsNone(o.stack)
    self.assertIsNone(o.stacktrace)

    with self.assertRaisesRegex(ValueError, '`tag` must be a string'):
      _ = Origin(a, 1)

  def test_include_stacktrace(self):
    a = Dict(a=1)
    o = Origin(a, '__init__', stacktrace=True, stacklimit=3)
    self.assertIs(o.source, a)
    self.assertEqual(o.tag, '__init__')
    self.assertEqual(len(o.stack), 3)
    self.assertIsNotNone(o.stacktrace)

    flags.set_origin_stacktrace_limit(2)
    o = Origin(a, '__init__', stacktrace=True)
    self.assertEqual(len(o.stack), 2)

  def test_root(self):
    a = Dict(a=1)
    b = Dict(b=2)
    c = Dict(c=3)

    c.sym_setorigin(b, 'foo')
    b.sym_setorigin(a, 'bar')
    self.assertIs(c.sym_origin.root.source, a)

  def test_history(self):
    a = Dict(a=1)
    b = Dict(b=2)
    c = Dict(c=3)

    c.sym_setorigin(b, 'foo')
    b.sym_setorigin(a, 'bar')
    self.assertEqual(
        c.sym_origin.history(),
        [
            Origin(a, 'bar'),
            Origin(b, 'foo'),
        ])

    self.assertEqual(
        c.sym_origin.history(lambda o: o.tag == 'foo'),
        [
            Origin(b, 'foo'),
        ])

    self.assertEqual(
        c.sym_origin.history(lambda o: o.tag == 'bar'),
        [
            Origin(a, 'bar'),
        ])

  def test_eq_ne(self):
    a = Dict(a=1)
    self.assertEqual(Origin(None, '__init__'), Origin(None, '__init__'))
    self.assertEqual(Origin(a, 'builder'), Origin(a, 'builder'))
    self.assertNotEqual(Origin(a, 'builder'), a)
    self.assertNotEqual(Origin(a, 'builder'), Origin(a, 'return'))
    self.assertNotEqual(Origin(a, 'builder'), Origin(Dict(a=1), 'builder'))

  def test_format(self):
    a = Dict(a=1)
    o = Origin(None, '__init__')
    self.assertEqual(o.format(compact=True), 'Origin(tag=\'__init__\')')

    o = Origin('/path/to/file', 'load')
    self.assertEqual(
        o.format(compact=False),
        "Origin(\n  tag='load',\n  source='/path/to/file'\n)"
    )

    o = Origin(a, 'builder')
    self.assertEqual(
        o.format(compact=True),
        'Origin(tag=\'builder\', source={a=1} at 0x%x)' % id(a))


if __name__ == '__main__':
  unittest.main()
