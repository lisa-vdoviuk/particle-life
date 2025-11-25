from dataclasses import dataclass, field
from typing import List, Dict, Any, Sequence
import json
import os

@dataclass
class SimulationConfig:
    """
    Place for all configuration parameters.

    Attributes:
    ---------------------------------------
    num_types: int 
        How many different particle types exist

    interaction_matrix: List[List[float]]
        interaction_matrix[i][j] describes how particles of type i
    
    particle_colors: list of str
        Color for each particle type. Length must be >= num_types

    friction: float
        Damping factor applied to velocities each update step

    max_velocity: float
        Maximum allowed speed for any particle (used for clamping)

    interaction_radius: float
        Maximum distance where forces between particles are applied

    random_motion: float
        Additional random “jitter” added to particle velocities
    """
    num_types: int = 4
    friction: float = 0.1
    max_velocity: float = 3.0
    interaction_radius: float = 50.0
    random_motion: float = 0.01

    particle_colors: List[str] = field(default_factory=list)
    interaction_matrix: List[List[float]] = field(init=False)

    def __post_init__(self) -> None:
        if not self.particle_colors:
            # default colors if none provided
            default_colors = ["red", "green", "yellow", "blue", "magenta", "cyan"]
            self.particle_colors = default_colors[: self.num_types]

        # initialize matrix with zeroes
        self._init_interaction_matrix(default_value=0.0)
    
    # -------------- helpers ------------------

    def _init_interaction_matrix(self, default_value: float = 0.0) -> None:
        self.interaction_matrix = [
            [float(default_value) for _ in range(self.num_types)]
            for _ in range(self.num_types)
        ]
    def _validate_type_index(self, t: int)->None:
        if not(0<=t<self.num_types):
            raise IndexError(
                f"Particle type index {t} out of range [0,{self.num_types- 1 }]"
            )
    def _validate_matrix_shape(self, matrix: Sequence[Sequence[Any]]) -> None:
        if len(matrix) != self.num_types:
            raise ValueError(
                f"Interaction matrix must have {self.num_types} rows "
                f"(got {len(matrix)})"
            )
        for row in matrix:
            if len(row)!= self.num_types:
                raise ValueError(
                    "Interaction matrix must be square "
                    f"({self.num_types} x {self.num_types})"
                )

    # ----------------- API for interaction matrix -----------------

    def get_interaction(self, type1: int, type2: int)-> float:
        # Returns interaction strength from type1 to type2
        self._validate_type_index(type1)
        self._validate_type_index(type2)
        return self.interaction_matrix[type1][type2]
    
    def set_interaction(self, type1: int, type2: int, value: float)->None:
        # Set interaction strength from type1 to type2
        self._validate_type_index(type1)
        self._validate_type_index(type2)
        self.interaction_matrix[type1][type2]=float(value)
    
    #-------------- parameter update (for GUI) ----------------------

    def update_parameter(self, param_name: str, value: float) -> None:
        if not hasattr(self, param_name):
            raise ValueError(f"Unknown config parameter: {param_name}")
        
        if param_name in {"interaction_matrix"}:
            raise ValueError("Use set_interaction() to change the interaction matrix.")
        if param_name == "num_types":
            raise ValueError(
                "Changing num_types after initialization is not supported."
            )
        setattr(self, param_name, float(value))

    # -------------- saving / loading config ------------------------

    def to_dict(self)->dict:
        # Converts the configuration into a plain dict (for JSON save)
        return {
            "num_types": self.num_types,
            "friction": self.friction,
            "max_velocity": self.max_velocity,
            "interaction_radius": self.interaction_radius,
            "random_motion": self.random_motion,
            "particle_colors": self.particle_colors,
            "interaction_matrix": self.interaction_matrix,
        }
    @classmethod
    def from_dict(cls, data: dict)-> "SimulationConfig":
        # Create a SimulationConfig from a dict (inverse of to_dict())
        num_types = int(data.get("num_types",4))

        cfg = cls(
            num_types=num_types,
            friction=float(data.get("friction", 0.1)),
            max_velocity=float(data.get("max_velocity", 3.0)),
            interaction_radius=float(data.get("interaction_radius", 50.0)),
            random_motion=float(data.get("random_motion", 0.01)),
            particle_colors=list(data.get("particle_colors", [])),
        )

        matrix = data.get("interaction_matrix")

        if matrix is not None:
            cfg._validate_matrix_shape(matrix)
            for i in range(num_types):
                for j in range(num_types):
                    cfg.interaction_matrix[i][j] = float(matrix[i][j])
        
        return cfg
    
    def save_config(self, file_path: str) -> None:
        """
        Save configuration as JSON.

        This will later be triggered by GUI
        or used during development.
        """
        data = self.to_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_config(cls, file_path: str) -> "SimulationConfig":
        # Load configuration from a JSON file
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)
        with open(file_path, "r", encoding = "urf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)