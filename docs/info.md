## How it works

Voxel Architect is a procedural Minecraft architecture engine. Send a decimal BUILD line
over UART and receive Minecraft Java 1.20+ `/fill` and `/setblock` commands followed by
`DONE`. The existing ESP32 LAN bridge consumes these unchanged. There is no CPU, external
RAM or framebuffer: ordered parametric box microcode, a palette/name ROM, a decimal
formatter and a UART generate the byte stream.

Five archetypes: casa (house), spawn (monumental plaza), castillo (castle), templo (temple),
isla (floating island). Four palettes: medieval stone/oak, desert sandstone, ocean
prismarine, dark/spruce. Details include directional stair roofs and slab ridges, log
frames, glazing, furniture, column capitals, battlements, lamps and per-column terrain noise.

Inputs RX and START have two-flop synchronizers; reset is synchronous active-low. The
UART midpoint-samples eight data bits and checks the stop bit. Default divisor is 572
clocks, giving +0.16% baud error. The parser saturates dimensions at 255 (zero becomes
one), wraps seeds to 16 bits and discards malformed/busy lines through LF. INIT latches
maximum coordinates and configuration. Six ROM expressions per box are evaluated and
registered sequentially: `(maximum*k >> 3) + signed_offset`. Motif repeats are compiler
unrolled, while island columns use a runtime nested loop. A seeded LFSR supplies texture.
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
screenshots. Block states are retained in output, but stairs, panes, doors and furniture
use voxel proxies in the renderer. Slabs use half-height. Water flow and support physics
are not simulated. In-game appearance still needs checking.

Local hardening uses ignored `tt/` cloned from tt-support-tools and LibreLane 3.0.14:
`python tt/tt_tool.py --create-user-config --harden`. Docker is required. The period is
15.151515 ns rather than the template's 20 ns. See `docs/verification.md` for results.

## External hardware

USB-UART adapter or the original serial bridge on a host PC. A Minecraft Java world/server
with command permission is required to execute the output. No external memory is needed.
