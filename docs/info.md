## How it works

Voxel Architect is a procedural Minecraft architecture engine. Send a decimal BUILD line
over UART and receive Minecraft Java 1.20+ `/fill` and `/setblock` commands followed by
`DONE`. The existing ESP32 LAN bridge consumes these unchanged. There is no CPU, external
RAM or framebuffer: ordered parametric box microcode, a palette/name ROM, a decimal
formatter and a UART generate the byte stream.

Five archetypes: casa (house), spawn (monumental plaza), castillo (castle), templo (temple),
isla (floating island). Four palettes: medieval stone/oak, desert sandstone, ocean
prismarine, dark/spruce. Details include directional stair roofs and slab ridges, log
frames, glazing, furniture, column capitals, battlements, lamps and a faceted floating island.

Inputs RX and START have two-flop synchronizers; reset is synchronous active-low. The
UART midpoint-samples eight data bits and checks the stop bit. Default divisor is 572
clocks, giving +0.16% baud error. The parser saturates dimensions at 255 (zero becomes
one), wraps seeds to 16 bits and discards malformed/busy lines through LF. INIT latches
maximum coordinates and configuration. A nine-cycle parameter unit precomputes all eighth
fractions by repeated addition into a small register file. Six ROM expressions per box
select these fractions, add a signed offset and register the result. Motif repeats are compiler
unrolled, while island columns use a runtime nested loop that merges equal-height Z runs.
The island's grass interior is level, with a one-block lowered edge. Half the maximum
X/Z distance from the center tapers its faceted underside to a single stone tip. A seeded
LFSR supplies architectural texture. The bridge's 22×22×10 island has a four-block
underside, three exposed trunk blocks and two canopy layers; height 14 grows these to
six blocks, four trunk blocks and three canopy layers. Both remain below 400 commands.
All START-button defaults remain unchanged, including the height-10 island.
Before formatting, each box is partitioned into disjoint tiles of at most 32 blocks on
each axis, guaranteeing at most 32,768 blocks per `/fill` without multipliers or dividers.
All tiles of one box complete before the next microinstruction changes the material/RNG.
The decimal formatter repeatedly subtracts 100 and 10 and suppresses leading zeroes.
Ready/valid backpressure holds characters until UART accepts them. Done asserts only
after the last newline stop bit. No large combinational dividers are used.

## How to test

Use a 66 MHz clock and 115200 baud, 8N1. UART RX is input 3, TX output 4. Connect common
ground and 3.3 V logic (not RS-232 voltages).

```
BUILD 12 12 8 1 0
BUILD 26 26 18 42 18
TEST_CASA
TEST_SPAWN
```

Arguments: width X, depth Z, height Y, seed, flags. Flags bits 3:0 select archetype 0..4;
bits 5:4 select palette 0..3. Invalid archetypes use casa. LF terminates; CR is ignored;
extra spaces are allowed. Unknown lines and lines overlapping busy are ignored. Wait for
DONE before the next build. Identical commands produce identical bytes. TEST_CASA uses
12×12×8, seed 1; TEST_SPAWN uses 30×30×12, seed 1. If any dimension is below eight,
the design degrades to a safe one-layer palette platform. All bounds are clipped, and
inverted boxes are skipped.

Alternatively set inputs 7:5 to archetype and 2:1 to palette, then raise START (input 0).
Defaults: casa 12×12×8, spawn 30×30×12, castillo 26×26×18, templo 18×18×10, isla 22×22×10.
START uses a free-running counter seed. UART commands win simultaneous requests.

Output 0: busy; 1: sticky done until next command; 2: TX active; 3: RX active; 4: UART TX
(idle high); 7:5: current archetype. Bidirectional pins remain inputs and output zero.
Input 4 is unused. Keep configuration inputs stable around START.

### Development

`model/architect.py` is the executable golden model. `tools/compile_rom.py` compiles its
typed expression programs and palette strings to `src/rom.vh`. The model directly evaluates
the programs, independently of the generated encoding. After changing the programs, run
the compiler, tests and renderer:

```
python -m pip install -r test/requirements.txt -r tools/requirements.txt
python tools/compile_rom.py --check
python -m unittest discover -s model -p 'test_*.py'
cd test && make
cd test && make REAL=yes
python tools/render.py --all
```

Run test commands from the repository root except `make`, which runs in `test/`.
`make GATES=yes` uses the CI-provided powered netlist and PDK and tests a complete short
UART build at production clock/baud without internal hierarchical probes.

Previews in `docs/img/` are schematic voxel-color isometric drawings, not Minecraft
screenshots. A quarter-block grid shows stair treads, slab halves, thin panes/doors and
small lantern bodies; furniture uses simplified proxies. The island uses a lower camera
angle to reveal its underside. Empty scenes render a labeled image. Water flow and support physics
are not simulated. In-game appearance still needs checking.

Hardening runs in the PR's GitHub Actions `gds` job, not locally on the two-core development
box. The period is 15.151515 ns rather than the template's 20 ns; the tile request remains
4x2 pending CI physical implementation. See `docs/verification.md` for results.

## External hardware

USB-UART adapter or the original serial bridge on a host PC. A Minecraft Java world/server
with command permission is required to execute the output. No external memory is needed.
