import os
import re
import numpy as np
from rdkit import Chem
from openbabel import pybel
from .geometry import Geometry

class StructureIO:
    def __init__(self, input):
        self.input = input
        self.basename = os.path.basename(self.input)
        self.format = os.path.splitext(self.basename)[1].replace(".", "")
        
    def get_input(self):
        return self.input
    
    def set_input(self, input):
        self.input = input
        self.basename = os.path.basename(self.input)
    
    def get_basename(self):
        return self.basename
        
    def get_format(self):
        return self.format
    
    def set_format(self, format):
        self.format = format
    
    # load mol object
    def file2mol(self, removeHs=False):
        mol = next(pybel.readfile(self.format, self.input))
        mol_block = mol.write("mol").strip()
        rdmol = Chem.MolFromMolBlock(mol_block, removeHs=removeHs)
        return rdmol
        
    # load mol object by string
    def str2mol(self, removeHs=False):
        mol = pybel.readstring(self.format, self.input)
        
        mol_block = mol.write("mol").strip()
        rdmol = Chem.MolFromMolBlock(mol_block, removeHs=removeHs)
        return rdmol
        
        

class GinpIO:
    def __init__(self, coords, args):
        self.coords = coords
        self.args = args
        self.basename = os.path.splitext(os.path.basename(args.input))[0]
        self.suffix = args.suffix
        self.output = args.output if args.output is not None else f"{self.basename}{self.suffix}.{args.ext}"
        
    def get_basename(self):
        return self.basename
    
    def get_output(self):
        return self.output
    
    # symbol spacing
    def spacer_symbol(self, symbol):
        constant_space = " " * 4
        if len(symbol) > 1:
            return f" {symbol}" + constant_space
        return f" {symbol} " + constant_space

    # coordinate spacing
    def spacer_coord(self, pos):
        digit = len(str(abs(int(pos))))
        space = " " * (5 - digit)
        if pos < 0:
            return space + f"{pos:.6f}"
        return space + f" {pos:.6f}"
        
    # format
    def formatted_coords(self):
        coords_strs = []
        for c in self.coords:
            s = self.spacer_symbol(c[0])
            x = self.spacer_coord(c[1])
            y = self.spacer_coord(c[2])
            z = self.spacer_coord(c[3])
            coords_strs.append(s + x + y + z)
        return coords_strs
        
    # generate gaussian input writelines
    def writelines(self):
        chk = f"{self.basename}{self.suffix}.chk"
        title = f"{self.basename} | TD-DFT ROOT={self.args.root}{' OPT' if self.args.opt else ''}"
        args = self.args
        
        basis = args.basis if args.ecp is None else "genecp"
        opt = f" opt" if args.opt else ""
        scf = f" scf={args.scf}" if args.scf is not None else ""
        verbose = "p" if args.verbose == 1 else ""
            
        header = [
            f"%chk={chk}",
            f"#{verbose} {args.functional}/{basis} td=(root={args.root}, nstate={args.nstate}){opt}{scf}",
            "",
            f"{title}",
            "",
            f"{args.charge} {args.multiplicity}"
        ]
        
        coords = self.formatted_coords()
        if args.ecp is not None:
            ecp_atoms = [
                "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
                "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
                "La", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
                "Tl", "Pb", "Bi", "Po", "At", "Rn",
            ]
            atom_list = list(set([c.split()[0] for c in coords]))
            assign_ecp_atoms = ""
            other_atoms = ""
            
            for atom in atom_list:
                if atom in ecp_atoms:
                    assign_ecp_atoms += f"{atom} "
                elif atom != "Bq":
                    other_atoms += f"{atom} "
            
            basis_set_block = [
                assign_ecp_atoms + "0",
                args.ecp,
                "****",
                other_atoms + "0",
                args.basis,
                "****",
            ]
            
            ecp_block = [
                assign_ecp_atoms + "0",
                args.ecp,
            ]
            
            coords += [""] + basis_set_block + [""] + ecp_block
        
        wl = header + coords + ["", ""]
        return wl
        
    # save gaussian input
    def save(self):
        wl = self.writelines()
        with open(self.output, "w") as f:
            f.writelines(f"{line}\n" for line in wl)



class GoutIO:
    def __init__(self, args):
        self.args = args
        self.basename = os.path.splitext(os.path.basename(args.input))[0]
        
    def get_basename(self):
        return self.basename
    
    # get output readlines
    def readlines(self):
        with open(self.args.input, "r") as f:
            rl = f.readlines()
        return rl
        
    # get input orientation in gout
    def get_coords(self):
        start_flag_ptn = re.compile(r"^\s*Input orientation:")
        end_flag_ptn = re.compile(r"^\s*------*")
        pt = Chem.GetPeriodicTable()
        rl = self.readlines()
        
        # capture coordinate
        match_lns = [ln for ln, line in enumerate(rl) if start_flag_ptn.match(line) is not None]
        
        # start line number
        start_lns = [ln + 4 for ln in match_lns]
        coord_strs = []
        
        # extract coordinate
        for start_ln in start_lns:
            coord_strs = []
            ln = start_ln
            end_flag_match = False
            while True:
                ln += 1
                if end_flag_ptn.match(rl[ln]):
                    end_flag_match = True
                if end_flag_match:
                    break
                coord_strs.append(rl[ln])
        
        coords_gau = [(char.split()) for char in coord_strs]
        coords = [(int(c[0]), pt.GetElementSymbol(int(c[1])), float(c[3]), float(c[4]), float(c[5])) for c in coords_gau]
        
        return coords
    
    def get_geometry(self):
        # get coordinate
        coords = self.get_coords()
        
        coords_str = f"{len(coords)}\ntitle\n" + "\n".join([f"{s}    {x}    {y}    {z}" for _, s, x, y, z in coords])
        
        # generate mol file
        sio = StructureIO("")
        sio.set_format("xyz")
        sio.set_input(coords_str)
        mol = sio.str2mol()
        
        # init geometry
        geom = Geometry(mol, self.args)
        return geom
