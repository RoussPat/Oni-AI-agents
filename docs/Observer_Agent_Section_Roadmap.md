# Observer Agents: Save Sections Roadmap

This roadmap defines, for each ONI save-file section, the expected data sources, the observing agent’s goal, and parallelizable tasks. It is aligned with our `SaveGame` structure (header, templates, world, settings, sim_data, game_objects, game_data) and current/planned agents.

## How to use this roadmap
- Parser tasks: low-level parsing work inside `src/oni_ai_agents/services/oni_save_parser/`
- Extraction tasks: populate stable JSON contracts via `SaveFileDataExtractor`
- Agent tasks: prompts/heuristics and outputs for observer agents
- Tests: unit/integration tests with real saves

---

## Metadata & Compatibility
- Expected data: `header.game_info`, `SaveGame.version`, DLC/mod flags, width/height
- Agent goal: Validate compatibility, surface warnings/anomalies for the core agent
- Parallel tasks
  - Parser: Ensure header JSON fields and version range exposed; record width/height from header if present
  - Extraction: `metadata` section with version/base/cluster/cycles/dup_count/dlc/mods/world dims
  - Agent: Rules to flag version mismatches, missing DLC content, deprecated objects
  - Tests: Saves across minor versions; DLC on/off

## Colony Overview
- Expected data: Aggregations across all sections
- Agent goal: Provide KPI snapshot and prioritized risks/opportunities
- Parallel tasks
  - Extraction: Compose KPIs from other sections (breathable %, kcal days, power margin, threats)
  - Agent: Prioritization heuristic; top-5 risks/opps
  - Tests: Scenario summaries vs expected risk ordering

## Duplicants (Roster)
- Expected data: From `game_objects` Minion group: MinionIdentity, MinionResume, MinionModifiers, Traits
- Agent goal: Crew health/readiness; assignment and training recommendations
- Parallel tasks
  - Parser: Minimal decoders for identity, vitals (calories/health/stress/stamina), traits, current job
  - Extraction: `duplicants` list with identity, role, vitals, traits
  - Agent: Alerts (starving, stressed), suggestions (role changes)
  - Tests: Names/roles/vitals parsed from reference saves

Status: Completed (v0.2)
- Parser implemented:
  - MinionIdentity (name/gender; improved `arrival_time` handling)
  - MinionResume (`currentRole`, `AptitudeBySkillGroup`; scaffolding for `MasteryByRoleID`)
  - MinionModifiers (extended vitals: decor, temperature, breath, bladder, immune, toxicity, radiation, morale)
  - Klei.AI.Traits / Klei.AI.Effects (known-ID mapping; unknowns omitted)
- Extraction (contract):
  - `duplicants.list[*]` with `identity` (name, gender, arrival_time), `role`, `vitals` (extended), `aptitudes` (normalized), `traits` (list), `effects` (list), `position`
- Tests: Enriched duplicants contract and extractor schema added; full suite passing

## Schedules & Priorities
- Expected data: Schedules and per-dup priorities from `game_data`/components
- Agent goal: Optimize schedules and priorities to reduce stress and idle time
- Parallel tasks
  - Parser: Read schedules; map priority sets
  - Extraction: `schedules`, `priorities` per duplicant
  - Agent: Detect conflicts (night owls on day shift), propose fixes
  - Tests: Known schedule layouts detected

## Skills & Roles
- Expected data: MinionResume mastery, aptitude, current role
- Agent goal: Recommend skill training paths aligned with colony needs
- Parallel tasks
  - Parser: Read MasteryByRoleID, AptitudeBySkillGroup
  - Extraction: `skills`, `aptitudes`, `current_role`
  - Agent: Next-skill recommendations, role swaps
  - Tests: Mastery/role parsed correctly

## Consumables & Permissions
- Expected data: Food/medicine permissions and policies
- Agent goal: Ensure correct consumables policies for health/morale
- Parallel tasks
  - Parser: Read policy structs
  - Extraction: `consumable_policies`
  - Agent: Flag dupes on wrong diets; propose changes
  - Tests: Policy matrices round-trip

