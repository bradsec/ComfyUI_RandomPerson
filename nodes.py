"""
Random Person Description Node for ComfyUI
==========================================

Produces a clean, consistently structured person description, e.g.:

  34 year old Brazilian female, heart face, warm beige complexion,
  hazel eyes, button nose, bow-shaped lips, auburn long hair worn
  loose waves, hourglass build

Each category also has its own individual output pin.

Per-category MODE:
  "random"     - pick any entry from the (sex-appropriate) full list
  "allow_list" - comma-separated label subset (blank = all)
  "fixed"      - use the exact label selected in the dropdown
  "off"        - omit this category entirely

Age uses numeric age_min / age_max (0 = no bound) or age_fixed.

Dual-API: the shared core (generate_person) is wrapped by a V1 class
(NODE_CLASS_MAPPINGS, authoritative on the 0.25.0 if/elif loader) and an
import-guarded V3 class (comfy_entrypoint) for builds whose loader prefers
the comfy_api schema. node_id "RandomPersonNode" is fixed in both so the
js/ sex-aware widget extension keeps matching.
"""

import json
import os
import random
from functools import lru_cache

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
MODES     = ["random", "allow_list", "fixed", "off"]
SEX_MODES = ["random", "male", "female"]
AGE_MODES = ["random", "fixed", "off"]


# -- Data helpers --------------------------------------------------------------

@lru_cache(maxsize=None)
def load(subdir, filename):
    # Parsed once per process. Callers must treat the result as read-only.
    # Matches the documented "edit data, restart ComfyUI" workflow.
    with open(os.path.join(DATA_DIR, subdir, filename), encoding="utf-8") as f:
        return json.load(f)

def load_shared(fn):    return load("shared", fn)
def load_sex(sex, fn):  return load(sex, fn)


def _labels(data):
    """Extract label list from a JSON data list."""
    return [item["label"] if isinstance(item, dict) else item for item in data]

def _union(*lists):
    """Merge multiple label lists, deduplicated and sorted."""
    seen, out = set(), []
    for lst in lists:
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
    return sorted(out)


# Build dropdown option lists once at import time.
_NAT_LABELS   = ["(none)"] + _labels(load_shared("nationality.json"))
_COMP_LABELS  = ["(none)"] + _labels(load_shared("complexion.json"))
_EYES_LABELS  = ["(none)"] + _labels(load_shared("eyes.json"))

# Sex-gated lists: union of male + female so the dropdown is valid for any sex.
_HAIR_COLOR_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "hair_color.json")),
                                          _labels(load_sex("female", "hair_color.json")))
_HAIR_STYLE_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "hair_style.json")),
                                          _labels(load_sex("female", "hair_style.json")))
_HAIR_LENGTH_LABELS = ["(none)"] + _union(_labels(load_sex("male", "hair_length.json")),
                                          _labels(load_sex("female", "hair_length.json")))
_BODY_TYPE_LABELS   = ["(none)"] + _union(_labels(load_sex("male", "body_type.json")),
                                          _labels(load_sex("female", "body_type.json")))
_FACE_SHAPE_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "face_shape.json")),
                                          _labels(load_sex("female", "face_shape.json")))
_NOSE_SHAPE_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "nose_shape.json")),
                                          _labels(load_sex("female", "nose_shape.json")))
_MOUTH_SHAPE_LABELS = ["(none)"] + _union(_labels(load_sex("male", "mouth_shape.json")),
                                          _labels(load_sex("female", "mouth_shape.json")))
_FACE_FEATURE_LABELS = ["(none)"] + _union(_labels(load_sex("male", "face_feature.json")),
                                           _labels(load_sex("female", "face_feature.json")))
_FACIAL_HAIR_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "facial_hair.json")),
                                           _labels(load_sex("female", "facial_hair.json")))
_MAKEUP_LABELS       = ["(none)"] + _union(_labels(load_sex("male", "makeup.json")),
                                           _labels(load_sex("female", "makeup.json")))
