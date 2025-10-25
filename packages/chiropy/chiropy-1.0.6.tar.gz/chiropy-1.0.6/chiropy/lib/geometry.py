import sys
import numpy as np
import networkx as nx
from itertools import combinations
from collections import defaultdict

class Geometry:
    def __init__(self, mol, args):
        self.mol = mol
        self.conf = self.mol.GetConformer()
        self.args = args
    
    def set_mol(self, mol):
        self.mol = mol
    
    def get_mol(self):
        return self.mol
        
    # molecule graph
    def get_graph(self):
        graph = nx.Graph()
        coords = np.array(self.mol_coords(is_indice=True))
        bond_info = self.mol_bond_info()
        
        indice = [int(c[0]) for c in coords]
        pos_list = np.array([[c[1], c[2], c[3]] for c in coords])

        # add node
        for i, pos in zip(indice, pos_list):
            symbol = self.mol.GetAtomWithIdx(i).GetSymbol()
            graph.add_node(i, symbol=symbol, pos=pos)

        # add edge
        nodes = graph.nodes(data=True)
        for b in bond_info:
            i = b[1][0]
            j = b[1][1]
            dist = np.linalg.norm(graph.nodes[i]["pos"] - graph.nodes[j]["pos"])
            graph.add_edge(i, j, distance=dist, order=b[0])
        return graph
        
    # bond info
    def mol_bond_info(self):
        bonds = []
        for bond in self.mol.GetBonds():
            a1 = bond.GetBeginAtomIdx()
            a2 = bond.GetEndAtomIdx()
            order = bond.GetBondTypeAsDouble()
            bonds.append([order, (a1, a2)])
        return bonds
        
    # coordinates of molecule
    def mol_coords(self, is_indice=False):
        coords = []
        
        for atom in self.mol.GetAtoms():
            index = atom.GetIdx()
            pos = self.conf.GetAtomPosition(index)
            if is_indice:
                coords.append((index, pos.x, pos.y, pos.z))
            else:
                coords.append((pos.x, pos.y, pos.z))
        return coords
    
    # masses of molecule
    def mol_masses(self):
        masses = []
        for atom in self.mol.GetAtoms():
            masses.append(atom.GetMass())
        return masses
        
    # center of mass of molecule
    def mol_center_of_mass(self):
        coords = np.array(self.mol_coords())
        masses = np.array(self.mol_masses())
        com = np.average(coords, axis=0, weights=masses)
        return com.tolist()
        
    # inertia tensor of molecule
    def mol_inertia_tensor(self):
        coords_centered = np.array(self.mol_coords()) - np.array(self.mol_center_of_mass())
        masses = self.mol_masses()
        
        xx = np.sum(masses * (coords_centered[:,1]**2 + coords_centered[:,2]**2))
        yy = np.sum(masses * (coords_centered[:,0]**2 + coords_centered[:,2]**2))
        zz = np.sum(masses * (coords_centered[:,0]**2 + coords_centered[:,1]**2))

        xy = -np.sum(masses * coords_centered[:,0] * coords_centered[:,1])
        xz = -np.sum(masses * coords_centered[:,0] * coords_centered[:,2])
        yz = -np.sum(masses * coords_centered[:,1] * coords_centered[:,2])

        inertia_tensor = np.array([
            [xx, xy, xz],
            [xy, yy, yz],
            [xz, yz, zz]
        ])
        return inertia_tensor.tolist()
        
    # long-axis vector of molecule
    def mol_long_axis_vec(self):
        eigvals, eigvecs = np.linalg.eigh(self.mol_inertia_tensor())
        vec = eigvecs[:, np.argmin(eigvals)]
        return vec.tolist()
        
    # length of long-axis
    def mol_long_axis_length(self):
        coords_centered = np.array(self.mol_coords()) - np.array(self.mol_center_of_mass())
        long_axis_vec = self.mol_long_axis_vec()
        
        proj = coords_centered @ long_axis_vec
        long_axis_length = proj.max() - proj.min()
        return float(long_axis_length)
        
    # height-axis vector of molecule
    def mol_height_axis_vec(self):
        # centoring
        q = np.array(self.mol_coords()) - np.array(self.mol_center_of_mass())
    
        # svd
        Q = np.dot(q.T, q)
        la, vectors = np.linalg.eig(Q)
        
        # eigenvector corresponding to the smallest eigenvalue
        vec = vectors.T[np.argmin(la)]
        return vec.tolist()
        
    # short-axis vector of molecule
    def mol_short_axis_vec(self):
        lav = np.array(self.mol_long_axis_vec())
        hav = np.array(self.mol_height_axis_vec())
        vec = np.cross(lav, hav)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()
    
    # length of short-axis
    def mol_short_axis_length(self):
        coords_centered = np.array(self.mol_coords()) - np.array(self.mol_center_of_mass())
        short_axis_vec = self.mol_short_axis_vec()
        
        proj = coords_centered @ short_axis_vec
        short_axis_length = proj.max() - proj.min()
        return float(short_axis_length)
        
    def is_arom(self, is_aroms_iterable, th_atoms_num=1):
        is_aroms = list(is_aroms_iterable)
        true_count = sum(bool(i) for i in is_aroms)
        return true_count > th_atoms_num
        
    # get aromatic atoms indices
    def arom_indices(self):
        arom_rings = []
        ri = self.mol.GetRingInfo()
        
        for ring in ri.AtomRings():
            if self.is_arom(self.mol.GetAtomWithIdx(a).GetIsAromatic() for a in ring):
                arom_rings.append(ring)
        
        if not arom_rings:
            print("No aromatic rings were detected in the molecule.")
            sys.exit(1)
        
        return arom_rings
        
    # merge common index atom between 2 rings
    def merged_arom_indices(self):
        ring_indices = self.arom_indices()
        
        value_to_lists = defaultdict(set)
        for i, lst in enumerate(ring_indices):
            for val in lst:
                value_to_lists[val].add(i)

        visited = set()
        result = []

        for i in range(len(ring_indices)):
            if i in visited:
                continue

            # collect indice by DFS
            stack = [i]
            group = set()
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                group.add(current)

                for val in ring_indices[current]:
                    for neighbor in value_to_lists[val]:
                        if neighbor not in visited:
                            stack.append(neighbor)

            merged = set()
            for idx in group:
                merged.update(ring_indices[idx])
            result.append(sorted(merged))
        return result
    
    # get aromatic atoms indice of pi-cores
    def core_indices(self):
        merged_arom_indices = self.merged_arom_indices()
        
        ring_sizes = [len(indice) for indice in merged_arom_indices]
        max_rings_i = np.where(ring_sizes == np.max(ring_sizes))[0]
        return [merged_arom_indices[i] for i in max_rings_i]
        
    # get aromatic atoms indice of largest pi-core
    def largest_core_indice(self):
        indice = max(self.core_indices(), key=len)
        return indice
        
    # get coordinates in aromatic atoms for each rings
    def arom_coords(self):
        arom_indices = self.arom_indices()
        arom_coords = []
        
        for indice in arom_indices:
            ring_coords = [self.conf.GetAtomPosition(i) for i in indice]
            posses = [(p.x, p.y, p.z) for p in ring_coords]
            arom_coords.append(posses)
        return arom_coords
    
    # get atoms coordinates of pi-core members
    def core_coords(self):
        core_indices = self.core_indices()
        largest_core_indice = self.largest_core_indice()
        core_coords = []
        
        for index in largest_core_indice:
            coord = self.conf.GetAtomPosition(index)
            pos = (coord.x, coord.y, coord.z)
            core_coords.append(pos)
        return core_coords
    
    # masses of pi-core
    def core_masses(self):
        masses = []
        largest_core_indice = self.largest_core_indice()
        atoms = [self.mol.GetAtomWithIdx(i) for i in largest_core_indice]
        
        for atom in atoms:
            masses.append(atom.GetMass())
        return masses
        
    # center of mass of pi-core
    def core_center_of_mass(self):
        coords = np.array(self.core_coords())
        masses = np.array(self.core_masses())
        com = np.average(coords, axis=0, weights=masses)
        return com.tolist()
        
    # inertia tensor of pi-core
    def core_inertia_tensor(self):
        coords_centered = np.array(self.core_coords()) - np.array(self.core_center_of_mass())
        masses = self.core_masses()
        
        xx = np.sum(masses * (coords_centered[:,1]**2 + coords_centered[:,2]**2))
        yy = np.sum(masses * (coords_centered[:,0]**2 + coords_centered[:,2]**2))
        zz = np.sum(masses * (coords_centered[:,0]**2 + coords_centered[:,1]**2))

        xy = -np.sum(masses * coords_centered[:,0] * coords_centered[:,1])
        xz = -np.sum(masses * coords_centered[:,0] * coords_centered[:,2])
        yz = -np.sum(masses * coords_centered[:,1] * coords_centered[:,2])

        inertia_tensor = np.array([
            [xx, xy, xz],
            [xy, yy, yz],
            [xz, yz, zz]
        ])
        return inertia_tensor.tolist()
        
    # long-axis vector of pi-core
    def core_long_axis_vec(self):
        eigvals, eigvecs = np.linalg.eigh(self.core_inertia_tensor())
        vec = eigvecs[:, np.argmin(eigvals)]
        return vec.tolist()
        
    # length of long-axis
    def core_long_axis_length(self):
        coords_centered = np.array(self.core_coords()) - np.array(self.core_center_of_mass())
        long_axis_vec = self.core_long_axis_vec()
        
        proj = coords_centered @ long_axis_vec
        long_axis_length = proj.max() - proj.min()
        return float(long_axis_length)
        
    # height-axis vector of pi-core
    def core_height_axis_vec(self):
        # centoring
        q = np.array(self.core_coords()) - np.array(self.core_center_of_mass())
    
        # svd
        Q = np.dot(q.T, q)
        la, vectors = np.linalg.eig(Q)
        
        # eigenvector corresponding to the smallest eigenvalue
        vec = vectors.T[np.argmin(la)]
        return vec.tolist()
        
    # short-axis vector of core
    def core_short_axis_vec(self):
        lav = np.array(self.core_long_axis_vec())
        hav = np.array(self.core_height_axis_vec())
        vec = np.cross(lav, hav)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()
    
    # length of short-axis
    def core_short_axis_length(self):
        coords_centered = np.array(self.core_coords()) - np.array(self.core_center_of_mass())
        short_axis_vec = self.core_short_axis_vec()
        
        proj = coords_centered @ short_axis_vec
        short_axis_length = proj.max() - proj.min()
        return float(short_axis_length)
        
    # centroid by aromatic ring
    def arom_centroid(self, coord):
        coord_np = np.array(coord)
        centroid = coord_np.mean(axis=0)
        arom_centroid = centroid.tolist()
        return arom_centroid
    
    # centroids for each aromatic rings
    def arom_centroids(self):
        arom_centroids = []
        coords = self.arom_coords()
        for coord in coords:
            centroid = self.arom_centroid(coord)
            arom_centroids.append(centroid)
        return arom_centroids
        
    # normal vector by aromatic ring
    def normal_vec(self, coord, centroid):
        # centoring
        q = np.array(coord) - np.array(centroid)
    
        # svd
        Q = np.dot(q.T, q)
        la, vectors = np.linalg.eig(Q)
        
        # eigenvector corresponding to the smallest eigenvalue
        vec = vectors.T[np.argmin(la)]
        return vec.tolist()
        
    # normal vectors for each aromatic rings
    def normal_vecs(self):
        vecs = []
        coords = self.arom_coords()
        centroids = self.arom_centroids()
        
        for coord, centroid in zip(coords, centroids):
            a, b, c = self.normal_vec(coord, centroid)
            vecs.append((a, b, c))
        return vecs
        
    # rotation matrix
    def rot_matrix(self, coord, centroid):
        u = np.array(self.normal_vec(coord, centroid))
        g = np.array([1, 1, 1])
        v = g - (g @ u) * u
        w = np.cross(u, v)
        
        v = v / np.linalg.norm(v)
        w = w / np.linalg.norm(w)
        
        return np.array([w, v, u])
    
    # rotation matrices
    def rot_matrices(self):
        matrices = []
        coords = self.arom_coords()
        centroids = self.arom_centroids()
        
        for coord, centroid in zip(coords, centroids):
            rot_matrix = self.rot_matrix(coord, centroid)
            matrices.append(rot_matrix)
        return matrices
        
    # core rotation matrix
    def core_rot_matrix(self):
        u = np.array(self.core_height_axis_vec())
        g = np.array([1, 1, 1])
        v = g - (g @ u) * u
        w = np.cross(u, v)
        
        v = v / np.linalg.norm(v)
        w = w / np.linalg.norm(w)
        
        return np.array([w, v, u])

    # original atoms coordinates
    def original_atoms_coords(self):
        coords = []
        for i in range(self.mol.GetNumAtoms()):
            pos = self.conf.GetAtomPosition(i)
            symbol = self.mol.GetAtomWithIdx(i).GetSymbol()
            coords.append((symbol, float(pos.x), float(pos.y), float(pos.z)))
        return coords
