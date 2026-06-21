# Random Person Description - Custom node for ComfyUI

Generates a randomised, structured physical description of a person for use in image generation prompts. Every attribute is drawn from curated JSON data files tuned for realistic, unambiguous output with SDXL and Flux models.

![node](samples/node.png)

## Purpose

Diffusion models drift toward a narrow set of "default" faces when a prompt leaves appearance vague, so batches of people start to look the same. This node feeds the model a specific, well-formed human description on every run: nationality, age, complexion and skin texture, eye colour, face shape and distinctive features, hair, facial hair, build, expression, accessories, and makeup. Pinning down those traits, and varying them per seed, pushes the model away from its defaults and toward more unique, individual people across a batch. Lock the traits you care about and let the rest randomise to explore variety without losing control.

The node will be located under **Add Node > utils**. Node name: **Random Person Description**.

**Example output (male):**
```
74 year old Pakistani male, oval face, light complexion, wrinkled skin, pale light grey eyes,
aquiline nose, wide-set lips, a scar through one eyebrow, ash grey shaved hair worn taper fade, a van dyke beard, athletic build, glasses
```

**Example output (female):**
```
43 year old Russian female, angular face, light medium complexion, smooth skin, natural grey eyes, button nose, wide-set lips, a faint scar through one eyebrow, red very short hair worn twist out, muscular build, reading glasses, bold lipstick
```

---

### Samples

![grid_001](samples/grid_001.jpg)
![grid_002](samples/grid_002.jpg)
![grid_003](samples/grid_003.jpg)
![grid_004](samples/grid_004.jpg)
![grid_005](samples/grid_005.jpg)
![grid_006](samples/grid_006.jpg)
![grid_007](samples/grid_007.jpg)


## Installation

### ComfyUI Manager (recommended)

In ComfyUI, open **Manager > Custom Nodes Manager**, search for **ComfyUI_RandomPerson**, click **Install**, then restart ComfyUI.

### Manual install

1. Copy the `ComfyUI_RandomPerson` folder into your `ComfyUI/custom_nodes/` directory
2. Restart ComfyUI

The node appears in the **Add Node** menu under **utils > Random Person Description**.

---

## Output Pins

| Pin | Contents | Example |
|---|---|---|
| `description` | Full comma-separated description string | `43 year old Russian female, angular face, ...` |
| `sex` | Resolved sex | `female` |
| `age` | Age as a plain number | `43` |
| `nationality` | Nationality descriptor | `Russian` |
| `complexion` | Skin tone and texture | `light medium, smooth skin` |
| `face` | Combined face attributes (shape, eyes, nose, mouth, distinctive feature) | `angular face, natural grey eyes, button nose, wide-set lips, a faint scar through one eyebrow` |
| `hair` | Combined hair description | `red very short hair worn twist out` |
| `facial_hair` | Beard / moustache style (empty for clean shaven) | `a van dyke beard` |
| `body_type` | Build | `muscular` |
| `expression` | Facial expression (empty for neutral) | `a soft smile` |
| `accessories` | Eyewear / jewellery (empty for none) | `reading glasses` |
| `makeup` | Makeup style (empty for none / male) | `bold lipstick` |
| `seed` | The seed used (useful for reproducibility) | `481046155` |

Wire `description` directly into a text prompt node, or use individual pins to route specific attributes to other parts of your workflow.

---

## Controls

### Seed & Randomise

| Control | Purpose |
|---|---|
| `seed` | Fixed seed, use the same value to reproduce an identical result |
| `randomize` | When **on**, ignores the seed and picks a new random person every run |

### Sex

Dropdown: `random` / `male` / `female`

When set to `male` or `female`, the dropdown options for hair style, hair colour, face shape, nose, mouth, body type, facial feature, facial hair, and makeup automatically filter to show only sex-appropriate options. Facial hair and makeup are effectively sex-specific: females never grow facial hair and males have no makeup options.

### Per-Category Controls

Every attribute category (nationality, complexion, skin texture, eyes, face shape, nose shape, mouth shape, facial feature, hair colour, hair style, hair length, facial hair, body type, expression, accessories, makeup) has three controls:

| Control | What it does |
|---|---|
| **mode** | How the value is chosen, see Mode Options below |
| **allow_list** | Comma-separated list of values to draw from (used when mode = `allow_list`) |
| **fixed** | A specific value to always use (used when mode = `fixed`) |

#### Mode Options

| Mode | Behaviour |
|---|---|
| `random` | Pick any value from the full list for the resolved sex |
| `allow_list` | Pick randomly from only the values you specify in the allow_list field |
| `fixed` | Always use the value selected in the fixed dropdown |
| `off` | **Skip this attribute entirely**, it will not appear in the description |

> **Tip: turning off attributes:** Set any category's mode to `off` to remove it from the output completely. For example, if you don't want a body type in the description, set `body_type_mode` to `off`.

#### Default modes

Core identity categories (nationality, complexion, eyes, face shape, nose shape, mouth shape, hair colour/style/length, body type, plus age and sex) default to `random`. The optional "flair" categories default to `off` so the base person stays clean and realistic, and you opt them in per category:

