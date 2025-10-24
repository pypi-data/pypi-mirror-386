# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""-------"""

from dataclasses import dataclass, field


@dataclass
class OpPhCalculationIterationPeriod:
    summer_heat_flow_to_ground_w: float = 0.0
    winter_ground_temp: float = 0.0
    summer_ground_temp: float = 0.0
    interior_air_temp: float = 0.0
    q_pi: float = 0.0
    q_ges: float = 0.0

    # --
    average_interior_temps: list[float] = field(default_factory=list)
    average_interior_temp: float = 0.0
    cos_amplitude: float = 0.0
    sin_amplitude: float = 0.0
    amplitude: float = 0.0
    phase_month: float = 0.0


@dataclass(frozen=True)
class OpPhCalculationIteration:
    periods: list[OpPhCalculationIterationPeriod] = field(default_factory=list)
