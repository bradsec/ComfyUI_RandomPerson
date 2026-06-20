import { app } from "../../scripts/app.js";

// ── Per-category labels that are sex-specific ─────────────────────────────────
// Mirrors the diff between data/male/ and data/female/ JSON files.

const MALE_ONLY = {
    hair_style_fixed:   ["braids short","buzz cut","crew cut","curly medium","locs long","locs short","messy medium","pompadour","quiff","side part","skin fade","slicked back","taper fade","undercut"],
    hair_length_fixed:  [],
    body_type_fixed:    ["barrel chested","broad shouldered","compact","dad bod"],
    face_shape_fixed:   ["rectangular"],
    nose_shape_fixed:   ["aquiline nose","curved nose bridge","roman nose","rounded nose tip"],
    mouth_shape_fixed:  [],
    hair_color_fixed:   [],
    face_feature_fixed: ["birthmark on jaw","heavy brow","mole on cheek","strong jaw","weathered skin"],
    facial_hair_fixed:  ["circle beard","full beard","goatee","heavy stubble","light stubble","moustache","mutton chops","short beard","soul patch","van dyke"],
    makeup_fixed:       [],
};

const FEMALE_ONLY = {
    hair_style_fixed:   ["braid over shoulder","braids","chin length bob","curtain bangs","half up","high ponytail","jaw length bob","layered","locs","loose curls","loose waves","messy","pixie","pulled back loose","space buns","tight curls","twist out"],
    hair_length_fixed:  ["chin length","very long"],
    body_type_fixed:    ["curvy","full figured","hourglass","pear","petite"],
    face_shape_fixed:   ["heart"],
    nose_shape_fixed:   ["button nose","upturned nose"],
    mouth_shape_fixed:  ["bow shaped lips","heart shaped lips","rosebud lips"],
    hair_color_fixed:   ["platinum blonde","strawberry blonde"],
    face_feature_fixed: ["arched brows","beauty mark","birthmark","wide eyes"],
    facial_hair_fixed:  [],
    makeup_fixed:       ["bold lipstick","bold makeup","glam makeup","minimal makeup","natural makeup","red lipstick","smokey eye","soft makeup","winged eyeliner"],
};

const SEX_GATED_WIDGETS = Object.keys(MALE_ONLY);

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
        if (nodeData.name !== "RandomPersonNode") return;

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

    // Re-apply after workflow load — widget values are restored before nodeCreated fires
    async nodeCreated(node) {
        if (node.comfyClass !== "RandomPersonNode") return;
        const sexWidget = node.widgets?.find(w => w.name === "sex");
        if (sexWidget) {
            setTimeout(() => applyFilters(node, sexWidget.value), 50);
        }
    },
});
