# ---------------------------------------------------------------------------
# @author Shota Inoue
# @date   2025-10-19
# @email  inoue.shota@st.kitasato-u.ac.jp
#
# Generate gaussian input for TD-DFT calculation by molecule structure file.
#
# Package dependencies:
#    - NumPy
#    - RDKit
#    - OpenBabel
#      - eigen
# ---------------------------------------------------------------------------

from .lib.geometry import Geometry
from .lib.io import StructureIO, GinpIO

# main function
def main(args):
    # make RDKit mol object
    sio = StructureIO(args.input)
    mol = sio.file2mol()
    
    # init geometry
    geom = Geometry(mol, args)
    
    # generate all coordinate
    original_coords = geom.original_atoms_coords()
    
    # init input file i/o
    ginpio = GinpIO(original_coords, args)
    
    # save gaussian com file
    ginpio.save()
    
    # notice
    print(f"Generate TD-DFT calculation file: {ginpio.get_output()}")

# execute
if __name__ == "__main__":
    main()
