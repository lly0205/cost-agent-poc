# -*- coding: utf-8 -*-
"""
Batch 2 outer perimeter calculation for 砼墙 retaining wall system
Building: 职工食堂及职工活动用房
Coordinate range: Y ~ -67,000 to -118,000
All dimensions in mm
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("Batch 2 Outer Perimeter Calculation — 砼墙 Retaining Wall System")
print("Building: 职工食堂及职工活动用房")
print("Y range: -67,000 to -118,000 (mm)")
print("=" * 70)

# ─────────────────────────────────────────────────
# NORTH WALL SEGMENTS (outermost Y ≈ -67,087)
# These are horizontal LINE segments on the north outer face
# ─────────────────────────────────────────────────
print("\n[ NORTH WALL — outer face Y ≈ -67,087 ]")

north_segments = [
    # (handle,  x_start,      x_end,        label)
    ("12881",  -4_821_195,   -4_813_295,    "7,900"),
    ("12883",  -4_812_795,   -4_804_795,    "8,000"),   # -4,804,795 per south reference; user states -4,804,345 for north
    ("12885",  -4_804_345,   -4_796_445,    "7,900"),   # Note: user gave -4,796,445 to -4,804,345
    ("1285C",  -4_795_945,   -4_791_945,    "4,000"),
    ("1285E",  -4_791_545,   -4_787_995,    "3,550"),
    ("12861",  -4_787_495,   -4_785_595,    "1,900"),
    ("12863",  -4_772_595,   -4_770_695,    "1,900"),
    ("12867",  -4_753_995,   -4_750_545,    "3,450"),
    # Eastern north segment (far east)
    ("1289B",  -4_720_295,   -4_711_895,    "8,400"),
]

# Restate with positive lengths (using abs of x difference)
north_data = []
for handle, x1, x2, label in north_segments:
    length = abs(x2 - x1)
    north_data.append((handle, min(x1, x2), max(x1, x2), length))
    print(f"  [{handle}] X: {min(x1,x2):,} → {max(x1,x2):,}  L = {length:,} mm")

north_explicit_total = sum(d[3] for d in north_data)
print(f"\n  Explicit segment total: {north_explicit_total:,} mm")

# Check for gap between 12867 (-4,753,995 to -4,750,545) and 1289B (-4,720,295 to -4,711,895)
# Gap: from -4,750,545 to -4,720,295 = 30,250mm — this gap in the north face likely corresponds
# to an internal recess or opening (possibly stairwell / elevator pit / different wall type)
gap_n1 = abs(-4_750_545 - (-4_770_695))   # between 12863 and 12867: -4,770,695 to -4,753,995 = 16,700
gap_n2 = abs(-4_720_295 - (-4_750_545))   # between 12867 and 1289B: 30,250mm
print(f"\n  Gap between 12863 and 12867: {gap_n1:,} mm  (X: -4,770,695 to -4,753,995)")
print(f"  Gap between 12867 and 1289B: {gap_n2:,} mm  (X: -4,750,545 to -4,720,295)")

# The gap of 30,250 mm between segment 12867 and 1289B is large — likely an opening
# in the north perimeter (courtyard / light-well / different structural zone)
# We will NOTE it but NOT add it to the perimeter (it is a void, not solid wall)

# West-most north segment starts at X = -4,821,195
# East-most north segment (1289B) ends at X = -4,711,895
north_overall_span = abs(-4_711_895 - (-4_821_195))
print(f"\n  Overall north span (west to east): {north_overall_span:,} mm = {north_overall_span/1000:.3f} m")

# ─────────────────────────────────────────────────
# SOUTH WALL SEGMENTS (outermost Y ≈ -118,087)
# ─────────────────────────────────────────────────
print("\n[ SOUTH WALL — outer face Y ≈ -118,087 ]")

south_segments = [
    ("128AD",  -4_821_195,   -4_813_295,    "7,900"),
    ("128AF",  -4_812_795,   -4_804_895,    "7,900"),
    ("128B3",  -4_804_395,   -4_796_495,    "7,900"),
    ("12875",  -4_795_995,   -4_791_945,    "4,050"),
    ("12877",  -4_791_545,   -4_787_995,    "3,550"),
    ("1286F",  -4_787_495,   -4_779_695,    "7,800"),
    ("128A3",  -4_779_195,   -4_771_195,    "8,000"),
    ("128A5",  -4_770_695,   -4_762_895,    "7,800"),
    ("128A7",  -4_762_395,   -4_754_445,    "7,950"),
    ("128A9",  -4_753_945,   -4_745_995,    "7,950"),
    ("12871",  -4_745_495,   -4_742_145,    "3,350"),
    ("12873",  -4_741_645,   -4_737_645,    "4,000"),
    ("128AB",  -4_737_145,   -4_729_245,    "7,900"),
]

south_data = []
for handle, x1, x2, label in south_segments:
    length = abs(x2 - x1)
    south_data.append((handle, min(x1, x2), max(x1, x2), length))
    print(f"  [{handle}] X: {min(x1,x2):,} → {max(x1,x2):,}  L = {length:,} mm")

south_total = sum(d[3] for d in south_data)
print(f"\n  South explicit segment total: {south_total:,} mm")

# South wall eastern end is at X = -4,729,245 (segment 128AB)
# East wall (L-shape) starts at X = -4,729,094 at Y = -78,887 and goes south to Y = -117,579
# These two x-values are very close (-4,729,245 vs -4,729,094) — essentially the same grid line
# The south wall ends where the east notch vertical begins

south_east_x = -4_729_245
print(f"\n  South wall eastern terminus: X = {south_east_x:,}")

# ─────────────────────────────────────────────────
# WEST WALL SEGMENTS (outermost X ≈ -4,821,695)
# ─────────────────────────────────────────────────
print("\n[ WEST WALL — outer face X ≈ -4,821,695 ]")

west_segments = [
    # (y_start, y_end, length_mm)
    # Going south (more negative Y)
    (-67_587,   -76_787,    9_200),
    (-77_287,   -80_737,    3_450),
    (-81_137,   -82_537,    1_400),
    (-82_937,   -86_287,    3_350),
    (-86_887,   -98_287,   11_400),
    (-98_787,  -102_137,    3_350),
    (-102_637, -107_887,    5_250),
    (-108_387, -117_587,    9_200),
]

west_total = 0
for y1, y2, length in west_segments:
    calc_len = abs(y2 - y1)
    print(f"  Y: {y1:,} → {y2:,}  stated={length:,}  calc={calc_len:,} mm")
    west_total += length

print(f"\n  West wall total: {west_total:,} mm")

# Verify west wall extent
west_y_north = -67_587
west_y_south = -117_587
west_span = abs(west_y_south - west_y_north)
print(f"  West wall Y span (north to south): {west_span:,} mm")

# Sum of gaps
west_gaps = west_span - west_total
print(f"  Gaps (window reveals, construction joints): {west_gaps:,} mm")

# ─────────────────────────────────────────────────
# EAST BOUNDARY — L-shaped step
# ─────────────────────────────────────────────────
print("\n[ EAST BOUNDARY — L-shaped step ]")

# The east boundary consists of:
# 1. North part: from north face (-67,087) going south to the step notch
#    at X = -4,711,895 (far eastern wall)
# 2. Horizontal step going west from X=-4,711,895 to X≈-4,729,094
# 3. South part: from step going further south at X≈-4,729,094 down to south face

# Segment 12879: East outer face at X=-4,711,895, Y=-77,287 to -79,237
east_seg_12879_length = abs(-79_237 - (-77_287))
print(f"\n  Segment [12879] at X=-4,711,895: Y=-77,287 → -79,237  L={east_seg_12879_length:,} mm")

# The east outer face at X=-4,711,895 must extend from the north outer face
# down to the step. Given:
# - North outer face: Y = -67,087
# - Top of step:      Y = -77,287 (where 12879 starts)
# Full eastern outer vertical: from -67,087 to -79,237
east_outer_vertical = abs(-79_237 - (-67_087))
print(f"  Full eastern outer vertical (Y: -67,087 → -79,237): {east_outer_vertical:,} mm")

# Horizontal step (notch going west)
# Segment 128B1: Y=-79,237, X from -4,728,744 to -4,711,895 = 16,849mm
east_step_horiz_128B1 = abs(-4_728_744 - (-4_711_895))
print(f"\n  Horizontal step [128B1] at Y=-79,237: X=-4,728,744 → -4,711,895  L={east_step_horiz_128B1:,} mm")

# Inner face of notch (Y=-78,887):
# from X=-4,712,195 to -4,729,094 = 16,899mm
# This is the inner (top) face of the step — NOT the outer perimeter
# For outer perimeter, use the OUTER bottom edge at Y=-79,237 → 128B1

# Eastern notch vertical (south part of the L step)
# At X = -4,729,094, going from Y=-78,887 to Y=-117,579
# For the OUTER perimeter, we use the outer face of this notch wall
# The outer face (further west/south) of this notch return is at X≈-4,729,094
east_notch_vertical = abs(-117_579 - (-79_237))
print(f"\n  Eastern notch vertical at X≈-4,729,094:")
print(f"  Y: -79,237 → -117,579  L={east_notch_vertical:,} mm")
# Note: the south wall ends at X=-4,729,245 and notch vertical is at X=-4,729,094
# Difference: 151mm — within wall thickness tolerance (same grid line)

# ─────────────────────────────────────────────────
# PERIMETER ASSEMBLY
# ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("OUTER PERIMETER ASSEMBLY")
print("=" * 70)

# The outer perimeter traces the outside of the entire wall system.
# Starting from northwest corner, going clockwise:
#
#  NW ──── North ──── NE corner ─ East outer vertical ─ Step horiz ─┐
#  │                                                                  │ (step)
#  West (vertical)                                      East notch vertical
#  │                                                                  │
#  SW ──── South (reversed, going east) ────────────────────────────┘
#
# Key: The north and south walls have GAPS (segments + gaps)
# The outer perimeter uses only the OUTER FACE of the enclosure,
# meaning the overall span (from westmost X to eastmost X) for H walls,
# and the full vertical span for V walls.
#
# HOWEVER: The north wall has a 30,250mm GAP between X=-4,750,545 and -4,720,295
# This gap means the north outer face is NOT continuous there —
# it could be an opening/notch/courtyard.
# For FORMWORK: we count actual wall faces, not voids.
# So we count only the solid wall segment lengths.

print("\n  Option A: Actual solid wall face lengths (for formwork)")
print("  (counts only where concrete wall actually exists)")

north_total_formwork = north_explicit_total
south_total_formwork = south_total
west_total_formwork = west_total

# For east boundary, we need to count the actual outer face perimeter:
# - East outer vertical: full height from north face to step bottom = 12,150mm
# - Step horizontal (outer bottom edge going west): 16,849mm
# - East notch outer vertical (going south): 38,342mm
east_outer_total = east_outer_vertical + east_step_horiz_128B1 + east_notch_vertical

print(f"\n  North wall (sum of solid segments): {north_total_formwork:,} mm  = {north_total_formwork/1000:.3f} m")
print(f"  South wall (sum of solid segments): {south_total_formwork:,} mm  = {south_total_formwork/1000:.3f} m")
print(f"  West wall  (sum of solid segments): {west_total_formwork:,} mm  = {west_total_formwork/1000:.3f} m")
print(f"  East boundary (L-shape):")
print(f"    - Outer vertical (N face→step):   {east_outer_vertical:,} mm")
print(f"    - Step horizontal (going west):    {east_step_horiz_128B1:,} mm")
print(f"    - Notch vertical (step→S face):    {east_notch_vertical:,} mm")
print(f"    East total:                        {east_outer_total:,} mm  = {east_outer_total/1000:.3f} m")

total_perimeter_A = north_total_formwork + south_total_formwork + west_total_formwork + east_outer_total
print(f"\n  TOTAL OUTER PERIMETER (Option A): {total_perimeter_A:,} mm")
print(f"                                    = {total_perimeter_A/1000:.3f} m")
print(f"                                    ≈ {total_perimeter_A/1000:.1f} m")

print("\n  Option B: Closed polygon outer perimeter (including north gap as void)")
print("  (traces the outer envelope, ignoring internal gaps)")

# For Option B (closed polygon approach):
# North: west face to east face = 4,821,195 - 4,711,895 = 109,300mm
# South: same span but only to eastern notch = 4,821,195 - 4,729,245 = 91,950mm
# West: north to south = 117,587 - 67,587 = 50,000mm
# East L-shape: already calculated

north_span_B = abs(-4_711_895 - (-4_821_195))  # full north outer span
south_span_B  = abs(-4_729_245 - (-4_821_195)) # south only to notch

print(f"\n  North span (W to E outer): {north_span_B:,} mm = {north_span_B/1000:.3f} m")
print(f"  South span (W to notch):   {south_span_B:,} mm = {south_span_B/1000:.3f} m")
print(f"  West span (N to S):        50,000 mm = 50.000 m  (Y: -67,587 to -117,587)")
print(f"  East L-boundary:           {east_outer_total:,} mm = {east_outer_total/1000:.3f} m")

total_perimeter_B = north_span_B + south_span_B + 50_000 + east_outer_total
print(f"\n  TOTAL OUTER PERIMETER (Option B): {total_perimeter_B:,} mm")
print(f"                                    = {total_perimeter_B/1000:.3f} m")

# ─────────────────────────────────────────────────
# DETAILED CHECK: North Gap Analysis
# ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("GAP ANALYSIS — North Wall")
print("=" * 70)

north_sorted = sorted(north_data, key=lambda x: x[1])  # sort by x_start
print("\nNorth segments sorted west to east:")
for i, (handle, x0, x1, length) in enumerate(north_sorted):
    print(f"  {i+1}. [{handle}] {x0:,} → {x1:,}  L={length:,}")
    if i > 0:
        gap = x0 - north_sorted[i-1][2]
        if gap > 100:
            print(f"     *** GAP before this segment: {gap:,} mm ***")

print("\nSouth segments sorted west to east:")
south_sorted = sorted(south_data, key=lambda x: x[1])
for i, (handle, x0, x1, length) in enumerate(south_sorted):
    print(f"  {i+1}. [{handle}] {x0:,} → {x1:,}  L={length:,}")
    if i > 0:
        gap = x0 - south_sorted[i-1][2]
        if gap > 100:
            print(f"     *** GAP before this segment: {gap:,} mm ***")

# ─────────────────────────────────────────────────
# SUMMARY FOR FORMWORK
# ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("FORMWORK QUANTITY SUMMARY")
print("=" * 70)
print("""
The retaining wall outer perimeter for formwork purposes:

