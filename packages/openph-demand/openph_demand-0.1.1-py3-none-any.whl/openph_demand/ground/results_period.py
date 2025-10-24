# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Dataclasses for the: PHPP | Ground."""

from dataclasses import dataclass
from math import atan, log, pi, sqrt
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.model.climate import OpPhClimateCalcPeriod
    from openph.phpp import OpPhPHPP


def sumxmy2(list_1: list[float], list_2: list[float]) -> float:
    """Utility function replicating the behavior of Excel's SUMXMY2() function."""
    if len(list_1) != len(list_2):
        raise ValueError("Error. Lists must be the same lenght")
    return sum((x - y) ** 2 for x, y in zip(list_1, list_2))


@dataclass
class OpPhGroundResultPeriod:
    phpp: "OpPhPHPP"
    period_climate: "OpPhClimateCalcPeriod"
    total_heat_flow_to_ground_w: float = 0.0


@dataclass
class OpPhGroundEstimate:
    """Data and Calculations to determine an approximate ground conductance value (W/K)

    PHPP V10 | Ground | C205:Q236
    """

    phpp: "OpPhPHPP"

    @property
    def thermal_conductivity_W_mk(self) -> float:
        """Wärmeleitfähigkeit

        PHPP V10 | Ground | H207

        Units: W/K
        """
        return 2.0

    @property
    def heat_capacity_MJ_m2_k(self) -> float:
        """Wärmekapazität

        PHPP V10 | Ground | H208

        Units: MJ/m2-K
        """
        return 2.0

    @property
    def periodic_penetration_depth_m(self) -> float:
        """periodische Eindringtiefe
        PHPP V10 | Ground | H209

        =IF(ISNUMBER(H208),SQRT(365*24*3600*H207/(PI()*H208*1000000)),"")

        Units: m
        """

        return sqrt(
            365
            * 24
            * 3600
            * self.thermal_conductivity_W_mk
            / (pi * self.heat_capacity_MJ_m2_k * 1_000_000)
        )

    @property
    def area_of_floor_slab_m2(self) -> float:
        """Fläche Bodenplatte / Kellerdecke
        PHPP V10 | Ground | H211

        =SUM(Areas!L16,Areas!L18)

        Units: m2
        """
        return (
            self.phpp.areas.walls_to_ground_area_m2
            + self.phpp.areas.floors_to_ground_area_m2
        )

    @property
    def aspect_ratio(self) -> float:
        """Seitenverhältnis Bodenplatte: 1

        PHPP V10 | Ground | H212
        """
        return 3.0

    @property
    def scope_of_floor_slab(self) -> float:
        """Umfang Bodenplatte / Kellerdecke

        PHPP V10 | Ground H213

        =IF(H211>0,MAX(2*(H212+1)*SQRT(H211/H212),2*H211/8),1)
        """
        if self.area_of_floor_slab_m2 > 0:
            return max(
                2
                * (self.aspect_ratio + 1)
                * sqrt(self.area_of_floor_slab_m2 / self.aspect_ratio),
                2 * self.area_of_floor_slab_m2 / 8,
            )
        else:
            return 1.0

    @property
    def characteristic_dimension_of_floor_slab(self) -> float:
        """charakt. Bodenplattenmaß

        PHPP V10 | Ground | H214

        =IF(AND(ISNUMBER(H211),H213>0),2*H211/H213,"")
        """
        try:
            return 2 * self.area_of_floor_slab_m2 / self.scope_of_floor_slab
        except ZeroDivisionError:
            return 0.0

    @property
    def conductance_of_something_W_m2K(self) -> float:
        """U-Wert BP / KD inkl. WB

        PHPP V10 | Ground | P213

        =IF(H211>0,P218/H211,1)

        Units: W/m2-k
        """
        try:
            return self.conductivity_of_building_W_K / self.area_of_floor_slab_m2
        except ZeroDivisionError:
            return 1.0

    @property
    def effective_soil_depth_m(self) -> float:
        """wirksame Dicke des Bodens

        PHPP V10 | Ground | P214

        =IF(AND(ISNUMBER(P213),P213>0),H207/P213,0)

        Units: m
        """
        try:
            return self.thermal_conductivity_W_mk / self.conductance_of_something_W_m2K
        except ZeroDivisionError:
            return 0.0

    @property
    def conductivity_of_building_W_K(self) -> float:
        """Leitwert Gebäude

        PHPP V10 | Ground | P218

        =SUM(Areas!AU16,Areas!AU18,Areas!AU24,Areas!AU25)

        Units: W/K
        """
        return (
            self.phpp.areas.total_walls_to_ground_heat_loss_factor_W_K
            + self.phpp.areas.total_floors_to_ground_heat_loss_factor_W_K
            + self.phpp.areas.total_perimeter_thermal_bridge_heat_loss_factor_W_K
            + self.phpp.areas.total_below_grade_thermal_bridge_heat_loss_factor_W_K
        )

    @property
    def floor_slab_transmittance_to_ground(self) -> float:
        """Bodenplatte auf Erdreich Wärmedurchgangskoeffizient

        PHPP V10 | Ground | H216

        =IF(P214>=H214,H207/(0.457*H214+P214),2*H207/(PI()*H214+P214)*LN(PI()*H214/P214+1))
        """
        if self.effective_soil_depth_m >= self.characteristic_dimension_of_floor_slab:
            return self.thermal_conductivity_W_mk / (
                0.457 * self.characteristic_dimension_of_floor_slab
                + self.effective_soil_depth_m
            )
        else:
            return (
                (2 * self.thermal_conductivity_W_mk)
                / (
                    pi * self.characteristic_dimension_of_floor_slab
                    + self.effective_soil_depth_m
                )
                * log(
                    pi
                    * self.characteristic_dimension_of_floor_slab
                    / self.effective_soil_depth_m
                    + 1
                )
            )

    @property
    def conductance_to_ground_W_K(self):
        """Zwischenergebnisse stationärer Leitwert

        PHPP V10 | Ground | H218

        =H216*H211*1.1

        Units: W/K
        """
        return (
            self.floor_slab_transmittance_to_ground * self.area_of_floor_slab_m2 * 1.1
        )

    @property
    def outer_harmonic_conductance(self):
        """äußerer harmonischer Leitwert

        PHPP V10 | Ground | H219

        =0.37*H213*H207*LN(H209/P214+1)

        Units: W/K
        """
        result = (
            0.37
            * self.scope_of_floor_slab
            * self.thermal_conductivity_W_mk
            * log(self.periodic_penetration_depth_m / self.effective_soil_depth_m + 1)
        )
        return result

    @property
    def outer_phase_shift(self):
        """äußere Phasenverschiebung

        PHPP V10 | Ground | H220

        =1.5-0.42*LN(H209/P214+1)+IF(1.5-0.42*LN(H209/P214+1)<0,6,0)

        Units: W/K
        """
        a = 1.5 - 0.42 * log(
            self.periodic_penetration_depth_m / self.effective_soil_depth_m + 1
        )
        if a < 0:
            b = 6
        else:
            b = 0
        return a + b

    @property
    def inner_harmonic_conductance(self):
        """innerer harmonischer Leitwert

        PHPP V10 | Ground | H221

        =H211*H207/P214*SQRT(2/((1+H209/P214)^2+1))

        Units: W/K
        """
        return (
            self.area_of_floor_slab_m2
            * self.thermal_conductivity_W_mk
            / self.effective_soil_depth_m
            * sqrt(
                2
                / (
                    (
                        1
                        + self.periodic_penetration_depth_m
                        / self.effective_soil_depth_m
                    )
                    ** 2
                    + 1
                )
            )
        )

    @property
    def inner_phase_shift(self):
        """innere Phasenverschiebung

        PHPP V10 | Ground | H222

        =MAX(0,1.5-6/PI()*ATAN(P214/(P214+H209)))

        Units: W/K
        """
        return max(
            0,
            1.5
            - 6
            / pi
            * atan(
                self.effective_soil_depth_m
                / (self.effective_soil_depth_m + self.periodic_penetration_depth_m)
            ),
        )
