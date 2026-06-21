# Segmented Nodes + Body Attributes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four opt-in body-detail attributes (shoulders, chest, bust size, bust shape) to the existing node, then add five group-focused segment nodes that reuse the same data and core, all under a "Random Person" menu category.

**Architecture:** A single shared core (`generate_person`) already resolves every category and builds the description. Phase 1 adds the new categories to the data layer, the category spec, and the builder/pins. Phase 2 replaces the two hand-written node classes with a factory that builds both the V1 and V3 classes for each entry in a `NODE_SPECS` list; segment nodes expose only their group's widgets and force every other category off, so the shared core yields the right fragment with zero duplicated selection logic.

**Tech Stack:** Python 3, stdlib only (`json`, `os`, `random`, `functools`). Tests use `unittest` (no pytest). ComfyUI dual API (legacy dict `INPUT_TYPES` + import-guarded `comfy_api.v0_0_2`). Browser widget gating in `js/random_person_node.js`.

## Global Constraints

- Tests run with: `python3 -m unittest test_random_person -v` (the binary is `python3`, not `python`).
- Data files use schema `{"label": str, "description": str}`. Sex-gated files live in `data/male/` and `data/female/`; a category that is real for only one sex uses a single `{"label": "none", "description": ""}` entry in the other sex's file (existing precedent: `data/male/makeup.json`, `data/female/facial_hair.json`).
- New attribute categories default to mode `"off"` (opt-in flair).
- Descriptors are neutral / SFW. Age is already clamped to >= 21 elsewhere; do not touch age logic.
- Never reorder existing `RETURN_NAMES` entries or existing `CATEGORY_SPECS` entries; only append, so existing ComfyUI workflows keep their output-slot links.
- The full node keeps `node_id = "RandomPersonNode"`.
- Commit after each task. Author under the user's git identity; no AI attribution in commit messages.

---

# PHASE 1 - Body attributes in the full node

## Task 1: Body data files

**Files:**
- Create: `data/male/shoulders.json`, `data/female/shoulders.json`
- Create: `data/male/chest.json`, `data/female/chest.json`
- Create: `data/male/bust_size.json`, `data/female/bust_size.json`
- Create: `data/male/bust_shape.json`, `data/female/bust_shape.json`
- Test: `test_random_person.py`

**Interfaces:**
- Produces: eight JSON files loadable via `core.load_sex(sex, "<key>.json")`, each a list of `{"label","description"}` dicts.

- [ ] **Step 1: Write the failing test**

Add this class to `test_random_person.py` (after the existing `TestBuildDescription` class):

```python
class TestBodyData(unittest.TestCase):

    BODY_KEYS = ("shoulders", "chest", "bust_size", "bust_shape")

    def test_all_body_files_load(self):
        for sex in ("male", "female"):
            for key in self.BODY_KEYS:
                data = core.load_sex(sex, f"{key}.json")
                self.assertTrue(len(data) >= 1, f"{sex}/{key}")
                for item in data:
                    self.assertIn("label", item)
                    self.assertIn("description", item)

    def test_male_bust_is_stub(self):
        for key in ("bust_size", "bust_shape"):
            labels = [i["label"] for i in core.load_sex("male", f"{key}.json")]
            self.assertEqual(labels, ["none"], key)

    def test_female_chest_is_stub(self):
        labels = [i["label"] for i in core.load_sex("female", "chest.json")]
        self.assertEqual(labels, ["none"])

    def test_shoulders_real_for_both(self):
        for sex in ("male", "female"):
            labels = [i["label"] for i in core.load_sex(sex, "shoulders.json")]
            self.assertGreater(len(labels), 1, sex)
            self.assertNotIn("none", labels)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestBodyData -v`
Expected: FAIL with `FileNotFoundError` (files do not exist yet).

- [ ] **Step 3: Create the data files**

`data/male/shoulders.json`:
```json
[
  { "label": "narrow",   "description": "narrow shoulders" },
  { "label": "average",  "description": "average shoulders" },
  { "label": "broad",    "description": "broad shoulders" },
  { "label": "sloping",  "description": "sloping shoulders" },
  { "label": "square",   "description": "square shoulders" },
  { "label": "muscular", "description": "muscular shoulders" }
]
```

`data/female/shoulders.json`:
```json
[
  { "label": "narrow",  "description": "narrow shoulders" },
  { "label": "average", "description": "average shoulders" },
  { "label": "broad",   "description": "broad shoulders" },
  { "label": "sloping", "description": "sloping shoulders" },
  { "label": "square",  "description": "square shoulders" },
  { "label": "soft",    "description": "soft shoulders" }
]
```

`data/male/chest.json`:
```json
[
  { "label": "flat",     "description": "a flat chest" },
  { "label": "average",  "description": "an average chest" },
  { "label": "broad",    "description": "a broad chest" },
  { "label": "muscular", "description": "a muscular chest" },
  { "label": "barrel",   "description": "a barrel chest" }
]
```

`data/female/chest.json`:
```json
[
  { "label": "none", "description": "" }
]
```

`data/female/bust_size.json`:
```json
[
  { "label": "petite",  "description": "petite" },
  { "label": "small",   "description": "small" },
  { "label": "average", "description": "average" },
  { "label": "full",    "description": "full" },
  { "label": "large",   "description": "large" }
]
```

`data/male/bust_size.json`:
```json
[
  { "label": "none", "description": "" }
]
```

`data/female/bust_shape.json`:
```json
[
  { "label": "round",     "description": "round" },
  { "label": "teardrop",  "description": "teardrop" },
  { "label": "wide-set",  "description": "wide-set" },
  { "label": "close-set", "description": "close-set" },
  { "label": "natural",   "description": "natural" }
]
```