_CLOTHING_LABELS    = ["(none)"] + _union(_labels(load_sex("male", "clothing.json")),
                                          _labels(load_sex("female", "clothing.json")))
_SHOULDERS_LABELS   = ["(none)"] + _union(_labels(load_sex("male", "shoulders.json")),
                                          _labels(load_sex("female", "shoulders.json")))
_CHEST_LABELS       = ["(none)"] + _union(_labels(load_sex("male", "chest.json")),
                                          _labels(load_sex("female", "chest.json")))
_BUST_SIZE_LABELS   = ["(none)"] + _union(_labels(load_sex("male", "bust_size.json")),
                                          _labels(load_sex("female", "bust_size.json")))
_BUST_SHAPE_LABELS  = ["(none)"] + _union(_labels(load_sex("male", "bust_shape.json")),
                                          _labels(load_sex("female", "bust_shape.json")))

# Shared (sex-agnostic) lists.
_SKIN_TEXTURE_LABELS = ["(none)"] + _labels(load_shared("skin_texture.json"))
_EYE_SHAPE_LABELS    = ["(none)"] + _labels(load_shared("eye_shape.json"))
_EYEBROWS_LABELS     = ["(none)"] + _labels(load_shared("eyebrows.json"))
_ACCESSORIES_LABELS  = ["(none)"] + _labels(load_shared("accessories.json"))
_EXPRESSION_LABELS   = ["(none)"] + _labels(load_shared("expression.json"))

# Per-category spec drives BOTH API wrappers so they cannot drift.
# (key, fixed_label_list, allow_list_placeholder)
CATEGORY_SPECS = [
    ("nationality",  _NAT_LABELS,          "e.g. American, Japanese, Italian"),
    ("complexion",   _COMP_LABELS,         "e.g. fair, olive, deep brown"),
    ("skin_texture", _SKIN_TEXTURE_LABELS, "e.g. smooth, freckled, wrinkled"),
    ("eyes",         _EYES_LABELS,         "e.g. deep brown, ice blue, hazel"),
    ("eye_shape",    _EYE_SHAPE_LABELS,    "e.g. almond, hooded, monolid, round"),
    ("eyebrows",     _EYEBROWS_LABELS,     "e.g. thick, arched, straight, bushy"),
    ("face_shape",   _FACE_SHAPE_LABELS,   "e.g. oval, square, heart"),
    ("nose_shape",   _NOSE_SHAPE_LABELS,   "e.g. straight nose, broad nose, snub nose"),
    ("mouth_shape",  _MOUTH_SHAPE_LABELS,  "e.g. full lips, thin lips, wide mouth"),
    ("face_feature", _FACE_FEATURE_LABELS, "e.g. high cheekbones, dimples, freckles"),
    ("hair_color",   _HAIR_COLOR_LABELS,   "e.g. jet black, auburn, platinum blonde"),
    ("hair_style",   _HAIR_STYLE_LABELS,   "e.g. bun, braids, pixie cut"),
    ("hair_length",  _HAIR_LENGTH_LABELS,  "e.g. short, medium, long"),
    ("facial_hair",  _FACIAL_HAIR_LABELS,  "e.g. full beard, stubble, goatee"),
    ("body_type",    _BODY_TYPE_LABELS,    "e.g. athletic, slim, curvy, stocky"),
    ("shoulders",    _SHOULDERS_LABELS,    "e.g. broad, narrow, sloping"),
    ("chest",        _CHEST_LABELS,        "e.g. broad, muscular, barrel"),
    ("bust_size",    _BUST_SIZE_LABELS,    "e.g. petite, average, full"),
    ("bust_shape",   _BUST_SHAPE_LABELS,   "e.g. round, teardrop, natural"),
    ("expression",   _EXPRESSION_LABELS,   "e.g. soft smile, serious, confident"),
    ("accessories",  _ACCESSORIES_LABELS,  "e.g. glasses, hoop earrings, nose ring"),
    ("makeup",       _MAKEUP_LABELS,       "e.g. natural makeup, bold lipstick, smokey eye"),
    ("clothing",     _CLOTHING_LABELS,     "e.g. t-shirt, leather jacket, blazer"),
]

