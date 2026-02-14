from particle_class import Particle
from simulation_config import SimulationConfig
from typing import List, Dict
import random
import math

# -------------------- NUMBA ADD-ON (optional acceleration) --------------------
# Numba accelerates the hot loop (neighbor search + pairwise forces)
try:
    import numpy as np
    from numba import njit
    NUMBA_OK = True
except Exception:
    NUMBA_OK = False

if NUMBA_OK:
    @njit(fastmath=True, cache=True)
    def _compute_forces_numba(xs, ys, types, matrix, r, cell_size, width, height, cell_range):
        # uniform grid (spatial hashing) with a linked-list per cell:
        n = xs.shape[0]
        beta = 0.3 # Reduced slightly for better "ocean" flow
        force_scale = 0.05 # Adjusted for stability
        fx = np.zeros(n, dtype=np.float32)
        fy = np.zeros(n, dtype=np.float32)

        if n == 0:
            return fx, fy

        inv_cell = 1.0 / cell_size
        radius2 = r * r

        nx = int(width * inv_cell) + 1
        ny = int(height * inv_cell) + 1
        ncell = nx * ny

        # head[cell] = first particle index in that cell, nxt[i] = next particle index in same cell.
        head = np.full(ncell, -1, dtype=np.int32)
        nxt = np.empty(n, dtype=np.int32)

        # build linked list per cell
        for i in range(n):
            cx = int(xs[i] * inv_cell)
            cy = int(ys[i] * inv_cell)

            # --- FIX: Removed grid wrapping ---
            # Removed grid wrapping so instead of wrapping with %, I clamp the values to the edges
            # This is needed because we added walls
            if cx < 0: cx = 0
            elif cx >= nx: cx = nx - 1
            if cy < 0: cy = 0
            elif cy >= ny: cy = ny - 1

            c = cx + cy * nx
            nxt[i] = head[c]
            head[c] = i

        # compute forces
        for i in range(n):
            xi = xs[i]
            yi = ys[i]
            ti = types[i]

            cxi = int(xi * inv_cell)
            cyi = int(yi * inv_cell)

            for dx_cell in range(-cell_range, cell_range + 1):
                gx = cxi + dx_cell
                # --- FIX: Ignore cells outside walls ---
                # Since the world isn't round anymore, we skip neighbor cells that don't exist
                if gx < 0 or gx >= nx:
                    continue

                for dy_cell in range(-cell_range, cell_range + 1):
                    gy = cyi + dy_cell
                    if gy < 0 or gy >= ny:
                        continue

                    cell = gx + gy * nx
                    j = head[cell]
                    while j != -1:
                        if j != i:
                            # --- FIX: Removed distance wrapping ---
                            # Deleted the code that calculated distance through the screen edges
                            dx = xs[j] - xi
                            dy = ys[j] - yi
                            
                            d2 = dx * dx + dy * dy

                            if d2 > 1e-6 and d2 <= radius2:
                                inv_d = 1.0 / math.sqrt(d2)
                                dist = d2 * inv_d
                                q = dist / r 
                                
                                # --- FIX: Better Collision Logic ---
                                if q < beta: 
                                    # This pushes particles apart even if their matrix interaction is 0
                                    # Prevents particles from phasing through each others
                                    strength = (q / beta - 1.0) * force_scale
                                else:
                                    tj = types[j]
                                    k = matrix[ti, tj]
                                    # Honestly found this formula online which makes it look more like liquid molecules than simple circles
                                    f = (1.0 - abs(2.0 * q - 1.0 - beta) / (1.0 - beta))
                                    strength = k * f * force_scale

                                fx[i] += dx * inv_d * strength
                                fy[i] += dy * inv_d * strength

                        j = nxt[j]

        return fx, fy
# ---------------------------------------------------------------------


