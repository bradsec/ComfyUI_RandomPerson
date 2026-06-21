"""Unit tests for the Random Person Description shared core.

Pure logic, no ComfyUI required: reads the bundled data/ JSON only.
Run: python -m unittest test_random_person -v
"""

import unittest

import nodes as core


def cat_args(**overrides):
    """All categories on 'random' by default; override with key=(mode, allow, fixed)."""
    args = {key: ("random", "", "(none)") for key, _, _ in core.CATEGORY_SPECS}
    args.update(overrides)
    return args


def run(seed=123, randomize=False, sex="female", age_mode="random",
        age_min=0, age_max=0, age_fixed=0, extra="", **cat):
    return core.generate_person(seed, randomize, sex, cat_args(**cat),
                                age_mode, age_min, age_max, age_fixed, extra)


class TestSelection(unittest.TestCase):

    def test_seed_reproducible(self):
        a = run(seed=42)
        b = run(seed=42)
        self.assertEqual(a, b)

    def test_different_seed_differs(self):
        # Not guaranteed in theory, but with this data the full string should differ.
        self.assertNotEqual(run(seed=1)[0], run(seed=999)[0])

    def test_randomize_returns_used_seed(self):
        out = run(randomize=True)
        used = out[-1]
        self.assertIsInstance(used, int)
        self.assertNotEqual(used, 0)
        # Re-running with that seed and randomize off reproduces the person.
        self.assertEqual(run(seed=used)[0], out[0])

    def test_off_mode_omits_body(self):
        out = run(body_type=("off", "", "(none)"))
        self.assertEqual(out[8], "")            # body_type pin empty
        self.assertNotIn("build", out[0].lower())

    def test_fixed_nationality(self):
        out = run(nationality=("fixed", "", "Japanese"))
        self.assertIn("japanese", out[3].lower())

    def test_allow_list_custom_value(self):
        # A token with no field overlap with any JSON entry is used as a literal.
        out = run(hair_color=("allow_list", "ultraviolet", "(none)"))
        self.assertIn("ultraviolet", out[6])  # hair pin carries the custom value

    def test_custom_nationality_not_dropped(self):
        # Regression F-NAT: a custom nationality (no "descriptor" key) must still
        # reach the description opener and the nationality pin.
        out = run(nationality=("allow_list", "Atlantean", "(none)"))
        self.assertEqual(out[3], "Atlantean")        # nationality pin
        self.assertIn("Atlantean", out[0])           # description opener

    def test_sex_resolved_from_random(self):
        self.assertIn(run(sex="random")[1], ("male", "female"))

    def test_flair_categories_default_off(self):
        # Optional categories must ship with mode default "off"; identity
        # categories must default "random".
        req = core.RandomPersonNode.INPUT_TYPES()["required"]
        for key in core.DEFAULT_OFF:
            self.assertEqual(req[f"{key}_mode"][1]["default"], "off", key)
        for key in ("nationality", "complexion", "eyes", "hair_color", "body_type"):
            self.assertEqual(req[f"{key}_mode"][1]["default"], "random", key)

    def test_female_never_grows_facial_hair(self):
        for seed in range(40):
            self.assertEqual(run(seed=seed, sex="female")[7], "")  # facial_hair pin empty

    def test_male_makeup_empty(self):
        for seed in range(40):
            self.assertEqual(run(seed=seed, sex="male")[11], "")   # makeup pin empty

    def test_skin_texture_in_complexion_pin(self):
        out = run(skin_texture=("fixed", "", "dewy"),
                  complexion=("fixed", "", "tan"))
        self.assertIn("tan", out[4])
        self.assertIn("dewy", out[4])

    def test_eye_shape_merges_into_eyes(self):
        # eye_shape sits in front of the eye colour, single "eyes" suffix, and
        # surfaces in the face pin.
        out = run(eye_shape=("fixed", "", "almond"),
                  eyes=("fixed", "", "green"))
        self.assertIn("almond", out[5])          # face pin
        self.assertIn("eyes", out[5])
        self.assertNotIn("eyes eyes", out[0])

    def test_eye_shape_alone_gets_suffix(self):
        out = run(eye_shape=("fixed", "", "hooded"), eyes=("off", "", "(none)"))
        self.assertIn("hooded eyes", out[5])

    def test_eyebrows_pin_and_off(self):
        on = run(eyebrows=("fixed", "", "thick"))
        self.assertIn("thick", on[5])            # face pin carries eyebrows
        off = run(eyebrows=("off", "", "(none)"))
        self.assertNotIn("eyebrow", off[5].lower())

    def test_eyebrows_default_off(self):
        req = core.RandomPersonNode.INPUT_TYPES()["required"]
        self.assertEqual(req["eyebrows_mode"][1]["default"], "off")

    def test_expression_pin_and_off(self):
        on = run(expression=("fixed", "", "serious"))
        self.assertIn("serious", on[9])
        off = run(expression=("off", "", "(none)"))
        self.assertEqual(off[9], "")


