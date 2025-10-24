import argparse as ap
import fnmatch
from . import ginp
from . import gout

# extension validator
def ext_validator(ptns):
    def extension(val):
        for ptn in ptns:
            if fnmatch.fnmatch(val, ptn):
                return val
        raise ap.ArgumentTypeError(f"{val} is an invalid extension file.")
    return extension
    
# negative values validator
def neg_validator(val):
    fval = int(val)
    if fval >= 0:
        return fval
    raise ap.ArgumentTypeError(f"{val!r} is not positive.")

# multiplicity
def mul_validator(val):
    try:
        ival = int(val)
    except ValueError:
        raise ap.ArgumentTypeError(f"{val!r} is not a valid integer.")

    if ival == 1 or ival == 2 or ival == 3:
        return ival
    raise ap.ArgumentTypeError(f"{ival} is an invalid multiplicity value.")

# main function (command line parser)
def main():
    parser = ap.ArgumentParser(
        prog="chiropy",
        description="Gaussian binding tool for analyze chiroptical properties."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ginp.py
    ptns_ginp = ["*.mol", "*.mol2", "*.sdf", "*.xyz", "*.pdb", "*.cif", "*.out", "*.log"]
    ptns_ginpout = ["*.gjf", "*.com"]
    
    parser_ginp = subparsers.add_parser("ginp", help="Generate TD-DFT calculation input.")
    parser_ginp.add_argument("-i", "--input", type=ext_validator(ptns_ginp), required=True, help="Path to molecule structure file.")
    parser_ginp.add_argument("-o", "--output", type=ext_validator(ptns_ginpout), help="Gaussian TD-DFT input file name.")
    parser_ginp.add_argument("-s", "--suffix", default="_tddft", help="Input file suffix.")
    parser_ginp.add_argument("-e", "--ext", choices=["gjf", "com"], default="gjf", help="Input file extension.")
    parser_ginp.add_argument("-f", "--functional", default="b3lyp", help="Gaussian DFT functional keyword.")
    parser_ginp.add_argument("-b", "--basis", default="6-31g(d)", help="Gaussian basis set keyword.")
    parser_ginp.add_argument("--ecp", help="Gaussian effective core potential keyword (automatic assignment to heavy atoms).")
    parser_ginp.add_argument("-c", "--charge", type=int, default=0, help="Gaussian molecule charge.")
    parser_ginp.add_argument("-m", "--multiplicity", type=mul_validator, default=1, help="Gaussian molecule multiplicity.")
    parser_ginp.add_argument("--nstate", type=neg_validator, default=3, help="Number of excited state.")
    parser_ginp.add_argument("--root", type=neg_validator, default=1, help="Excited state number under consideration.")
    parser_ginp.add_argument("--scf", help="Gaussian SCF condition.")
    parser_ginp.add_argument("--opt", action="store_true", help="Perform excited state optimization.")
    parser_ginp.add_argument("--verbose", type=int, choices=[0, 1], default=0, help="Gaussian output verbosity.")
    parser_ginp.set_defaults(func=ginp.main)

    # gout.py
    ptns_gout = ["*.out", "*.log"]
    
    parser_gout = subparsers.add_parser("gout", help="Analize TD-DFT calculation output.")
    parser_gout.add_argument("-i", "--input", type=ext_validator(ptns_gout), required=True, help="Gaussian TD-DFT calculation output.")
    parser_gout.add_argument("--state", type=neg_validator, default=1, help="Excited state number.")
    parser_gout.add_argument("--symbol", action="store_true", help="Display atom symbols instead of ball-and-stick model.")
    parser_gout.add_argument("--showh", action="store_true", help="Display hydrogen atoms.")
    parser_gout.add_argument("--notext", action="store_true", help="Do not display properties as text.")
    parser_gout.add_argument("--dark", action="store_true", help="Display result with darktheme.")
    parser_gout.add_argument("--image", action="store_true", help="Export properties on chemical structure to png file.")
    parser_gout.add_argument("--summary", action="store_true", help="Display summarized result on stdout.")
    parser_gout.set_defaults(func=gout.main)

    # execute
    args = parser.parse_args()
    args.func(args)



if __name__ == "__main__":
    main()
