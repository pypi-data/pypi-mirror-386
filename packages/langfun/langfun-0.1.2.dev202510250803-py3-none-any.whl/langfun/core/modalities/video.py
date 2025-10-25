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
"""Video modality."""

import functools
from langfun.core.modalities import mime


class Video(mime.Mime):
  """Video."""

  MIME_PREFIX = 'video'

  @functools.cached_property
  def video_format(self) -> str:
    return self.mime_type.removeprefix(self.MIME_PREFIX + '/')

  def _mime_control_for(self, uri: str) -> str:
    return f'<video controls> <source src="{uri}"> </video>'
