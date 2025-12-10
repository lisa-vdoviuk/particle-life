import os
from simulation_config import SimulationConfig
from particle_system import ParticleSystem
from visualizer import Visualizer

PRESETS_DIR = "presets"  # folder with JSON presets


def configure_matrix_from_console(config: SimulationConfig) -> None:
    """
    Entering interaction matrix values through console
    """
    num_types = config.num_types
    colors = config.particle_colors

    print("\n=== Interaction Matrix Setup ===")
    print("Particles types and their colors:")
    for t in range(num_types):
        print(f"  Type {t}: {colors[t]}")
    print()
    print(
        "Entering forces between particles [-1.0, 1.0].\n"
        "  > positive value  = attraction\n"
        "  > negative value  = repulstion\n"
        "  > Enter without a value = 0.0 (no interaction)\n"
    )

    matrix = config.interaction_matrix

    for i in range(num_types):
        for j in range(num_types):
            while True:
                try:
                    prompt = (
                        f"Interaction from type {i} ({colors[i]}) "
                        f"to type {j} ({colors[j]}) "
                        "(value -1.0..1.0, default 0.0): "
                    )
                    s = input(prompt).strip()

                    if s == "":
                        val = 0.0
                    else:
                        val = float(s)

                    if not -1.0 <= val <= 1.0:
                        print("Value has to be between -1.0 and 1.0.")
                        continue

                    matrix.set_interaction(i, j, val)
                    break
                except ValueError:
                    print("Enter a number, for example: 0.3, -0.7, 1, 0...")

    print("\nInteraction matrix is saved in configuration.")


def save_preset(config: SimulationConfig) -> None:
    """
    Save current SimulationConfig as a JSON-preset.
    """
    os.makedirs(PRESETS_DIR, exist_ok=True)
    name = input("Enter a preset name: ").strip()
    if not name:
        name = "preset1"
    file_path = os.path.join(PRESETS_DIR, f"{name}.json")
    
    config.save_config(file_path)
    print(f"Preset was saved in: {file_path}")


def load_preset():
    """
    Load preset from the folder presets through SimulationConfig.load_config().
    Returns SimulationConfig or None, if user canceled.
    """
    if not os.path.isdir(PRESETS_DIR):
        print("there's no presets folder yet.")
        return None

    files = [f for f in os.listdir(PRESETS_DIR) if f.endswith(".json")]
    if not files:
        print("There's no presets in presets folder.")
        return None

    print("\nPresets::")
    for idx, fname in enumerate(files):
        print(f"  [{idx}] {fname}")
    print()

    while True:
        choice = input(
            "Enter a preset number: "
        ).strip()
        if choice == "":
            return None
        try:
            idx = int(choice)
            if 0 <= idx < len(files):
                file_path = os.path.join(PRESETS_DIR, files[idx])
                
                cfg = SimulationConfig.load_config(file_path)
                print(f"Preset: {files[idx]} has loaded")
                return cfg
            else:
                print("There's no preset with this index.")
        except ValueError:
            print("Enter a number (0, 1, 2, ...).")


def create_or_load_config() -> SimulationConfig:

    print("\n=== Simulation configuration ===")
    print("[1] Load preset from JSON")
    print("[2] Enter own interaction matrix")
    choice = input("Choose [1/2] (default 2): ").strip()

    if choice == "1":
        cfg = load_preset()
        if cfg is not None:
            return cfg
        print("Preset was no chosen.")

    # Create new config
    cfg = SimulationConfig()


    cfg.friction = 0.02        
    cfg.max_velocity = 6.0    
    cfg.random_motion = 0.05   

    configure_matrix_from_console(cfg)

    save_choice = input(
        "Save matrix as a JSON preset? [y/N]: "
    ).strip().lower()
    if save_choice == "y":
        save_preset(cfg)

    input("Press Enter, to start visualization...")
    return cfg


def main() -> None:
    # Window size
    width, height = 800, 600

    
    config = create_or_load_config()

    
    system = ParticleSystem(
        particles=[],
        config=config,
        width=width,
        height=height,
    )

    
    types = list(range(config.num_types))

   
    system.add_particles(count=100, types=types)

    
    visualizer = Visualizer(
        system,
        width,
        height,
        target_fps=60,
        speed_factor=4.0,
    )
    visualizer.run()


if __name__ == "__main__":
    main()
