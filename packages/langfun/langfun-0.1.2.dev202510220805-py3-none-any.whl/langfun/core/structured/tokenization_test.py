# Copyright 2023 The Langfun Authors
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

import asyncio
import unittest
import langfun.core as lf
from langfun.core.llms import fake
from langfun.core.structured import tokenization
import pyglove as pg


class Answer(pg.Object):
  result: int


class TokenizationTest(unittest.TestCase):

  def test_bad_call(self):

    with self.assertRaisesRegex(ValueError, '`lm` must be specified'):
      tokenization.tokenize('hi')

  def test_tokenize(self):
    self.assertEqual(
        tokenization.tokenize('hi', lm=fake.Echo()),
        [('hi', 0)]
    )

  def test_atokenize(self):
    with lf.context(lm=fake.Echo()):
      self.assertEqual(
          asyncio.run(tokenization.atokenize('hi')),
          [('hi', 0)]
      )

  def test_tokenize_with_lm_from_the_context(self):
    with lf.context(lm=fake.Echo()):
      self.assertEqual(
          tokenization.tokenize('hi'),
          [('hi', 0)]
      )


if __name__ == '__main__':
  unittest.main()
