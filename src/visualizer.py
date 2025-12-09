import pygame
from particle_system import ParticleSystem
from simulation_config import SimulationConfig


class Visualizer:
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

        self.running = True
        self.simulation_running = False

        self.ui_height = 60
        self.window_width = self.width
        self.window_height = self.height + self.ui_height

        pygame.init()
        pygame.display.set_caption("Particle Life - Milestone 3")
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height)
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)

        # Buttons
        self.start_button_rect = pygame.Rect(20, self.height + 10, 100, 40)
        self.stop_button_rect = pygame.Rect(140, self.height + 10, 100, 40)

        
        config: SimulationConfig = system.config
        self.type_colors: list[pygame.Color] = []
        for c in config.particle_colors:
            try:
                self.type_colors.append(pygame.Color(c))
            except ValueError:
                self.type_colors.append(pygame.Color(255, 255, 255))

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(self.target_fps)
            dt = dt_ms / 1000.0

            self._handle_events()

            if self.simulation_running:
                
                if dt > 0.05:
                    dt = 0.05

                
                self.system.update_system(dt * self.speed_factor)

            self._draw()

        pygame.quit()

    # -------- events --------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos)

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        if self.start_button_rect.collidepoint(pos):
            self.simulation_running = True
        elif self.stop_button_rect.collidepoint(pos):
            self.simulation_running = False

    # -------- drawing --------

    def _draw(self) -> None:
        
        self.screen.fill((0, 0, 0), rect=(0, 0, self.width, self.height))

        self._draw_particles()

        # UI panel down
        self.screen.fill(
            (20, 20, 20),
            rect=(0, self.height, self.width, self.ui_height),
        )
        self._draw_buttons()
        self._draw_status_text()

        pygame.display.flip()

    def _draw_particles(self) -> None:
        particles = self.system.particles
        screen = self.screen
        draw_circle = pygame.draw.circle
        type_colors = self.type_colors

        for p in particles:
            x = int(p.position_x)
            y = int(p.position_y)
            color = type_colors[p.particle_type]
            draw_circle(screen, color, (x, y), 3)

    def _draw_buttons(self) -> None:
        # Start
        pygame.draw.rect(
            self.screen, (0, 200, 0), self.start_button_rect, border_radius=8
        )
        start_text = self.font.render("Start", True, (0, 0, 0))
        self.screen.blit(
            start_text,
            start_text.get_rect(center=self.start_button_rect.center),
        )

        # Stop
        pygame.draw.rect(
            self.screen, (200, 0, 0), self.stop_button_rect, border_radius=8
        )
        stop_text = self.font.render("Stop", True, (0, 0, 0))
        self.screen.blit(
            stop_text,
            stop_text.get_rect(center=self.stop_button_rect.center),
        )

    def _draw_status_text(self) -> None:
        fps = self.clock.get_fps()
        text = f"FPS: {fps:4.1f} | Particles: {len(self.system.particles)}"
        status = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(
            status,
            (self.width - status.get_width() - 10, self.height + 18),
        )
