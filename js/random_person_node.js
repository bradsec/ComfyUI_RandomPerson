import { app } from "../../scripts/app.js";

// Per-category differences are checked against bundled JSON by the unit tests.

const MALE_ONLY = {
    face_shape_fixed: ["rectangular"],
    nose_shape_fixed: ["curved nose bridge", "snub nose"],
    mouth_shape_fixed: [],
    face_feature_fixed: ["birthmark on jaw", "heavy brow", "mole on cheek", "strong jaw"],
    hair_color_fixed: ["red"],
    hair_style_fixed: ["bowl cut", "braids short", "buzz cut", "caesar cut", "crew cut", "curly", "curly medium", "french crop", "locs long", "locs short", "messy medium", "pompadour", "quiff", "side part", "skin fade", "slicked back", "taper fade", "undercut", "wavy"],
    hair_length_fixed: [],
    facial_hair_fixed: ["circle beard", "full beard", "goatee", "heavy stubble", "light stubble", "moustache", "mutton chops", "short beard", "soul patch", "van dyke"],
    body_type_fixed: ["compact", "dad bod", "medium build", "slight"],
    shoulders_fixed: ["muscular"],
    chest_fixed: ["average", "barrel", "broad", "flat", "muscular"],
    bust_size_fixed: ["none"],
    bust_shape_fixed: ["none"],
    makeup_fixed: ["eyeliner", "subtle concealer"],
    clothing_fixed: ["bomber jacket", "crew-neck sweater", "flannel shirt", "henley shirt", "parka", "polo shirt", "three-piece suit", "tracksuit", "wool overcoat", "work shirt"],
    footwear_fixed: [],
};

const FEMALE_ONLY = {
    face_shape_fixed: ["heart"],
    nose_shape_fixed: ["button nose"],
    mouth_shape_fixed: ["bow shaped lips", "heart shaped lips", "rosebud lips"],
    face_feature_fixed: ["beauty mark", "birthmark"],
    hair_color_fixed: ["platinum blonde", "strawberry blonde"],
    hair_style_fixed: ["blunt cut", "braid over shoulder", "braids", "chignon", "chin length bob", "cropped short", "curtain bangs", "fishtail braid", "french braid", "half up", "high ponytail", "jaw length bob", "layered", "locs", "loose curls", "loose waves", "messy", "pixie", "pulled back loose", "shag", "space buns", "tight curls", "twist out", "updo", "wispy", "wolf cut"],
    hair_length_fixed: ["chin length", "very long"],
    facial_hair_fixed: ["chin hair", "light facial hair"],
    body_type_fixed: ["curvy", "full figured", "hourglass", "pear", "petite"],
    shoulders_fixed: ["soft"],
    chest_fixed: ["none"],
    bust_size_fixed: ["average", "extra large", "full", "large", "petite", "small"],
    bust_shape_fixed: ["close-set", "round", "teardrop", "wide-set"],
    makeup_fixed: ["bold lipstick", "bold makeup", "minimal makeup", "natural makeup", "smokey eye", "winged eyeliner"],
    clothing_fixed: ["blouse", "camisole", "cardigan", "cocktail dress", "jumpsuit", "knit sweater", "maxi dress", "off-shoulder top", "peplum top", "sundress", "wool coat", "wrap dress"],
    footwear_fixed: ["ballet flats", "high heels", "kitten heels", "knee-high boots", "mary janes", "platform heels", "stilettos", "strappy heels", "wedges"],
};

const SEX_GATED_WIDGETS = Object.keys(MALE_ONLY);

const GATED_NODE_IDS = new Set([
    "RandomPersonNode",
    "RandomPersonFace",
    "RandomPersonHair",
    "RandomPersonBody",
    "RandomPersonStyle",
]);

// ── Apply sex filter to all gated widgets on a node ───────────────────────────

function applyFilters(node, sex) {
    for (const widgetName of SEX_GATED_WIDGETS) {
        const w = node.widgets?.find(w => w.name === widgetName);
        if (!w?.options?.values) continue;

        // Store the full unfiltered list on first encounter
        if (!w._allValues) w._allValues = [...w.options.values];

        if (sex === "random") {
            // Restore all options
            w.options.values = [...w._allValues];
        } else {
            const excluded = new Set(
                sex === "male" ? (FEMALE_ONLY[widgetName] || [])
                               : (MALE_ONLY[widgetName]   || [])
            );
            w.options.values = w._allValues.filter(v => v === "(none)" || !excluded.has(v));

            // If the selected value was just hidden, reset to (none)
            if (excluded.has(w.value)) w.value = "(none)";
        }
    }

    node.setDirtyCanvas?.(true, true);
}

// ── Extension ─────────────────────────────────────────────────────────────────

app.registerExtension({
    name: "RandomPersonNode.SexAwareWidgets",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!GATED_NODE_IDS.has(nodeData.name)) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);

            // Default width
            if (this.size) this.size[0] = 420;

            // Watch the sex widget
            const sexWidget = this.widgets?.find(w => w.name === "sex");
            if (sexWidget) {
                // Apply immediately for the current value
                applyFilters(this, sexWidget.value);

                // Intercept changes
                const node = this;
                const origCallback = sexWidget.callback;
                sexWidget.callback = function (value) {
                    origCallback?.call(this, value);
                    applyFilters(node, value);
                };
            }

            return result;
        };

        // Nodes 2.0 width fallbacks
        if (typeof nodeType.prototype.getDefaultSize === "function") {
            nodeType.prototype.getDefaultSize = function () {
                return [420, this.size?.[1] ?? 600];
            };
        } else {
            nodeType.prototype.defaultWidth = 420;
        }
    },

    // Re-apply after workflow load: widget values are restored before nodeCreated fires
    async nodeCreated(node) {
        if (!GATED_NODE_IDS.has(node.comfyClass)) return;
        const sexWidget = node.widgets?.find(w => w.name === "sex");
        if (sexWidget) {
            setTimeout(() => applyFilters(node, sexWidget.value), 50);
        }
    },
});