`data/male/bust_shape.json`:
```json
[
  { "label": "none", "description": "" }
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest test_random_person.TestBodyData -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add data/male/shoulders.json data/female/shoulders.json \
        data/male/chest.json data/female/chest.json \
        data/male/bust_size.json data/female/bust_size.json \
        data/male/bust_shape.json data/female/bust_shape.json \
        test_random_person.py
git commit -m "feat: add shoulders, chest, and bust data files"
```

---

## Task 2: Register body categories in the spec

**Files:**
- Modify: `nodes.py` (label lists block; `CATEGORY_SPECS`; `SEX_GATED`; `DEFAULT_OFF`)
- Test: `test_random_person.py`

**Interfaces:**
- Consumes: data files from Task 1.
- Produces: categories `shoulders`, `chest`, `bust_size`, `bust_shape` present in `core.CATEGORY_SPECS`, in `core.SEX_GATED`, and in `core.DEFAULT_OFF`. Each gets `_mode`/`_allow_list`/`_fixed` widgets in `INPUT_TYPES`, all defaulting to mode `"off"`.

- [ ] **Step 1: Write the failing test**

Add to `TestBodyData` in `test_random_person.py`:

```python
    def test_body_categories_default_off(self):
        req = core.RandomPersonNode.INPUT_TYPES()["required"]
        for key in self.BODY_KEYS:
            self.assertIn(f"{key}_mode", req, key)
            self.assertEqual(req[f"{key}_mode"][1]["default"], "off", key)

    def test_body_categories_are_sex_gated(self):
        for key in self.BODY_KEYS:
            self.assertIn(key, core.SEX_GATED, key)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestBodyData.test_body_categories_default_off -v`
Expected: FAIL with `KeyError: 'shoulders_mode'` (category not registered yet).

- [ ] **Step 3: Add the label lists**

In `nodes.py`, find the sex-gated label-list block that ends with `_MAKEUP_LABELS` (around line 91-92). Immediately after the `_MAKEUP_LABELS` assignment, add:

```python
_SHOULDERS_LABELS   = ["(none)"] + _union(_labels(load_sex("male", "shoulders.json")),
                                          _labels(load_sex("female", "shoulders.json")))
_CHEST_LABELS       = ["(none)"] + _union(_labels(load_sex("male", "chest.json")),
                                          _labels(load_sex("female", "chest.json")))
_BUST_SIZE_LABELS   = ["(none)"] + _union(_labels(load_sex("male", "bust_size.json")),
                                          _labels(load_sex("female", "bust_size.json")))
_BUST_SHAPE_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "bust_shape.json")),
                                          _labels(load_sex("female", "bust_shape.json")))
```

