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

"""Responsible for fetching media specific information from various sources."""

from __future__ import annotations

import enum
import logging
import warnings
from typing import Any, get_args

from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import enricher
from media_fetching.sources import fetcher, models

logger = logging.getLogger('media-fetching')


class MediaFetchingService:
  """Extracts media information from a specified source.

  Attributes:
    source_fetcher: Initialized concrete fetcher for getting media data.
    source: Alias of a source.
  """

  def __init__(
    self,
    source: str | models.InputSource | None = None,
    source_fetcher: models.BaseMediaInfoFetcher | None = None,
  ) -> None:
    """Initializes MediaFetchingService.

    Args:
      source: [Deprecated] Alias of a source.
      source_fetcher: Initialized concrete fetcher for getting media data.
    """
    if not source and not source_fetcher:
      raise exceptions.MediaFetchingError('Missing source_fetcher parameter.')
    if source and not source_fetcher:
      warnings.warn(
        'Initialization from source argument is deprecated.'
        'Provide initialized source_fetcher instead',
        FutureWarning,
        stacklevel=2,
      )
      self.fetcher = _get_source_fetcher(source)
      self.source = source
    else:
      fetcher_alias = None
      for alias, (_, fetcher_class) in fetcher.FETCHERS.items():
        if isinstance(source_fetcher, fetcher_class):
          fetcher_alias = alias
          break

      if not fetcher_alias:
        raise exceptions.MediaFetchingError(
          f'Unsupported fetcher: {source_fetcher.__class__.__name__}'
        )
      self.fetcher = source_fetcher
      self.source = fetcher_alias

  @classmethod
  def from_source_alias(
    cls,
    source: str | models.InputSource = 'googleads',
  ) -> MediaFetchingService:
    """Initialized MediaFetchingService from source alias."""
    source_fetcher = _get_source_fetcher(source)
    return cls(source_fetcher=source_fetcher)

  def fetch(
    self,
    request: models.FetchingParameters,
    extra_parameters: dict[str, dict[str, Any]] | None = None,
  ) -> report.GarfReport:
    """Extracts data from specified source."""
    logger.info(
      "Fetching data from source '%s' with parameters: %s",
      self.source,
      request,
    )
    media_data = self.fetcher.fetch_media_data(request)
    if extra_info_modules := request.extra_info:
      extra_data = enricher.prepare_extra_info(
        performance=media_data,
        media_type=request.media_type,
        modules=extra_info_modules,
        params=extra_parameters,
      )
      enricher.enrich(media_data, extra_data)
    return media_data


def _get_source_fetcher(
  source: str | models.InputSource,
) -> models.BaseMediaInfoFetcher:
  if isinstance(source, enum.Enum):
    source = source.value
  if not (fetcher_info := fetcher.FETCHERS.get(source)):
    raise exceptions.MediaFetchingError(
      f'Incorrect source: {source}. Only {get_args(models.InputSource)} '
      'are supported.'
    )
  return fetcher_info[1]()
