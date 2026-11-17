# Voxel Architect ASIC — design spec (Tiny Tapeout, SkyWater sky130, 66 MHz)

Port of the user's ESP32 "Voxel Architect" (original source: ~/va_src, `Voxel Architect.ino`, bridge `puente_lan/bot_lan.js`)
to a Tiny Tapeout ASIC. The chip must build *better* structures than the ESP32: professional Minecraft
builder style (vMario-like): depth and layering, framed walls, textured palettes, stair/slab roofs with overhang,
detailing — while emitting far fewer commands (box primitives instead of per-voxel slice meshing).

## Top level
- Module `tt_um_astryon_voxel_architect`, standard TT ports (ui_in, uo_out, uio_in, uio_out, uio_oe, ena, clk, rst_n).
- `info.yaml`: clock_hz 66000000, language Verilog, tiles chosen after hardening (start 2x2, grow up to 8x2 if needed).
- Parameter CLK_HZ (default 66_000_000), BAUD (default 115200); tests may override for speed.
- Pins (TT demo-board UART convention):
  - ui_in[3] = UART RX, uo_out[4] = UART TX (8N1, idle high).
  - ui_in[0] = START button (rising edge, synchronized): build using DIP config: ui_in[7:5] archetype, ui_in[2:1] palette, default dims for that archetype (same defaults as bot_lan.js `!construir`), seed from free-running counter.
  - uo_out[0] = busy, uo_out[1] = done (level, until next command), uo_out[2] = tx active, uo_out[3] = rx activity, uo_out[7:5] = current archetype.
  - uio: unused, uio_oe = 0, uio_out = 0.
- All inputs to the UART RX and START go through 2-FF synchronizers. Synchronous active-low reset.

## Serial protocol (must stay compatible with puente_lan/bot_lan.js, unchanged)
RX lines (terminated by \n, \r ignored, case-sensitive, extra spaces tolerated):
- `BUILD <max_x> <max_z> <max_y> <seed> <flags>` decimal; flags bits 3:0 archetype (0 casa,1 spawn,2 castillo,3 templo,4 isla), bits 5:4 palette (0 medieval stone/oak,1 desert sandstone,2 ocean prismarine,3 dark/spruce).
- `TEST_CASA` = BUILD 12 12 8 1 0 ; `TEST_SPAWN` = BUILD 30 30 12 1 1.
- Dims clamped to 8 bits (1..255); seed 16 bits; out-of-range archetype -> casa. Too-small dims degrade gracefully to a smaller archetype (like ESP32 does), never emit an invalid/empty box.
- Unknown lines ignored. Lines received while busy are ignored.
TX output (ASCII, each line ends with \n):
- optional info line starting with `[ASIC]` (bridge logs it).
- `/fill ~x1 ~y1 ~z1 ~x2 ~y2 ~z2 <block>` or `/setblock ~x ~y ~z <block>` when the box is a single voxel. Coordinates unsigned decimal, no leading zeros, x1<=x2 etc., always within [0,max-1].
- `DONE` at the end.
- Minecraft Java 1.20+ block ids/states (e.g. `stone_brick_stairs[facing=north,half=bottom]`, `spruce_slab[type=top]`, `lantern[hanging=true]`, `oak_log[axis=x]`). Every emitted name must be a valid id.
- Ordering: later commands overwrite earlier ones (fill replace), so programs build coarse-to-fine: volume -> hollow -> frame -> details.

## Architecture
1. UART RX (16x oversample or mid-bit sample) -> line parser (decimal accumulators, token FSM).
2. Parameter unit: on BUILD computes a small register file of derived params once (mx, my, mz, wall height, keep height, insets, centers ... per archetype; sequential divide/multiply is fine — no big combinational dividers on the 66 MHz path).
3. Architecture sequencer: per-archetype microcode programs in ROM. Each instruction = a box whose 6 bounds are parametric expressions `(P[i] * k) >> 3 + off` (or equivalent), a material role, and optional repeat: iterate N times or until a bound condition, applying per-bound deltas each iteration (gives windows/pillar rows, crenellations, stepped stair roofs shrinking inward, layered spires). Optional seeded LFSR "scatter" picks texture variants per iteration (mossy/cracked mixes as column/patch fills), and per-column noise loop for the isla terrain archetype.
4. Material/palette unit: role x palette -> block id; block name ROM (compress with shared tokens if area demands).
5. Formatter: binary->decimal (3 digits, sequential double-dabble OK) + string streaming into UART TX with backpressure.
- Must close timing at 66 MHz (15.15 ns) on sky130 — pipeline/register ROM outputs as needed.
- Deterministic: same BUILD line -> same output byte stream.

## Archetypes (target quality)
- casa: stone/cobble plinth wider than footprint, log corner + mid pillars, plank infill recessed, window rows (glass panes) with stair sills/trapdoor shutters, door with step, stair gable roof with 1-block overhang and slab ridge, chimney, lanterns, interior floor + furniture (bed, table, chest, furnace).
- spawn: monumental plaza: tiered platform, patterned floor (checker/rings), central fountain/monument with water, columns ring, lantern posts, paths to 4 sides.
- castillo: curtain wall with crenellations and walkway, 4 corner round-ish/square towers taller with caps, gatehouse with iron-bars portcullis, central keep with windows and stair roof, courtyard path, torches.
- templo: stepped pyramid/ziggurat or columned temple with pediment roof, chiseled accents, inner sanctum with gold, sea lanterns lighting.
- isla: floating island: per-column noise heights, grass top, dirt, stone underside tapering, small tree.
Palettes recolor roles (wall, frame, roof, trim, floor, accent, light, glass).

## Verification
- Python golden model (`model/`) producing the identical byte stream.
- cocotb tests (TT template `test/`) compare RTL UART TX output to the model for each archetype/palette, several seeds/dims, TEST_CASA/TEST_SPAWN, START button path; check parser robustness.
- `tools/render.py`: parse command stream -> voxel grid -> isometric PNG preview per archetype (docs/img), plus validator: bounds, valid names, command counts.
- Gate-level sim in CI (TT template GL test) must pass.