`skin_texture`, `face_feature`, `facial_hair`, `expression`, `accessories`, `makeup`

The example outputs above have several of these enabled to show the full range.

#### Allow List: Custom Values

The allow_list field accepts comma-separated values. These can be:

- **Labels from the JSON data**, e.g. `auburn, golden blonde, platinum blonde`, the node will pick randomly from the matched entries
- **Custom values not in any list**, e.g. `fire engine red, pastel pink`, unknown tokens are treated as literal descriptors and added to the pool

This means you can mix standard and custom values freely:
```
auburn, copper red, fire engine red
```

### Age

| Control | Purpose |
|---|---|
| `age_mode` | `random`, `fixed`, or `off` |
| `age_min` | Minimum age (0 = no lower bound). Cannot go below 21. |
| `age_max` | Maximum age (0 = no upper bound, defaults to 90) |
| `age_fixed` | Exact age to use when mode = `fixed`. Values below 21 are clamped to 21. |

### Extra Attributes

A free-text area at the bottom of the node. Enter any custom descriptors separated by commas, they are appended to the end of the description exactly as written.

```
wearing glasses, tattoo on left arm, silver hoop earrings
```

This is the right place for clothing, accessories, expressions, or any detail not covered by the built-in categories.

---

## Available Values

### Nationality (40)
American, Algerian, Argentinian, Australian, Bangladeshi, Brazilian, British, Canadian, Chinese, Colombian, Dutch, Egyptian, Ethiopian, Filipino, French, German, Ghanaian, Greek, Indian, Iranian, Italian, Jamaican, Japanese, Kenyan, Korean, Mexican, Moroccan, Nigerian, Pakistani, Peruvian, Polish, Russian, South African, Spanish, Sudanese, Swedish, Thai, Turkish, Ugandan, Vietnamese

### Complexion (15)
porcelain, fair, light, light medium, warm beige, warm olive, olive, medium, warm medium, tan, golden brown, medium brown, deep brown, deep, ebony

### Skin Texture (10)
smooth, clear, dewy, glowing, freckled, fine lines, wrinkled, sun-spotted, acne scars, ruddy

> Skin texture is separate from complexion (tone). It appends after the complexion in both the `description` and the `complexion` pin, e.g. `tan, smooth skin`.

### Eye Colour (23)
brown, dark brown, light brown, near black, hazel, hazel green, hazel brown, amber, blue, light blue, dark blue, ice blue, grey blue, steel blue, green, light green, dark green, olive green, blue green, grey, pale grey, dark grey, grey green

> Eye colour descriptions are deliberately grounded: e.g. `green` outputs as `muted natural green eyes` and `amber` as `warm amber-brown eyes`, to prevent image models rendering oversaturated or unrealistic eye colours.

### Hair Colour
**Male (25):** jet black, black, dark brown, chestnut brown, warm brown, brown, medium brown, light brown, auburn, copper red, red, dark red, warm honey, golden blonde, blonde, dark blonde, light blonde, sandy, ash blonde, salt and pepper, silver, ash grey, dark grey, grey, white

**Female (27):** same as male plus strawberry blonde, platinum blonde

### Hair Style
**Male (31):** afro, bowl cut, braids short, bun, buzz cut, caesar cut, coiled natural, cornrows, crew cut, cropped short, curly, curly medium, dreadlocks, faux hawk, french crop, locs long, locs short, low ponytail, messy medium, mohawk, mullet, pompadour, quiff, side part, skin fade, slicked back, straight, taper fade, textured crop, undercut, wavy

**Female (39):** afro, blunt cut, braid over shoulder, braids, bun, chignon, chin length bob, coiled natural, cornrows, cropped short, curly, curtain bangs, dreadlocks, faux hawk, fishtail braid, french braid, half up, high ponytail, jaw length bob, layered, locs, loose curls, loose waves, low ponytail, messy, mohawk, mullet, pixie, pulled back loose, shag, space buns, straight, textured crop, tight curls, twist out, updo, wavy, wispy, wolf cut

### Hair Length
**Male (7):** shaved, very short, short, ear length, medium, shoulder, long

**Female (9):** shaved, very short, short, ear length, chin length, medium, shoulder, long, very long

### Face Shape
**Male (8):** oval, square, rectangular, round, oblong, diamond, triangular, angular

**Female (8):** oval, round, square, heart, diamond, oblong, triangular, angular

### Nose Shape (14 each)
**Male:** straight nose, aquiline nose, broad nose, rounded nose tip, curved nose bridge, snub nose, roman nose, wide nose, flat nose, narrow nose, upturned nose, high nose bridge, low nose bridge, crooked nose

**Female:** straight nose, upturned nose, button nose, broad nose, aquiline nose, snub nose, narrow nose, wide nose, crooked nose, flat nose, roman nose, rounded nose tip, high nose bridge, low nose bridge

### Mouth Shape
**Male (9):** thin lips, full lips, wide mouth, narrow mouth, downturned mouth, upturned mouth, defined cupids bow, prominent lower lip, wide set lips

