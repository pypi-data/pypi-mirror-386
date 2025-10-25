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
"""Interface for modality (e.g. Image, Video, etc.)."""

import abc
import contextlib
import functools
import hashlib
import re
from typing import Any, ContextManager, Iterator
from langfun.core import component
import pyglove as pg


class Modality(component.Component, pg.views.HtmlTreeView.Extension):
  """Base class for multimodal object."""

  REF_START = '<<[['
  REF_END = ']]>>'

  def _on_bound(self):
    super()._on_bound()
    # Invalidate cached hash and id if modality member is changed.
    self.__dict__.pop('hash', None)
    self.__dict__.pop('id', None)

  def format(self, *args, **kwargs) -> str:
    if not pg.object_utils.thread_local_get(_TLS_MODALITY_AS_REF, False):
      return super().format(*args, **kwargs)

    capture_scope = get_modality_capture_context()
    if capture_scope is not None:
      capture_scope.capture(self)
    return Modality.text_marker(self.id)

  def __str_kwargs__(self) -> dict[str, Any]:
    # For modality objects, we don't want to use markdown format when they
    # are rendered as parts of the prompt.
    kwargs = super().__str_kwargs__()
    kwargs.pop('markdown', None)
    return kwargs

  @abc.abstractmethod
  def to_bytes(self) -> bytes:
    """Returns content in bytes."""

  @functools.cached_property
  def hash(self) -> str:
    """Returns a 8-byte MD5 hash as the identifier for this modality object."""
    return hashlib.md5(self.to_bytes()).hexdigest()[:8]

  @classmethod
  def text_marker(cls, var_name: str) -> str:
    """Returns a marker in the text for this object."""
    return Modality.REF_START + var_name + Modality.REF_END

  @functools.cached_property
  def id(self) -> str | None:
    """Returns the referred name of this object in its template."""
    modality_type = _camel_to_snake(self.__class__.__name__)
    return f'{modality_type}:{self.hash}'

  @classmethod
  def from_value(cls, value: pg.Symbolic) -> dict[str, 'Modality']:
    """Returns a dict of path to modality from a symbolic value."""
    modalities = {}
    def _visit(k, v, p):
      del k, p
      if isinstance(v, Modality):
        modalities[v.id] = v
        return pg.TraverseAction.CONTINUE
      return pg.TraverseAction.ENTER

    pg.traverse(value, _visit)
    return modalities


class ModalityRef(pg.Object, pg.typing.CustomTyping):
  """References of modality objects in a symbolic tree.

  `ModalityRef` was introduced to placehold modality objects in a symbolic
  tree, to prevent message from being chunked in the middle of a Python
  structure.
  """

  id: str

  def custom_apply(
      self, path: pg.KeyPath, value_spec: pg.ValueSpec, *args, **kwargs
  ) -> tuple[bool, Any]:
    return (False, self)

  @classmethod
  def placehold(cls, value: pg.Symbolic) -> pg.Symbolic:
    """Returns a copy of value by replacing modality objects with refs.

    Args:
      value: A symbolic value.

    Returns:
      A copy of value with all child `Modality` objects replaced with
        `ModalityRef` objects.
    """

    def _placehold(k, v, p):
      del k, p
      if isinstance(v, Modality):
        return ModalityRef(id=v.id)
      return v
    return value.clone().rebind(_placehold, raise_on_no_change=False)

  @classmethod
  def restore(cls, value: pg.Symbolic, modalities: dict[str, Modality]) -> Any:
    """Returns a copy of value by replacing refs with modality objects."""
    def _restore(k, v, p):
      del k, p
      if isinstance(v, ModalityRef):
        modality_object = modalities.get(v.id)
        if modality_object is None:
          raise ValueError(
              f'Modality {v.id} not found in modalities {modalities.keys()}'
          )
        return modality_object
      return v
    return value.rebind(_restore, raise_on_no_change=False)


class ModalityError(RuntimeError):  # pylint: disable=g-bad-exception-name
  """Exception raised when modality is not supported."""


#
# Context managers to deal with modality objects.
#


_TLS_MODALITY_CAPTURE_SCOPE = '__modality_capture_scope__'
_TLS_MODALITY_AS_REF = '__format_modality_as_ref__'


def format_modality_as_ref(enabled: bool = True) -> ContextManager[None]:
  """A context manager that formats modality objects as references."""
  return pg.object_utils.thread_local_value_scope(
      _TLS_MODALITY_AS_REF, enabled, False
  )


class _ModalityCaptureContext:
  """A context to capture modality objects when being rendered."""

  def __init__(self):
    self._references: dict[str, pg.Ref[Modality]] = {}

  def capture(self, modality: Modality) -> None:
    """Captures the modality object."""
    self._references[modality.id] = pg.Ref(modality)

  @property
  def references(self) -> dict[str, pg.Ref[Modality]]:
    """Returns the modality references captured in this context."""
    return self._references


@contextlib.contextmanager
def capture_rendered_modalities() -> Iterator[dict[str, pg.Ref[Modality]]]:
  """Capture modality objects whose references is being rendered.

  Example:
    ```
    image = lf.Image.from_url(...)
    with lf.modality.capture_rendered_modalities() as rendered_modalities:
      with lf.modality.format_modality_as_ref():
        print(f'Hello {image}')
    self.assertEqual(rendered_modalities, {'image:<hash>': pg.Ref(image)})
    ```
  """
  context = get_modality_capture_context()
  top_level = context is None
  if top_level:
    context = _ModalityCaptureContext()
    pg.object_utils.thread_local_set(_TLS_MODALITY_CAPTURE_SCOPE, context)

  try:
    yield context.references  # pylint: disable=attribute-error
  finally:
    if top_level:
      pg.object_utils.thread_local_del(_TLS_MODALITY_CAPTURE_SCOPE)


def get_modality_capture_context() -> _ModalityCaptureContext | None:
  """Returns the current modality capture context."""
  return pg.object_utils.thread_local_get(_TLS_MODALITY_CAPTURE_SCOPE, None)


def _camel_to_snake(name: str) -> str:
  """Converts a camelCase name to snake_case."""
  return re.sub(
      pattern=r'([A-Z]+)', repl=r'_\1', string=name
  ).lower().lstrip('_')
