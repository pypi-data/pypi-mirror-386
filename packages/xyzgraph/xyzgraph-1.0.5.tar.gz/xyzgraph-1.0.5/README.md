# xyzgraph: Molecular Graph Construction from Cartesian Coordinates

**xyzgraph** is a Python toolkit for building molecular graphs (bond connectivity, bond orders, formal charges, and partial charges) directly from 3D atomic coordinates in XYZ format. It provides both **cheminformatics-based** and **quantum chemistry-based** (xTB) workflows.

[![PyPI Downloads](https://static.pepy.tech/badge/xyzgraph)](https://pepy.tech/projects/xyzgraph)

---

## Table of Contents

1. [Key Features](#key-features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Methodology Overview](#methodology-overview)
5. [Workflow Comparison](#workflow-comparison)
6. [CLI Reference](#cli-reference)
7. [Python API](#python-api)
8. [Visualization](#visualization)
9. [Limitations & Future Work](#limitations--future-work)
10. [References](#references)
11. [Contributing & Contact](#contributing--contact)

---

## Key Features

- **Distance-based initial bonding** using *consistent* van der Waals radii across *all elements* from Charry and Tkatchenko [[1]](https://doi.org/10.1021/acs.jctc.4c00784)
- **Two construction methods**:
  - `cheminf`: Pure cheminformatics with bond order optimization
  - `xtb`: semi-empirical calculation of bond orders via xTB Wiberg bond orders with Mulliken charges [[2]](https://pubs.acs.org/doi/10.1021/acs.jctc.8b01176)
- **Cheminformatics modes**:
  - `--quick`: Fast (crude) valence adjustment
  - Full optimization with valence and charge minimisation
    - `--optimizer`:  
      **beam**: optimization across multiple paths (slightly slower, default)  
      **greedy**: iterative valence adjustment
- **Aromatic detection**: Hückel 4n+2 rule for 6-membered rings
- **Charge computation**: Gasteiger (cheminf) or Mulliken (xTB) partial charges
- **RDkit/xyz2mol comparison** validation against RDKit bond perception [[3]](https://github.com/jensengroup/xyz2mol), [[4]](https://github.com/rdkit)
- **ASCII 2D depiction** with layout alignment for method comparison (see also [[5]](https://github.com/whitead/moltext))

---

## Installation

### From PyPI

```bash
pip install xyzgraph
```

### From Source

```bash
git clone https://github.com/aligfellow/xyzgraph.git
cd xyzgraph
pip install .
# or simply
pip install git+https://github.com/aligfellow/xyzgraph.git
```

### Dependencies

- **Core**: `numpy`, `networkx`, `rdkit`
- **Optional**: [xTB binary](https://github.com/grimme-lab/xtb) (for `--method xtb`)

To install xTB (Linux/macOS) see [here](https://github.com/grimme-lab/xtb):

```bash
conda install -c conda-forge xtb # or download from GitHub releases
```

---

## Quick Start

### CLI Examples

**Minimal usage** (auto-displays ASCII depiction):

```bash
xyzgraph molecule.xyz
```

**Specify charge and method**:

```bash
xyzgraph molecule.xyz --method xtb --charge -1 --multiplicity 2
```

**Detailed debug output**:

```bash
xyzgraph molecule.xyz --debug
```

**Compare with RDKit**:

```bash
xyzgraph molecule.xyz --compare-rdkit
```

### Python Example

**Basic usage**:

```python
from xyzgraph import build_graph, graph_to_ascii, read_xyz_file

atoms = read_xyz_file("molecule.xyz") 
G = build_graph(atoms, charge=0)
# OR
G = build_graph("molecule.xyz", charge=0)

# Print ASCII structure
print(graph_to_ascii(G, scale=3.0, include_h=False))
```

---

## Methodology Overview

### Design Philosophy

xyzgraph offers two distinct pathways for molecular graph construction:

1. **Cheminformatics Path** (`method='cheminf'`): 
   - Pure graph-based approach using chemical heuristics
   - No external quantum chemistry calls
   - Cached scoring, valence, edge and graph properties
   - Fast and suitable for both organic *and* inorganic molecules

2. **Quantum Chemistry Path** (`method='xtb'`):
   - Uses GFN2-xTB (extended tight-binding) calculations [[2]](https://pubs.acs.org/doi/10.1021/acs.jctc.8b01176)
   - Reads in Wiberg bond orders and Mulliken charges from output
   - Potentially more accurate for unusual bonding situations 
      - *though, xTB may be less robust in these situations*
   - Requires xTB binary installation

### Cheminformatics Workflow (method='cheminf')

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Input Processing                                             │
│    • Parse XYZ file internally                                  │
│    • Load reference data (VDW radii, valences, electrons)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 2. Initial Bond Graph (Distance-Based)                          │
│    • Compute pairwise distances                                 │
│    • Apply scaled VDW thresholds (default --threshold 1.0):     │
|      - H-H: 0.38 × (r₁ + r₂) × threshold                        │
│      - H-nonmetal: 0.42 × (r₁ + r₂) × threshold                 │
│      - H-metal: 0.48 × (r₁ + r₂) × threshold                    │
│      - Nonmetal-nonmetal: 0.55 × (r₁ + r₂) × threshold          │
│      - Metal-ligand: 0.6 × (r₁ + r₂) (unscaled by threshold)    │
│    • Bonds sorted by confidence: 1.0 (short) to 0.0 (at thresh) │
│    • High confidence (>0.4): added directly                     │
│    • Low confidence (≤0.4): geometric validation applied        │
│                                                                 │
│    Geometric Validation (for elongated/TS bonds):               │
│    • Acute angle check: 15° (metals) / 30° (non-metals)         │
│    • Collinearity check: distinguishes trans vs spurious        │
│    • Diagonal check: preventing false 3-ring formation          │
│    → Allows TS bonds with --threshold 1.2-1.3 (≥1.35 unstable)  │
│                                                                 │
│    • Create graph with single bonds (order = 1.0)               │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 3. Ring Pruning                                                 │
│    • Detect cycles (NetworkX cycle_basis)                       │
│    • Remove geometrically distorted small rings (3,4-membered)  │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 3.5 Kekulé Initialization for Conjugated Rings                  │
│    • Find 5/6-membered planar rings with C/N/O/S/B/P/Se         │
│    • Initialize alternating bond orders (5-ring: 2-1-2-1-1,     │
│      6-ring: 2-1-2-1-2-1)                                       │
│    • Handle fused rings (naphthalene, anthracene):              │
│      - Detecting shared edges from previous rings               │
│      - Validated across extended ring system                    │
│    • Gives optimizer excellent starting point                   │
│    • Reduces iterations needed for conjugated systems           │
│    • Broader atom set than aromatic detection (P, Se included)  │
└────────────────────┬────────────────────────────────────────────┘
                     │
          ┌──────────┴─────────────┐
          │                        │
┌─────────▼────────────┐   ┌───────▼──────────────────────────────┐
│ 4a. Quick Mode       │   │ 4b. Full Optimization                │
│  • Lock metal bonds  │   │  • Lock metal bonds at 1.0           │
│  • 3 iterations      │   │  • Iterative BIDIRECTIONAL search:   │
│  • Promote bonds     │   │    - Test both +1 AND -1 changes     │
│    where both atoms  │   │    - Allows Kekulé structure swaps   │
│    need increased    │   │  • Score = f(valence_error,          │
│    valence           │   │             formal_charges,          │
│  • Distance check    │   │             electronegativity,       │
│                      │   │             conjugation_penalty)     │
│                      │   │  • Optimizer choice:                 │
│                      │   │    - Beam: parallel hypotheses       │
│                      │   │    - Greedy: single best change      │
│                      │   │  • Cache where possible for speed    │
│                      │   │  • Top-k edge candidate selection    │
└─────────┬────────────┘   └──────────┬───────────────────────────┘
          └───────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 5. Aromatic Detection (Hückel 4n+2)                             │
│    • Find 5/6-membered rings with C/N/O/S/B                     │
│    • Count π electrons (sp² carbons → 1e, N/O/S LP → 2e)        │
│    • Apply Hückel rule: 4n+2 π electrons                        │
│    • Set aromatic bonds to 1.5                                  │
│    • Other heteroatoms (e.g. P, Se) use Kekulé structures       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 6. Formal Charge Assignment                                     │
│    • For each non-metal atom:                                   │
│      - B = 2 × Σ(bond_orders)                                   │
│      - L = max(0, target - B)  [target: 2 for H, 8 otherwise]   │
│      - formal = V_electrons - (L + B/2)                         │
│    • Balance total to match system charge                       │
│    • Metals forced to 0 (coordination not oxidation state)      │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 7. Gasteiger Partial Charges                                    │
│    • Convert bond orders to RDKit bond types                    │
│    • Compute Gasteiger charges                                  │
│    • Adjust for total charge conservation                       │
│    • Aggregate H charges onto heavy atoms                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 9. Output Graph                                                 │
│    Nodes: symbol, formal_charge, charges{}, agg_charge, valence │
│    Edges: bond_order, bond_type, metal_coord                    │
└─────────────────────────────────────────────────────────────────┘
```

### xTB Workflow (method='xtb')

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Input Processing                                             |
│    • Parse XYZ file internally                                  │
│    • Write XYZ to temporary directory                           │
│    • Set up xTB calculation parameters                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 2. Run xTB Calculation                                          │
│    Command: xtb <file>.xyz --chrg <charge> --uhf <unpaired>     │
│    • GFN2-xTB Hamiltonian                                       │
│    • Single-point calculation                                   │
│    • Wiberg bond order analysis                                 │
│    • Mulliken population analysis                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 3. Parse xTB Output                                             │
│    • Read wbo file (Wiberg bond orders)                         │
│    • Read charges file (Mulliken atomic charges)                │
│    • Threshold: bond_order > 0.5 → create edge                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 4. Build Graph from xTB Data                                    │
│    • Create nodes with Mulliken charges                         │
│    • Create edges with Wiberg bond orders                       │
│    • No further optimization needed                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 5. Cleanup (optional)                                           │
│    • Remove temporary xTB files (unless --no-clean)             │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 6. Output Graph                                                 │
│    Nodes: symbol, charges{'mulliken': ...}, agg_charge, valence │
│    Edges: bond_order (Wiberg), bond_type, metal_coord           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow Comparison

| Feature | cheminf (quick) | cheminf (full) | xtb |
|---------|----------------|----------------|-----|
| **Speed** | Very Fast | Fast | Moderate |
| **Accuracy** | Okay for simple molecules | Very good across various systems | Only limited by xTB performance (QM-based) |
| **External deps** | None | None | Requires xTB binary |
| **Bond orders** | Heuristic (integer-like) | Optimized formal charge and valency | Wiberg (fractional) |
| **Charges** | Gasteiger | Gasteiger | Mulliken |
| **Metal complexes** | Limited | Reasonable | Reasonable (limited by xTB metal performance) |
| **Conjugated systems** | Basic | Excellent | Excellent |
| **Best for** | Quick checks, where connectivity most important | Most cases | Awkward bonding, validation |

### When to Use Each Method

**Use `--method cheminf` (default)**:

- Most use cases
- No xTB installation available
- Batch processing structures

**Use `--method cheminf --quick`**:

- Extremely large molecules
- Initial rapid screening
- When approximate bond orders suffice

**Use `--method xtb`**:

- Validation of cheminf results
- Unusual electronic structures
- Low confidence in bonding structure

### Optimizer Algorithms (cheminf full mode only)

**Beam Search Optimizer** (`--optimizer beam` default, `--beam-width 3` default):

- Explores multiple optimization paths in parallel
- Maintains top-k hypotheses at each iteration (of top candidates)
- Bidirectional: tests both +1 and -1 bond orders for each hypothesis
- More robust against local minima
- Slower, but better convergence
- Best for robust bonding assignment across periodic table

**Greedy Optimizer** (`--optimizer greedy`):

- Tests all top candidate edges, picks single best change per iteration
- Bidirectional: tests both +1 and -1 bond order changes
- Fast and effective for most molecules
- Can get stuck in local minima (*e.g.* alpha, beta unsaturated systems)

---

## CLI Reference

### Command Syntax

```bash
> xyzgraph -h
usage: xyzgraph [-h] [--method {cheminf,xtb}] [-q] [--max-iter MAX_ITER] [--edge-per-iter EDGE_PER_ITER] [-o {greedy,beam}] [-bw BEAM_WIDTH] [--bond BOND]
                [--unbond UNBOND] [-c CHARGE] [-m MULTIPLICITY] [-b] [-d] [-a] [-as ASCII_SCALE] [-H] [--compare-rdkit] [--no-clean]
                xyz

Build molecular graph from XYZ.

positional arguments:
  xyz                   Input XYZ file

options:
  -h, --help            show this help message and exit
  --method {cheminf,xtb}
                        Graph construction method (default: cheminf) (xtb requires xTB binary installed and available in PATH)
  -q, --quick           Quick mode: fast heuristics, less accuracy (NOT recommended)
  --max-iter MAX_ITER   Maximum iterations for bond order optimization (default: 50, cheminf only)
  -t THRESHOLD, --threshold THRESHOLD
                        vdW Scaling factor for bond detection thresholds (default: 1.0)
  --edge-per-iter EDGE_PER_ITER
                        Number of edges to adjust per iteration (default: 10, cheminf only)
  -o {greedy,beam}, --optimizer {greedy,beam}
                        Optimization algorithm (default: beam, cheminf , BEAM recommended)
  -bw BEAM_WIDTH, --beam-width BEAM_WIDTH
                        Beam width for beam search (default: 5). i.e. number of candidate graphs to retain per iteration
  --bond BOND           Specify atoms that must be bonded in the graph construction. Example: --bond 0,1 2,3
  --unbond UNBOND       Specify that two atoms indices are NOT bonded in the graph construction. Example: --unbond 0,1 1,2
  -c CHARGE, --charge CHARGE
                        Total molecular charge (default: 0)
  -m MULTIPLICITY, --multiplicity MULTIPLICITY
                        Spin multiplicity (auto-detected if not specified)
  -b, --bohr            XYZ file provided in units bohr (default is Angstrom)
  -d, --debug           Enable debug output (construction details + graph report)
  -a, --ascii           Show 2D ASCII depiction (auto-enabled if no other output)
  -as ASCII_SCALE, --ascii-scale ASCII_SCALE
                        ASCII scaling factor (default: 3.0)
  -H, --show-h          Include hydrogens in visualizations (hidden by default)
  --compare-rdkit       Compare with xyz2mol output (uses rdkit implementation)
  --no-clean            Keep temporary xTB files (only for --method xtb)
  --threshold-h-nonmetal THRESHOLD_H_NONMETAL
                        ADVANCED: vdW threshold for H-nonmetal bonds (default: 0.42)
  --threshold-h-metal THRESHOLD_H_METAL
                        ADVANCED: vdW threshold for H-metal bonds (default: 0.5)
  --threshold-metal-ligand THRESHOLD_METAL_LIGAND
                        ADVANCED: vdW threshold for metal-ligand bonds (default: 0.65)
  --threshold-nonmetal THRESHOLD_NONMETAL
                        ADVANCED: vdW threshold for nonmetal-nonmetal bonds (default: 0.55)

```

**Method comparison**:

```bash
xyzgraph molecule.xyz --debug > cheminf.txt
xyzgraph molecule.xyz --method xtb --debug > xtb.txt
diff cheminf.txt xtb.txt
```

**Validate against RDKit**:

```bash
xyzgraph molecule.xyz --compare-xyz2mol
```

---

## Python API

Direct graph construction:

```python
from xyzgraph import build_graph, graph_debug_report

# Cheminf full optimization
G_full = build_graph(
      atoms='molecule.xyz',
      charge=0,
      max_iter=50,              # maximum iterations (normally converged <20)
      edge_per_iter=6,          # default 10
      bond=[(0,1)],             # ensure a bond between 0 and 1
      debug=True
   )
```

---

## Visualization

### ASCII Depiction

xyzgraph includes a built-in ASCII renderer for 2D molecular structures. This is heavily inspired by work elsewhere, *e.g.* [[5]](https://github.com/whitead/moltext) by Andrew White.

```python
from xyzgraph import graph_to_ascii

# Basic rendering
ascii_art = graph_to_ascii(G, scale=3.0, include_h=False)
print(ascii_art)
```

**Output example** (acyl isothiouronium):

```text
                                       C
                                        \
                                        \
                                         C-------C
                                      ///
        ---C-               /C-------C
    C---     ---          //          \           /C----
   /            -C------N\            \          /      ---C
  C             /        \\           /C-------C/           \\
   \\          /          \\        //          \             C
     \\    ---C-          -C\-----N/            \           //
       C---     ----   ---         \             C---     //
                    -S-             \                ----C
                                    /C===
                                  // =======O
                                C\       ====
                                 \\
                                  \\
                                  /C\
                                //
                              C/
```

**Features**:

- Single bonds: `-`, `|`, `/`, `\`
- Double bonds: `=`, `‖` (parallel lines)
- Triple bonds: `#`
- Aromatic: 1.5 bond orders shown as single
- Special edges: `*` (TS), `.` (NCI) if `G.edges[i,j]['TS']=True`

### Layout Alignment

Compare methods by aligning their ASCII depictions:

```python
from xyzgraph import build_graph, graph_to_ascii

# Build with both methods
G_cheminf = build_graph(atoms, method='cheminf')
G_xtb = build_graph(atoms, method='xtb')

# Generate aligned depictions
ascii_ref, layout = graph_to_ascii(G_cheminf)
ascii_xtb = graph_to_ascii(G_xtb, reference_layout=layout)

print("Cheminf:\n", ascii_ref)
print("\nxTB:\n", ascii_xtb)
```

### Debug Report

Tabular listing of all atoms and bonds:

```python
from xyzgraph import graph_debug_report

report = graph_debug_report(G, include_h=False)
print(report)
```

**Full example**:

```text
> xyzgraph benzene_NH4-cation-pi.xyz -c 1 -a -d

============================================================
BUILDING GRAPH (CHEMINF, FULL MODE)
Atoms: 17, Charge: 1, Multiplicity: 1
============================================================

  Added 17 atoms
  Initial bonds: 16
  Found 1 rings
  Initial bonds: 16
  Pruning distorted rings (sizes: [3, 4])
  Initialized 1 6-membered carbon rings with Kekulé pattern
============================================================
  
BEAM SEARCH OPTIMIZATION (width=3)
============================================================
  Initial score: 15.50
  
Iteration 1:
      No improvements found in any beam, stopping
  
Applying best solution to graph...
------------------------------------------------------------
  Explored 13 states across 1 iterations
  Found 0 improvements
  Score: 15.50 → 15.50
------------------------------------------------------------

============================================================
AROMATIC RING DETECTION (Hückel 4n+2)
============================================================
  
Ring 1 (6-membered): ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']
    π electrons: 6 (C0:1, C1:1, C2:1, C3:1, C4:1, C5:1)
    ✓ AROMATIC (4n+2 rule: n=1)

------------------------------------------------------------
  SUMMARY: 1 aromatic rings, 6 bonds set to 1.5
------------------------------------------------------------

    Gasteiger charge calculation failed: Explicit valence for atom # 12 N, 4, is greater than permitted

============================================================
GRAPH CONSTRUCTION COMPLETE
============================================================

# Molecular Graph: 17 atoms, 16 bonds
# total_charge=1  multiplicity=1  sum(gasteiger)=+1.000  sum(gasteiger_raw)=+0.000
# (C–H hydrogens hidden; heteroatom-bound hydrogens shown; valences still include all H)
# [idx] Sym  val=.. chg=.. agg=.. | neighbors: idx(order / aromatic flag)
[  0]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 1(1.50*) 5(1.50*)
[  1]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 0(1.50*) 2(1.50*)
[  2]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 1(1.50*) 3(1.50*)
[  3]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 2(1.50*) 4(1.50*)
[  4]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 3(1.50*) 5(1.50*)
[  5]  C  val=4.00  formal=+0  chg=+0.059  agg=+0.118 | 0(1.50*) 4(1.50*)
[ 12]  N  val=4.00  formal=+1  chg=+0.059  agg=+0.294 | 13(1.00) 14(1.00) 15(1.00) 16(1.00)
[ 13]  H  val=1.00  formal=+0  chg=+0.059  agg=+0.059 | 12(1.00)
[ 14]  H  val=1.00  formal=+0  chg=+0.059  agg=+0.059 | 12(1.00)
[ 15]  H  val=1.00  formal=+0  chg=+0.059  agg=+0.059 | 12(1.00)
[ 16]  H  val=1.00  formal=+0  chg=+0.059  agg=+0.059 | 12(1.00)

# Bonds (i-j: order) (filtered)
[ 0- 1]: 1.50
[ 0- 5]: 1.50
[ 1- 2]: 1.50
[ 2- 3]: 1.50
[ 3- 4]: 1.50
[ 4- 5]: 1.50
[12-13]: 1.00
[12-14]: 1.00
[12-15]: 1.00
[12-16]: 1.00

============================================================
# ASCII Depiction
============================================================
         -C-------------------C-
      ---                       ----
  ----                              ----
C-                                      -C
  \\                                 ///
    \\\                            //
       \\                       ///
         \C-------------------C/


                    H
                    |
                    |
                    |
H-------------------N--------------------H
                    |
                    |
                    |
                    H
```

---

## Limitations & Future Work

### Current Limitations

1. **Metal Complexes**
   - Bond orders locked at 1.0 (no d-orbital chemistry)
   - Metal-metal bonds *partially* supported (single bond allowed)
   - Can deal with **both** ionic *and* neutral ligands

2. **Radicals & Open-Shell Systems**
   - Unlikely to appropriately solve a valence structure
   - Not explicity dealt with currently
   - *May* behave, *may* be unreliable

3. **Zwitterions**
   - Formal charge and valence analysis does identify `-[N+](=O)(-[O-])` bonding and formal charge pattern
   - This is performed **without pattern matching**
   - *May* not always be fully robust

4. **Large Conjugated Systems**
   - May need many iterations for convergence (kekule initialised rings)

5. **Charged Aromatics**
   - Hückel electron counting is simplistic
   - Should still solve with valence/charge optimisation

---

### Built-in Comparison

xyzgraph can directly compare its output to rdkit/xyz2mol:

```bash
xyzgraph molecule.xyz --compare-rdkit --debug
```

**Output includes**:

- Layout-aligned ASCII depictions
- Edge differences (bonds only in one method)
- Bond order differences (Δ ≥ 0.25)

**Example**:

```text
# Bond differences: only_in_native=1   only_in_rdkit=0   bond_order_diffs=2
#   only_in_native: 4-7
#   bond_order_diffs (Δ≥0.25):
#     1-2   native=1.50   rdkit=1.00   Δ=+0.50
#     2-3   native=2.00   rdkit=1.50   Δ=+0.50
```

---

## Examples

This section demonstrates xyzgraph's capabilities on real molecular systems, showcasing Kekulé initialization, aromatic detection, metal coordination analysis, and formal charge assignment.

### Example 1: Metal Complex (Ferrocene-Manganese Hydride)

This example demonstrates xyzgraph's handling of organometallic complexes with multiple ligand types.

**System:** [(η⁵-Cp)₂Fe][Mn(H)(CO)₂(PNN)] - Ferrocene cation with manganese hydride complex  
**File:** `examples/mnh.xyz` (77 atoms)

**Command:**
```bash
xyzgraph examples/mnh.xyz --ascii --debug
```

**Key Features:**
- Detection of Cp⁻ (cyclopentadienyl) rings coordinated to Fe
- Metal coordination summary (Fe²⁺, Mn¹⁺) with ligand classification
- Hydride ligand (H⁻) recognition
- Carbonyl (CO) ligands with triple-bonded oxygen
- Aromatic Cp rings with charge contribution to π system

**Output (truncated):**

```text
KEKULE INITIALIZATION FOR AROMATIC RINGS
    
Ring 1 (5-membered): ['C7', 'C13', 'C11', 'C9', 'C8']
      ✓ Detected Cp-like ring (all 5 C bonded to Fe0)
      π electrons estimate: 6
    
Ring 2 (6-membered): ['C37', 'C39', 'C41', 'C43', 'C45', 'C36']
      π electrons estimate: 6
    
Ring 3 (6-membered): ['C34', 'C32', 'C30', 'C28', 'C26', 'C25']
      π electrons estimate: 6
    
Ring 4 (6-membered): ['C55', 'C53', 'N6', 'C52', 'C58', 'C57']
      π electrons estimate: 6
    
Ring 5 (5-membered): ['C15', 'C17', 'C19', 'C21', 'C23']
      ✓ Detected Cp-like ring (all 5 C bonded to Fe0)
      π electrons estimate: 6
  
------------------------------------------------------------
  SUMMARY: Initialized 5 ring(s) with Kekulé pattern
------------------------------------------------------------

BEAM SEARCH OPTIMIZATION (width=5)
  Locked 16 metal bonds
  Initial score: 456.70
  
Iteration 1:
      Generated 2 candidates, keeping top 2
      ✓ New best: O3-C64      Δtotal =  81.00  score =   375.70
  
Iteration 2:
      Generated 4 candidates, keeping top 4
      ✓ New best: O4-C65      Δtotal =  81.00  score =   294.70
  
Iteration 3:
      Generated 6 candidates, keeping top 5
      ✓ New best: O3-C64      Δtotal =  20.00  score =   274.70
  
Iteration 4:
      Generated 5 candidates, keeping top 5
      ✓ New best: O4-C65      Δtotal =  20.00  score =   254.70
  
Iteration 5:
      No improvements found in any beam, stopping
  
------------------------------------------------------------
  Explored 181 states across 5 iterations
  Found 4 improvements
  Score: 456.70 → 254.70
------------------------------------------------------------

FORMAL CHARGE CALCULATION
    
Initial formal charges:
        Sum: -3 (target: +0)
      
  Metal coordination summary:
        
[  0] Fe  oxidation_state=+2  coordination=10
          • 5-ring (-1)  [donor: C13]
          • 5-ring (-1)  [donor: C19]
        
[  1] Mn  oxidation_state=+1  coordination=6
          •      H (-1)  [donor: H67]
          •     CO ( 0)  [donor: C64]
          •     CO ( 0)  [donor: C65]
          •      N ( 0)  [donor: N6]
          •      P ( 0)  [donor: P2]
          •      N ( 0)  [donor: N5]
    
Metal complex detected: 
        Residual: +3 (represents metal oxidation states)

AROMATIC RING DETECTION (Hückel 4n+2)
  
Ring 1 (5-membered): ['C7', 'C13', 'C11', 'C9', 'C8']
    π electrons: 6 (C7:1, C13:1, C11:1, C9:1, C8:1+1(charge))
    ✓ AROMATIC (4n+2 rule: n=1)
  
Ring 5 (5-membered): ['C15', 'C17', 'C19', 'C21', 'C23']
    π electrons: 6 (C15:1, C17:1, C19:1, C21:1, C23:1+1(charge))
    ✓ AROMATIC (4n+2 rule: n=1)

------------------------------------------------------------
  SUMMARY: 5 aromatic rings, 28 bonds set to 1.5
------------------------------------------------------------

# Selected atoms from molecular graph:
[  0] Fe  val=10.00  metal=0.00  formal=0   | 7(1.00) 8(1.00) 9(1.00) 11(1.00) 13(1.00) ...
[  1] Mn  val=6.00  metal=0.00  formal=0   | 2(1.00) 5(1.00) 6(1.00) 64(1.00) 65(1.00) 67(1.00)
[  3]  O  val=3.00  metal=0.00  formal=+1  | 64(3.00)
[  4]  O  val=3.00  metal=0.00  formal=+1  | 65(3.00)
[  8]  C  val=4.00  metal=1.00  formal=-1  | 0(1.00) 7(1.50*) 9(1.50*) 47(1.00)
[ 23]  C  val=4.00  metal=1.00  formal=-1  | 0(1.00) 15(1.50*) 21(1.50*)
[ 64]  C  val=3.00  metal=1.00  formal=-1  | 1(1.00) 3(3.00)
[ 65]  C  val=3.00  metal=1.00  formal=-1  | 1(1.00) 4(3.00)
[ 67]  H  val=0.00  metal=1.00  formal=-1  | 1(1.00)
```

**ASCII Depiction:**
>[!TIP]
> Don't look at this in too much detail, not good for complex molecular visualisation...
```text
            C---------C
           /           \
           /            \               C--
          /              \            //   ----
         /                \         //         --C
         /                 C      //             |
        C                 /      C                |
         \               /       |                |
          \             /         |               |
           \            /         |   O            |
            \          /          |  #             C
             C--------C            |#            //
                       \          #C--         //
                        \        //   ----   //
                         \\    /C       H --C     C---------C                  C
      C----                \ // \      /         /           \                /
     / \   -----C         --P    \    /   C#####/             \              /
  C----\---    /\     ----   \\   \   / //     /####O         \             /
  |\\\  \  --//----C--         \\ \  ///      /                \           /
 /|   \  \  /  ---\|             \\ //   ----N                  C---------N
C----- \\\ /---   |                Mn----     \                /           \
 |    ----Fe---   |                |           \              /            \
 |  ---- /|\\  ----C               |           \             /              \
 C--    /|   \\---|                |             \           /                \
  \\  // |---- \\|                |              C---------C                 \
   \\/---|     --C\               |             /                             C
    C-\\|  ----    \\\          --N-          //
        C--           \\    ----  | ---      /
                        \C--      |    ---  /
                         |        |       -C
                         |        |
                        |         |
                        |         H
                        |
                        C
```

![mnh](examples/mnh.svg)

**Analysis:**
- **Ferrocene fragment:** Fe(II) coordinated to two Cp⁻ ligands (η⁵ coordination)
- **Cp rings:** Detected as aromatic with 6 π electrons (includes -1 charge contribution from each ring)
- **Manganese center:** Mn(I) with octahedral-like coordination
  - Hydride (H⁻) ligand correctly identified (formal charge -1)
  - Two CO ligands with C≡O triple bonds (formal charges: C: -1, O: +1), net neutral ligand
  - Phosphine (P) and amine (N) dative bond donors
- **Charge balance:** System is neutral (Fe(II) + Mn(I) - 2×Cp⁻ - H⁻ = 0)

---

### Example 2: Organic Cation (Acyl Isothiouronium)

This example shows aromatic detection, formal charge assignment, and handling of heteroaromatic systems.

**System:** Acyl isothiouronium cation (quaternary nitrogen)  
**File:** `examples/isothio.xyz` (52 atoms, +1 charge)

**Command:**
```bash
xyzgraph examples/isothio.xyz --charge 1 --ascii --debug
```

**Key Features:**
- Benzene ring aromatic detection
- 5-membered heterocycle evaluation (thiazole-like ring)
- Formal charge on quaternary nitrogen (N⁺)
- Beam search optimization of carbonyl bond order

**Output (truncated):**

```text
> xyzgraph examples/isothio.xyz -a -d -as 2 --charge 1

============================================================
KEKULE INITIALIZATION FOR AROMATIC RINGS
============================================================
    
Ring 1 (6-membered): ['C24', 'C23', 'C22', 'C21', 'C26', 'C25']
      π electrons estimate: 6
       
Ring 4 (6-membered): ['C8', 'C9', 'C10', 'C11', 'C12', 'C7']
      π electrons estimate: 6
  
------------------------------------------------------------
  SUMMARY: Initialized 2 ring(s) with Kekulé pattern
------------------------------------------------------------

============================================================
BEAM SEARCH OPTIMIZATION (width=5)
============================================================
  Initial score: 657.00
  
Iteration 1:
      Generated 3 candidates, keeping top 3
      ✓ New best: C1-C2       Δtotal =  72.00  score =   585.00
  
Iteration 2:
      Generated 5 candidates, keeping top 5
      ✓ New best: N18-C19     Δtotal = 116.50  score =   468.50
  
Iteration 3:
      Generated 4 candidates, keeping top 4
      ✓ New best: O0-C1       Δtotal =  71.00  score =   397.50
  
Iteration 4:
      No improvements found in any beam, stopping
  
Applying best solution to graph...
------------------------------------------------------------
  Explored 148 states across 4 iterations
  Found 3 improvements
  Score: 657.00 → 397.50
------------------------------------------------------------

============================================================
FORMAL CHARGE CALCULATION
============================================================
    
Initial formal charges:
        Sum: +1 (target: +1)
        Charged atoms:
            N18: +1
    
No residual charge distribution needed (sum matches target)

============================================================
AROMATIC RING DETECTION (Hückel 4n+2)
============================================================
  
Ring 1 (6-membered): ['C24', 'C23', 'C22', 'C21', 'C26', 'C25']
    π electrons: 6 (C24:1, C23:1, C22:1, C21:1, C26:1, C25:1)
    ✓ AROMATIC (4n+2 rule: n=1)
  
Ring 2 (5-membered): ['N18', 'C19', 'S20', 'C21', 'C26']
    π electrons: 7 (N18:2(LP), C19:1, S20:2(LP), C21:1, C26:1)
    ✗ Not aromatic (4n+2 rule violated)
  
Ring 3 (6-membered): ['N18', 'C17', 'C13', 'C6', 'N5', 'C19']
    ✗ Not planar, skipping aromaticity check
  
Ring 4 (6-membered): ['C8', 'C9', 'C10', 'C11', 'C12', 'C7']
    π electrons: 6 (C8:1, C9:1, C10:1, C11:1, C12:1, C7:1)
    ✓ AROMATIC (4n+2 rule: n=1)

------------------------------------------------------------
  SUMMARY: 2 aromatic rings, 12 bonds set to 1.5
------------------------------------------------------------

    Gasteiger charge calculation failed: Explicit valence for atom # 18 N, 4, is greater than permitted

============================================================
GRAPH CONSTRUCTION COMPLETE
============================================================

# Molecular Graph: 52 atoms, 55 bonds
# total_charge=1  multiplicity=1  sum(gasteiger)=+1.000  sum(gasteiger_raw)=+0.000
# (C–H hydrogens hidden; heteroatom-bound hydrogens shown; valences still include all H)
# [idx] Sym  val=.. metal=.. formal=.. chg=.. agg=.. | neighbors: idx(order / aromatic flag)
# (val = organic valence excluding metal bonds; metal = metal coordination bonds)
[  0]  O  val=2.00  metal=0.00  formal=0   chg=+0.019  agg=+0.019 | 1(2.00)
[  1]  C  val=4.00  metal=0.00  formal=0   chg=+0.019  agg=+0.019 | 0(2.00) 2(1.00) 5(1.00)
[  5]  N  val=3.00  metal=0.00  formal=0   chg=+0.019  agg=+0.019 | 1(1.00) 6(1.00) 19(1.00)
[ 18]  N  val=4.00  metal=0.00  formal=+1  chg=+0.019  agg=+0.019 | 17(1.00) 19(2.00) 26(1.00)
[ 19]  C  val=4.00  metal=0.00  formal=0   chg=+0.019  agg=+0.019 | 5(1.00) 18(2.00) 20(1.00)
[ 20]  S  val=2.00  metal=0.00  formal=0   chg=+0.019  agg=+0.019 | 19(1.00) 21(1.00)
```

**ASCII Depiction:**
```text
                            C
                           /
                         //
                        C\
                         \\
                         \\
                         /C\
                        /
               O======C/
               ========\
   /C------C           \           /S-
  /         \           N---     //   ---     --C\
C/          \         //    ---C\        -C---    \\
\           \        /          \\       /          \C
 \          /C------C           \\       /          /
  \        /         \           N\-----C           /
  C------C/          \         //        \\         /
                      C---    /            \    ---C
                    //    ---C              C---
           C---    /
               ---C
                   \
                   \
                    C
```

![isothiouronium](examples/isothio.svg)

**Analysis:**
- **Benzene rings:** Two rings correctly identified as aromatic (bond order 1.5)
- **5-membered heterocycle:** N-C-S-C-C ring retains Kekulé structure with N=C double bond
- **Quaternary nitrogen:** N16 assigned +1 formal charge (4 bonds, no lone pairs)
- **a,b-unsaturated:** O=C and C=C double bonds correctly optimized

---

## Bond Detection Thresholds

xyzgraph uses distance-based bond detection with thresholds derived from van der Waals (vdW) radii by Charry and Tkatchenko [[1]](https://doi.org/10.1021/acs.jctc.4c00784). By default, these thresholds are calibrated for different atom pair types:

| Atom Pair Type | Default Threshold | Parameter Name |
|---------------|-------------------|----------------|
| H-H | 0.38 × (r₁ + r₂) | `threshold_h_h` |
| H-nonmetal | 0.42 × (r₁ + r₂) | `threshold_h_nonmetal` |
| H-metal | 0.48 × (r₁ + r₂) | `threshold_h_metal` |
| Metal-ligand | 0.6 × (r₁ + r₂) | `threshold_metal_ligand` |
| Nonmetal-nonmetal | 0.55 × (r₁ + r₂) | `threshold_nonmetal_nonmetal` |

Where r₁ and r₂ are the VDW radii of the two atoms.

### Modification (Not Recommended)

**Global Scaling**:  

- The `--threshold` (or `threshold` in Python) parameter provides a simple way to globally scale **all** thresholds.  
- This is safer than modifying individual thresholds.  
- e.g. `--threshold 1.1`  
  - threshold_h_nonmetal × (r₁ + r₂) × **1.1**

> [!WARNING]  
> *these are **unstable** at >1.3*

**Individual Scaling**:

These parameters are exposed for users who need to:

- Handle unusual bonding situations not covered by defaults  
- Specifically wish to obtain dense connectivity  
- Fine-tune bond detection for specific molecular systems  
- Debug or validate bond detection behavior  

Can be performed using the cli *e.g.* `--threshold_h_nonmetal 0.5` or directly in python within `build_graph(threshold_h_nonmetal=0.5)`

> [!WARNING]  
> Modifying these thresholds is **not recommended** unless you have a specific reason and understand the implications  
> Changing values can produce *chemically invalid structures*

---

## References

1. **van der Waals Radii**: Jorge Charry and Alexandre Tkatchenko, *J. Chem. Theory Comput.*, 2024, **20**, 7469–7478. [DOI](https://doi.org/10.1021/acs.jctc.4c00784).

2. **xTB (Extended Tight Binding)**: Christoph Bannwarth, Sebastian Ehlert, and Stefan Grimme, *J. Chem. Theory Comput.* 2019, **15**, 1652–1671. [DOI](https://pubs.acs.org/doi/10.1021/acs.jctc.8b01176). [Repo](https://github.com/grimme-lab/xtb).

3. **xyz2mol**: Jan Jensen *et al.*, [xyz2mol](https://github.com/jensengroup/xyz2mol). Now integrated into RDKit as `Chem.rdDetermineBonds.DetermineBonds()`. See also Y. Kim, W. Y. Kim, *Bull. Korean Chem. Soc.*, 2015, **36**, 1769–1777.

4. **RDKit**: RDKit: Open-source cheminformatics. [https://www.rdkit.org](https://www.rdkit.org). [Repo](https://github.com/rdkit).

5. **moltext**: A. White, *moltext*. [Repo](https://github.com/whitead/moltext)

---

## Contributing & Contact

Contributions welcome! Please open an issue or pull request and get in touch with any questions [here](https://github.com/aligfellow/xyzgraph/issues).
