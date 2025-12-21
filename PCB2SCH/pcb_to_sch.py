import skip, sys
from sexpdata import Symbol as SexpSymbol
from functools import cmp_to_key

ORIGIN = (20, 20)
UNITSIZE = 2.54
HORIZ_SIZE = 20 # Number of components horizontally
HORIZ_SPACE = UNITSIZE * 7
VERT_SPACE  = UNITSIZE * 7
PCB_FILEPATH = "/home/max/Documents/KiCad/SEM-Vacuum/Vacuum.kicad_pcb"
SCH_FILEPATH = "/home/max/Documents/KiCad/SEM-Vacuum/Vacuum.kicad_sch"

# Use this to set a template for components. For example, to set how a resistor appears,
# create a resistor with reference 'Rref'. If there is no template for a component, the
# program will look for a 'Symbol' property, which should contain a symbol identifier (e.g. 74xx:74LS20).
templates = {'R': None, 'D': None}

schem = skip.Schematic(SCH_FILEPATH)
pcb = skip.PCB(PCB_FILEPATH)

def get_coords(count: int):
  return ((count % HORIZ_SIZE) * HORIZ_SPACE + ORIGIN[0], int((count / HORIZ_SIZE)) * VERT_SPACE + ORIGIN[1])

def compare_symbols(sym1, sym2):
  ltr1 = ''.join(filter(str.isalpha, sym1.Reference.value))
  ltr2 = ''.join(filter(str.isalpha, sym2.Reference.value))
  num1 = int(''.join(filter(str.isdigit, sym1.Reference.value)) or 0)
  num2 = int(''.join(filter(str.isdigit, sym2.Reference.value)) or 0)
  
  if ltr1 == ltr2:
    if num1 == num2:
      return sym1.unit.value - sym2.unit.value
    else:
      return num1 - num2
  elif ltr1 > ltr2:
    return 1
  else:
    return -1

ignored_symbols = []

# Assign templates
for t in templates:
  match = schem.symbol.reference_matches(t + 'ref')
  if match:
    templates[t] = match[0]
    ignored_symbols.append(t + 'ref')
  else:
    print(f"Error: Missing template for {t}. Please create a symbol with reference \"{t}ref\".")
    sys.exit(1)

count = 0
wip_symbols = []
for f in pcb.footprint:
  ref = f.property.Reference.value
  val = f.property.Value.value
  
  if len(ref) > 0:
    
    # Update existing symbols
    existing = schem.symbol.reference_matches(ref)
    if existing:
      existing[0].Value = val
      ignored_symbols.append(ref)
      continue
      
    
    if ref[0] in templates:
      clone = templates[ref[0]].clone()
      clone.setAllReferences(ref)
      clone.Value = val
      
      clone.move(*get_coords(count))
    
    elif 'Symbol' in f.property:
      if ref == 'IC30':
        pass
      sym = skip.Symbol.from_lib(schem, f.property.Symbol.getValue(), ref, *get_coords(count), 1)
      wip_symbols.append(sym.Reference.value) # List of symbols that need further handling
    
    else:
      print(f"Warning: Invalid footprint: {ref}")
      
    count += 1
  else:
    print("Warning: Footprint has missing reference")
  
schem.write(SCH_FILEPATH)

input("""
First phase complete. Please open the schematic in KiCad 
and go to 'Tools'->'Update Symbols from Library'.
Check 'Update all symbols in schematic' and hit 'Update'.
Save the file and hit enter here: """)

schem.reload()

# Add all of the unplaced units
for ref in wip_symbols:
  symbol = schem.symbol.reference_matches(ref)[0]
  if symbol.lib_symbol and 'symbol' in symbol.lib_symbol:
    
    num_units = int(len(symbol.lib_symbol.symbol) / 2) # For some reason every symbol has two library symbols
    if num_units > 1:
      for unit in range(2, num_units + 1):
        # Add missing units
        skip.Symbol.from_lib(schem, symbol.lib_id.value, ref, *get_coords(count), unit)
        count += 1
  else:
    print(f"Warning: Library did not load for {ref}. Please check in KiCad.")

# Rearrange all of the symbols
count = 0
sorted_symbols = sorted(filter(lambda s : s.Reference.value not in ignored_symbols, schem.symbol), key=cmp_to_key(compare_symbols))
for symbol in sorted_symbols:
    symbol.move(*get_coords(count))
    count += 1

schem.write(SCH_FILEPATH)
print("Second phase complete. Reload schematic in KiCad.")