# Categories whose data lives under data/<sex>/ rather than data/shared/.
SEX_GATED = {"hair_color", "hair_style", "hair_length", "body_type", "face_shape",
             "nose_shape", "mouth_shape", "face_feature", "facial_hair", "makeup",
             "shoulders", "chest", "bust_size", "bust_shape", "clothing"}

# Optional "flair" categories default to mode "off" so the base description stays
# clean and realistic; the user opts them in per category. Core identity
# categories (nationality, complexion, eyes, face/nose/mouth shape, hair, body)
# default to "random".
DEFAULT_OFF = {"skin_texture", "eyebrows", "face_feature", "facial_hair",
               "expression", "accessories", "makeup",
               "shoulders", "chest", "bust_size", "bust_shape", "clothing"}


def _mode_default(key):
    return "off" if key in DEFAULT_OFF else "random"

# Tooltips (shared by both APIs).
_SEED_TIP   = "Seed for reproducibility. With randomize off, the same seed reproduces the same person."
_RAND_TIP   = "On: pick a new random person every run, ignoring the seed widget. Off: use the seed."
_SEX_TIP    = "random, male, or female. male/female filter the sex-specific dropdowns in the UI."
_MODE_TIP   = "How this attribute is chosen: random (any), allow_list (subset you list), fixed (the dropdown value), off (omit it)."
_ALLOW_TIP  = "Comma-separated values used when mode=allow_list. Unknown values are added as literal descriptors."
_FIXED_TIP  = "Exact value used when mode=fixed. (none) falls back to random."
_AGEMIN_TIP = "Minimum age. 0 = no lower bound (defaults to 21). Cannot go below 21."
_AGEMAX_TIP = "Maximum age. 0 = no upper bound (defaults to 90). Minimum is always 21."
_AGEFIX_TIP = "Exact age when mode=fixed. 0 = ignored. Values below 21 are clamped to 21."
_EXTRA_TIP  = "Free text appended to the description as-is, comma-separated. Clothing, accessories, expression, etc."

RETURN_NAMES = ("description", "sex", "age", "nationality", "complexion",
                "face", "hair", "facial_hair", "body_type",
                "expression", "accessories", "makeup",
                "shoulders", "chest", "bust", "clothing", "seed")


# -- Selection logic -----------------------------------------------------------

def item_matches(item, token):
    """
    Fuzzy multi-field match (case-insensitive).
    Priority: exact (2) > token-in-field or field-in-token (1) > no match (0).
    """
    if isinstance(item, dict):
        fields = [item.get("label", ""), item.get("descriptor", ""),
                  item.get("from", ""), item.get("description", "")]
    else:
        fields = [str(item)]

    fields = [f.lower() for f in fields if f]
    for field in fields:
        if token == field:   return 2
    for field in fields:
        if token in field:   return 1   # "america" in "american"
        if field in token:   return 1   # "french" in "french canadian"
    return 0


def _best_match(full_list, token):
    """Return the best-matching item for token, or None."""
    scored = [(item_matches(item, token), item) for item in full_list]
    scored = [(s, item) for s, item in scored if s > 0]
    if not scored:
        return None
    best_score = max(s for s, _ in scored)
    candidates = [item for s, item in scored if s == best_score]
    # Among equal-score candidates, prefer shortest label (most specific match).
    if isinstance(candidates[0], dict):
        candidates.sort(key=lambda x: len(x.get("label", "")))
    return candidates[0]