**Female (12):** same as male plus bow shaped lips, heart shaped lips, rosebud lips

### Facial Feature (distinctive marks)
**Male (13):** heavy brow, scar through eyebrow, deep set eyes, high cheekbones, cleft chin, strong jaw, laugh lines, gap toothed smile, dimples, freckles, mole on cheek, birthmark on jaw, weathered skin

**Female (12):** high cheekbones, scar through eyebrow, deep set eyes, wide eyes, cleft chin, dimples, gap toothed smile, freckles, beauty mark, birthmark, laugh lines, arched brows

> Folded into the `face` pin alongside shape, eyes, nose, and mouth.

### Body Type
**Male (18):** slim, lean, wiry, slight, average, medium build, athletic, muscular, stocky, broad shouldered, tall lean, tall athletic, lanky, heavyset, barrel chested, compact, softly built, dad bod

**Female (19):** slim, lean, wiry, petite, slight, average, medium build, athletic, muscular, tall lean, tall athletic, lanky, pear, hourglass, curvy, full figured, softly built, heavyset, stocky

### Facial Hair (male)
clean shaven, light stubble, heavy stubble, short beard, full beard, goatee, moustache, circle beard, van dyke, mutton chops, soul patch

> Females have only `clean shaven`, so a random female never grows facial hair. `clean shaven` outputs nothing.

### Expression (11)
neutral, soft smile, warm smile, slight smile, serious, stern, pensive, confident, relaxed, intense gaze, laughing

> `neutral` outputs nothing, so many people carry no expression text.

### Accessories / Eyewear (12)
none, glasses, thin framed glasses, round glasses, thick framed glasses, reading glasses, sunglasses, stud earrings, hoop earrings, nose ring, nose stud, small ear piercings

> `none` outputs nothing.

### Makeup (female)
none, natural makeup, soft makeup, minimal makeup, bold makeup, glam makeup, smokey eye, winged eyeliner, red lipstick, bold lipstick

> Males have only `none`. `none` outputs nothing.

---

## Tips

**Reproducing a result**: when you find a description you like, set `randomize` to off and note the seed value from the `seed` output pin. Set `seed` to that value and re-queue to get the same result.

**Locking some attributes, randomising others**: set the attributes you want fixed to `fixed` mode, leave the rest on `random`. For example, fix nationality to `Japanese` and complexion to `warm medium` while letting everything else randomise.

**Building a character type**: use `allow_list` mode with a curated set of values per category to constrain randomness to a character archetype. For example, for a rugged older man: `age_min = 45`, `body_type_allow_list = athletic, broad shouldered, muscular`, `hair_color_allow_list = salt and pepper, silver, grey`.

**Adding detail the node doesn't cover**: use the `extra_attributes` text area for anything else: clothing, accessories, expression, pose hints, scars, tattoos, jewellery, makeup, etc. Each comma-separated entry is appended as its own descriptor.

**Turning off attributes you don't need**: if your workflow already handles body type from another node, or you don't want age in the prompt, set that category's mode to `off`. The attribute disappears from the description entirely.

---

## Data Files

All values live in `data/` as plain JSON files. You can edit them directly to add, remove, or change any value, no code changes needed. New entries take effect on the next ComfyUI restart.

```
data/
├── shared/          # used by both male and female
│   ├── nationality.json
│   ├── complexion.json
│   ├── skin_texture.json
│   ├── eyes.json
│   ├── expression.json
│   ├── accessories.json
│   └── age.json
├── male/
│   ├── hair_color.json
│   ├── hair_style.json
│   ├── hair_length.json
│   ├── facial_hair.json
│   ├── face_shape.json
│   ├── nose_shape.json
│   ├── mouth_shape.json
│   ├── face_feature.json
│   ├── body_type.json
│   └── makeup.json
└── female/
    └── (same files as male/)
```

Each JSON entry follows this structure:
```json
{ "label": "auburn", "description": "auburn" }
```
The `label` is what appears in dropdowns. The `description` is what goes into the prompt. They can differ: for example, eye colours use grounded descriptions (`"label": "green", "description": "muted natural green eyes"`), and `clean shaven` / `neutral` / `none` use an empty description so they add nothing to the output.

A leftover `face_feature.json` also exists under `shared/` from earlier data; it is not loaded (facial features are sex-gated). Safe to ignore or delete.

---

## Testing

Unit tests cover the selection logic with no ComfyUI install required (they read only the bundled `data/` JSON):

```
cd ComfyUI_RandomPerson
python -m unittest test_random_person -v
```

---

## Requirements

- ComfyUI (any recent version, Nodes 2.0 compatible)
- Python 3.10+
- No additional pip packages required

The node registers on both the legacy V1 dict API (`NODE_CLASS_MAPPINGS`) and the V3 schema API (`comfy_entrypoint`), so it loads on older and newer ComfyUI builds alike. The shared selection core is wrapped by thin adapters for each API.

---

## Support

If you find this useful, please consider [starring the repo](https://github.com/bradsec/ComfyUI_RandomPerson). Stars help other people discover these nodes.
