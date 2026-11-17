# Verification checkpoint

Final keep/island quality checkpoint: `afd0b97` on `devin/voxel-architect`.
Narrow-door review fix: `ec15444`; empty-scene renderer fix: `ef41ffa`.
The independent `/fill`-limit fix is `cd0b5b59d14c2f547bbd98b9f78f666410a474c0`.

## Functional verification

`python tools/compile_rom.py --check` completed successfully. Model validation:

```
$ python -m unittest discover -s model -p 'test_*.py'
............
----------------------------------------------------------------------
Ran 12 tests in 0.959s

OK
```

Icarus Verilog 11.0 and cocotb 2.1.0, full `make` from `test/`:

```
** test_architect.serial_model_comparison   PASS   128451340.00         369.43     347704.60  **
** test_architect.maximum_build             PASS    30353610.00          78.87     384848.55  **
** test_architect.parser_and_start          PASS     2197500.00           5.61     391467.67  **
** TESTS=3 PASS=3 FAIL=0 SKIP=0                    161002450.00         453.91     354699.27  **
```

This compares physical UART bytes with the golden model across all five archetypes and
four palettes, multiple seeds/dimensions, clamp/overflow cases, shorthand commands,
CRLF/extra spaces, malformed lines, busy-line discard, and the START path. START uses
the unseeded spawn geometry for an externally observable comparison. The model tests
also validate bounds, supported names, deterministic output, and malformed output streams.

Production parameters, `make REAL=yes` from `test/`:

```
** test_architect.serial_model_comparison   PASS     4616041.65          13.07     353060.12  **
** test_architect.maximum_build             SKIP           0.00           0.00          -.--  **
** test_architect.parser_and_start          SKIP           0.00           0.00          -.--  **
** TESTS=3 PASS=1 FAIL=0 SKIP=2                      4616041.65          13.08     353042.52  **
```

This sends `BUILD 1 1 1 1 0` at the default 66 MHz / 115200 baud and checks the complete
37-byte platform-and-DONE response, not just an isolated character. START is deliberately
covered only in the fast regression. The simulator logs a cosmetic Icarus root-iteration
warning (`vpi_iterate returned NULL for type vpiInstance for object NULL`).

All five 255×255×255 archetypes are checked for valid names, bounds, command shape and
volume without allocating a voxel grid. Exact-limit, partial edge tile, single-voxel,
empty bounds and rejected over-limit output cases are also covered. Geometry assertions
check the raised house frame, door, stairs, chimney, island tip, trunk and foliage.
The final pass also checks keep walls across both storeys, floor, two window rows,
sills, corbel course, roof support and the open courtyard path. Island tests assert
the exact canopy populations (21/9 blocks at height 10, 21/9/5 at height 14), exposed
trunk lengths, dirt stratum, one-block edge transition and a single bottom tip.
Widths 8–12 across all palettes retain both house door halves. Renderer tests cover
normal, air-only, DONE-only and invalid scenes.

The maximum-house test's complete 37,451-byte physical-UART output matches the model byte for byte and every
fill passes the volume validator. Fast coverage also includes a 255×255 platform and
a 40³ house to exercise tiles across all axes and partial final tiles, the reported
`BUILD 8 12 8 1 0` narrow-door case and the taller `BUILD 22 22 14 1 4` island.

The generated ROM is an explicit simulation compile dependency. Without it, incremental
`make` could compare a stale compiled RTL ROM against an updated Python model.

## Synthesis and physical implementation

Paired synthesis uses Yosys 0.9 with the same sky130 HD TT Liberty file and commands for
both the earlier `46f2a54` checkpoint and final RTL:

```
read_verilog -I src src/architect.v src/uart.v src/parser.v
synth -top tt_um_astryon_voxel_architect -flatten
dfflibmap -liberty $LIB
abc -liberty $LIB
stat -liberty $LIB
```

`LIB` is `sky130_fd_sc_hd__tt_025C_1v80.lib` from sky130A PDK revision
`8afc8346a57fe1ab7934ba5a6056ea8b43078e71`.

| Identical synthesis flow | Mapped cells | Cell area (µm²) |
|---|---:|---:|
| Earlier `46f2a54` RTL | 7,778 | 54,506.0256 |
| Previous quality + fill-limit RTL | 8,921 | 61,700.4256 |
| Final keep/island + narrow-door RTL | 9,044 | 62,080.7904 |
| Final change from previous quality round | +1.4% | +0.6% |

Final pre-mapping generic count is 17,113 cells. These are synthesis estimates, not
post-placement utilization or timing signoff. This unconstrained host flow differs from
the earlier LibreLane synthesis (7,726 instances / 85,010.2816 µm²); the paired comparison
above avoids conflating tool-flow changes with RTL growth. Old Yosys skips unsupported
scan/enabled-flop Liberty alternatives, while mapping the design's ordinary flops.

The initial **2x2** attempt failed detailed placement:

```
[ERROR DPL-0036] Detailed placement failed.
```

`info.yaml` still requests **4x2** at **15.151515 ns**. The previous local 4x2 run reached
detailed routing but was killed because this two-core box was too slow. It produced no
final post-route timing/DRC/LVS signoff. No new local hardening was started for this round;
the PR's GitHub Actions `gds` job owns physical verification. Area fit and 66 MHz closure
for the updated RTL remain pending CI; synthesis alone does not establish either.

## Preview inspection

The five generated PNGs were opened and visually inspected after refining roof/gable,
temple, and island proportions. Final defaults, palette 0, seed 1:

| Image | Commands before DONE | Occupied logical voxels |
|---|---:|---:|
| `img/casa.png` | 77 | 460 |
| `img/spawn.png` | 54 | 2641 |
| `img/castillo.png` | 261 | 3033 |
| `img/templo.png` | 51 | 1081 |
| `img/isla.png` | 291 | 574 |
| `img/isla-tall.png` (22×22×14) | 327 | 1038 |

The keep is now a two-storey stone hall with mossy/cracked corner variation, window
rows and sills, a gate-facing door, a corbel course and a seated stair roof. Its footprint
sits behind the courtyard approach. At height 10 the island reserves four blocks below
the grass for the cone and three exposed trunk blocks below two rounded canopy layers.
At height 14 the cone grows to six blocks and the crown gains its third layer.
Bridge dimensions and START defaults have not changed.

These are schematic, color-coded previews. Quarter-block geometry shows stairs, slabs,
panes, doors and lanterns. The island has a lower camera angle to reveal its underside.
Furniture shapes are simplified. Minecraft textures, lighting, water updates,
block support and actual in-game execution have not been verified.

## Implementation choices

Repeated motifs are compiler-unrolled into box microcode instead of a hardware repeat
opcode. Island columns merge runs with equal top and underside height; the top is
level except for a one-block edge drop, and the underside uses half the maximum X/Z
center distance, rounded up, to form a faceted cone. All boxes then pass
through a 32-cube tiler, preserving material and coarse-to-fine command ordering.
The parameter unit precomputes eighth fractions
of the maximum coordinates by repeated addition. Builds with any dimension below eight
emit a clipped one-layer palette platform rather than an incomplete large archetype.
No serial-protocol or pinout changes are required by the original LAN bridge.