def resolve(mode, full_list, allow_str="", fixed_val=""):
    """Pick one item from full_list according to mode. Returns None if off."""
    if mode == "off":
        return None

    if mode == "fixed" and fixed_val.strip() and fixed_val.strip() != "(none)":
        token = fixed_val.strip().lower()
        match = _best_match(full_list, token)
        if match is not None:
            return match
        print(f"[RandomPersonNode] WARNING: fixed '{fixed_val}' not found - using random.")

    if mode == "allow_list" and allow_str.strip():
        tokens = [s.strip() for s in allow_str.split(",") if s.strip()]

        matched_items, custom_strings = [], []
        for t in tokens:
            tl = t.lower()
            hits = [item for item in full_list if item_matches(item, tl) > 0]
            if hits:
                matched_items.extend(hits)
            else:
                custom_strings.append(t)   # not in JSON - treat as literal custom value

        seen, deduped = set(), []
        for item in matched_items:
            key = id(item)
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        pool = deduped + [{"label": s, "description": s} for s in custom_strings]
        if pool:
            return random.choice(pool)
        print(f"[RandomPersonNode] WARNING: allow_list '{allow_str}' matched nothing - using random.")

    return random.choice(full_list)


def resolve_age(mode, age_min, age_max, age_fixed_val, all_ages):
    if mode == "off":
        return None
    if mode == "fixed" and age_fixed_val > 0:
        age_fixed_val = max(age_fixed_val, 21)
        exact = [a for a in all_ages if a["age"] == age_fixed_val]
        if exact:
            return exact[0]
        print(f"[RandomPersonNode] WARNING: age {age_fixed_val} not in data - using random.")
    lo = max(age_min, 21) if age_min > 0 else 21
    hi = min(age_max, 90) if age_max > 0 else 90
    if lo > hi:
        lo, hi = hi, lo
    pool = [a for a in all_ages if lo <= a["age"] <= hi]
    if not pool:
        print(f"[RandomPersonNode] WARNING: no ages in {lo}-{hi} - using full list.")
        pool = all_ages
    return random.choice(pool)


def d(item, key="description"):
    """Extract a string from a dict item, or the item itself."""
    return item.get(key, "") if isinstance(item, dict) else str(item)


def nat_text(item):
    """Nationality display text. Falls back when a custom allow_list value has
    no 'descriptor' key (custom items carry only label/description)."""
    if not item:
        return ""
    if isinstance(item, dict):
        return item.get("descriptor") or item.get("description") or item.get("label") or ""
    return str(item)


def _bust_phrase(size_str, shape_str):
    """Combine bust size and shape into one descriptor, or '' if neither."""
    lead = size_str or shape_str
    if not lead:
        return ""
    article = "an" if lead[:1].lower() in "aeiou" else "a"
    if size_str and shape_str:
        return f"{article} {size_str}, {shape_str} bust"
    return f"{article} {lead} bust"


# -- Description builder -------------------------------------------------------

def build_description(sex, nat, age, skin_texture,
                      face_shape, complexion, eyes, nose_shape, mouth_shape, face_feature,
                      hair_color, hair_style, hair_length, facial_hair,
                      body, expression, accessories, makeup, extra_attributes="",
                      eye_shape=None, eyebrows=None,
                      shoulders=None, chest=None, bust_size=None, bust_shape=None,
                      clothing=None):
    """Produce a single comma-separated descriptor string."""
    parts = []

    def add(item, fmt="{}"):
        """Append a category's description if it resolves to non-empty text."""
        s = d(item).strip() if item else ""
        if s:
            parts.append(fmt.format(s))

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

    add(face_shape, "{} face")
    add(complexion, "{} complexion")
    add(skin_texture)
    shape_str = d(eye_shape).strip() if eye_shape else ""
    if eyes or shape_str:
        color_str = d(eyes).strip() if eyes else ""
        base = (color_str if "eyes" in color_str.lower() else f"{color_str} eyes") if color_str else "eyes"
        parts.append(f"{shape_str} {base}" if shape_str else base)
    add(eyebrows)
    add(nose_shape)
    add(mouth_shape)
    add(face_feature)

    # Hair: "auburn long hair worn loose waves"
    hair_color_str  = d(hair_color)  if hair_color  else None
    hair_length_str = d(hair_length) if hair_length else None
    hair_style_str  = d(hair_style)  if hair_style  else None
    if hair_color_str or hair_length_str or hair_style_str:
        pre_hair = " ".join(p for p in [hair_color_str, hair_length_str] if p)
        if pre_hair and hair_style_str:
            parts.append(f"{pre_hair} hair worn {hair_style_str}")
        elif pre_hair:
            parts.append(f"{pre_hair} hair")
        elif hair_style_str:
            parts.append(f"hair worn {hair_style_str}")

    add(facial_hair)

    if body:
        build_str = d(body)
        parts.append(build_str if build_str.lower().endswith("build") else f"{build_str} build")

    add(shoulders)
    add(chest)

    bust = _bust_phrase(d(bust_size).strip() if bust_size else "",
                        d(bust_shape).strip() if bust_shape else "")
    if bust:
        parts.append(bust)

    add(expression)
    add(accessories)
    add(makeup)
    add(clothing)

    if extra_attributes and extra_attributes.strip():
        for attr in extra_attributes.split(","):
            attr = attr.strip().strip(".")
            if attr:
                parts.append(attr)

    return ", ".join(parts)


