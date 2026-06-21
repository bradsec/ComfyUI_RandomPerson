# Segmented Nodes + Body Attributes - Design

Date: 2026-06-21
Status: Approved, ready for implementation plan

## Goal

Two related changes to ComfyUI_RandomPerson:

1. Add new body-detail attributes (shoulders, chest, bust size, bust shape) to
   the existing all-in-one node, defaulting off.
2. Add a set of smaller, group-focused segment nodes that reuse the same JSON
   data and shared core, and move every node into a dedicated "Random Person"
   menu category (out of "utils").

The all-in-one node stays. Segment nodes are additive.

## Sequencing (phased)

- Phase 1: new body categories in the full node only. Ship and verify first.
- Phase 2: factory refactor, segment nodes, menu category move, JS gating.

Each phase is independently testable and committable.

## Phase 1 - New body attributes

### New categories (all sex-gated, all default off)

| Key          | Real for | Opposite-sex file | Labels |
|--------------|----------|-------------------|--------|
| `shoulders`  | both     | n/a (both real)   | narrow, average, broad, sloping, square, muscular (m) / soft (f) |
| `chest`      | male     | female = `none` stub | flat, average, broad, muscular, barrel |
| `bust_size`  | female   | male = `none` stub   | petite, small, average, full, large |
| `bust_shape` | female   | male = `none` stub   | round, teardrop, wide-set, close-set, natural |

Opposite-sex stub = a single `{"label": "none", "description": ""}` entry,
matching the existing pattern (`data/male/makeup.json` has one `none`,
`data/female/facial_hair.json` has one `clean shaven`).

Wording is neutral / SFW: anatomical descriptors for image prompts, not
sexualized. Age floor is already clamped to 21 elsewhere.

### Data files

New files under `data/male/` and `data/female/` for each key
(`shoulders.json`, `chest.json`, `bust_size.json`, `bust_shape.json`). Same
`{label, description}` schema as existing sex-gated files.

Description values carry the noun so the builder can append directly, e.g.
`"broad shoulders"`, `"a muscular chest"`, size `"full"`, shape `"round"`.

### nodes.py wiring

- Add the four keys to `CATEGORY_SPECS` (placed in the body region, after
  `body_type`).
- Add all four to `SEX_GATED`.
- Add all four to `DEFAULT_OFF`.
- `build_description`: after the build/`body_type` part, append, in order:
  `shoulders`, `chest`, then a combined `bust` phrase.
  - `bust` phrase combines `bust_size` + `bust_shape`:
    - both -> `"a {size}, {shape} bust"` (e.g. `"a full, round bust"`)
    - size only -> `"a {size} bust"`
    - shape only -> `"a {shape} bust"`
    - neither -> omitted
  - New params added to `build_description` as trailing keyword args
    (default None) so existing positional callers and tests are unaffected,
    same approach used for `eye_shape`/`eyebrows`.
- Output pins (full node): append new pins to `RETURN_NAMES` at the end
  (`shoulders`, `chest`, `bust`). Appending keeps existing output slots stable,
  so existing workflows do not break.
  - `bust` pin = the combined size+shape phrase.

### Tests (Phase 1)

- New body categories default off (mode default == "off").
- Male node: `bust_size`/`bust_shape` never produce output; `chest` can.
- Female node: `chest` never produces output; `bust` can.
- `bust` pin combines size + shape when both fixed.
- Existing tests stay green.

## Phase 2 - Segment nodes + menu category

### Node set

All under `CATEGORY = "Random Person"`. The existing full node also moves here
but keeps `node_id = "RandomPersonNode"` so existing workflows survive (category
is cosmetic; node_id is the stable identity).

| Node id                 | Display name                      | Categories |
|-------------------------|-----------------------------------|------------|
| `RandomPersonNode`      | Random Person Description         | all (full node, unchanged behaviour) |
| `RandomPersonIdentity`  | Random Person: Identity           | age, nationality, complexion, skin_texture |
| `RandomPersonFace`      | Random Person: Face & Expression  | face_shape, eyes, eye_shape, eyebrows, nose_shape, mouth_shape, face_feature, expression |
| `RandomPersonHair`      | Random Person: Hair               | hair_color, hair_style, hair_length, facial_hair |
| `RandomPersonBody`      | Random Person: Body               | body_type, shoulders, chest, bust_size, bust_shape |
| `RandomPersonStyle`     | Random Person: Style              | accessories, makeup |

Every node also has its own `sex`, `seed`, `randomize` widgets. `age` only on
Identity and Full.

### Usage model: independent generators

Each segment node stands alone with its own seed/sex/randomize and produces its
own fragment. No shared "PERSON" wire, no Combine node, no per-key seeding. If a
user wants a full prompt from segments, they concatenate fragments with any
existing string node. Segment fragments are NOT guaranteed to reconstruct the
full node's person for a given seed (independent RNG draw order); that is
acceptable for modular use.

### Architecture: factory-built classes

Refactor so node classes are generated from a spec list rather than hand-written,
to avoid duplicating selection/IO logic across 6 nodes x 2 APIs.

- A `NODE_SPECS` list of `(node_id, display_name, keys, include_age)`.
- A factory builds, per spec, both the V1 class (dict API) and the V3 schema
  (import-guarded `comfy_api`), exposing only that node's category widgets plus
  `sex` (always) and `age` (when `include_age`).
- The shared `generate_person` core runs unchanged. Categories not present in a
  node are forced `off`, so the existing builder already yields the correct
  fragment.
- Per node, outputs = a `description` fragment (only that node's parts,
  comma-joined) + the structured pins for its categories + `sex` + `seed`.
  - Identity owns the `"34 year old Brazilian female"` opener.
  - Face fragment example: `oval face, almond hazel eyes, arched eyebrows,
    button nose, full lips, a soft smile`.

### Sex gating + JS

- Sex-gated categories gate per node off that node's own `sex` widget.
- `js/random_person_node.js` currently hooks a single node id. Refactor to apply
  the sex filter across every node id that contains sex-gated widgets: Full,
  Face, Hair, Body, Style (not Identity, which exposes no gated dropdowns beyond
  `sex`).
- The JS male/female label maps must include the new body categories'
  sex-specific values.

### Tests (Phase 2)

- Each segment node's fragment contains only its group's categories, nothing
  from other groups.
- Identity node owns the age/nationality/sex opener; other segments do not emit it.
- Sex gating respected per node (e.g. Hair node, sex=female -> no facial_hair).
- Factory produces the expected node_ids and display names; all default modes
  match the shared `DEFAULT_OFF` policy.

## Out of scope (YAGNI)

- No shared PERSON context wire.
- No Combine/concat node (use existing string nodes).
- No per-key deterministic seeding.
- No new attributes beyond the four body categories.

## Compatibility / risk notes

- Full node keeps node_id and appends (never reorders) output pins -> existing
  graphs keep working; only menu location changes.
- Adding new default-off random categories does not change existing default
  output, since off categories are omitted. (Note: `eye_shape`, added earlier,
  defaults random and already shifted per-seed output in 1.0.8; the new body
  categories default off and do not.)
- Bust/chest descriptors are SFW and opt-in (default off).