## Rooms & Decor
- Expected data: Room assignments/types, decor values (from buildings/tiles)
- Agent goal: Validate room bonuses and decor coverage
- Parallel tasks
  - Parser: Room system data; decor summaries by area
  - Extraction: `rooms` with type/validity and decor aggregates
  - Agent: Fix invalid rooms; improve morale hotspots
  - Tests: Detect invalid/broken rooms

## Power Grid
- Expected data: Generators, consumers, wires, batteries, circuits
- Agent goal: Reliability and efficiency of power distribution
- Parallel tasks
  - Parser: Circuit grouping, production/consumption snapshots, battery charge
  - Extraction: `power_grid` circuits with metrics and issues
  - Agent: Overload mitigation, generation deficits, battery sizing
  - Tests: Overload/deficit cases recognized

## Gas Conduits
- Expected data: Gas pipes, bridges, pumps, vents, network groupings
- Agent goal: Resolve blockages and element mixing; balance flows
- Parallel tasks
  - Parser: Network detection; per-net flow summaries and composition
  - Extraction: `gas_networks` with sources/sinks/flow/blockages
  - Agent: Routing/bridge/vent adjustments
  - Tests: Mixed-element and blockage scenarios

## Liquid Conduits
- Expected data: Liquid pipes, bridges, pumps, vents, temps/germs
- Agent goal: Prevent scalding/freezing/germ spread; ensure supply
- Parallel tasks
  - Parser: Network detection; temps/germs; flow rates
  - Extraction: `liquid_networks` with health metrics
  - Agent: Heat exchange, sterilization, overpressure fixes
  - Tests: Overpressure/temperature/germ cases

## Solid Conveyor Rails
- Expected data: Rails, loaders, receptacles, routes
- Agent goal: Unjam logistics; optimize routes and throughput
- Parallel tasks
  - Parser: Net detection; jam points; throughput
  - Extraction: `solid_rails`
  - Agent: Route redesign suggestions
  - Tests: Jam detection

## Automation Network
- Expected data: Wires, ports, sensors, gates
- Agent goal: Correct miswired or idle signals; improve automation logic
- Parallel tasks
  - Parser: Net graph; device states snapshot
  - Extraction: `automation` nets and device states
  - Agent: Misconfiguration hints; sensor placement
  - Tests: Known logic circuits recognized

## Transport/Pathing
- Expected data: Transit tubes, doors, ladders; door permissions
- Agent goal: Reduce pathing costs and chokepoints
- Parallel tasks
  - Parser: Tube networks/door states
  - Extraction: `transport`
  - Agent: Door policy changes; tube segments additions
  - Tests: Pathing chokepoint cases

## Storage & Materials Inventory
- Expected data: Storage components, item stacks by tag/element
- Agent goal: Centralize and ensure critical resource availability
- Parallel tasks
  - Parser: Collect storage contents; aggregate by tag
  - Extraction: `inventory` by tag and per-storage utilization
  - Agent: Storage policy and fetch errand reduction
  - Tests: Inventory totals match save

## Food & Kitchens
- Expected data: Edibles, fridges, cooking buildings, spoilage timers
- Agent goal: Maintain safe kcal buffer; plan recipes
- Parallel tasks
  - Parser: Aggregate kcal and spoilage
  - Extraction: `food` with kcal_total and items
  - Agent: Recipe queue suggestions; cold-chain
  - Tests: Kcal days computed

## Farming (Plants)
- Expected data: Plant species, growth stage, environment requirements
- Agent goal: Ensure sustained crop output
- Parallel tasks
  - Parser: Plant states and requirements
  - Extraction: `farming` plants list
  - Agent: Atmosphere/temp/fertilizer recommendations
  - Tests: Growth blocking detection

## Critters & Ranching
- Expected data: Critter species, ages, pens, reproduction
- Agent goal: Stable populations and ranch bonuses
- Parallel tasks
  - Parser: Critter states, room pens
  - Extraction: `ranching`
  - Agent: Culling/breeding plans; overcrowding fixes
  - Tests: Overcrowding detection

