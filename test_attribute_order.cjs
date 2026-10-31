const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

let extension;
const source = fs.readFileSync('js/random_person_node.js', 'utf8')
    .replace('import { app } from "../../scripts/app.js";', '');
vm.runInNewContext(source, {
    app: { registerExtension(value) { extension = value; } },
    setTimeout(callback) { callback(); },
});

async function check(nodeId, names) {
    class Node {
        constructor() {
            this.comfyClass = nodeId;
            this.properties = {};
            this.widgets = names.map(name => ({ name, value: name, options: { values: [] } }));
        }
        configure(info) { this.restored = info; }
    }
    await extension.beforeRegisterNodeDef(Node, { name: nodeId });
    const node = new Node();
    const oldNames = ["seed", "control_after_generate", "randomize", "sex",
        "eyes_mode", "eyes_allow_list", "eyes_fixed", "eye_shape_mode",
        "eye_shape_allow_list", "eye_shape_fixed", "eyebrows_mode",
        "eyebrows_allow_list", "eyebrows_fixed", "face_shape_mode",
        "face_shape_allow_list", "face_shape_fixed", "nose_shape_mode",
        "nose_shape_allow_list", "nose_shape_fixed", "mouth_shape_mode",
        "mouth_shape_allow_list", "mouth_shape_fixed", "face_feature_mode",
        "face_feature_allow_list", "face_feature_fixed", "expression_mode",
        "expression_allow_list", "expression_fixed", "extra_attributes"];
    const values = oldNames.map(name => name);
    node.configure({ widgets_values: values, properties: {} });
    assert.deepEqual(Array.from(node.restored.widgets_values), names);
    assert.equal(node.restored.properties.rp_widget_layout, 2);

    node.configure({ widgets_values: values, widgets_values_named: { face_shape_mode: 'fixed' }, properties: {} });
    assert.equal(node.restored.widgets_values[names.indexOf('face_shape_mode')], 'fixed');

    node.configure({ widgets_values: names, properties: { rp_widget_layout: 2 } });
    assert.deepEqual(node.restored.widgets_values, names);

    node.widgets.find(w => w.name === 'face_shape_mode').value = 'fixed';
    node.widgets.find(w => w.name === 'eyes_mode').value = 'allow_list';
    node.configure({ widgets_values: names, properties: { rp_widget_layout: 2 } });
    assert.equal(node.widgets.find(w => w.name === 'face_shape_fixed').hidden, false);
    assert.equal(node.widgets.find(w => w.name === 'face_shape_allow_list').hidden, true);
    assert.equal(node.widgets.find(w => w.name === 'eyes_allow_list').hidden, false);
    assert.equal(node.widgets.find(w => w.name === 'eyes_fixed').hidden, true);
    assert.equal(node.widgets.find(w => w.name === 'face_shape_fixed').serialize, undefined);
}

check('RandomPersonFace', ["seed", "control_after_generate", "randomize", "sex",
    "face_shape_mode", "face_shape_allow_list", "face_shape_fixed",
    "eye_shape_mode", "eye_shape_allow_list", "eye_shape_fixed",
    "eyes_mode", "eyes_allow_list", "eyes_fixed",
    "eyebrows_mode", "eyebrows_allow_list", "eyebrows_fixed",
    "nose_shape_mode", "nose_shape_allow_list", "nose_shape_fixed",
    "mouth_shape_mode", "mouth_shape_allow_list", "mouth_shape_fixed",
    "face_feature_mode", "face_feature_allow_list", "face_feature_fixed",
    "expression_mode", "expression_allow_list", "expression_fixed", "extra_attributes"])
    .catch(error => { console.error(error); process.exitCode = 1; });
