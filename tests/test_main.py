import types
import src.main as main
import builtins
import os

def _mock_inputs(monkeypatch, answers):
    """Feed a sequence of numbers into input()"""
    it = iter(answers)

    def fake_input(_prompt=""):
        return next(it)

    monkeypatch.setattr(builtins, "input", fake_input)

#-------------------------------
# configure matrix from console
#-------------------------------
def test_configure_matrix_from_console(monkeypatch):
    """
    Covers:
    - printing
    - empty input -> 0.0
    - float parsing
    - out-of-range -> retry
    - ValueError -> retry
    """
    calls = []

    class FakeMatrix:
        def set_interaction(self, i, j, val):
            calls.append((i,j,val))
        
    fake_cfg = types.SimpleNamespace(
        num_types=2,
        particle_colors =["red", "blue"],
        interaction_matrix=FakeMatrix(),
    )

    """
    2x2 = 4 values expected:
    (0,0): "" -> 0.0
    (0,1): "0.3" -> 0.3
    (1,0): "2" (out of range) -> retry -> "-0.5"
    (1,1): "x" (ValueError) -> retry -> "" -> 0.0
    """
    _mock_inputs(monkeypatch,["", "0.3", "2", "-0.5", "x", ""])

    main.configure_matrix_from_console(fake_cfg)

    assert calls == [
        (0,0,0.0),
        (0,1,0.3),
        (1,0,-0.5),
        (1,1, 0.0),
    ]

#---------------
# save_preset
#---------------
def test_save_preset_default_name(monkeypatch):
    """
    Covers:
    - os.makedirs called
    - empty name -> preset1.json
    - config.save_config invoked with correct path
    """
    recorded = {"makedirs": None, "save_path": None}

    monkeypatch.setattr(os, "makedirs", lambda path, exist_ok:recorded.update({"makedirs":(path, exist_ok)}))
    _mock_inputs(monkeypatch, [""]) # empty preset name => preset1

    class FakeCfg:
        def save_config(self,path):
            recorded["save_path"]=path
    
    main.save_preset(FakeCfg())

    assert recorded["makedirs"][0]== main.PRESETS_DIR
    assert recorded["makedirs"][1] is True
    assert recorded["save_path"].endswith(os.path.join(main.PRESETS_DIR, "preset1.json"))

def test_save_preset_custom_name(monkeypatch):
    recorded = {"save_path": None}
    monkeypatch.setattr(os, "makedirs", lambda *_a, **_k: None)
    _mock_inputs(monkeypatch, ["mypreset"])

    class FakeCfg:
        def save_config(self, path):
            recorded["save_path"] = path

    main.save_preset(FakeCfg())
    assert recorded["save_path"].endswith(os.path.join(main.PRESETS_DIR, "mypreset.json"))

#------------
#load_preset()
#------------

def test_load_preset_no_presets_dir(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda _p: False)
    assert main.load_preset() is None

def test_load_preset_no_json_files(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda _p: True)
    monkeypatch.setattr(os, "listdir", lambda _p: ["readme.txt", "a.png"])
    assert main.load_preset() is  None

def test_load_preset_cancel_with_empty_choice(monkeypatch):
    monkeypatch.setattr(os.path, "isdir", lambda _p: True)
    monkeypatch.setattr(os, "listdir", lambda _p: ["a.json", "b.json"])
    _mock_inputs(monkeypatch, [""])  # cancel
    assert main.load_preset() is None

def test_load_preset_invalid_then_valid_choice(monkeypatch):
    """
    Covers while-loop branches:
    - invalid index
    - ValueError
    - finally valid selection
    """
    monkeypatch.setattr(os.path, "isdir", lambda _p: True)
    monkeypatch.setattr(os, "listdir", lambda _p: ["a.json", "b.json"])

    # invalid index -> ValueError -> valid
    _mock_inputs(monkeypatch, ["5", "x", "1"])

    class FakeSimCfg:
        @staticmethod
        def load_config(path):
            return {"loaded_from": path}

    monkeypatch.setattr(main, "SimulationConfig", FakeSimCfg)

    cfg = main.load_preset()
    assert cfg["loaded_from"].endswith(os.path.join(main.PRESETS_DIR, "b.json"))

#--------------------
#create_or_load_config
#--------------------
def test_create_or_load_config_choice_1_returns_loaded_cfg(monkeypatch):
    fake_loaded = types.SimpleNamespace(tag="loaded")
    _mock_inputs(monkeypatch, ["1"])  # choose load preset

    monkeypatch.setattr(main, "load_preset", lambda: fake_loaded)

    cfg = main.create_or_load_config()
    assert cfg is fake_loaded