class TestAge(unittest.TestCase):

    def test_age_off(self):
        out = run(age_mode="off")
        self.assertEqual(out[2], "")
        self.assertNotIn("year old", out[0])

    def test_age_fixed_clamped_to_min(self):
        out = run(age_mode="fixed", age_fixed=15)
        self.assertGreaterEqual(int(out[2]), 21)

    def test_age_range_respected(self):
        ages = core.load_shared("age.json")
        for seed in range(30):
            picked = core.resolve_age("random", 30, 40, 0, ages)
            self.assertTrue(30 <= picked["age"] <= 40)


class TestBuildDescription(unittest.TestCase):

    def test_empty_when_all_none(self):
        self.assertEqual(core.build_description(*( [""] + [None] * 17 )), "")

    def test_extra_attributes_appended(self):
        out = run(extra="wearing glasses, gold earrings")
        self.assertIn("wearing glasses", out[0])
        self.assertIn("gold earrings", out[0])

    def test_eyes_no_double_suffix(self):
        # An eyes description already containing "eyes" must not get " eyes" appended.
        args = [""] + [None] * 17
        args[6] = {"description": "muted natural green eyes"}   # eyes positional slot
        s = core.build_description(*args)
        self.assertNotIn("eyes eyes", s)

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

    def test_body_categories_default_off(self):
        req = core.RandomPersonNode.INPUT_TYPES()["required"]
        for key in self.BODY_KEYS:
            self.assertIn(f"{key}_mode", req, key)
            self.assertEqual(req[f"{key}_mode"][1]["default"], "off", key)

    def test_body_categories_are_sex_gated(self):
        for key in self.BODY_KEYS:
            self.assertIn(key, core.SEX_GATED, key)

    def test_chest_in_description_male(self):
        out = run(sex="male", chest=("fixed", "", "broad"))
        self.assertIn("a broad chest", out[0])

    def test_bust_combines_size_and_shape_female(self):
        out = run(sex="female",
                  bust_size=("fixed", "", "full"),
                  bust_shape=("fixed", "", "round"))
        self.assertIn("a full, round bust", out[0])

    def test_bust_size_only_female(self):
        out = run(sex="female", bust_size=("fixed", "", "petite"),
                  bust_shape=("off", "", "(none)"))
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

    def test_bust_average_uses_an(self):
        out = run(sex="female", bust_size=("fixed", "", "average"),
                  bust_shape=("off", "", "(none)"))
        self.assertIn("an average bust", out[0])

    def test_bust_full_uses_a(self):
        out = run(sex="female", bust_size=("fixed", "", "full"),
                  bust_shape=("off", "", "(none)"))
        self.assertIn("a full bust", out[0])


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

    def test_node_specs_cover_all_ids(self):
        ids = [s[0] for s in core.NODE_SPECS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids[0], "RandomPersonNode")
        self.assertEqual(len(ids), 6)

    def test_every_output_name_is_a_known_pin(self):
        for _id, _name, _keys, _age, outs in core.NODE_SPECS:
            for name in outs:
                self.assertIn(name, core.RETURN_NAMES, f"{_id}:{name}")


class TestClothing(unittest.TestCase):

    def test_clothing_defaults_off(self):
        req = core.RandomPersonNode.INPUT_TYPES()["required"]
        self.assertEqual(req["clothing_mode"][1]["default"], "off")

    def test_clothing_is_sex_gated(self):
        self.assertIn("clothing", core.SEX_GATED)

    def test_clothing_pin_carries_value(self):
        out = run(sex="female", clothing=("fixed", "", "leather jacket"))
        idx = core.RETURN_NAMES.index("clothing")
        self.assertEqual(out[idx], "a leather jacket")
        self.assertIn("a leather jacket", out[0])

    def test_male_never_gets_female_only_garment(self):
        female_only_descs = {
            "a blouse", "a camisole", "a cardigan", "a cocktail dress",
            "a jumpsuit", "a knit sweater", "a maxi dress", "an off-shoulder top",
            "a peplum top", "a sundress", "a wool coat", "a wrap dress",
        }
        for seed in range(30):
            out = run(seed=seed, sex="male", clothing=("random", "", "(none)"))
            idx = core.RETURN_NAMES.index("clothing")
            val = out[idx]
            if val:
                self.assertNotIn(val, female_only_descs, f"seed={seed}: male got female-only '{val}'")

    def test_female_never_gets_male_only_garment(self):
        male_only_descs = {
            "a flannel shirt", "a polo shirt", "a henley shirt", "a work shirt",
            "a bomber jacket", "a crew-neck sweater", "a parka", "a three-piece suit",
            "a tracksuit", "a wool overcoat",
        }
        for seed in range(30):
            out = run(seed=seed, sex="female", clothing=("random", "", "(none)"))
            idx = core.RETURN_NAMES.index("clothing")
            val = out[idx]
            if val:
                self.assertNotIn(val, male_only_descs, f"seed={seed}: female got male-only '{val}'")

    def test_style_node_exposes_clothing(self):
        req = core.NODE_CLASS_MAPPINGS["RandomPersonStyle"].INPUT_TYPES()["required"]
        self.assertIn("clothing_mode", req)
        self.assertIn("clothing", core.NODE_CLASS_MAPPINGS["RandomPersonStyle"].RETURN_NAMES)


if __name__ == "__main__":
    unittest.main()
