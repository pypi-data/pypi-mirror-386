# ---------------------------------------------------------------------------
# @author Shota Inoue
# @date   2025-10-19
# @email  inoue.shota@st.kitasato-u.ac.jp
#
# Analize gaussian output for TD-DFT calculation.
#
# Package dependencies:
#    - NumPy
#    - RDKit
#    - OpenBabel
#      - eigen
#    - NetworkX
#    - Matplotlib
# ---------------------------------------------------------------------------

from .lib.io import StructureIO, GoutIO
from .lib.calculator import Calculator
from .lib.visualizer import Visualizer
import numpy as np

# main function
def main(args):
    # init out file i/o
    goutio = GoutIO(args)
    
    # init chiroptical props calculator
    calc = Calculator(goutio, args)
    
    if not args.summary:
        # init visualizer
        vis = Visualizer(calc, args)
        
        # visualize chiroptical props
        vis.visualize()
    else:
        etdm = calc.etdm()
        mtdm = calc.mtdm()
        print("------------------------------------------------")
        print(" \033[1mState  |mu|    |m|    E-M/deg     g\033[0m")
        print("------------------------------------------------")
        for e, m in zip(etdm, mtdm):
            state = e["state"]
            norm_etdm = np.linalg.norm([e["x"], e["y"], e["z"]])
            norm_mtdm = np.linalg.norm([m["x"], m["y"], m["z"]])
            em_angle = calc.em_angle(state) or None
            g_fac = calc.g_fac(state) or None
            
            def format_f(val):
                if val is None:
                    return "None"
                return f"{val:.2f}"
                
            def format_e(val):
                if val is None:
                    return "None"
                return f"{val:.2e}"
            
            print(f" {state}\t{format_f(norm_etdm)}\t{format_f(norm_mtdm)}\t{format_f(em_angle)}\t{format_e(g_fac)}")
        print("------------------------------------------------")
# execute
if __name__ == "__main__":
    main()