def test_create_or_load_config_choice_1_falls_back_to_manual(monkeypatch):
    """
    Covers:
    - choice == "1" but load_preset returns None
    - falls back to SimulationConfig() path
    - assigns friction/max_velocity/random_motion
    - configure_matrix_from_console called
    - save_choice not 'y'
    - press enter
    """
    calls = {"configured": False, "saved": False}

    _mock_inputs(monkeypatch, ["1", "n", ""])  # 1 -> load fails, then save_choice 'n', then press enter

    monkeypatch.setattr(main, "load_preset", lambda: None)

    class FakeCfg:
        def __init__(self):
            self.num_types = 4
            self.particle_colors = ["a", "b", "c", "d"]
            self.interaction_matrix = object()
            self.friction = None
            self.max_velocity = None
            self.random_motion = None

    monkeypatch.setattr(main, "SimulationConfig", FakeCfg)

    def fake_configure(cfg):
        calls["configured"] = True

    monkeypatch.setattr(main, "configure_matrix_from_console", fake_configure)
    monkeypatch.setattr(main, "save_preset", lambda _cfg: calls.update({"saved": True}))

    cfg = main.create_or_load_config()

    assert isinstance(cfg, FakeCfg)
    assert cfg.friction == 0.02
    assert cfg.max_velocity == 6.0
    assert cfg.random_motion == 0.05
    assert calls["configured"] is True
    assert calls["saved"] is False  # because save_choice was "n"

def test_create_or_load_config_manual_and_save(monkeypatch):
    """
    Covers:
    - default choice (manual)
    - save_choice == 'y' triggers save_preset
    """
    calls = {"configured": False, "saved": False}

    # choice "" -> default manual
    # save_choice 'y'
    # press enter
    _mock_inputs(monkeypatch, ["", "y", ""])

    class FakeCfg:
        def __init__(self):
            self.num_types = 4
            self.particle_colors = ["a", "b", "c", "d"]
            self.interaction_matrix = object()
            self.friction = None
            self.max_velocity = None
            self.random_motion = None

    monkeypatch.setattr(main, "SimulationConfig", FakeCfg)

    monkeypatch.setattr(main, "configure_matrix_from_console", lambda _cfg: calls.update({"configured": True}))
    monkeypatch.setattr(main, "save_preset", lambda _cfg: calls.update({"saved": True}))

    cfg = main.create_or_load_config()
    assert isinstance(cfg, FakeCfg)
    assert calls["configured"] is True
    assert calls["saved"] is True

#---------------
#main()
#---------------
def test_main_creates_system_adds_particles_and_runs_visualizer(monkeypatch):
    """
    Covers:
    - main() orchestrates config -> system -> add_particles -> visualizer.run
    """
    fake_config = types.SimpleNamespace(num_types=4)

    monkeypatch.setattr(main, "create_or_load_config", lambda: fake_config)

    calls = {
        "particle_system_init": None,
        "add_particles": None,
        "visualizer_init": None,
        "visualizer_run_called": False,
    }

    class FakeParticleSystem:
        def __init__(self, particles, config, width, height):
            calls["particle_system_init"] = {
                "particles": particles,
                "config": config,
                "width": width,
                "height": height,
            }

        def add_particles(self, count, types):
            calls["add_particles"] = {"count": count, "types": types}

    class FakeVisualizer:
        def __init__(self, system, width, height, target_fps, speed_factor):
            calls["visualizer_init"] = {
                "system": system,
                "width": width,
                "height": height,
                "target_fps": target_fps,
                "speed_factor": speed_factor,
            }

        def run(self):
            calls["visualizer_run_called"] = True

    monkeypatch.setattr(main, "ParticleSystem", FakeParticleSystem)
    monkeypatch.setattr(main, "Visualizer", FakeVisualizer)

    main.main()

    assert calls["particle_system_init"]["width"] == 800
    assert calls["particle_system_init"]["height"] == 600
    assert calls["particle_system_init"]["config"] is fake_config

    assert calls["add_particles"]["count"] == 3000
    assert calls["add_particles"]["types"] == list(range(fake_config.num_types))

    assert calls["visualizer_init"]["target_fps"] == 60
    assert calls["visualizer_init"]["speed_factor"] == 4.0
    assert calls["visualizer_run_called"] is True