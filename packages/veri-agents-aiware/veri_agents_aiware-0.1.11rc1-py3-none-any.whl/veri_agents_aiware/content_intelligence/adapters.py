from __future__ import annotations

import logging
from typing import Any, Iterable, Protocol, Tuple
from collections.abc import Callable
from aiware.client import AsyncAiware
import async_lru
from functools import partial

import polars as pl
from aiware.client.search_models import SearchRequest, SliceSearchResult, TdoSliceMetadata
from veri_agents_aiware.aiware_client.async_client import AsyncAgentsAiware
from veri_agents_aiware.content_intelligence.data import (
    new_segments_table,
    create_segment_dict,
    SegmentsTable,
    TargetByFolder,
    TargetByIds,
    TargetByOrg,
    TargetSelector,
    coalesce_segments,
)
from veri_agents_aiware.content_intelligence.ops import (
    AbsTime,
    MediaTime,
    FindTranscriptOp,
    FindFaceOp,
    FindLogoOp,
    GetTdoTranscriptOp,
    GetTdoFacesOp,
    GetTdoLogosOp,
)
from veri_agents_aiware.content_intelligence.tdo import MediaTDO
from veri_agents_aiware.content_intelligence.plan import InvalidPlanError

log = logging.getLogger(__name__)


# ---------------- Protocol (no generic find) ----------------

class SegmentAdapter(Protocol):
    # FIND methods
    async def find_transcript(
        self, op: FindTranscriptOp, target: TargetSelector
    ) -> SegmentsTable: ...

    async def find_face(
        self, op: FindFaceOp, target: TargetSelector
    ) -> SegmentsTable: ...

    async def find_logo(
        self, op: FindLogoOp, target: TargetSelector
    ) -> SegmentsTable: ...

    # GET_TDO methods
    async def get_tdos(
        self, target: TargetSelector, include_segments: bool
    ) -> list[MediaTDO]: ...

    async def get_tdo_transcript(
        self, op: GetTdoTranscriptOp, target: TargetSelector
    ) -> SegmentsTable: ...

    async def get_tdo_faces(
        self, op: GetTdoFacesOp, target: TargetSelector
    ) -> SegmentsTable: ...

    async def get_tdo_logos(
        self, op: GetTdoLogosOp, target: TargetSelector
    ) -> SegmentsTable: ...


# ---------------- Helpers ----------------

def _iter_transcript_windows(
    results_obj: SliceSearchResult,
) -> Iterable[Tuple[TdoSliceMetadata, dict[str, Any]]]:
    """
    Yield (recording_metadata, window_dict) for each transcript window
    across all slice results.
    """
    for res in results_obj.results or []:
        rec: TdoSliceMetadata | None = res.recording
        if not rec:
            continue
        for hit in res.hits or []:
            t = hit.get("transcript")
            if not t:
                continue
            for win in t.get("transcript") or []:
                yield rec, win


def transcript_windows_to_segments(results_obj: SliceSearchResult) -> SegmentsTable:
    """One Segment per transcript window (context span)."""
    rows = []
    for rec, win in _iter_transcript_windows(results_obj):
        tdo_id = str(rec.recordingId or "")
        start = float(win.get("startTime", 0.0))
        end = float(win.get("endTime", 0.0))

        meta = {
            "text": win.get("text"),
            "term_hits": win.get("hits", []),
            "slice": {
                "relativeStartTimeMs": rec.relativeStartTimeMs,
                "relativeStopTimeMs": rec.relativeStopTimeMs,
                "absoluteStartTimeMs": rec.absoluteStartTimeMs,
                "absoluteStopTimeMs": rec.absoluteStopTimeMs,
            },
            "aion": {"transcript": {"hits": win.get("hits", [])}},
        }

        rows.append(
            create_segment_dict(
                tdo_id=tdo_id,
                start_s=start,
                end_s=end,
                signal="transcript",
                channel="audio",
                label=None,
                score=0.0,
                transcript=win.get("text"),
                meta=meta,
            )
        )
    return new_segments_table(rows)


