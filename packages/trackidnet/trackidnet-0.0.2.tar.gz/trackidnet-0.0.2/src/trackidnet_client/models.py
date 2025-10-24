"""Data models for API responses."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

class Track(BaseModel):
    """Represents a single track."""

    model_config = ConfigDict(populate_by_name=True)

    start_time: str | None = Field(None, alias="startTime")
    end_time: str | None = Field(None, alias="endTime")
    artist: str | None = None
    title: str | None = None
    label: str | None = None


class Tracklist(BaseModel):
    """Represents a tracklist (audiostream)."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    slug: str | None = None
    url: str | None = None
    duration: str | None = None
    tracks: list[Track] | None = None

    @model_validator(mode="before")
    @classmethod
    def populate_tracks_from_detection_processes(cls, data):
        """Populate tracks field from detectionProcesses if tracks is None."""
        if isinstance(data, dict):
            tracks = data.get("tracks")
            detection_processes = data.get("detectionProcesses")

            if tracks is None and detection_processes:
                all_tracks = []
                for process in detection_processes:
                    if process.get("detectionProcessMusicTracks"):
                        all_tracks.extend(process["detectionProcessMusicTracks"])
                if all_tracks:
                    data = data.copy()
                    data["tracks"] = all_tracks
        return data


class SearchResult(BaseModel):
    """Represents search results."""

    results: list[Tracklist] = Field(alias="audiostreams")
    page: int | None = None
    per_page: int | None = None
