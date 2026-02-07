import pygame
import time
from particle_system import ParticleSystem
from simulation_config import SimulationConfig


class Slider:
    """
    Simple horizontal slider used for controlling numeric parameters.

    The slider works in local coordinates of the panel surface.
    We pass an (offset_x, offset_y) when handling mouse events so it
    can convert from global screen coordinates to local ones.
    """

    def __init__(
        self,
        label: str,
        param_name: str,
        rect: pygame.Rect,
        min_val: float,
        max_val: float,
        initial_value: float,
    ) -> None:
        self.label = label
        self.param_name = param_name  # name in SimulationConfig, or "" if purely visual
        self.rect = rect  # local to the panel surface
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_value
        self.dragging = False

    # ------------------------------------------------------------------ #
    # event handling
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event, offset: tuple[int, int]) -> None:
        """
        Handle mouse events. `offset` is (panel_x, panel_y) so that we
        can convert from global event.pos to local slider coordinates.
        """
        if not hasattr(event, "pos"):
            return

        ox, oy = offset
        mx, my = event.pos
        local_pos = (mx - ox, my - oy)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(local_pos):
                self.dragging = True
                self._set_value_from_pos(local_pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_value_from_pos(local_pos[0])

    def _set_value_from_pos(self, local_x: int) -> None:
        t = (local_x - self.rect.x) / self.rect.width
        t = max(0.0, min(1.0, t))
        self.value = self.min_val + t * (self.max_val - self.min_val)

    # ------------------------------------------------------------------ #
    # drawing
    # ------------------------------------------------------------------ #
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw slider and its label onto the given surface."""
        # label above the slider
        label_surf = font.render(self.label, True, (230, 230, 230))
        surface.blit(label_surf, (self.rect.x, self.rect.y - 18))

        # track background
        pygame.draw.rect(surface, (60, 60, 60), self.rect, border_radius=6)

        # filled portion
        if self.max_val > self.min_val:
            filled_width = int(
                (self.value - self.min_val)
                / (self.max_val - self.min_val)
                * self.rect.width
            )
        else:
            filled_width = 0

        if filled_width > 0:
            filled = pygame.Rect(
                self.rect.x,
                self.rect.y,
                filled_width,
                self.rect.height,
            )
            pygame.draw.rect(surface, (140, 140, 140), filled, border_radius=6)

        # handle circle
        handle_x = self.rect.x + filled_width
        handle_y = self.rect.y + self.rect.height // 2
        pygame.draw.circle(surface, (230, 230, 230), (handle_x, handle_y), 6)


class Visualizer:
    """
    Main visualizer window.

    Responsible for:
      * Running the simulation loop
      * Rendering particles with trails
      * Rendering a small control panel on the top-right
    """

    def __init__(
        self,
        system: ParticleSystem,
        width: int,
        height: int,
        target_fps: int = 60,
        speed_factor: float = 1.0,
    ) -> None:
        self.system = system
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.speed_factor = speed_factor

        # overall state flags
        self.running = True
        self.simulation_running = True
        self.heatmap_open = False

        # right-side panel base geometry
        self.panel_width = 320
        self.panel_min_height = 360  # minimal height, can grow dynamically
        self.panel_margin = 20
        self.panel_rect = pygame.Rect(
            self.width - self.panel_width - self.panel_margin,
            self.panel_margin,
            self.panel_width,
            self.panel_min_height,
        )

        # collapsible panel state
        self.panel_collapsed = False
        # button is in panel-local coordinates
        self.collapse_button_rect = pygame.Rect(10, 10, 26, 22)

        # selected particle for inspection
        self.selected_particle = None

        # particle visual radius (controlled by "Size" slider)
        self.particle_radius = 3.0
        # variables for the heatmap
        self.selected_cell = (0,0)
        self.matrix_origin = (40,75)
        self.matrix_cell_size = 60
        self.matrix_gap = 1
        self.grid_size = 4
        self.matrix_cell_rects = {}
        

        pygame.init()
        pygame.display.set_caption("Particle Life")
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE) # added resizable feature
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)

        # particle type colors (pygame.Color objects)
        config: SimulationConfig = system.config
        self.type_colors: list[pygame.Color] = []
        for c in config.particle_colors:
            try:
                self.type_colors.append(pygame.Color(c))
            except ValueError:
                self.type_colors.append(pygame.Color(255, 255, 255))

        self._circle_cache: dict[tuple[int, int], pygame.Surface] = {}
        self._frame = 0
        self.fade_every_n_frames = 3

        # surfaces used for trails effect
        self.trail_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.fade_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # slightly transparent black, used to slowly fade old trails
        self.fade_surface.fill((0, 0, 0, 20))

        # for reset: remember initial particle count and types
        self.initial_particle_count = len(self.system.particles)
        self.available_types = list(range(config.num_types))

        # ------------------------ UI layout ------------------------ #
        btn_width = self.panel_width - 32
        btn_height = 32
        btn_x = 16
        top_y = 52

        # panel-local button rectangles
        self.play_button_rect = pygame.Rect(btn_x, top_y, btn_width, btn_height)
        self.reset_button_rect = pygame.Rect(
            btn_x, top_y + btn_height + 10, btn_width, btn_height
        )
        self.randomize_button_rect = pygame.Rect(
            btn_x, top_y + 2 * (btn_height + 10), btn_width, btn_height
        )
        self.edit_button_rect = pygame.Rect(
            btn_x, top_y + 3 * (btn_height + 10), btn_width, btn_height

        )
        self.back_button_rect = pygame.Rect(
            btn_x, top_y + 7.5 * (btn_height + 10), btn_width, btn_height

        )


        # sliders (panel-local coordinates)
        slider_start_y = top_y + 3 * (btn_height + 28)
        slider_height = 16
        slider_spacing = 46
        slider_rects: list[pygame.Rect] = []
        for i in range(3):  # currently 3 sliders are used in UI
            r = pygame.Rect(
                16,
                slider_start_y + i * slider_spacing,
                btn_width,
                slider_height,
            )
            slider_rects.append(r)

        self.sliders: list[Slider] = [
            Slider(
                "Size",
                "",
                slider_rects[0],
                1.0,
                6.0,
                self.particle_radius,
            ),
            Slider(
                "Spread",
                "interaction_radius",
                slider_rects[1],
                20.0,
                150.0,
                config.interaction_radius,
            ),
            Slider(
                "Chaos",
                "random_motion",
                slider_rects[2],
                0.0,
                0.2,
                config.random_motion,
            )   
            # If you want Friction slider back, add one more rect and here:
            # Slider("Friction", "friction", slider_rects[3], 0.0, 0.2, config.friction),
        ]
        
        # calculates the overall height of the heatmap
        grid_height = self.grid_size * self.matrix_cell_size + (self.grid_size -1) *self.matrix_gap
        heat_slider_start_y = self.matrix_origin[1] + grid_height + 20
        #creates the slider for the heatmap
        heat_slider_rect = pygame.Rect(
            16,
            heat_slider_start_y,
            btn_width,
            slider_height,
        )
        self.heat_slider = Slider(
            "Interaction",
            "",
            heat_slider_rect,
            -1.0,
            1.0,
            config.get_interaction(0,0)
        )
        #Drawing the rects for the Heatmap
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x = self.matrix_origin[0] + j * (self.matrix_cell_size + self.matrix_gap)
                y = self.matrix_origin[1] + i * (self.matrix_cell_size + self.matrix_gap)
                matrix_rect =pygame.Rect(x , y, self.matrix_cell_size, self.matrix_cell_size)
                # saves cell(index) + rect in a dictionary -> you can refer to the rect of every cell
                self.matrix_cell_rects[(i, j)] = matrix_rect
    # ==================================================================
    # main loop
    # ==================================================================
    def run(self) -> None:
        time_physics = 0
        time_draw = 0
        frame_count = 0

        while self.running:
            dt_ms = self.clock.tick(self.target_fps)
            dt = dt_ms / 1000.0

            self._handle_events()

            if self.simulation_running:
                # clamp very large time steps (e.g. when window is dragged)
                if dt > 0.05:
                    dt = 0.05
                t0 = time.perf_counter()
                self.system.update_system(dt * self.speed_factor)
                time_physics += time.perf_counter() - t0

            t0 = time.perf_counter()
            self._draw()
            time_draw += time.perf_counter() - t0

            frame_count += 1

            if frame_count % 120 == 0:
                avg_physics = (time_physics / frame_count) * 1000
                avg_draw = (time_draw / frame_count) * 1000
                total = avg_physics + avg_draw
                print(f"Physics: {avg_physics:.2f}ms | Draw: {avg_draw:.2f}ms | Total: {total:.2f}ms | Target: 16.67ms")

                time_physics = 0
                time_draw = 0
                frame_count = 0

            #self._draw()

        pygame.quit()

    # ==================================================================
    # event handling
    # ==================================================================
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # quick pause / unpause
                    self.simulation_running = not self.simulation_running
            
            elif event.type == pygame.VIDEORESIZE:
                w, h = event.size # new window size after the resize event
                # updates visualizer size
                self.width, self.height = w, h
                # updates particle system bounds
                self.system.width = w
                self.system.height = h
                # recreates the main display surface with the new size
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                # recreates the trail surface
                self.trail_surface = pygame.Surface((w, h), pygame.SRCALPHA)
                # recreates fade surface used to fade old frames
                self.fade_surface = pygame.Surface((w, h), pygame.SRCALPHA)
                self.fade_surface.fill((0, 0, 0, 20))

            if event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                self._handle_mouse_event(event)

    def _handle_mouse_event(self, event: pygame.event.Event) -> None:
        # panel offset used to convert to local coordinates
        panel_offset = (self.panel_rect.x, self.panel_rect.y)

        # first, sliders (only when panel is visible)
        if not self.panel_collapsed:
            if not self.heatmap_open:
                for slider in self.sliders:
                    slider.handle_event(event, panel_offset)

                # apply slider values to config or visuals
                config = self.system.config
                for slider in self.sliders:
                    if slider.param_name:
                        config.update_parameter(slider.param_name, slider.value)
                    else:
                        # visual-only parameter: particle size
                        self.particle_radius = slider.value
            # adds slider and applys slider value to config
            if self.heatmap_open:
                self.heat_slider.handle_event(event, panel_offset)
                if self.heat_slider.dragging:
                    config = self.system.config
                    (i, j) = self.selected_cell
                    config.set_interaction(i, j, self.heat_slider.value)

        # handle simple mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_click(event.pos)

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        mx, my = pos

        # convert to panel-local coordinates
        local_x = mx - self.panel_rect.x
        local_y = my - self.panel_rect.y

        # click on collapse / expand button
        if self.collapse_button_rect.collidepoint(local_x, local_y):
            self.panel_collapsed = not self.panel_collapsed
            return

        # if click is inside panel area, check buttons
        if 0 <= local_x < self.panel_width and 0 <= local_y < self.panel_rect.height:
            if not self.panel_collapsed:
                if not self.heatmap_open:
                    if self.play_button_rect.collidepoint(local_x, local_y):
                        self.simulation_running = not self.simulation_running
                        return
                    if self.reset_button_rect.collidepoint(local_x, local_y):
                        self._reset_particles()
                        return
                    if self.randomize_button_rect.collidepoint(local_x, local_y):
                        self._randomize_system()
                        return
                    if self.edit_button_rect.collidepoint(local_x, local_y):
                        self.heatmap_open = not self.heatmap_open
                        return
                else:
                    if self.back_button_rect.collidepoint(local_x,local_y):
                        self.heatmap_open = not self.heatmap_open
                    
                    # iterates over cells, checks if they're clicked and saves it in selected_cell
                    for ((i,j), matrix_rect) in self.matrix_cell_rects.items():
                        if matrix_rect.collidepoint(local_x,local_y):
                            self.selected_cell = (i,j)
                    return
                    

            # click was on the panel, do not select a particle
            return

        # click in simulation area: select nearest particle
        self._select_particle_at(pos)

    # ------------------------------------------------------------------ #
    # system helpers
    # ------------------------------------------------------------------ #
    def _select_particle_at(self, pos: tuple[int, int]) -> None:
        x, y = pos
        min_dist_sq = 15 * 15  # selection radius
        closest = None

        for p in self.system.particles:
            dx = p.position_x - x
            dy = p.position_y - y
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest = p

        self.selected_particle = closest

    def _reset_particles(self) -> None:
        """Clear system and create a fresh set of particles."""
        self.system.reset_system()
        self.system.add_particles(
            count=self.initial_particle_count,
            types=self.available_types,
        )
        # clear trails as well
        self.trail_surface.fill((0, 0, 0, 0))

    def _randomize_system(self) -> None:
        """Randomize interaction matrix and restart the system."""
        self.system.config.randomize_interactions()
        self._reset_particles()

    # ==================================================================
    # drawing
    # ==================================================================
    def _draw(self) -> None:
        # background
        self.screen.fill((0, 0, 0))

        # particles with nice trailing effect
        self._draw_particles_with_trails()


        # UI overlay
        self._draw_ui_panel()

        pygame.display.flip()

    def _draw_particles_with_trails(self) -> None:
        self._frame += 1
        # slightly darken previous trails
        if self._frame % self.fade_every_n_frames == 0:
            self.trail_surface.blit(self.fade_surface, (0, 0))

        # draw new particle positions onto the trail surface
        for p in self.system.particles:
            x = int(p.position_x)
            y = int(p.position_y)
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                continue

            color = self.type_colors[p.particle_type]
            r = int(self.particle_radius) # сache integer radius to avoid repeated type conversion in draw calls
            pygame.draw.circle(self.trail_surface, color, (x, y), r)

        # blit the trails onto the main screen
        self.screen.blit(self.trail_surface, (0, 0))

        # highlight selected particle with a thin outline
        if self.selected_particle is not None:
            p = self.selected_particle
            x = int(p.position_x)
            y = int(p.position_y)
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (x, y),
                int(self.particle_radius) + 3,
                width=1,
            )
    
    def _get_circle_sprite(self, color: pygame.Color, radius: int) -> pygame.Surface:
        """Return cached circle surface for (color, radius)."""
        key = (color.r << 16) | (color.g << 8) | color.b, radius
        surf = self._circle_cache.get(key)
        if surf is not None:
            return surf

        size = radius * 2 + 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (size // 2, size // 2), radius)
        self._circle_cache[key] = surf
        return surf

    def _draw_ui_panel(self) -> None:
        w, h = self.screen.get_size()
        self.panel_rect.x = w - self.panel_width - self.panel_margin
        self.panel_rect.y = self.panel_margin
        """
        Draw semi-transparent control panel on the top-right.
        Panel height is dynamic so performance text always fits.
        """
        # when collapsed, only header row is visible
        if self.panel_collapsed:
            panel_height = 44
        else: 
            # estimate how many lines of info we will draw
            base_info_lines = 2  # FPS + Particles
            extra_lines = 0
            if self.selected_particle is not None:
                extra_lines = 6  # "", "Selected:", type, pos, speed (5 + 1 blank)

            info_lines_count = base_info_lines + extra_lines
            info_block_height = 16 * info_lines_count

            last_slider_bottom = max(s.rect.bottom for s in self.sliders)
            # start of info block just under sliders
            info_start_y = last_slider_bottom + 24

            panel_height = max(
                self.panel_min_height,
                info_start_y + info_block_height + 16,
            )             

        # update panel rect height for correct mouse interaction
        self.panel_rect.height = panel_height

        # create semi-transparent surface for the panel
        panel_surface = pygame.Surface(
            (self.panel_width, panel_height), pygame.SRCALPHA
        )
        panel_surface.fill((15, 15, 15, 180))

        # collapse / expand button
        pygame.draw.rect(
            panel_surface,
            (230, 230, 230),
            self.collapse_button_rect,
            border_radius=8,
        )
        arrow = "▲" if not self.panel_collapsed else "▼"
        arrow_surf = self.small_font.render(arrow, True, (0, 0, 0))
        arrow_rect = arrow_surf.get_rect(
            center=self.collapse_button_rect.center
        )
        panel_surface.blit(arrow_surf, arrow_rect.topleft)

        # title text
        title_surf = self.font.render("Life settings", True, (230, 230, 230))
        title_rect = title_surf.get_rect()
        title_rect.midleft = (self.collapse_button_rect.right + 10, 21)
        panel_surface.blit(title_surf, title_rect.topleft)

        if not self.panel_collapsed:
            if not self.heatmap_open:
                # buttons
                self._draw_buttons(panel_surface)

                # sliders
                for slider in self.sliders:
                    slider.draw(panel_surface, self.small_font)

                # info block (FPS + selected particle) directly under sliders
                last_slider_bottom = max(s.rect.bottom for s in self.sliders)
                info_start_y = last_slider_bottom + 24
                self._draw_info_block(panel_surface, info_start_y)

                # heatmap part of the drawing
            if self.heatmap_open:
                for ((i,j),rect) in self.matrix_cell_rects.items():
                    # gets current interaction values out of config and prepares the string shown on cells
                    config_value = self.system.config.get_interaction(i,j)
                    config_color_value = config_value
                    config_value = str(round(config_value,2))
                    #  since RGB input only works if integer is positive and between 0-255 we normalise the Value between 0-1
                    config_color_value = (config_color_value + 1) / 2
                    # function for the red color, becomes larger when interaction value is larger
                    rgb_value_1 = round((config_color_value * 255))
                    # function for the blue part of the color, becomes smaller when interaction value is larger
                    rgb_value_2 = round((255 * (1-config_color_value)))
                    # Draws Heatmap with changing colors, aswell as display for each value in each cell
                    pygame.draw.rect(panel_surface, (rgb_value_1, 0, rgb_value_2), rect)
                    pygame.draw.rect(panel_surface, (30, 30, 30), rect, width=2)
                    cell_text = self.small_font.render(config_value,False,(0,0,0))
                    cell_text_rect = cell_text.get_rect()
                    cell_text_rect = rect.center
                    panel_surface.blit(cell_text, cell_text_rect)
                    # draws "edge" around the selected cell to dispay a cell is clicked
                    if (i,j) == self.selected_cell:
                        pygame.draw.rect(panel_surface, (230, 230, 230), rect, width=3)

                self.heat_slider.draw(panel_surface,self.small_font)   
                self._draw_buttons(panel_surface)       
                
        # finally blit panel to the main screen
        self.screen.blit(panel_surface, (self.panel_rect.x, self.panel_rect.y))

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """
        Draw control buttons on the given surface.

        Buttons are transparent with a white outline only,
        for a minimalist look.
        """

        def draw_button(rect: pygame.Rect, text: str) -> None:
            # white outline, transparent fill
            pygame.draw.rect(
                surface,
                (230, 230, 230),
                rect,
                width=2,
                border_radius=10,
            )
            label = self.small_font.render(text, True, (230, 230, 230))
            label_rect = label.get_rect(center=rect.center)
            surface.blit(label, label_rect.topleft)
        if not self.heatmap_open:
            draw_button(
                self.play_button_rect,
                "Pause" if self.simulation_running else "Play",
            )
            draw_button(self.reset_button_rect, "Reset")
            draw_button(self.randomize_button_rect, "Randomize")
            draw_button(self.edit_button_rect, "Edit")
        else: 
            draw_button(self.back_button_rect, "Back")

    def _draw_info_block(self, surface: pygame.Surface, start_y: int) -> None:
        """
        Show FPS and selected particle data inside the panel.
        The block starts at `start_y`, which is placed below the sliders.
        """
        x = 18
        y = start_y

        fps = self.clock.get_fps()
        lines = [
            f"FPS: {fps:4.1f}",
            f"Particles: {len(self.system.particles)}",
        ]

        if self.selected_particle is not None:
            p = self.selected_particle
            speed = (p.velocity_x ** 2 + p.velocity_y ** 2) ** 0.5
            lines += [
                "",
                "Selected:",
                f"  type: {p.particle_type}",
                f"  pos: ({p.position_x:.1f}, {p.position_y:.1f})",
                f"  speed: {speed:.2f}",
            ]

        for line in lines:
            surf = self.small_font.render(line, True, (230, 230, 230))
            surface.blit(surf, (x, y))
            y += 16
