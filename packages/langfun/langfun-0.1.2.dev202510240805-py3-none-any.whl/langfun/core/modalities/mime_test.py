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
"""MIME tests."""
import inspect
import unittest
from unittest import mock

import langfun.core as lf
from langfun.core.modalities import mime
import pyglove as pg


def mock_request(*args, **kwargs):
  del args, kwargs
  return pg.Dict(content=b'foo')


def mock_readfile(*args, **kwargs):
  del args, kwargs
  return b'bar'


class CustomMimeTest(unittest.TestCase):

  def test_is_text(self):
    self.assertTrue(mime.Custom('text/plain', b'foo').is_text)
    self.assertTrue(mime.Custom('text/xml', b'foo').is_text)
    self.assertTrue(mime.Custom('application/json', b'foo').is_text)
    self.assertTrue(mime.Custom('application/x-python-code', b'foo').is_text)
    self.assertFalse(mime.Custom('application/pdf', b'foo').is_text)
    self.assertFalse(mime.Custom('application/octet-stream', b'foo').is_text)

  def test_from_byes(self):
    content = mime.Mime.from_bytes(b'hello')
    self.assertIs(content.__class__, mime.Mime)

    content = mime.Custom('text/plain', b'foo')
    self.assertEqual(content.to_bytes(), b'foo')
    self.assertEqual(content.mime_type, 'text/plain')
    self.assertTrue(content.is_text)
    self.assertFalse(content.is_binary)
    self.assertEqual(content.to_text(), 'foo')
    self.assertTrue(content.is_compatible('text/plain'))
    self.assertFalse(content.is_compatible('text/xml'))
    self.assertIs(content.make_compatible('text/plain'), content)

    with self.assertRaisesRegex(
        lf.ModalityError, '.* cannot be converted to supported types'
    ):
      content.make_compatible('application/pdf')

    with self.assertRaisesRegex(
        ValueError, 'Either uri or content must be provided.'
    ):
      mime.Custom('text/plain')

  def test_uri(self):
    content = mime.Custom.from_uri('http://mock/web/a.txt', mime='text/plain')
    with mock.patch('requests.get') as mock_requests_stub:
      mock_requests_stub.side_effect = mock_request
      self.assertEqual(content.uri, 'http://mock/web/a.txt')
      self.assertEqual(content.content_uri, 'data:text/plain;base64,Zm9v')
      self.assertEqual(content.embeddable_uri, 'http://mock/web/a.txt')

    content = mime.Custom.from_uri('a.txt', mime='text/plain')
    with mock.patch('pyglove.io.readfile') as mock_readfile_stub:
      mock_readfile_stub.side_effect = mock_readfile
      self.assertEqual(content.uri, 'a.txt')
      self.assertEqual(content.content_uri, 'data:text/plain;base64,YmFy')
      self.assertEqual(content.embeddable_uri, 'data:text/plain;base64,YmFy')

  def test_from_uri(self):
    content = mime.Custom.from_uri('http://mock/web/a.txt', mime='text/plain')
    with mock.patch('requests.get') as mock_requests_stub:
      mock_requests_stub.side_effect = mock_request
      self.assertEqual(content.to_bytes(), b'foo')
      self.assertEqual(content.mime_type, 'text/plain')

    content = mime.Custom.from_uri('a.txt', mime='text/plain')
    with mock.patch('pyglove.io.readfile') as mock_readfile_stub:
      mock_readfile_stub.side_effect = mock_readfile
      self.assertEqual(content.to_bytes(), b'bar')
      self.assertEqual(content.mime_type, 'text/plain')

    content = mime.Mime.from_uri('data:text/plain;base64,Zm9v')
    self.assertIsNone(content.uri)
    self.assertEqual(content.mime_type, 'text/plain')
    self.assertEqual(content.content, b'foo')
    self.assertEqual(content.content_uri, 'data:text/plain;base64,Zm9v')
    self.assertEqual(content.embeddable_uri, 'data:text/plain;base64,Zm9v')

    with self.assertRaisesRegex(ValueError, 'Invalid data URI'):
      mime.Mime.from_uri('data:text/plain')

    with self.assertRaisesRegex(ValueError, 'Invalid data URI'):
      mime.Mime.from_uri('data:text/plain;abcd')

    with self.assertRaisesRegex(ValueError, 'Unsupported encoding'):
      mime.Mime.from_uri('data:text/plain;base16,abcd')

  def assert_html_content(self, html, expected):
    expected = inspect.cleandoc(expected).strip()
    actual = html.content.strip()
    if actual != expected:
      print(actual)
    self.assertEqual(actual, expected)

  def test_html(self):
    self.assert_html_content(
        mime.Custom('text/plain', b'foo').to_html(
            enable_summary_tooltip=False,
            enable_key_tooltip=False,
        ),
        """
        <details open class="pyglove custom"><summary><div class="summary-title">Custom(...)</div></summary><embed type="text/plain" src="data:text/plain;base64,Zm9v"/></details>
        """
    )
    self.assert_html_content(
        mime.Custom('text/plain', b'foo').to_html(
            enable_summary_tooltip=False,
            enable_key_tooltip=False,
            extra_flags=dict(
                raw_mime_content=True,
            )
        ),
        """
        <embed type="text/plain" src="data:text/plain;base64,Zm9v"/>
        """
    )
    self.assert_html_content(
        mime.Custom('text/plain', b'foo').to_html(
            enable_summary_tooltip=False,
            enable_key_tooltip=False,
            extra_flags=dict(
                display_modality_when_hover=True,
            )
        ),
        """
        <details open class="pyglove custom"><summary><div class="summary-title">Custom(...)</div><span class="tooltip"><embed type="text/plain" src="data:text/plain;base64,Zm9v"/></span></summary><embed type="text/plain" src="data:text/plain;base64,Zm9v"/></details>
        """
    )


if __name__ == '__main__':
  unittest.main()