# -- Shared core (called by both API wrappers) ---------------------------------

def generate_person(seed, randomize, sex, category_args,
                    age_mode, age_min, age_max, age_fixed, extra_attributes):
    """
    category_args: dict keyed by category prefix with (mode, allow_list, fixed)
    tuples for each entry in CATEGORY_SPECS. Returns the output tuple matching
    RETURN_NAMES.
    """
    if randomize:
        seed = random.randint(0, 0xFFFFFFFF)
    random.seed(seed)

    resolved_sex = sex if sex in ("male", "female") else random.choice(["male", "female"])

    def load_list(key):
        sub = resolved_sex if key in SEX_GATED else "shared"
        return load(sub, f"{key}.json")

    p = {}
    for key, _, _ in CATEGORY_SPECS:
        mode, allow, fixed = category_args[key]
        p[key] = resolve(mode, load_list(key), allow, fixed)
    age = resolve_age(age_mode, age_min, age_max, age_fixed, load_shared("age.json"))

    description = build_description(
        resolved_sex, p["nationality"], age, p["skin_texture"],
        p["face_shape"], p["complexion"], p["eyes"], p["nose_shape"], p["mouth_shape"], p["face_feature"],
        p["hair_color"], p["hair_style"], p["hair_length"], p["facial_hair"],
        p["body_type"], p["expression"], p["accessories"], p["makeup"],
        extra_attributes, eye_shape=p["eye_shape"], eyebrows=p["eyebrows"],
        shoulders=p["shoulders"], chest=p["chest"],
        bust_size=p["bust_size"], bust_shape=p["bust_shape"],
        clothing=p["clothing"])

    def dd(key, sub_key="description"):
        item = p[key]
        return d(item, sub_key) if item else ""

    out_age  = str(age["age"])           if age else ""
    out_nat  = nat_text(p["nationality"])
    out_comp = ", ".join(filter(None, [dd("complexion"), dd("skin_texture")]))
    out_hair = " ".join(filter(None, [dd("hair_color"), dd("hair_length"), dd("hair_style")]))

    def _eyes_str():
        shape = dd("eye_shape")
        color = dd("eyes")
        if not (shape or color):
            return ""
        base = (color if "eyes" in color.lower() else f"{color} eyes") if color else "eyes"
        return f"{shape} {base}" if shape else base

    out_face = ", ".join(filter(None, [
        f"{dd('face_shape')} face" if dd("face_shape") else "",
        _eyes_str(),
        dd("eyebrows"),
        dd("nose_shape"),
        dd("mouth_shape"),
        dd("face_feature"),
    ]))

    out_bust = _bust_phrase(dd("bust_size"), dd("bust_shape"))

    return (description, resolved_sex, out_age, out_nat, out_comp,
            out_face, out_hair, dd("facial_hair"), dd("body_type"),
            dd("expression"), dd("accessories"), dd("makeup"),
            dd("shoulders"), dd("chest"), out_bust, dd("clothing"), seed)


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


# -- V1 node factory -----------------------------------------------------------

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
     ["clothing", "accessories", "makeup"], False,
     ("description", "sex", "clothing", "accessories", "makeup", "seed")),
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


# -- V3 node factory (import-guarded comfy_api schema) -------------------------

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
