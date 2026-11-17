# Verification checkpoint

RTL/model checkpoint: `f452239` on `devin/voxel-architect`.

## Functional verification

`python tools/compile_rom.py --check` completed successfully. Model validation:

```
$ python -m unittest discover -s model -p 'test_*.py'
....
----------------------------------------------------------------------
Ran 4 tests in 0.481s

OK
```

Icarus Verilog 11.0 and cocotb 2.1.0, `make` from `test/`:

```
** test_architect.serial_model_comparison   PASS   116492120.00         368.61     316029.96  **
** test_architect.parser_and_start          PASS     1640200.00           6.47     253507.74  **
** TESTS=2 PASS=2 FAIL=0 SKIP=0                    118132320.00         375.08     314951.03  **
```

This compares physical UART bytes with the golden model across all five archetypes and
four palettes, multiple seeds/dimensions, clamp/overflow cases, shorthand commands,
CRLF/extra spaces, malformed lines, busy-line discard, and the START path. START uses
the unseeded spawn geometry for an externally observable comparison. The model tests
also validate bounds, supported names, deterministic output, and malformed output streams.

Production parameters, `make REAL=yes` from `test/`:

```
** test_architect.serial_model_comparison   PASS     4616026.50          26.40     174857.41  **
** test_architect.parser_and_start          SKIP           0.00           0.00          -.--  **
** TESTS=2 PASS=1 FAIL=0 SKIP=1                      4616026.50          26.40     174834.37  **
```

This sends `BUILD 1 1 1 1 0` at the default 66 MHz / 115200 baud and checks the complete
37-byte platform-and-DONE response, not just an isolated character. START is deliberately
covered only in the fast regression. The simulator logs a cosmetic Icarus root-iteration
warning (`vpi_iterate returned NULL for type vpiInstance for object NULL`).

The generated ROM is an explicit simulation compile dependency. Without it, incremental
`make` could compare a stale compiled RTL ROM against an updated Python model.

## Synthesis and physical implementation

Generic Yosys 0.9:

```
yosys -p 'read_verilog -I src src/architect.v src/uart.v src/parser.v; synth -top tt_um_astryon_voxel_architect; stat'
Number of cells:              14929
$_DFF_P_                       751
Number of memories:               0
Number of processes:              0
```

This is an unmapped generic-cell estimate, not a sky130 standard-cell count or an area
signoff. The local Tiny Tapeout flow uses LibreLane 3.0.14 in Docker, sky130A, and a
15.151515 ns clock period. Its lint checks report zero errors, warnings, timing constructs,
and inferred latches.

The initial **2x2** attempt failed detailed placement:

```
[ERROR DPL-0036] Detailed placement failed.
```

`info.yaml` therefore selects **4x2**. The final 4x2 run reached clock-tree synthesis and
post-CTS timing repair. Before repair, nominal TT setup slack was +2.209 ns, but nominal
SS setup slack was -5.063 ns; nominal TT alone is not evidence of timing closure. Full
post-route timing, DRC, LVS and gate-level simulation are not yet signed off at this checkpoint.
Local reports and logs are ignored under `runs/` and `*.log`; reproduce with:

```
python tt/tt_tool.py --create-user-config --harden
```

## Preview inspection

The five generated PNGs were opened and visually inspected after refining roof/gable,
temple, and island proportions. Final defaults, palette 0, seed 1:

| Image | Commands before DONE | Occupied logical voxels |
|---|---:|---:|
| `img/casa.png` | 73 | 578 |
| `img/spawn.png` | 44 | 2640 |
| `img/castillo.png` | 213 | 2601 |
| `img/templo.png` | 39 | 1310 |
| `img/isla.png` | 883 | 1074 |

These are schematic, color-coded isometric previews. Stairs/slabs use half-voxel geometry;
pane/door/furniture shapes are simplified. Minecraft textures, lighting, water updates,
block support and actual in-game execution have not been verified.

## Implementation choices

Repeated motifs are compiler-unrolled into box microcode instead of a hardware repeat
opcode. Island columns use a runtime loop. The parameter unit precomputes eighth fractions
of the maximum coordinates by repeated addition. Builds with any dimension below eight
emit a clipped one-layer palette platform rather than an incomplete large archetype.
No serial-protocol or pinout changes are required by the original LAN bridge.
