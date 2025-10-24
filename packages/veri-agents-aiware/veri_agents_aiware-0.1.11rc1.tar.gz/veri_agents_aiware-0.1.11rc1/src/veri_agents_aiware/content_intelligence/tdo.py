from datetime import datetime
from functools import lru_cache
import logging
import asyncio
import async_lru

from aiware.aion import Aion, AionObjectType, AionSeries
from pydantic import BaseModel

from veri_agents_aiware.aiware_client.async_client import (
    AsyncAgentsAiware,
)
from .data import (
    Signal,
    SegmentsTable,
    create_tdo_dict,
    create_segment_dict,
    new_segments_table,
)
from .parallel_downloading import adownload_all

logger = logging.getLogger(__name__)


class MediaTDO(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    id: str
    createdDateTime: datetime | None
    modifiedDateTime: datetime | None
    startDateTime: datetime | None
    stopDateTime: datetime | None
    duration_s: float | None = None  # Computed as stop - start
    name: str | None
    asset_type: str | None
    segments: dict[str, SegmentsTable] = {}

    def as_tdo_dict(self) -> dict:
        return create_tdo_dict(
            tdo_id=self.id,
            tdo_name=self.name,
            created_datetime=self.createdDateTime,
            asset_type=self.asset_type,
            start_datetime=self.startDateTime,
            stop_datetime=self.stopDateTime,
            duration_s=self.duration_s,
        )
        
    @classmethod
    async def _fetch_segments(cls, aion_uris: list[str], tdo) -> dict[str, SegmentsTable]:
        aion_jsons = await adownload_all(aion_uris)

        # Parse them to Aion objects, populate segments
        segments_data: dict[str, list[dict]] = {}  # Signal -> list of segment dicts
        for aj in aion_jsons:
            # TODO: hack:
            # AionObjectType.OCR = "OCR"

            try:
                aion = Aion.model_validate(aj, strict=False)
            except Exception as e:
                logger.error("Failed to parse AION JSON for TDO  %s", str(tdo.id))
                continue

            if aion.series is None:
                logger.warning("Non-series AION (currently) ignored for TDO %s", tdo.id)
            else:
                for s in aion.series:
                    channel = label = confidence = transcript = None
                    signal: Signal | None = None
                    # Logo detections
                    if s.object and s.object.type == AionObjectType.LOGO:
                        channel = "video"
                        signal = "logo"
                        label = s.object.label
                        confidence = s.object.confidence
                    # Object detections
                    elif s.object and s.object.type == AionObjectType.OBJECT:
                        channel = "video"
                        signal = "object"
                        label = s.object.label
                        confidence = s.object.confidence
                    # Face detections
                    elif s.object and s.object.type == AionObjectType.FACE:
                        channel = "video"
                        signal = "face"
                        label = s.object.label
                        confidence = s.object.confidence
                    # Transcript
                    elif s.words:
                        channel = "audio"
                        signal = "transcript"
                        transcript = " ".join(
                            w.word for w in s.words if w.word and w.best_path
                        )
                    else:
                        logger.warning("Skipping unhandled AionSeries (TDO %s)", tdo.id)
                        continue

                    if signal not in segments_data:
                        segments_data[signal] = []

                    segment_dict = create_segment_dict(
                        tdo_id=tdo.id,
                        start_s=s.start_time_ms / 1000.0,
                        end_s=s.stop_time_ms / 1000.0,
                        channel=channel,
                        signal=signal or "unknown",
                        score=confidence,
                        label=label,
                        transcript=transcript,
                        engine_id=aion.source_engine_id,
                        engine_name=aion.source_engine_name,
                        # abs_start_epoch_s=None,
                        # abs_end_epoch_s=None,
                        # bbox=None,
                        # poly=None,
                        # meta={},
                    )
                    segments_data[signal].append(segment_dict)

        # Convert segment data to DataFrames
        segments: dict[str, SegmentsTable] = {}
        for signal_key, data in segments_data.items():
            segments[signal_key] = new_segments_table(data)
        return segments

    @classmethod
    async def from_tdo_ids(
        cls,
        aiware: AsyncAgentsAiware,
        tdo_ids: list[str],
        include_segments: bool = True,
    ) -> list["MediaTDO"]:
        """Fetch multiple TDOs in parallel."""
        tasks = [
            cls.from_tdo_id(aiware, tdo_id, include_segments) for tdo_id in tdo_ids
        ]
        return [tdo for tdo in await asyncio.gather(*tasks) if tdo]

    @classmethod
    @async_lru.alru_cache(maxsize=128)
    async def from_tdo_id(
        cls,
        aiware: AsyncAgentsAiware,
        tdo_id: str,
        include_segments: bool = True,
    ) -> "MediaTDO":
        """Fetch a TDO by ID, optionally download and parse its AION assets to populate segments."""
        tdo = (await aiware.rag_get_tdo_content(tdo_id)).temporalDataObject
        if tdo is None:
            raise ValueError(f"TDO with id {tdo_id} not found")

        aion_uris = []
        asset_type = None
        if tdo.assets is not None and tdo.assets.records is not None:
            for a in tdo.assets.records:
                if a and a.assetType == "vtn-standard":
                    if a.signedUri is not None:
                        aion_uris.append(a.signedUri)
                elif a and a.assetType == "media":
                    asset_type = a.contentType

        segments = {}
        if include_segments:
            segments = await cls._fetch_segments(aion_uris, tdo)

        return cls(
            id=tdo.id,
            createdDateTime=tdo.createdDateTime,
            modifiedDateTime=tdo.modifiedDateTime,
            startDateTime=tdo.startDateTime,
            stopDateTime=tdo.stopDateTime,
            duration_s=(
                (tdo.stopDateTime - tdo.startDateTime).total_seconds()
                if tdo.startDateTime and tdo.stopDateTime
                else None
            ),
            name=tdo.name,
            asset_type=asset_type,
            segments=segments,
        )
