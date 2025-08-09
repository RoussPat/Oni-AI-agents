# ONI Save Parser: Gaps and Improvements

This document summarizes current extraction capabilities, gaps vs the research parsers, and a prioritized roadmap.

## What we extract today (exact)
- Header JSON (parsed and exposed): keys like `baseName`, `clusterId`, `numberOfCycles`, `numberOfDuplicants`, `saveMajorVersion`, `saveMinorVersion`, `dlcIds`, `isAutoSave`, etc. Plus injected: `buildVersion`, `headerVersion`, `isCompressed`.
- Derived fields:
  - `SaveGame.version` from header (`major`, `minor`)
  - `SaveGame.header.cluster_id`, `num_cycles`, `num_duplicants`
  - Summary: `version`, `cycles`, `duplicants`, `object_groups`, `total_objects`, `object_counts`, `world_data_size`, `sim_data_size`
- Section wrapper (placeholder values unless noted):
  - `resources`: `cycles` (int), `base_name` (str), `cluster_id` (str), `food` (None), `oxygen` (None), `power` (None), `materials` ({}), `storage_usage` ({})
  - `duplicants`: `count` (int), `health_status` ({}), `morale_levels` ({}), `skill_assignments` ({}), `current_tasks` ({}), `stress_levels` ({})
  - `threats`: `diseases` ({}), `temperature_zones` ({}), `pressure_issues` ({}), `contamination` ({}), `hostile_creatures` ({})

## Big missing pieces (vs research repos)
- Compression & section framing: body sizes, compression flags, and boundaries not parsed; world/sim/settings/objects/game-data not decoded.
- Type templates: not implemented; required to interpret components/behaviors.
- Game objects: duplicants/buildings/items/components/behaviors not parsed into structures.
- Writer/idempotent round-trip: not implemented; no regression via round-trip testing.
- Incremental/trampoline parsing & progress hooks: not present.
- Versioning: support range 7.11–7.17; fallback minor defaults inconsistent.
- World/sim: preserved as binary without framing metadata.

## Proposed roadmap (phased)
1) Section framing & compression
- Parse header flags; read section sizes; implement zlib decompression; store world/sim/settings/object/game-data as framed blobs.
- Expose `world_data_size`, `sim_data_size`, checksums/offsets.

2) Type templates
- Implement template table parsing; map template `name` -> schema for components/behaviors.

3) Game object tree
- Parse object groups and nested objects; attach components/behaviors using templates.
- Minimal decoders: duplicant stats (health, stress, calories, traits, skills) and common building state.

4) Data extraction contract v1
- Fill `resources` with real values (food kcal, O2 production/storage, power generation/consumption; materials by element/mass).
- Fill `duplicants` (health/stress/morale/skills/tasks).
- Fill `threats` (diseases counts, extreme temps/pressures, contamination hotspots, hostile critters).

5) Writer & round-trip tests
- Implement write path preserving ordering (kv tuples) and idempotent round-trip tests.

6) Progress/cancellation hooks
- Provide progress callbacks; prepare for iterator-based trampoline later.

## Parallel workstreams by section

See `docs/Observer_Agent_Section_Roadmap.md` for detailed, section-specific tasks that teams can execute in parallel. Prioritize:
- Templates decoding → unlocks Duplicants/Buildings/Networks
- Network graph builders → Power/Gas/Liquid/Automation sections
- World-grid histograms → Atmosphere/Heat/Germs sections
- Data contracts v0.1 → Agents can develop against stable keys while parsing deepens

## Acceptance criteria (per phase)
- Phase 1: Can parse body frames and decompress; summary sizes/offsets exposed; all unit tests green.
- Phase 2: Templates parsed; visible map of available components/behaviors.
- Phase 3: Duplicants/buildings decoded minimally; counts present in `object_counts`.
- Phase 4: Section data populated with non-placeholder metrics; observer agents run without mock data.
- Phase 5: Round-trip identical (uncompressed content) on sample saves.

## Notes
- World/sim content remains preserved; framing enables safe future parsing without blocking agents.
- Aligns with JS repo parity for read/write; defers esoteric game objects until core metrics are stable.
