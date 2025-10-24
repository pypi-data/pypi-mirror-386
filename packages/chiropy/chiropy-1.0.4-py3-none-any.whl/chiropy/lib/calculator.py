import re
import numpy as np
from rdkit import Chem
from rdkit.Chem import Draw
import networkx as nx
import sys

class Calculator:
    def __init__(self, goutio, args):
        self.goutio = goutio
        self.args = args
        
    # get etdm data
    def etdm(self):
        rl = self.goutio.readlines()
        geom = self.goutio.get_geometry()
        
        in_block = False
        dipole_data = []

        for line in rl:
            if "Ground to excited state transition electric dipole moments" in line:
                in_block = True
                continue
            
            if in_block:
                if re.match(r'^\s*state', line):
                    continue
                if re.match(r'^\s*Ground to excited state transition velocity dipole moments', line):
                    in_block = False
                
                m = re.match(
                    r'^\s*(\d+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)',
                    line
                )
                if m:
                    state = int(m.group(1))
                    x = float(m.group(2))
                    y = float(m.group(3))
                    z = float(m.group(4))
                    dip_s = float(m.group(5))
                    osc = float(m.group(6))
                    dipole_data.append({
                        "state": state,
                        "x": x,
                        "y": y,
                        "z": z,
                        "dip_s": dip_s,
                        "osc": osc
                    })
        
        max_state = max([d["state"] for d in dipole_data])
        
        return dipole_data[-max_state:]

    # get mtdm data
    def mtdm(self):
        rl = self.goutio.readlines()
        geom = self.goutio.get_geometry()
        
        in_block = False
        dipole_data = []

        for line in rl:
            if "Ground to excited state transition magnetic dipole moments" in line:
                in_block = True
                continue
            
            if in_block:
                if re.match(r'^\s*state', line):
                    continue
                if re.match(r'^\s*Ground to excited state transition velocity quadrupole moments', line):
                    in_block = False
                
                m = re.match(
                    r'^\s*(\d+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)\s+([-\d\.Ee]+)',
                    line
                )
                if m:
                    state = int(m.group(1))
                    x = float(m.group(2))
                    y = float(m.group(3))
                    z = float(m.group(4))
                    dipole_data.append({
                        "state": state,
                        "x": x,
                        "y": y,
                        "z": z,
                    })
        max_state = max([d["state"] for d in dipole_data])

        return dipole_data[-max_state:]

    # etdm vector
    def etdm_vec(self, state):
        try:
            etdm = self.etdm()
            data = etdm[state - 1]
        except:
            print("State number is invalid.")
            sys.exit(0)
        return np.array([data["x"], data["y"], data["z"]])

    # mtdm vector
    def mtdm_vec(self, state):
        try:
            mtdm = self.mtdm()
            data = mtdm[state - 1]
        except:
            print("State number is invalid.")
            sys.exit(0)
        return np.array([data["x"], data["y"], data["z"]])

    # E-M angle
    def em_angle(self, state, rad=False):
        etdm_vec = self.etdm_vec(state)
        mtdm_vec = self.mtdm_vec(state)
        
        dot = np.dot(etdm_vec, mtdm_vec)
        norm_etdm = np.linalg.norm(etdm_vec)
        norm_mtdm = np.linalg.norm(mtdm_vec)
        
        if norm_etdm * norm_mtdm == 0:
            return None
        
        cos_theta = dot / (norm_etdm * norm_mtdm)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)

        theta = np.arccos(cos_theta)
        if rad:
            return theta
        theta = np.degrees(theta)
        return theta
    
    # g-factor
    def g_fac(self, state):
        theta = self.em_angle(state, rad=True)
        
        if theta is None:
            return None
        
        etdm_vec = self.etdm_vec(state)
        mtdm_vec = self.mtdm_vec(state)
        norm_etdm = np.linalg.norm(etdm_vec)
        norm_mtdm = np.linalg.norm(mtdm_vec)
        
        val = (4 * norm_etdm * norm_mtdm * np.cos(theta)) / (norm_etdm ** 2 + norm_mtdm ** 2)
        return val