def transcript_tokens_to_segments(results_obj: SliceSearchResult) -> SegmentsTable:
    """One Segment per token-level hit inside each window."""
    rows = []
    for rec, win in _iter_transcript_windows(results_obj):
        tdo_id = str(rec.recordingId or "")
        text = win.get("text")
        for h in win.get("hits") or []:
            start = float(h.get("startTime", 0.0))
            end = float(h.get("endTime", 0.0))

            meta = {
                "text": text,
                "term_hit": h,
                "slice": {
                    "relativeStartTimeMs": rec.relativeStartTimeMs,
                    "relativeStopTimeMs": rec.relativeStopTimeMs,
                    "absoluteStartTimeMs": rec.absoluteStartTimeMs,
                    "absoluteStopTimeMs": rec.absoluteStopTimeMs,
                },
                "aion": {"transcript": {"hit": h}},
            }

            rows.append(
                create_segment_dict(
                    tdo_id=tdo_id,
                    start_s=start,
                    end_s=end,
                    signal="transcript",
                    channel="audio",
                    label=h.get("queryTerm"),
                    score=0.0,
                    transcript=text,
                    meta=meta,
                )
            )
    return new_segments_table(rows)


def face_detections_to_segments(results_obj: SliceSearchResult, inject_label: str | None = None) -> SegmentsTable:
    """Convert face recognition results to Segment objects."""
    rows = []
    for res in results_obj.results or []:
        rec = res.recording
        if not rec:
            continue
        tdo_id = str(rec.recordingId or "")
        for hit in res.hits or []:
            series_list = hit.get("face-recognition", {}).get("series", [])
            for series in series_list:
                entity_id = series.get("entityId")
                library_id = series.get("libraryId")
                # Some indexes store as `series` of fixed ms bins vs explicit "detections"
                # Support both: prefer `detections`; else build a pseudo-detection from series start/end.
                detections = series.get("detections") or []
                if detections:
                    for det in detections:
                        start = float(det.get("start", 0.0)) / 1000.0
                        end = float(det.get("end", 0.0)) / 1000.0
                        conf = float(det.get("confidence", 0.0))

                        rows.append(
                            create_segment_dict(
                                tdo_id=tdo_id,
                                start_s=start,
                                end_s=end,
                                signal="face",
                                channel="video",
                                #entity_id=entity_id,
                                label=inject_label or entity_id,
                                score=conf,
                                bbox=det.get("boundingBox"),
                                poly=det.get("boundingPoly"),
                            )
                        )
                else:
                    # Fallback: series-level time in ms keys "start"/"end" if present
                    start = float(series.get("start", 0.0)) / 1000.0
                    end = float(series.get("end", 0.0)) / 1000.0
                    conf = float(series.get("confidence", 0.0))
                    if end > start:  # sanity guard
                        rows.append(
                            create_segment_dict(
                                tdo_id=tdo_id,
                                start_s=start,
                                end_s=end,
                                signal="face",
                                channel="video",
                                label=entity_id,
                                score=conf,
                            )
                        )
    return new_segments_table(rows)


