# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Performs tagging of media based on various taggers.

Media can be images, videos, urls, texts.
"""

from media_tagging.media_tagging_service import (
  MediaTaggingRequest,
  MediaTaggingService,
)

__all__ = [
  'MediaTaggingService',
  'MediaTaggingRequest',
]
__version__ = '2.0.0'