class ParticleSystem:
    def __init__(self, particles: List[Particle], config: SimulationConfig, width: int, height: int):
        self.particles = particles
        self.config = config
        self.width = width
        self.height = height
        self._force_frame = 0
        self._grid = {}

        # numpy-matrix cache
        self._numba_matrix_np = None
        self._numba_matrix_shape = None
        #dirty-flag to check if interaction values changed
        self.matrix_dirty = True

    def add_particles(self, count: int, types: List[int]):
        """Adds particles with positions and types"""
        for _ in range(count):
            particle_type = random.choice(types)
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)

            # Minimum starting velocity
            vx = random.uniform(-0.5, 0.5)
            vy = random.uniform(-0.5, 0.5)

            color = self.config.particle_colors[particle_type]

            p = Particle(
                particle_type=particle_type,
                position_x=x,
                position_y=y,
                velocity_x=vx,
                velocity_y=vy,
                color=color
            )
            self.particles.append(p)

    def update_system(self, dt: float):
        """Updated the whole system"""
        self._force_frame += 1
        self.calculate_forces(dt)

        friction = self.config.friction
        max_v = self.config.max_velocity
        rnd_m = self.config.random_motion
        rnd_change = rnd_m

        for particle in self.particles:
            particle.update_position(
                dt,
                friction,
                max_v,
                rnd_change
            )

            # --- FIX: Wall Bouncing ---
            # Replaced the % wrap with simple bouncing logic
            # Simply checks if particle hits the edge and reverses velocity
            if particle.position_x < 0:
                particle.position_x = 0
                particle.velocity_x *= -1
            elif particle.position_x > self.width:
                particle.position_x = self.width
                particle.velocity_x *= -1

            if particle.position_y < 0:
                particle.position_y = 0
                particle.velocity_y *= -1
            elif particle.position_y > self.height:
                particle.position_y = self.height
                particle.velocity_y *= -1

    # -------------------- PYTHON --------------------
    def _calculate_forces_python(self):
        """
        Reference (pure Python) implementation of particle interactions.

        - Simple and readable
        - Uses uniform grid (spatial hashing)
        - NOT optimized for performance
        - Intended only as fallback or for debugging / reference
        """

        particles = self.particles
        config = self.config

        if not particles:
            return

        # locals for the faster optimisation
        sqrt = math.sqrt
        interaction_matrix = config.interaction_matrix.matrix

        # interaction radius (distance)
        r = float(config.interaction_radius)
        if r <= 0.0:
            return

        radius_squared = r * r  # compare squared distances to avoid sqrt when possible
        inv_r = 1.0 / r         # precompute the inverse of interaction radius for the optimisation

        # we use cell size as r so we only check the current cell and the neighbor cells
        cell_size = r
        inv_cell = 1.0 / cell_size  # precompute the inverse cell for the optimisation
        cell_range = 1              # checks 1 cell away -> 3x3 blocks (current cell + 8 neighbors)

        # creates the dict with all the particles cell locations
        grid = self._grid
        grid.clear()

        # grid keeps particles
        for p in particles:
            cx = int(p.position_x * inv_cell)
            cy = int(p.position_y * inv_cell)
            key = (cx, cy)
            if key not in grid:
                grid[key] = []
            grid[key].append(p)

        # computes the forces for all the particles in the cell
        for i in particles:
            xi = i.position_x
            yi = i.position_y
            ti = i.particle_type

            # row in the matrix for the particle i type (faster optimisation)
            row = interaction_matrix[ti]

            force_x = 0.0
            force_y = 0.0

            # cell coordinates for particle i
            cxi = int(xi * inv_cell)
            cyi = int(yi * inv_cell)

            # checks current cells and the 8 neighboring cells
            for dx_cells in range(-cell_range, cell_range + 1):
                for dy_cells in range(-cell_range, cell_range + 1):
                    cell = grid.get((cxi + dx_cells, cyi + dy_cells))
                    if not cell:
                        continue

                    # iterate particles in the neighbor cells
                    for j in cell:
                        if j is i:
                            continue  # skips self

                        # takes the interaction coefficient from the matrix
                        k = row[j.particle_type]
                        if k == 0.0:
                            continue  # skips if no interaction

                        dx = j.position_x - xi
                        dy = j.position_y - yi
                        d_squared = dx * dx + dy * dy

                        # ignores extremely small distances (avoid division by zero)
                        # also ignores particles outside the cutoff radius
                        if d_squared < 1e-6 or d_squared > radius_squared:
                            continue

                        # computes the distance and normalized direction
                        inv_d = 1.0 / sqrt(d_squared)
                        dist = d_squared * inv_d

                        strength = k * (1.0 - dist * inv_r)

                        # calculate the forces (direction * strength)
                        force_x += dx * inv_d * strength
                        force_y += dy * inv_d * strength

            i.apply_force(force_x, force_y)
    # -------------------------------------------------------------------------------

    def calculate_forces(self, dt):
        """Calculates the forces between all the particles. Uses Numba if available."""
        particles = self.particles
        n = len(particles)
        if n == 0:
            return

        r = float(self.config.interaction_radius)
        if r <= 0.0:
            return

        # if numba not available
        if not NUMBA_OK:
            raise RuntimeError("Numba is required for this simulation")

        # Grid parameters (tunable)
        cell_size = r * 0.6
        cell_range = int(math.ceil(r / cell_size))

        # prepare arrays
        xs = np.empty(n, dtype=np.float32)
        ys = np.empty(n, dtype=np.float32)
        types = np.empty(n, dtype=np.int32)

        for i, p in enumerate(particles):
            xs[i] = p.position_x
            ys[i] = p.position_y
            types[i] = p.particle_type

        # cache matrix as numpy float32
        mat_list = self.config.interaction_matrix.matrix
        shape = (len(mat_list), len(mat_list[0])) if len(mat_list) else (0, 0)

        if self._numba_matrix_np is None or self._numba_matrix_shape != shape or self.matrix_dirty == True:
            self._numba_matrix_np = np.asarray(mat_list, dtype=np.float32)
            self._numba_matrix_shape = shape
            self.matrix_dirty = False

        fx, fy = _compute_forces_numba(
            xs, ys, types, self._numba_matrix_np,
            float(r), float(cell_size),
            int(self.width), int(self.height),
            int(cell_range)
        )

        # apply forces back
        for i, p in enumerate(particles):
            p.velocity_x += float(fx[i]) * dt
            p.velocity_y += float(fy[i]) * dt

    def get_particles_data(self) -> List[Dict]:
        """Return the data for visualization"""
        result = []
        for p in self.particles:
            particle_data = {
                "x": p.position_x,
                "y": p.position_y,
                "vx": p.velocity_x,
                "vy": p.velocity_y,
                "type": p.particle_type,
                "color": p.color
            }
            result.append(particle_data)
        return result

    def reset_system(self):
        """Resets the system"""
        self.particles.clear()