def logo_detections_to_segments(results_obj: SliceSearchResult) -> SegmentsTable:
    """Convert logo recognition results to Segment objects."""
    rows = []
    for res in results_obj.results or []:
        rec = res.recording
        if not rec:
            continue
        tdo_id = str(rec.recordingId or "")
        for hit in res.hits or []:
            series_list = hit.get("logo-recognition", {}).get("series", [])
            for series in series_list:
                entity_id = series.get("entityId")
                library_id = series.get("libraryId")
                detections = series.get("detections") or []
                if detections:
                    for det in detections:
                        start = float(det.get("start", 0.0)) / 1000.0
                        end = float(det.get("end", 0.0)) / 1000.0
                        conf = float(det.get("score", 0.0))

                        rows.append(
                            create_segment_dict(
                                tdo_id=tdo_id,
                                start_s=start,
                                end_s=end,
                                signal="logo",
                                channel="video",
                                label=entity_id,
                                score=conf,
                                bbox=det.get("boundingBox"),
                                poly=det.get("boundingPoly"),
                            )
                        )
                else:
                    start = float(series.get("start", 0.0)) / 1000.0
                    end = float(series.get("end", 0.0)) / 1000.0
                    conf = float(series.get("score", 0.0))
                    if end > start:
                        meta = {
                            "entityId": entity_id,
                            "libraryId": library_id,
                            "slice": {
                                "relativeStartTimeMs": rec.relativeStartTimeMs,
                                "relativeStopTimeMs": rec.relativeStopTimeMs,
                                "absoluteStartTimeMs": rec.absoluteStartTimeMs,
                                "absoluteStopTimeMs": rec.absoluteStopTimeMs,
                            },
                            "aion": {"logo-recognition": {"series": series}},
                        }

                        rows.append(
                            create_segment_dict(
                                tdo_id=tdo_id,
                                start_s=start,
                                end_s=end,
                                signal="logo",
                                channel="video",
                                label=entity_id,
                                score=conf,
                                meta=meta,
                            )
                        )
    return new_segments_table(rows)


def _clip_by_media_time(segs: SegmentsTable, mt: MediaTime | None) -> SegmentsTable:
    if not mt or (mt.from_s is None and mt.to_s is None):
        return segs
    if segs.is_empty():
        return segs

    f = float(mt.from_s) if mt.from_s is not None else float("-inf")
    t = float(mt.to_s) if mt.to_s is not None else float("inf")

    # Filter for overlapping segments and clip them
    overlapping = segs.filter(~((pl.col("end_s") <= f) | (pl.col("start_s") >= t)))

    if overlapping.is_empty():
        return new_segments_table([])

    # Clip the start and end times
    clipped = overlapping.with_columns(
        [
            pl.when(pl.col("start_s") < f)
            .then(f)
            .otherwise(pl.col("start_s"))
            .alias("start_s"),
            pl.when(pl.col("end_s") > t)
            .then(t)
            .otherwise(pl.col("end_s"))
            .alias("end_s"),
        ]
    )

    return clipped


def _build_abs_time_filters(abs_time: AbsTime | None) -> list[dict[str, Any]]:
    """
    Build search-server range filters for absolute/wall-clock time.
    NOTE: Field names may vary per index; adjust to what your deployment supports
    (e.g., "recording.absoluteStartTimeMs", "recording.createdTime", "recording.modifiedTime").
    Here we use "recording.absoluteStartTimeMs" with ISO strings when available.
    """
    if not abs_time:
        return []

    filters: list[dict[str, Any]] = []
    rng: dict[str, Any] = {}

    # Prefer ISO if provided
    if abs_time.from_iso:
        rng["gte"] = abs_time.from_iso
    if abs_time.to_iso:
        rng["lte"] = abs_time.to_iso

    # Else fall back to epoch seconds (server must accept it for that field)
    if not rng:
        if abs_time.from_epoch_s is not None:
            rng["gte"] = abs_time.from_epoch_s
        if abs_time.to_epoch_s is not None:
            rng["lte"] = abs_time.to_epoch_s

    if rng:
        filters.append(
            {"operator": "range", "field": "recording.absoluteStartTimeMs", **rng}
        )

    return filters


def _and_query(
    main: dict[str, Any], extra_filters: list[dict[str, Any]] | dict[str, Any] | None
) -> dict[str, Any]:
    if not extra_filters:
        return main
    if isinstance(extra_filters, dict):
        extra_filters = [extra_filters]
    return {
        "operator": "and",
        "conditions": [main] + extra_filters,
    }


# ---------------- aiWARE adapter ----------------

