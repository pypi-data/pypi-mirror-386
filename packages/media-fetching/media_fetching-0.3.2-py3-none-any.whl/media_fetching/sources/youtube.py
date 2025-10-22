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

"""Defines fetching data from YouTube channel."""

from collections.abc import Sequence

import garf_youtube_data_api
import pydantic
from garf_core import report

from media_fetching.sources import models


class YouTubeFetchingParameters(models.FetchingParameters):
  """YouTube specific parameters for getting media data."""

  channel: str
  metrics: Sequence[str] = [
    'views',
    'likes',
  ]
  segments: Sequence[str] | None = None
  extra_info: Sequence[str] | None = pydantic.Field(default_factory=list)


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from YouTube Data API."""

  def fetch_media_data(
    self,
    fetching_request: YouTubeFetchingParameters,
  ) -> report.GarfReport:
    """Get all public videos from YouTube channel."""
    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
    channel_uploads_playlist_query = """
    SELECT
      contentDetails.relatedPlaylists.uploads AS uploads_playlist
    FROM channels
    """
    videos_playlist = youtube_api_fetcher.fetch(
      channel_uploads_playlist_query,
      id=[fetching_request.channel],
    )

    channel_videos_query = """
    SELECT
      contentDetails.videoId AS video_id
    FROM playlistItems
    """
    videos = youtube_api_fetcher.fetch(
      channel_videos_query,
      playlistId=videos_playlist.to_list(row_type='scalar', distinct=True),
      maxResults=50,
    ).to_list(row_type='scalar', distinct=True)

    video_performance_query = """
    SELECT
      id AS media_url,
      snippet.title AS media_name,
      contentDetails.duration AS video_duration,
      statistics.viewCount AS views,
      statistics.likeCount AS likes
    FROM videos
    """
    return youtube_api_fetcher.fetch(video_performance_query, id=videos)