(`_union` already drops the `none` stub's duplicate cleanly; `(none)` remains the off-sentinel option.)

- [ ] **Step 4: Append to `CATEGORY_SPECS`**

In `nodes.py`, in the `CATEGORY_SPECS` list, find the `("body_type", ...)` line and insert these four lines immediately after it:

```python
    ("shoulders",   _SHOULDERS_LABELS,   "e.g. broad, narrow, sloping"),
    ("chest",       _CHEST_LABELS,       "e.g. broad, muscular, barrel"),
    ("bust_size",   _BUST_SIZE_LABELS,   "e.g. petite, average, full"),
    ("bust_shape",  _BUST_SHAPE_LABELS,  "e.g. round, teardrop, natural"),
```

- [ ] **Step 5: Add to `SEX_GATED` and `DEFAULT_OFF`**

Change the `SEX_GATED` set to include the four new keys:

```python
SEX_GATED = {"hair_color", "hair_style", "hair_length", "body_type", "face_shape",
             "nose_shape", "mouth_shape", "face_feature", "facial_hair", "makeup",
             "shoulders", "chest", "bust_size", "bust_shape"}
```

Change the `DEFAULT_OFF` set to include the four new keys:

```python
DEFAULT_OFF = {"skin_texture", "eyebrows", "face_feature", "facial_hair",
               "expression", "accessories", "makeup",
               "shoulders", "chest", "bust_size", "bust_shape"}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS (all existing tests plus the two new ones). Adding categories that the builder does not yet read is harmless; `generate_person` resolves them into its `p` dict but does not pass them to `build_description` until Task 3.

- [ ] **Step 7: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "feat: register shoulders, chest, bust categories (default off)"
```

---

## Task 3: Build body attributes into the description and output pins

**Files:**
- Modify: `nodes.py` (`build_description` signature + body block; `generate_person` call + return; `RETURN_NAMES`)
- Test: `test_random_person.py`

**Interfaces:**
- Consumes: categories registered in Task 2.
- Produces:
  - `build_description(...)` gains trailing keyword params `shoulders=None, chest=None, bust_size=None, bust_shape=None`.
  - `RETURN_NAMES` gains `"shoulders"`, `"chest"`, `"bust"` appended before `"seed"`.
  - The `bust` output pin and the bust phrase in the description combine size + shape: both -> `"a {size}, {shape} bust"`; size only -> `"a {size} bust"`; shape only -> `"a {shape} bust"`.

- [ ] **Step 1: Write the failing test**

Add to `test_random_person.py` (inside `TestBodyData`):

```python
    def test_chest_in_description_male(self):
        out = run(sex="male", chest=("fixed", "", "broad"))
        self.assertIn("a broad chest", out[0])

    def test_bust_combines_size_and_shape_female(self):
        out = run(sex="female",
                  bust_size=("fixed", "", "full"),
                  bust_shape=("fixed", "", "round"))
        self.assertIn("a full, round bust", out[0])

    def test_bust_size_only_female(self):
        out = run(sex="female", bust_size=("fixed", "", "petite"))
        self.assertIn("a petite bust", out[0])

    def test_shoulders_pin_present(self):
        names = core.RETURN_NAMES
        self.assertIn("shoulders", names)
        self.assertIn("chest", names)
        self.assertIn("bust", names)
        out = run(sex="male", shoulders=("fixed", "", "broad"))
        idx = names.index("shoulders")
        self.assertEqual(out[idx], "broad shoulders")

    def test_male_never_grows_bust(self):
        for seed in range(30):
            out = run(seed=seed, sex="male",
                      bust_size=("random", "", "(none)"),
                      bust_shape=("random", "", "(none)"))
            bust_idx = core.RETURN_NAMES.index("bust")
            self.assertEqual(out[bust_idx], "", seed)

    def test_female_never_grows_chest(self):
        for seed in range(30):
            out = run(seed=seed, sex="female", chest=("random", "", "(none)"))
            chest_idx = core.RETURN_NAMES.index("chest")
            self.assertEqual(out[chest_idx], "", seed)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestBodyData.test_bust_combines_size_and_shape_female -v`
Expected: FAIL (bust phrase not built; `out[0]` lacks "bust").

- [ ] **Step 3: Extend `build_description`**

In `nodes.py`, change the `build_description` signature. The current final line of the signature is:

```python
                      body, expression, accessories, makeup, extra_attributes="",
                      eye_shape=None, eyebrows=None):
```

Replace it with:

```python
                      body, expression, accessories, makeup, extra_attributes="",
                      eye_shape=None, eyebrows=None,
                      shoulders=None, chest=None, bust_size=None, bust_shape=None):
```

Then find the body block in `build_description`:

```python
    if body:
        build_str = d(body)
        parts.append(build_str if build_str.lower().endswith("build") else f"{build_str} build")

    add(expression)
```

Insert the body-detail handling between the `if body:` block and `add(expression)`:

```python
    if body:
        build_str = d(body)
        parts.append(build_str if build_str.lower().endswith("build") else f"{build_str} build")

    add(shoulders)
    add(chest)

    size_str  = d(bust_size).strip()  if bust_size  else ""
    shape_str = d(bust_shape).strip() if bust_shape else ""
    if size_str and shape_str:
        parts.append(f"a {size_str}, {shape_str} bust")
    elif size_str or shape_str:
        parts.append(f"a {size_str or shape_str} bust")

    add(expression)
```

- [ ] **Step 4: Pass the new categories from `generate_person`**

In `nodes.py`, find the `build_description(...)` call inside `generate_person`. Its current tail is:

```python
        p["body_type"], p["expression"], p["accessories"], p["makeup"],
        extra_attributes, eye_shape=p["eye_shape"], eyebrows=p["eyebrows"])
```

Replace with:

```python
        p["body_type"], p["expression"], p["accessories"], p["makeup"],
        extra_attributes, eye_shape=p["eye_shape"], eyebrows=p["eyebrows"],
        shoulders=p["shoulders"], chest=p["chest"],
        bust_size=p["bust_size"], bust_shape=p["bust_shape"])
```

- [ ] **Step 5: Append the new output pins**

In `nodes.py`, change `RETURN_NAMES`. Current:

```python
RETURN_NAMES = ("description", "sex", "age", "nationality", "complexion",
                "face", "hair", "facial_hair", "body_type",
                "expression", "accessories", "makeup", "seed")
```

Replace with:

```python
RETURN_NAMES = ("description", "sex", "age", "nationality", "complexion",
                "face", "hair", "facial_hair", "body_type",
                "expression", "accessories", "makeup",
                "shoulders", "chest", "bust", "seed")
```

Then find the `return (...)` at the end of `generate_person`:

```python
    return (description, resolved_sex, out_age, out_nat, out_comp,
            out_face, out_hair, dd("facial_hair"), dd("body_type"),
            dd("expression"), dd("accessories"), dd("makeup"), seed)
```

Just before that `return`, add the three new output values:

```python
    size_str  = dd("bust_size")
    shape_str = dd("bust_shape")
    if size_str and shape_str:
        out_bust = f"a {size_str}, {shape_str} bust"
    elif size_str or shape_str:
        out_bust = f"a {size_str or shape_str} bust"
    else:
        out_bust = ""

    return (description, resolved_sex, out_age, out_nat, out_comp,
            out_face, out_hair, dd("facial_hair"), dd("body_type"),
            dd("expression"), dd("accessories"), dd("makeup"),
            dd("shoulders"), dd("chest"), out_bust, seed)
```

- [ ] **Step 6: Run the full suite**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS (all). The V1 `RETURN_TYPES = ("STRING",) * (len(RETURN_NAMES) - 1) + ("INT",)` and the V3 output loop both derive from `RETURN_NAMES`, so the new pins are typed automatically.

- [ ] **Step 7: Smoke-check output**

Run:
```bash
python3 -c "
import nodes as c
def cat(**o):
    a={k:('random','','(none)') for k,_,_ in c.CATEGORY_SPECS}; a.update(o); return a
for sex in ('male','female'):
    out=c.generate_person(7,False,sex,cat(shoulders=('random','','(none)'),chest=('random','','(none)'),bust_size=('random','','(none)'),bust_shape=('random','','(none)')),'random',0,0,0,'')
    print(out[0])
"
```
Expected: male line includes shoulders + a chest phrase and NO bust; female line includes shoulders + a bust phrase and NO chest.

- [ ] **Step 8: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "feat: render shoulders, chest, bust in description and output pins"
```

---

# PHASE 2 - Segment nodes + menu category

## Task 4: Opener shows sex only with age or nationality

**Files:**
- Modify: `nodes.py` (`build_description` opener block)
- Test: `test_random_person.py`

**Interfaces:**
- Produces: the description opener includes the sex word only when an age or nationality part is present. A node with neither (a face-only fragment) starts directly with its first attribute, not a bare `"female"`.

- [ ] **Step 1: Write the failing test**

Add a method to `TestBuildDescription` in `test_random_person.py`:

```python
    def test_opener_omits_bare_sex(self):
        # sex present but no age and no nationality -> no leading "female".
        args = [""] + [None] * 17
        args[0] = "female"                 # sex positional slot
        args[4] = {"description": "oval"}  # face_shape slot -> "oval face"
        s = core.build_description(*args)
        self.assertTrue(s.startswith("oval face"), s)
        self.assertNotIn("female", s)

    def test_opener_keeps_sex_with_age(self):
        # age + sex -> "<n> year old female ..."
        s = core.build_description(
            "female", None, {"age": 30}, *( [None] * 15 ))
        self.assertIn("year old female", s)
```

Note: `build_description` positional order is `sex, nat, age, skin_texture, ...`; `args[2]` is age, `args[4]` is face_shape.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestBuildDescription.test_opener_omits_bare_sex -v`
Expected: FAIL (current opener appends bare `"female"`, so the string starts with `"female, oval face"`).

- [ ] **Step 3: Change the opener block**

In `nodes.py`, find the opener block in `build_description`:

```python
    # Opener: "34 year old Brazilian female"
    age_str = f"{age['age']} year old" if age else None
    nat_str = nat_text(nat) or None
    sex_str = sex if sex else None
    opener_parts = [p for p in [age_str, nat_str, sex_str] if p]
    if opener_parts:
        parts.append(" ".join(opener_parts))
```

Replace with:

```python
    # Opener: "34 year old Brazilian female". Sex is shown only alongside an age
    # or nationality, so a face-only fragment does not start with a bare "female".
    age_str = f"{age['age']} year old" if age else None
    nat_str = nat_text(nat) or None
    sex_str = sex if sex else None
    opener_parts = [p for p in [age_str, nat_str] if p]
    if opener_parts:
        if sex_str:
            opener_parts.append(sex_str)
        parts.append(" ".join(opener_parts))
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS. Existing `test_age_off` still passes because nationality defaults random, so the opener keeps `"<nat> female"`.

- [ ] **Step 5: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "feat: opener shows sex only with age or nationality"
```

---

## Task 5: Per-node output subsetting helper

**Files:**
- Modify: `nodes.py` (`_collect_category_args` gains a `keys` param; add `person_dict` helper)
- Test: `test_random_person.py`

**Interfaces:**
- Produces:
  - `_collect_category_args(kwargs, keys=None)` - when `keys` is given, only those category keys are read from `kwargs`; every other category is set to `("off", "", "(none)")`. Default `keys=None` reads all categories (unchanged behaviour).
  - `person_dict(result)` -> `dict` mapping each name in `RETURN_NAMES` to its value in a `generate_person` result tuple.

- [ ] **Step 1: Write the failing test**

Add a new class to `test_random_person.py`:

```python
class TestNodeHelpers(unittest.TestCase):

    def test_collect_args_restricts_keys(self):
        kwargs = {}
        for key, _, _ in core.CATEGORY_SPECS:
            kwargs[f"{key}_mode"] = "random"
            kwargs[f"{key}_allow_list"] = ""
            kwargs[f"{key}_fixed"] = "(none)"
        args = core._collect_category_args(kwargs, keys=["eyes"])
        self.assertEqual(args["eyes"][0], "random")
        self.assertEqual(args["hair_color"], ("off", "", "(none)"))

    def test_person_dict_maps_names(self):
        result = run(seed=5, sex="female")
        dmap = core.person_dict(result)
        self.assertEqual(set(dmap.keys()), set(core.RETURN_NAMES))
        self.assertEqual(dmap["seed"], result[-1])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestNodeHelpers -v`
Expected: FAIL (`person_dict` does not exist; `_collect_category_args` rejects the `keys` argument).

- [ ] **Step 3: Update `_collect_category_args` and add `person_dict`**

In `nodes.py`, replace the existing `_collect_category_args`:

```python
def _collect_category_args(kwargs):
    """Pull the (mode, allow_list, fixed) triple for each category from kwargs."""
    return {
        key: (kwargs[f"{key}_mode"], kwargs[f"{key}_allow_list"], kwargs[f"{key}_fixed"])
        for key, _, _ in CATEGORY_SPECS
    }
```

with:

```python
def _collect_category_args(kwargs, keys=None):
    """Pull the (mode, allow_list, fixed) triple for each category from kwargs.

    When `keys` is given, only those categories are read from kwargs; every
    other category is forced "off". This lets a segment node expose a subset of
    widgets while the shared core still receives a full category map.
    """
    active = set(keys) if keys is not None else None
    out = {}
    for key, _, _ in CATEGORY_SPECS:
        if (active is None or key in active) and f"{key}_mode" in kwargs:
            out[key] = (kwargs[f"{key}_mode"],
                        kwargs[f"{key}_allow_list"],
                        kwargs[f"{key}_fixed"])
        else:
            out[key] = ("off", "", "(none)")
    return out


def person_dict(result):
    """Map a generate_person result tuple to {return_name: value}."""
    return dict(zip(RETURN_NAMES, result))
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS. The existing `RandomPersonNode.generate` still calls `_collect_category_args(kwargs)` with no `keys`, so behaviour is unchanged.

- [ ] **Step 5: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "refactor: add keyed category collection and person_dict helper"
```

---

## Task 6: V1 node factory and segment nodes

**Files:**
- Modify: `nodes.py` (replace the hand-written `RandomPersonNode` class with a factory; add `NODE_SPECS`; rebuild `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS`)
- Test: `test_random_person.py`

**Interfaces:**
- Consumes: `_collect_category_args(kwargs, keys)`, `person_dict`, `generate_person`, `CATEGORY_SPECS`, `RETURN_NAMES`, `MODES`, `SEX_MODES`, `AGE_MODES`, tooltip constants.
- Produces:
  - `NODE_SPECS` - list of `(node_id, display_name, keys, include_age, output_names)`.
  - `make_v1_node(spec)` -> a ComfyUI V1 node class with `CATEGORY = "Random Person"`, exposing only its keys' widgets (plus `sex`, plus age widgets when `include_age`), and returning only `output_names`.
  - `NODE_CLASS_MAPPINGS` containing all six node classes keyed by node_id; full node still keyed `"RandomPersonNode"`.

- [ ] **Step 1: Write the failing test**

Add to `test_random_person.py`:

```python
class TestSegmentNodes(unittest.TestCase):

    def _node(self, node_id):
        return core.NODE_CLASS_MAPPINGS[node_id]

    def test_all_nodes_registered(self):
        for node_id in ("RandomPersonNode", "RandomPersonIdentity",
                        "RandomPersonFace", "RandomPersonHair",
                        "RandomPersonBody", "RandomPersonStyle"):
            self.assertIn(node_id, core.NODE_CLASS_MAPPINGS, node_id)

    def test_all_nodes_in_random_person_category(self):
        for cls in core.NODE_CLASS_MAPPINGS.values():
            self.assertEqual(cls.CATEGORY, "Random Person")

    def test_identity_exposes_only_its_widgets(self):
        req = self._node("RandomPersonIdentity").INPUT_TYPES()["required"]
        self.assertIn("nationality_mode", req)
        self.assertIn("age_mode", req)
        self.assertNotIn("eyes_mode", req)
        self.assertNotIn("hair_color_mode", req)

    def test_face_node_has_no_age(self):
        req = self._node("RandomPersonFace").INPUT_TYPES()["required"]
        self.assertIn("eyes_mode", req)
        self.assertNotIn("age_mode", req)

    def test_face_fragment_excludes_other_groups(self):
        cls = self._node("RandomPersonFace")
        kwargs = {}
        req = cls.INPUT_TYPES()["required"]
        for name, (typ, opts) in req.items():
            if name.endswith("_mode"):
                kwargs[name] = "random"
            elif name.endswith("_allow_list"):
                kwargs[name] = ""
            elif name.endswith("_fixed"):
                kwargs[name] = "(none)"
        out = cls().generate(seed=3, randomize=False, sex="female", **kwargs)
        names = cls.RETURN_NAMES
        desc = out[names.index("description")]
        self.assertNotIn("build", desc)        # body excluded
        self.assertNotIn("hair", desc)         # hair excluded
        self.assertNotIn("year old", desc)     # age excluded

    def test_body_node_outputs_bust_pin(self):
        cls = self._node("RandomPersonBody")
        self.assertIn("bust", cls.RETURN_NAMES)
        self.assertIn("shoulders", cls.RETURN_NAMES)
        self.assertNotIn("hair", cls.RETURN_NAMES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest test_random_person.TestSegmentNodes -v`
Expected: FAIL (`RandomPersonIdentity` not in `NODE_CLASS_MAPPINGS`).

- [ ] **Step 3: Replace the V1 class with a factory**

In `nodes.py`, delete the entire hand-written `class RandomPersonNode:` block (from `class RandomPersonNode:` down to and including its `IS_CHANGED` method) and the two lines:

```python
NODE_CLASS_MAPPINGS        = {"RandomPersonNode": RandomPersonNode}
NODE_DISPLAY_NAME_MAPPINGS = {"RandomPersonNode": "Random Person Description"}
```

Replace all of that with:

```python
_ALL_KEYS = [k for k, _, _ in CATEGORY_SPECS]

# (node_id, display_name, category keys, include_age, output pin names)
NODE_SPECS = [
    ("RandomPersonNode", "Random Person Description", _ALL_KEYS, True, RETURN_NAMES),
    ("RandomPersonIdentity", "Random Person: Identity",
     ["nationality", "complexion", "skin_texture"], True,
     ("description", "sex", "age", "nationality", "complexion", "seed")),
    ("RandomPersonFace", "Random Person: Face & Expression",
     ["face_shape", "eyes", "eye_shape", "eyebrows", "nose_shape",
      "mouth_shape", "face_feature", "expression"], False,
     ("description", "sex", "face", "expression", "seed")),
    ("RandomPersonHair", "Random Person: Hair",
     ["hair_color", "hair_style", "hair_length", "facial_hair"], False,
     ("description", "sex", "hair", "facial_hair", "seed")),
    ("RandomPersonBody", "Random Person: Body",
     ["body_type", "shoulders", "chest", "bust_size", "bust_shape"], False,
     ("description", "sex", "body_type", "shoulders", "chest", "bust", "seed")),
    ("RandomPersonStyle", "Random Person: Style",
     ["accessories", "makeup"], False,
     ("description", "sex", "accessories", "makeup", "seed")),
]

_NODE_DESCRIPTION = "Generate a randomised, structured physical person description for image prompts."


def make_v1_node(node_id, display_name, keys, include_age, output_names):
    """Build a ComfyUI V1 node class exposing only `keys` and returning `output_names`."""
    key_set = set(keys)

    class _RandomPersonV1:
        CATEGORY    = "Random Person"
        FUNCTION    = "generate"
        OUTPUT_NODE = False
        DESCRIPTION = _NODE_DESCRIPTION
        RETURN_NAMES = output_names
        RETURN_TYPES = tuple("INT" if n == "seed" else "STRING" for n in output_names)

        @classmethod
        def INPUT_TYPES(cls):
            required = {
                "seed":      ("INT",     {"default": 0, "min": 0, "max": 0xFFFFFFFF, "tooltip": _SEED_TIP}),
                "randomize": ("BOOLEAN", {"default": True, "tooltip": _RAND_TIP}),
                "sex":       (SEX_MODES, {"default": "random", "tooltip": _SEX_TIP}),
            }
            for key, fixed_labels, placeholder in CATEGORY_SPECS:
                if key not in key_set:
                    continue
                required[f"{key}_mode"]       = (MODES, {"default": _mode_default(key), "tooltip": _MODE_TIP})
                required[f"{key}_allow_list"] = ("STRING", {"default": "", "multiline": False,
                                                            "placeholder": placeholder, "tooltip": _ALLOW_TIP})
                required[f"{key}_fixed"]      = (fixed_labels, {"default": "(none)", "tooltip": _FIXED_TIP})
            if include_age:
                required["age_mode"]  = (AGE_MODES, {"default": "random"})
                required["age_min"]   = ("INT", {"default": 0, "min": 0, "max": 90, "tooltip": _AGEMIN_TIP})
                required["age_max"]   = ("INT", {"default": 0, "min": 0, "max": 90, "tooltip": _AGEMAX_TIP})
                required["age_fixed"] = ("INT", {"default": 0, "min": 0, "max": 90, "tooltip": _AGEFIX_TIP})
            required["extra_attributes"] = ("STRING", {"default": "", "multiline": True,
                                                       "placeholder": "e.g. wearing glasses, tattoo on left arm",
                                                       "tooltip": _EXTRA_TIP})
            return {"required": required}

        def generate(self, seed, randomize, sex, **kwargs):
            age_mode  = kwargs.get("age_mode", "off") if include_age else "off"
            age_min   = kwargs.get("age_min", 0)
            age_max   = kwargs.get("age_max", 0)
            age_fixed = kwargs.get("age_fixed", 0)
            extra     = kwargs.get("extra_attributes", "")
            cat_args  = _collect_category_args(kwargs, keys)
            result    = generate_person(seed, randomize, sex, cat_args,
                                        age_mode, age_min, age_max, age_fixed, extra)
            dmap = person_dict(result)
            return tuple(dmap[name] for name in output_names)

        @classmethod
        def IS_CHANGED(cls, randomize, seed, **kwargs):
            return float("nan") if randomize else seed

    _RandomPersonV1.__name__ = node_id
    _RandomPersonV1.__qualname__ = node_id
    return _RandomPersonV1


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
for _spec in NODE_SPECS:
    _cls = make_v1_node(*_spec)
    NODE_CLASS_MAPPINGS[_spec[0]] = _cls
    NODE_DISPLAY_NAME_MAPPINGS[_spec[0]] = _spec[1]

# Backwards-compatible alias: tests and external imports reference this name.
RandomPersonNode = NODE_CLASS_MAPPINGS["RandomPersonNode"]
```

Note: keep the existing module-level `RETURN_NAMES`, `RETURN_TYPES` references intact above this block - `RETURN_NAMES` is defined earlier (Task 3) and is reused as the full node's `output_names`. The standalone module-level `RETURN_TYPES` constant that previously sat on the class is no longer needed; if a module-level `RETURN_TYPES = ...` line exists outside the class, leave it only if referenced elsewhere (it is not - the factory computes types per node).

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS (all, including `TestSegmentNodes`). The `RandomPersonNode = NODE_CLASS_MAPPINGS[...]` alias keeps every existing test that references `core.RandomPersonNode` working.

- [ ] **Step 5: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "feat: add V1 node factory and segment nodes under Random Person"
```

---

## Task 7: V3 schema factory for all nodes

**Files:**
- Modify: `nodes.py` (replace the single `RandomPersonNodeV3` with a factory driven by `NODE_SPECS`)
- Test: `test_random_person.py`

**Interfaces:**
- Consumes: `NODE_SPECS`, `generate_person`, `person_dict`, `_collect_category_args`.
- Produces: one V3 `io.ComfyNode` subclass per spec, all returned by `comfy_entrypoint`. No behaviour change when `comfy_api` is absent (import-guarded).

- [ ] **Step 1: Write the failing test**

Add to `TestSegmentNodes` in `test_random_person.py`:

```python
    def test_node_specs_cover_all_ids(self):
        ids = [s[0] for s in core.NODE_SPECS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids[0], "RandomPersonNode")
        self.assertEqual(len(ids), 6)

    def test_every_output_name_is_a_known_pin(self):
        for _id, _name, _keys, _age, outs in core.NODE_SPECS:
            for name in outs:
                self.assertIn(name, core.RETURN_NAMES, f"{_id}:{name}")
```

- [ ] **Step 2: Run test to verify it fails (or passes structurally)**

Run: `python3 -m unittest test_random_person.TestSegmentNodes.test_every_output_name_is_a_known_pin -v`
Expected: PASS already if Task 6 specs are correct (this test guards the V3 factory's assumption that every output name maps to a `RETURN_NAMES` pin). If it FAILS, fix the offending `output_names` entry in `NODE_SPECS` before continuing.

- [ ] **Step 3: Replace the V3 block with a factory**

In `nodes.py`, replace the entire `try: from comfy_api.v0_0_2 import ...` block (the whole V3 section down to the `except ImportError: pass`) with:

```python
try:
    from comfy_api.v0_0_2 import io, ComfyExtension

    def _make_v3_node(node_id, display_name, keys, include_age, output_names):
        key_set = set(keys)

        class _RandomPersonV3(io.ComfyNode):
            @classmethod
            def define_schema(cls) -> io.Schema:
                inputs = [
                    io.Int.Input("seed", default=0, min=0, max=0xFFFFFFFF, tooltip=_SEED_TIP),
                    io.Boolean.Input("randomize", default=True, tooltip=_RAND_TIP),
                    io.Combo.Input("sex", options=SEX_MODES, default="random", tooltip=_SEX_TIP),
                ]
                for key, fixed_labels, placeholder in CATEGORY_SPECS:
                    if key not in key_set:
                        continue
                    inputs += [
                        io.Combo.Input(f"{key}_mode", options=MODES, default=_mode_default(key), tooltip=_MODE_TIP),
                        io.String.Input(f"{key}_allow_list", default="", multiline=False,
                                        placeholder=placeholder, tooltip=_ALLOW_TIP),
                        io.Combo.Input(f"{key}_fixed", options=fixed_labels, default="(none)", tooltip=_FIXED_TIP),
                    ]
                if include_age:
                    inputs += [
                        io.Combo.Input("age_mode", options=AGE_MODES, default="random"),
                        io.Int.Input("age_min", default=0, min=0, max=90, tooltip=_AGEMIN_TIP),
                        io.Int.Input("age_max", default=0, min=0, max=90, tooltip=_AGEMAX_TIP),
                        io.Int.Input("age_fixed", default=0, min=0, max=90, tooltip=_AGEFIX_TIP),
                    ]
                inputs.append(
                    io.String.Input("extra_attributes", default="", multiline=True,
                                    placeholder="e.g. wearing glasses, tattoo on left arm", tooltip=_EXTRA_TIP))
                outputs = []
                for name in output_names:
                    if name == "seed":
                        outputs.append(io.Int.Output(id="seed", display_name="seed", tooltip=_SEED_TIP))
                    else:
                        outputs.append(io.String.Output(id=name, display_name=name))
                return io.Schema(
                    node_id=node_id,
                    display_name=display_name,
                    category="Random Person",
                    description=_NODE_DESCRIPTION,
                    inputs=inputs,
                    outputs=outputs,
                )

            @classmethod
            def fingerprint_inputs(cls, randomize, seed, **kwargs):
                return float("nan") if randomize else seed

            @classmethod
            def execute(cls, seed, randomize, sex, **kwargs) -> io.NodeOutput:
                age_mode  = kwargs.get("age_mode", "off") if include_age else "off"
                age_min   = kwargs.get("age_min", 0)
                age_max   = kwargs.get("age_max", 0)
                age_fixed = kwargs.get("age_fixed", 0)
                extra     = kwargs.get("extra_attributes", "")
                cat_args  = _collect_category_args(kwargs, keys)
                result    = generate_person(seed, randomize, sex, cat_args,
                                            age_mode, age_min, age_max, age_fixed, extra)
                dmap = person_dict(result)
                return io.NodeOutput(*(dmap[name] for name in output_names))

        _RandomPersonV3.__name__ = node_id + "V3"
        _RandomPersonV3.__qualname__ = _RandomPersonV3.__name__
        return _RandomPersonV3

    _V3_NODES = [_make_v3_node(*spec) for spec in NODE_SPECS]

    class RandomPersonExtension(ComfyExtension):
        async def get_node_list(self):
            return _V3_NODES

    async def comfy_entrypoint() -> "RandomPersonExtension":
        return RandomPersonExtension()

except ImportError:
    # Older ComfyUI without comfy_api: V1 mappings above are the only path.
    pass
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS. `comfy_api` is absent in the test environment, so the V3 block is skipped, but the import-guard and `NODE_SPECS`-driven structure are exercised by the V1 tests and the two new structural tests.

- [ ] **Step 5: Commit**

```bash
git add nodes.py test_random_person.py
git commit -m "feat: build V3 schema nodes from NODE_SPECS factory"
```

---

## Task 8: Extend JS sex-gating to all gated nodes

**Files:**
- Modify: `js/random_person_node.js`
- Test: manual (no JS test harness in repo)

**Interfaces:**
- Consumes: the V1/V3 node ids that contain sex-gated widgets.
- Produces: the browser extension applies the male/female dropdown filter to every gated node id, and the male/female label maps include the new body categories.

- [ ] **Step 1: Read the current file**

Read `js/random_person_node.js` in full to confirm the structure before editing. Confirmed semantics (do not re-derive): `MALE_ONLY[w]` holds the male-only labels, which `applyFilters` excludes when `sex === "female"`; `FEMALE_ONLY[w]` holds female-only labels, excluded when `sex === "male"`. `SEX_GATED_WIDGETS = Object.keys(MALE_ONLY)`, so every gated widget MUST have a key in `MALE_ONLY` (an empty array is fine) or it is never filtered. `(none)` is always kept. Two hooks gate on the node id: `beforeRegisterNodeDef` (`nodeData.name !== "RandomPersonNode"`) and `nodeCreated` (`node.comfyClass !== "RandomPersonNode"`).

- [ ] **Step 2: Add the new body category labels to both maps**

In the `MALE_ONLY` object, add these four entries (these labels are hidden when the node's sex is female):

```javascript
    shoulders_fixed:   ["muscular"],
    chest_fixed:       ["average","barrel","broad","flat","muscular"],
    bust_size_fixed:   [],
    bust_shape_fixed:  [],
```

In the `FEMALE_ONLY` object, add these four entries (hidden when the node's sex is male):

```javascript
    shoulders_fixed:   ["soft"],
    chest_fixed:       [],
    bust_size_fixed:   ["average","full","large","petite","small"],
    bust_shape_fixed:  ["close-set","natural","round","teardrop","wide-set"],
```

Both maps must include all four keys (even the empty ones) because `SEX_GATED_WIDGETS` is derived from `Object.keys(MALE_ONLY)` and the lookup `FEMALE_ONLY[widgetName] || []` tolerates a missing key but the `MALE_ONLY` key is what registers the widget for filtering. The shared shoulder labels (narrow, average, broad, sloping, square) appear in neither map, so they stay visible for both sexes.

- [ ] **Step 3: Gate every node id that has sex-gated widgets**

Near the top of the file (after the `FEMALE_ONLY` / `SEX_GATED_WIDGETS` declarations), add a set of the node ids that carry gated widgets:

```javascript
const GATED_NODE_IDS = new Set([
    "RandomPersonNode",
    "RandomPersonFace",
    "RandomPersonHair",
    "RandomPersonBody",
    "RandomPersonStyle",
]);
```

`RandomPersonIdentity` is intentionally excluded (it has no sex-gated dropdowns beyond `sex`).

In the `beforeRegisterNodeDef` hook, replace:

```javascript
        if (nodeData.name !== "RandomPersonNode") return;
```

with:

```javascript
        if (!GATED_NODE_IDS.has(nodeData.name)) return;
```

In the `nodeCreated` hook, replace:

```javascript
        if (node.comfyClass !== "RandomPersonNode") return;
```

with:

```javascript
        if (!GATED_NODE_IDS.has(node.comfyClass)) return;
```

The existing `applyFilters` loop already skips widgets a node does not have (`node.widgets?.find(...)` returns undefined and `continue`s), so the same `SEX_GATED_WIDGETS` loop is safe on every node regardless of which gated widgets it actually exposes.

- [ ] **Step 4: Manual verification**

Document for the executor: load ComfyUI, add each of the five gated nodes, toggle `sex` male/female, and confirm sex-specific values appear/disappear in `shoulders_fixed`, `chest_fixed`, `bust_size_fixed`, `bust_shape_fixed`, and that the existing hair/body/makeup/facial_hair filtering still works. Confirm the Identity node has no broken filtering (it has no gated dropdowns).

- [ ] **Step 5: Commit**

```bash
git add js/random_person_node.js
git commit -m "feat: extend sex-gating to segment nodes and body categories"
```

---

## Task 9: README and version bump

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Test: `python3 -m unittest test_random_person -v` (final full run)

**Interfaces:**
- Produces: documentation of the new nodes and body attributes; version bumped to `1.1.0` (new nodes = minor version).

- [ ] **Step 1: Update the Purpose trait list**

In `README.md`, in the Purpose paragraph, extend the trait list to include the body details. Find:

```
build, expression, accessories, and makeup.
```

Replace with:

```
build, shoulders, chest or bust, expression, accessories, and makeup.
```

- [ ] **Step 2: Document the node set**

In `README.md`, under the install/usage area where the single node is described ("The node appears in the **Add Node** menu under **utils > Random Person Description**."), replace the `utils` reference and add the node list:

```markdown
The nodes appear in the **Add Node** menu under **Random Person**:

- **Random Person Description** - the full node, every attribute on one node.
- **Random Person: Identity** - sex, age, nationality, complexion, skin texture.
- **Random Person: Face & Expression** - face shape, eyes, eyebrows, nose, mouth, distinctive features, expression.
- **Random Person: Hair** - hair colour, style, length, facial hair.
- **Random Person: Body** - build, shoulders, chest, bust size and shape.
- **Random Person: Style** - accessories and makeup.

The segment nodes are independent generators: each has its own seed and sex and emits its group's fragment. Concatenate the `description` outputs with any string node to assemble a full prompt.
```

Also update the earlier line `## Installation` section reference `under **utils > Random Person Description**` if present elsewhere - search for `utils` in `README.md` and replace each menu reference with `Random Person`.

- [ ] **Step 3: Add the new output pins to the pin table**

In `README.md`, in the Output Pins table, add rows after the `body_type` row:

```markdown
| `shoulders` | Shoulder descriptor (empty when off) | `broad shoulders` |
| `chest` | Chest descriptor, male (empty when off / female) | `a muscular chest` |
| `bust` | Combined bust size and shape, female (empty when off / male) | `a full, round bust` |
```

- [ ] **Step 4: Bump the version and refresh registry description**

In `pyproject.toml`, change:

```toml
version = "1.0.8"
```

to:

```toml
version = "1.1.0"
```

Also update the stale `[project].description` (it still says "Located under Add Node > utils. Node name: Random Person Description."). Replace that trailing sentence so it reads:

```toml
description = "Generate randomised, structured physical person descriptions for image-generation prompts. Sex-aware traits, per-category random/allow_list/fixed/off modes, age ranges, body details, and individual output pins. Full node plus Identity, Face, Hair, Body, and Style segment nodes under the Random Person menu category."
```

- [ ] **Step 5: Final full test run**

Run: `python3 -m unittest test_random_person -v`
Expected: PASS (all).

- [ ] **Step 6: Validate all JSON parses**

Run:
```bash
python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('data/**/*.json',recursive=True)]; print('all json ok')"
```
Expected: `all json ok`

- [ ] **Step 7: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs: document segment nodes and body attributes; bump 1.1.0"
```

---

## Self-Review notes (for the executor)

- The data layer (Task 1) is independent and testable alone.
- Phase 1 (Tasks 1-3) ships a working full node with body attributes before any node-structure change.
- Phase 2 (Tasks 4-9) is purely additive node-layer work; the full node's behaviour is preserved by the `RandomPersonNode` alias and unchanged `output_names = RETURN_NAMES`.
- The only manual-verification task is the JS gating (Task 8); everything else has automated `unittest` coverage.