## World Grid (Cells)
- Expected data: Per-cell element, mass, temp, disease, radiation (DLC)
- Agent goal: Provide spatial summaries for other agents
- Parallel tasks
  - Parser: Preserve or minimally decode cell data; efficient histograms
  - Extraction: `world_grid_summary` (histograms, breathable %, hotspots)
  - Agent: None standalone; feeds atmosphere/heat/germs
  - Tests: Histogram accuracy

## Oxygen/Atmosphere
- Expected data: From world grid and O2 producers/consumers
- Agent goal: Keep breathable %, balance O2 production/consumption
- Parallel tasks
  - Extraction: `atmosphere` with breathable %, O2 balance
  - Agent: Producer placement and seal suggestions
  - Tests: Low-O2 scenario recognition

## Heat & Temperature Hazards
- Expected data: Cell temps, building temps, overheat thresholds
- Agent goal: Avoid overheat/freezing; plan heat management
- Parallel tasks
  - Extraction: `heat` hotzones and risks
  - Agent: Cooling/heating strategies
  - Tests: Overheat risk detection

## Germs/Disease
- Expected data: Germ counts by cell/liquid/solid, dup exposures
- Agent goal: Reduce transmission and sanitize flows
- Parallel tasks
  - Extraction: `germs` hotspots and exposure risks
  - Agent: Wash basins, chlorine loops, UV, routing
  - Tests: Outbreak scenarios

## World Features & Geysers
- Expected data: Geyser types/outputs, POIs, teleporters
- Agent goal: Plan exploitation and hazard management
- Parallel tasks
  - Parser: Identify geysers/POIs
  - Extraction: `world_features`
  - Agent: Mining/exploitation plans
  - Tests: Geyser identification accuracy

## Research/Tech
- Expected data: `game_data.research`
- Agent goal: Prioritize techs for strategic goals
- Parallel tasks
  - Parser: Research trees, completed/in-progress
  - Extraction: `research`
  - Agent: Next-tech recommendations
  - Tests: Tech completion states

## Achievements/Objectives
- Expected data: `game_data.achievements`
- Agent goal: Track long-term goals and near-term wins
- Parallel tasks
  - Parser: Achievements data
  - Extraction: `achievements`
  - Agent: Suggestions to unlock targets
  - Tests: Progress tracking

## Events/Notifications
- Expected data: Recent alerts/logs
- Agent goal: Triage unresolved criticals
- Parallel tasks
  - Parser: Alert/event buffers
  - Extraction: `events`
  - Agent: Triage and assignment to systems
  - Tests: Critical alert capture

## Settings & Mods
- Expected data: `settings.game_settings`, `settings.world_settings`, header mods
- Agent goal: Ensure strategies respect rules/configs
- Parallel tasks
  - Parser: Decode settings blocks
  - Extraction: `settings`
  - Agent: Constraint-aware suggestions
  - Tests: Settings reflected

## Space & Rockets (DLC)
- Expected data: Rocket modules, missions, cluster map
- Agent goal: Plan missions and logistics
- Parallel tasks
  - Parser: Rocket states and cluster nodes
  - Extraction: `rockets`
  - Agent: Mission planning
  - Tests: Rocket parsing

## Maintenance & Breakage
- Expected data: Building states: broken, entombed, overheated, repair errands
- Agent goal: Reduce downtime and prevent failures
- Parallel tasks
  - Parser: Building flags and pending errands
  - Extraction: `maintenance`
  - Agent: Repair priorities and preventive actions
  - Tests: Failure detection

---

### Cross-cutting workstreams (parallel)
- Type templates decoding (unblocks most object-level sections)
- Network graph builders (power/conduits/automation)
- World-grid histogrammer (feeds atmosphere/heat/germs)
- Data contracts v0.1 in `SaveFileDataExtractor` for all sections
- Test fixtures: a small set of public saves covering edge cases