class AiwareSegmentAdapter:
    def __init__(self, aiware_client: AsyncAiware):
        self.client: AsyncAgentsAiware = AsyncAgentsAiware.extend_async(aiware_client)

    async def _get_tdo_ids_from_target(self, target: TargetSelector) -> list[str]:
        """ Get list of TDO IDs from the target selector.

        Given a TargetSelector, return the list of TDO IDs it represents, for example all TDOs in a folder.
        
        Args:
            target: TargetSelector to specify which TDOs to retrieve.
            
        Returns:
            List of TDO IDs.
        """
        match target:
            case TargetByOrg():
                # Get all TDO IDs in the org
                raise NotImplementedError("org-based search not implemented yet")
            case TargetByIds(tdo_ids=ids):
                return ids
            case TargetByFolder(folder_id=fid, folder_name=None):
                raise NotImplementedError("folder_id-based search not implemented yet")
            case TargetByFolder(folder_id=None, folder_name=fname):
                raise NotImplementedError(
                    "folder_name-based search not implemented yet"
                )
            case _:
                raise TypeError(f"Unhandled target: {target!r}")

    @async_lru.alru_cache(ttl=180)
    async def _entities_to_ids(self, library_type: str) -> dict[str, list[str]]:
        """
        Cache all entity names to IDs mapping for the org.
        
        Returns:
            Dict mapping lowercased entity names to list of entity IDs.

        Note: names may not be unique, hence list of IDs.
        """
        limit = 500
        cnt = limit
        offset = 0
        # TODO: build this with fuzzy search etc.
        # TODO: handle libraryTypeId='people' etc.
        # Cache name->id mapping for entities in all libraries, names might not be unique
        entity_map = {}
        libs = await self.client.get_libraries()
        if not (libs and libs.libraries and libs.libraries.records):
            return entity_map
        lib_ids = [lib.id for lib in libs.libraries.records if lib and lib.libraryTypeId == library_type]

        while cnt >= limit:
            entities = await self.client.get_entities(
                libraryIds=lib_ids, limit=limit, offset=offset
            )
            if entities and entities.entities and entities.entities.records:
                cnt = len(entities.entities.records)
                for entity in entities.entities.records:
                    if entity and entity.name and entity.id:
                        entity_map.setdefault(entity.name.lower(), []).append(entity.id)
            else:
                cnt = 0
            offset += cnt
        return entity_map

    async def _find_entity_by_name(self, name: str, library_type: str) -> list[str]:
        """ Find entity IDs by exact name match (case-insensitive).

        Args:
            name: Entity name to search for.
            library_type: Type of entity, e.g. "person" or "logo".

        Returns:
            List of entity IDs matching the name.
        
        Raises ValueError if not found.
        """
        entity_map = await self._entities_to_ids(library_type)
        log.info(f"Searching for entity name '{name}' in map: {len(entity_map)} entries")
        entity_ids = entity_map.get(name.strip().lower())
        if not entity_ids:
            raise ValueError(f"Entity not found: {name}")
        return entity_ids

    async def search_paginated(
        self,
        req: SearchRequest,
        segments_converter: Callable[[SliceSearchResult], SegmentsTable],
    ) -> SegmentsTable:
        """ Helper to do paginated search and convert results to segments.
            Handles pagination by repeatedly querying until fewer results than `limit` are returned.

        Args:
            req: SearchRequest with initial query, index, limit, offset (offset will be modified).
            segments_converter: Function to convert SliceSearchResult to SegmentsTable.

        Returns:
            SegmentsTable with all results concatenated.

        Note: modifies req.offset and req.limit
        """
        req.offset = 0
        if not req.limit:
            req.limit = 100
        cnt = req.limit
        segs_list = []
        while cnt >= req.limit:
            results: SliceSearchResult = await self.client.search_media(req)
            segs = segments_converter(results)
            segs_list.append(segs)

            if results and results.results:
                cnt = len(results.results)
            else:
                cnt = 0
            req.offset += cnt
        all_segs = pl.concat(segs_list) if segs_list else new_segments_table([])
        return all_segs

    def _build_target_query(
        self, target: TargetSelector | None
    ) -> dict[str, Any] | None:
        """Build a query fragment for the target - e.g. TDO ID or folder ID."""
        if not target:
            return None

        match target:
            case TargetByOrg():
                return None
            case TargetByIds(tdo_ids=ids):
                return {"operator": "terms", "field": "recordingId", "values": ids}
            case TargetByFolder(folder_id=fid, folder_name=None):
                raise NotImplementedError("folder_id-based search not implemented yet")
            case TargetByFolder(folder_id=None, folder_name=fname):
                raise NotImplementedError(
                    "folder_name-based search not implemented yet"
                )
            case _:
                raise TypeError(f"Unhandled target: {target!r}")

    async def find_transcript(
        self, op: FindTranscriptOp, target: TargetSelector
    ) -> SegmentsTable:
        """ Find transcript segments matching the query and target.

        Args:
            op: FindTranscriptOp with query, abs_time, media_time, granularity.
            target: TargetSelector to limit the search scope.

        Returns:
            SegmentsTable with transcript segments matching the criteria.
        """
        base_query = {
            "operator": "query_string",
            "field": "transcript.transcript",
            "value": op.query.lower(),
        }
        query = _and_query(base_query, _build_abs_time_filters(op.abs_time))
        query = _and_query(query, self._build_target_query(target))
        req = SearchRequest(index=["mine"], query=query)

        log.debug("Transcript search: %s", req)
        # Use granularity from op to determine processing mode
        if op.granularity in ("window", "sentence"):
            search_results: SliceSearchResult = await self.client.search_media(
                req
            )
            segs = transcript_windows_to_segments(search_results)
            return _clip_by_media_time(segs, op.media_time)
        elif op.granularity in ("token", "word"):
            search_results: SliceSearchResult = await self.client.search_media(
                req
            )
            segs = transcript_tokens_to_segments(search_results)
            return _clip_by_media_time(segs, op.media_time)
        else:
            raise ValueError(f"unknown granularity {op.granularity}")

    async def find_face(self, op: FindFaceOp, target: TargetSelector) -> SegmentsTable:
        """Find face segments by entityId or entity name.

        Args:
            op: FindFaceOp with where clause containing either 'entityId' or 'name'.
            target: TargetSelector to limit the search scope.

        Returns:
            SegmentsTable with face segments matching the criteria.
        """
        name = op.where.get("name")
        if "entityId" in op.where:
            entity_ids = [op.where.get("entityId")]
        else:
            if name:
                entity_ids = await self._find_entity_by_name(name, library_type="people")
                if not entity_ids:
                    raise ValueError(f"Entity not found: {name}")
            else:
                raise ValueError(
                    "find_face.where must include {'entityId': '...'} or {'name': '...'}"
                )

        base_query = {
            "operator": "terms",
            "field": "face-recognition.series.entityId",
            "values": entity_ids,
        }
        query = _and_query(base_query, _build_abs_time_filters(op.abs_time))
        query = _and_query(query, self._build_target_query(target))

        req = SearchRequest(index=["mine"], query=query, limit=500)
        segs = await self.search_paginated(req, partial(face_detections_to_segments, inject_label=name))
        return _clip_by_media_time(segs, op.media_time)

    async def find_logo(self, op: FindLogoOp, target: TargetSelector) -> SegmentsTable:
        """Find logo segments by entityId or entity name.

        Args:
            op: FindLogoOp with where clause containing either 'entityId' or 'name'.
            target: TargetSelector to limit the search scope.

        Returns:
            SegmentsTable with logo segments matching the criteria.
        """
        # TODO: seems logos don't really use entity IDs in general
        if "entityId" in op.where:
            entity_ids = [op.where.get("entityId")]
        else:
            name = op.where.get("name")
            if name:
                entity_ids = [name]
                # TODO: fuzzy find in aggregate logo list, currently library does not seem to be used for logos

                #entity_ids = await self._find_entity_by_name(name, library_type="logos")
                #if not entity_ids:
                #    raise ValueError(f"Entity not found: {name}")
            else:
                raise ValueError(
                    "find_face.where must include {'entityId': '...'} or {'name': '...'}"
                )

        base_query = {
            "operator": "terms",
            "field": "logo-recognition.series.found",
            "values": entity_ids,
        }
        query = _and_query(base_query, _build_abs_time_filters(op.abs_time))
        query = _and_query(query, self._build_target_query(target))

        req = SearchRequest(index=["mine"], query=query, limit=500)
        log.debug("Logo search: %s", req)
        segs = await self.search_paginated(req, logo_detections_to_segments)
        return _clip_by_media_time(segs, op.media_time)

    async def get_tdos(
        self, target: TargetSelector, include_segments: bool
    ) -> list[MediaTDO]:
        """Get MediaTDO objects for the given target.

        Args:
            target: TargetSelector to specify which TDOs to retrieve.
            include_segments: Whether to include segments (i.e. reading AION) in the MediaTDO objects or just metadata.

        Returns:
            List of MediaTDO objects.
        """
        tdo_ids = await self._get_tdo_ids_from_target(target)
        tdos = await MediaTDO.from_tdo_ids(
            self.client, tdo_ids, include_segments=include_segments
        )
        return tdos

    async def get_tdo_transcript(
        self, op: GetTdoTranscriptOp, target: TargetSelector
    ) -> SegmentsTable:
        """Get transcript segments for TDOs in the target.

        Args:
            op: GetTdoTranscriptOp with optional media_time to clip segments.
            target: TargetSelector to specify which TDOs to retrieve transcripts for.

        Returns:
            SegmentsTable with transcript segments from the TDOs.
        """
        result_dfs = []
        tdo_ids = await self._get_tdo_ids_from_target(target)
        # TODO: retry
        tdos = await MediaTDO.from_tdo_ids(
            self.client, tdo_ids, include_segments=True
        )
        for tdo in tdos:
            transcript_segments = tdo.segments.get("transcript")
            if transcript_segments is not None and not transcript_segments.is_empty():
                result_dfs.append(transcript_segments)

        if result_dfs:
            result_df = pl.concat(result_dfs)
            if op.granularity == "utterance":
                return coalesce_segments(result_df, tolerance_s=0.1)
            elif op.granularity == "full":
                return coalesce_segments(result_df, tolerance_s=None)
        return new_segments_table([])

    async def get_tdo_faces(
        self, op: GetTdoFacesOp, target: TargetSelector
    ) -> SegmentsTable:
        """Get face segments for TDOs in the target.

        Args:
            op: GetTdoFacesOp with optional media_time to clip segments.
            target: TargetSelector to specify which TDOs to retrieve faces for.

        Returns:
            SegmentsTable with face segments from the TDOs.
        """
        result_dfs = []
        tdo_ids = await self._get_tdo_ids_from_target(target)
        tdos = await MediaTDO.from_tdo_ids(
            self.client, tdo_ids, include_segments=True
        )
        for tdo in tdos:
            face_segments = tdo.segments.get("face")
            if face_segments is not None and not face_segments.is_empty():
                result_dfs.append(face_segments)

        if result_dfs:
            return pl.concat(result_dfs)
        else:
            return new_segments_table([])

    # async def _get_tdos(self, tdo_ids: list[str], include_segments: bool = True) -> list[MediaTDO]:
    #     tdos = await MediaTDO.from_tdo_ids(self.client, tdo_ids, include_segments=include_segments)
    #     self.state.tdo_table = TdoTable([{"tdo_id": tdo.tdo_id, "tdo_name": tdo.name} for tdo in tdos if tdo])
    #     return tdos

    async def get_tdo_logos(
        self, op: GetTdoLogosOp, target: TargetSelector
    ) -> SegmentsTable:
        """Get logo segments for TDOs in the target.

        Args:
            op: GetTdoLogosOp with optional media_time to clip segments.
            target: TargetSelector to specify which TDOs to retrieve logos for.

        Returns:
            SegmentsTable with logo segments from the TDOs.
        """
        result_dfs = []
        tdo_ids = await self._get_tdo_ids_from_target(target)
        tdos = await MediaTDO.from_tdo_ids(
            self.client, tdo_ids, include_segments=True
        )
        for tdo in tdos:
            logo_segments = tdo.segments.get("logo")
            if logo_segments is not None and not logo_segments.is_empty():
                result_dfs.append(logo_segments)

        if result_dfs:
            return pl.concat(result_dfs)
        else:
            return new_segments_table([])