INTERPRETATION:
  The wall system appears to be a non-rectangular layout with:
  - A continuous western wall (full height both sides)
  - North and south walls with construction joints / gaps (~500mm gaps
    between segments — these are wall panel joints, NOT openings)
  - An L-shaped eastern boundary with a recessed notch
  - A large gap in the north wall between X=-4,750,545 and -4,720,295
    (30,250mm) — this is likely an opening/stairwell/separate structure

FOR FORMWORK (Option A — actual concrete wall faces only):""")
print(f"  North wall face:  {north_total_formwork/1000:.2f} m")
print(f"  South wall face:  {south_total_formwork/1000:.2f} m")
print(f"  West wall face:   {west_total_formwork/1000:.2f} m")
print(f"  East boundary:    {east_outer_total/1000:.2f} m")
print(f"  ─────────────────────────────")
print(f"  TOTAL:            {total_perimeter_A/1000:.2f} m")
print(f"\nFOR CLOSED PERIMETER (Option B — outer envelope, fills gaps):")
print(f"  North wall span:  {north_span_B/1000:.2f} m")
print(f"  South wall span:  {south_span_B/1000:.2f} m")
print(f"  West wall span:   50.00 m")
print(f"  East boundary:    {east_outer_total/1000:.2f} m")
print(f"  ─────────────────────────────")
print(f"  TOTAL:            {total_perimeter_B/1000:.2f} m")

print("\n\nNote on ~500mm gaps between north/south segments:")
print("  These are likely wall construction joints or panel boundaries,")
print("  NOT actual openings. If so, north=109.30m, south=91.95m should")
print("  be used (the full outer span), yielding Option B = correct perimeter.")

print("\nNote on north 30,250mm gap (X: -4,750,545 to -4,720,295):")
print("  This is large enough to be a real opening (courtyard, stairwell).")
print("  Treat as void — do NOT add to formwork.")
