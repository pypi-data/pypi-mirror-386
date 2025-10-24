import os
import sys
from importlib.resources import files
import numpy as np
import networkx as nx
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.colors as mcl

class Visualizer:
    def __init__(self, calc, args):
        self.calc = calc
        self.args = args
        self.basename = os.path.splitext(os.path.basename(args.input))[0]
        
    def get_basename(self):
        return self.basename
        
    # visualize
    def visualize(self):
        atom_colors = {
            "H": "lightgray",
            "B": "pink",
            "C": "gray",
            "N": "blue",
            "O": "red",
            "F": "cyan",
            "Si": "lightblue",
            "P": "darkorange",
            "S": "yellow",
            "Cl": "green",
            "Se": "sandybrown",
            "Br": "salmon",
            "I": "blueviolet",
            "Sc": "#E6E6F2",
            "Ti": "#B3B3CC",
            "V": "#A680B3",
            "Cr": "#8A99C7",
            "Mn": "#9C4FA3",
            "Fe": "orange",
            "Co": "#4D80FF",
            "Ni": "#4FB34F",
            "Cu": "#C78033",
            "Zn": "#7D7FB0",
            "Y": "#94FFFF",
            "Zr": "#94E0E0",
            "Nb": "#73C2C2",
            "Mo": "#619999",
            "Tc": "#4D8080",
            "Ru": "#4069E0",
            "Rh": "#4069E0",
            "Pd": "silver",
            "Ag": "#BFBFBF",
            "Cd": "#57A6C2",
            "La": "#70B0F2",
            "Hf": "#4D8080",
            "Ta": "#4D8080",
            "W": "#1F1F1F",
            "Re": "#404040",
            "Os": "#4D4D4D",
            "Ir": "#808080",
            "Pt": "silver",
            "Au": "gold",
            "Hg": "#B3B3B3",
            "Tl": "#A8534D",
            "Pb": "#565656",
            "Bi": "#9E4F48",
            "Po": "#993333",
            "At": "#760076",
            "Rn": "#3FDFFF",
            "*": "purple",
        }
        
        background = "#000b29" if self.args.dark else "#ffffff"
        foreground = "#ffffff" if self.args.dark else "#000000"
        negative = "#7852dc" if self.args.dark else "#9900fa"
        positive = "#1e46b4" if self.args.dark else "#152eff"

        arial_path = files("chiropy.assets") / "Arial.ttf"
        arial = fm.FontProperties(fname=arial_path)
        
        plt.rcParams["font.family"] = arial.get_name()
        plt.rcParams["mathtext.fontset"] = "cm"

        plt.rcParams["figure.facecolor"] = background
        plt.rcParams["axes.facecolor"]   = background
        plt.rcParams["text.color"] = foreground
        plt.rcParams["axes.labelcolor"] = foreground
        plt.rcParams["xtick.color"] = foreground
        plt.rcParams["ytick.color"] = foreground
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")
        fig.canvas.manager.set_window_title(f"Visualizer | {self.args.input}")
        
        # get graph
        geom = self.calc.goutio.get_geometry()
        graph = geom.get_graph()

        # get nodes coordinate
        pos = nx.get_node_attributes(graph, "pos")
        symbols = nx.get_node_attributes(graph, "symbol")

        # draw nodes
        for i, (x, y, z) in pos.items():
            size = 100 if symbols[i] == "H" else 300
            fsize = 16 if symbols[i] == "H" else 24
            color = atom_colors[symbols[i]]
            
            # display node
            if symbols[i] != "*":
                if self.args.showh:
                    if self.args.symbol:
                        ax.text(x, y, z, symbols[i], c=color, fontsize=fsize, fontweight="bold", ha="center", va="center")
                    else:
                        ax.scatter(x, y, z, s=size, c=color)
                elif symbols[i] != "H":
                    if self.args.symbol:
                        ax.text(x, y, z, symbols[i], c=color, fontsize=fsize, fontweight="bold", ha="center", va="center")
                    else:
                        ax.scatter(x, y, z, s=size, c=color)

        # draw edges
        nodes = graph.nodes(data=True)
        for i, j, data in graph.edges(data=True):
            symbol_i = nodes[i]["symbol"]
            symbol_j = nodes[j]["symbol"]
            
            # skip display hydrogen
            if not self.args.showh and (symbol_i == "H" or symbol_j == "H"):
                continue
            
            x = [pos[i][0], pos[j][0]]
            y = [pos[i][1], pos[j][1]]
            z = [pos[i][2], pos[j][2]]
            
            if data["order"] == 3:
                ax.plot(x, y, z, color="gray", linewidth=7.5)
                bv = np.array([x[1] - x[0], y[1] - y[0], z[1] - z[0]])
                
                # normal vec
                tmp = np.array([0, 0, 1]) if not np.allclose(bv[:2], 0) else np.array([0, 1, 0])
                u = np.cross(bv, tmp)
                u /= np.linalg.norm(u)
                offset = 0.05
                for sft in [-offset, offset]:
                    s = np.array((x[0], y[0], z[0])) + sft * u
                    e = np.array((x[1], y[1], z[1])) + sft * u
                    ax.plot([s[0], e[0]], [s[1], e[1]], [s[2], e[2]], color=background, linewidth=1.5)
            elif data["order"] == 2:
                ax.plot(x, y, z, color="gray", linewidth=4.5)
                ax.plot(x, y, z, color=background, linewidth=1.5)
            elif data["order"] == 1.5:
                ax.plot(x, y, z, color="gray", linestyle=(0, (1, 1)), linewidth=4.5)
                ax.plot(x, y, z, color=background, linewidth=1.5)
            else:
                ax.plot(x, y, z, color="gray", linewidth=2)
                
        # draw transition moment vectors
        # get center of mass
        com_x, com_y, com_z = np.array(geom.mol_center_of_mass())
        
        # get etdm and mtdm
        etdm_x, etdm_y, etdm_z = self.calc.etdm_vec(self.args.state)
        mtdm_x, mtdm_y, mtdm_z = self.calc.mtdm_vec(self.args.state)
        scale = 2.0
        
        ax.quiver(com_x, com_y, com_z, scale * etdm_x, scale * etdm_y, scale * etdm_z, color=positive, arrow_length_ratio=0.2, linewidth=2)
        ax.quiver(com_x, com_y, com_z, scale * mtdm_x, scale * mtdm_y, scale * mtdm_z, color=negative, arrow_length_ratio=0.2, linewidth=2)
        
        # display prop values
        def format_f(val):
            if val is None:
                return "\mathrm{{None}}"
            return f"{val:.2f}\ \mathrm{{deg}}"
            
        def format_e(val):
            if val is None:
                return "\mathrm{{None}}"
            s = f"{val:.2e}"
            mantissa, exp = s.split("e")
            exp = int(exp)
            return f"{mantissa} \\times 10^{{{exp}}}"
            
        em_angle = format_f(self.calc.em_angle(self.args.state))
        g_fac = format_e(self.calc.g_fac(self.args.state))
        
        if not self.args.notext:
            ax.text2D(
                0.00,
                0.98,
                f"State {self.args.state}",
                transform=ax.transAxes,
                fontsize=26,
                color=foreground,
                fontweight="bold",
                verticalalignment="top",
                horizontalalignment="left",
            )
            
            ax.text2D(
                0.00,
                0.90,
                rf"$\theta_{{\mu m}} = {em_angle}$",
                transform=ax.transAxes,
                fontsize=20,
                color=foreground,
                verticalalignment="top",
                horizontalalignment="left",
            )
            
            ax.text2D(
                0.00,
                0.85,
                rf"$g = {g_fac}$",
                transform=ax.transAxes,
                fontsize=20,
                color=foreground,
                verticalalignment="top",
                horizontalalignment="left",
            )
            
            ax.text2D(
                1.00,
                0.90,
                rf"$|\boldsymbol{{\mu}}| = {np.linalg.norm([etdm_x, etdm_y, etdm_z]):.2f}$",
                transform=ax.transAxes,
                fontsize=20,
                color=positive,
                verticalalignment="top",
                horizontalalignment="right",
            )
            
            ax.text2D(
                1.00,
                0.85,
                rf"$|\boldsymbol{{m}}| = {np.linalg.norm([mtdm_x, mtdm_y, mtdm_z]):.2f}$",
                transform=ax.transAxes,
                fontsize=20,
                color=negative,
                verticalalignment="top",
                horizontalalignment="right",
            )
        
        x_max = np.max([item[1][0] for item in pos.items()])
        x_min = np.min([item[1][0] for item in pos.items()])
        y_max = np.max([item[1][1] for item in pos.items()])
        y_min = np.min([item[1][1] for item in pos.items()])
        z_max = np.max([item[1][2] for item in pos.items()])
        z_min = np.min([item[1][2] for item in pos.items()])
            
        ax.set_axis_off()
        ax.set_box_aspect([x_max - x_min, y_max - y_min, z_max - z_min])
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        plt.tight_layout()
        
        # show plot or save
        if self.args.image:
            imgname = f"{self.get_basename()}.png"
            plt.savefig(imgname, dpi=300, bbox_inches="tight")
            print(f"Generate chemical structure: {imgname}")
            plt.close()
        else:
            plt.show()


