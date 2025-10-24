# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""OpPhPHPP Dataclasses for the: PHPP | Ground."""

from math import atan, cos, pi, sin, sqrt
from typing import TYPE_CHECKING

# -- Need to do this to avoid circular imports
if TYPE_CHECKING:
    from openph.model.climate import OpPhClimateCalcPeriod
    from openph.phpp import OpPhPHPP

    from openph_demand.cooling_demand.calc_periods import OpPhCoolingDemandCalcPeriod
    from openph_demand.heating_demand.calc_periods import OpPhHeatingDemandCalcPeriod

from openph_demand.get_solvers import (
    get_openph_energy_demand_solver,
    get_openph_ground_solver,
)
from openph_demand.ground.calc_periods import (
    OpPhCalculationIteration,
    OpPhCalculationIterationPeriod,
)


def calc_interior_temperature_C(
    phpp: "OpPhPHPP",
    gg_temp_winter_c: float,
    gg_temp_summer_c: float,
) -> float:
    """

    PHPP V10 | Ground | E127:P127

    =MAX($F$122,MIN(IF($N$122="x",$I$122,MAX($I$122,E126)),AVERAGE(E125,E126)))

    Units: C
    """

    min_interior_temp_c = phpp.set_points.min_interior_temp_c
    max_interior_temp_c = phpp.set_points.max_interior_temp_c
    active_cooling_on = phpp.active_cooling_on
    winter_temp_c = gg_temp_winter_c
    summer_temp_c = gg_temp_summer_c

    if active_cooling_on:
        summer_interior_temp = max_interior_temp_c
    else:
        summer_interior_temp = max(max_interior_temp_c, summer_temp_c)

    avg_gg_temp = (winter_temp_c + summer_temp_c) / 2
    return max(min_interior_temp_c, min(summer_interior_temp, avg_gg_temp))


def calc_cos_amplitude(
    period_interior_temperatures_c: list[float],
    period_numbers: list[int],
) -> float:
    """
    PHPP V10 | Ground | T126

    =SUMPRODUCT(E127:P127,COS(PI()*$E$123:$P$123/6))/6

    E123:P123 = Month numbers (1, 2, 3, ..., 12)
    E127:P127 = Monthly interior temperatures (°C)

    Units: -
    """
    # Calculate SUMPRODUCT(E127:P127, COS(PI() * E123:P123 / 6))
    sum_product_result = sum(
        temp * cos(pi * month / 6)
        for temp, month in zip(period_interior_temperatures_c, period_numbers)
    )

    # Divide by 6
    return sum_product_result / 6


def calc_sin_amplitude(
    period_interior_temperatures_c: list[float],
    period_numbers: list[int],
) -> float:
    """
    PHPP V10 | Ground | T127

    =SUMPRODUCT(E127:P127,SIN(PI()*$E$123:$P$123/6))/6

    Units: -
    """
    # Calculate SUMPRODUCT(E127:P127, SIN(PI() * E123:P123 / 6))
    sum_product_result = sum(
        temp * sin(pi * month / 6)
        for temp, month in zip(period_interior_temperatures_c, period_numbers)
    )

    # Divide by 6
    return sum_product_result / 6


def calc_amplitude(_cos_amplitude: float, _sin_amplitude: float) -> float:
    """
    PHPP V10 | Ground | T128

    =SQRT(T126^2+T127^2)

    Units: -
    """
    return sqrt(_cos_amplitude**2 + _sin_amplitude**2)


def calc_phase_month(
    _amplitude: float, _cos_amplitude: float, _sin_amplitude: float
) -> float:
    """
    PHPP V10 | Ground | T129

    =IF(T128<0.00000001,0,ATAN(T127/T126)/2/PI()*12+IF(T126<0,6,0))

    Units: -
    """

    if _amplitude < 0.00000001:
        return 0
    else:
        if _cos_amplitude < 0:
            value = 6
        else:
            value = 0
        return (atan(_sin_amplitude / _cos_amplitude) / 2 / pi) * 12 + value


def calc_winter_ground_temp(
    _phpp: "OpPhPHPP",
    _period_heating: "OpPhHeatingDemandCalcPeriod",
    _period_climate: "OpPhClimateCalcPeriod",
    _previous_iteration_q_res: float,
) -> float:
    """
    PHPP V10 | Ground | E132:P132

    ==(
        (Heating!$R$101 + Heating!$R$104) * Heating!T$69
        - E129 + Heating!$R$103 * $P$11
        + Heating!$R$105* Heating!T$75
        + Heating!T$114 / Heating!T$96 * 1000
    ) / ( Heating!$R$101 + Heating!$R$104+ Heating!$R$103+ Heating!$R$105)
    """
    energy_demand = get_openph_energy_demand_solver(_phpp)
    ground_solver = get_openph_ground_solver(_phpp)
    # Calculate numerator
    numerator = (
        (
            energy_demand.heating_demand.conductance_factor_to_outdoor_air
            + energy_demand.heating_demand.convection_factor_W_K
        )
        * _period_climate.temperature_air_c
        - _previous_iteration_q_res
        + energy_demand.heating_demand.conductance_factor_to_EWU
        * ground_solver.average_ground_surface_temp_C
        + energy_demand.heating_demand.radiation_factor_W_K
        * _period_climate.temperature_sky_c
        + _period_heating.total_heat_gain / _period_climate.period_length_hours * 1000
    )

    # Calculate denominator
    denominator = (
        energy_demand.heating_demand.conductance_factor_to_outdoor_air
        + energy_demand.heating_demand.convection_factor_W_K
        + energy_demand.heating_demand.conductance_factor_to_EWU
        + energy_demand.heating_demand.radiation_factor_W_K
    )

    # Return result
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return 0.0


def calc_summer_ground_temp(
    _phpp: "OpPhPHPP",
    _period_cooling: "OpPhCoolingDemandCalcPeriod",
    _period_climate: "OpPhClimateCalcPeriod",
    _previous_iteration_q_res: float,
) -> float:
    """
    PHPP V10 | Ground | E133:P133

    =(
        (Cooling!$R$112 + Cooling!$R$114 + Cooling!T$125) * Cooling!T$84
        - E129
        + Cooling!T$126 * $P$11
        + Cooling!T$135 * Cooling!T$134
        + Cooling!T$140 * Cooling!T$137
        + Cooling!$R$115 * Cooling!T$91
        + E$124
    )/(Cooling!$R$112 + Cooling!$R$114 + Cooling!T$125 + Cooling!T$126 + Cooling!T$135 + Cooling!T$140 + Cooling!$R$115)
    """
    ground_solver = get_openph_ground_solver(_phpp)
    # Calculate Total Heat Input from all elements
    total_heat_input = (
        (
            _phpp.areas.envelop_conductance_to_ambient_air_W_K
            + _phpp.areas.envelope_convective_factor_W_K
            + _period_cooling.balanced_mech_vent_conductance_to_air_W_K
        )
        * _period_climate.temperature_air_c
        - _previous_iteration_q_res
        + _period_cooling.balanced_mech_vent_conductance_to_soil_W_K
        * ground_solver.average_ground_surface_temp_C
        + _period_cooling.exhaust_mech_vent_thermal_conductance_W_K
        * _period_cooling.exhaust_mech_vent_average_temperature_C
        + _period_cooling.envelope_vent_window_effective_thermal_conductance_W_K
        * _period_cooling.envelope_vent_air_average_temperature_C
        + _phpp.areas.envelope_radiative_factor_W_K * _period_climate.temperature_sky_c
        + _period_cooling.summer_heat_supply_to_ground_W
    )
    # Calculate Total Thermal Conductance of all Elements
    total_thermal_conductance = (
        _phpp.areas.envelop_conductance_to_ambient_air_W_K
        + _phpp.areas.envelope_convective_factor_W_K
        + _period_cooling.balanced_mech_vent_conductance_to_air_W_K
        + _period_cooling.balanced_mech_vent_conductance_to_soil_W_K
        + _period_cooling.exhaust_mech_vent_thermal_conductance_W_K
        + _period_cooling.envelope_vent_window_effective_thermal_conductance_W_K
        + _phpp.areas.envelope_radiative_factor_W_K
    )

    # Return result
    try:
        return total_heat_input / total_thermal_conductance
    except ZeroDivisionError:
        return 0.0


def calc_q_pi(
    _amplitude: float,
    _phase_month: float,
    _inner_harmonic_conductance: float,
    _inner_phase_shift: float,
    _period_number: int,
    _previous_iteration_q_pi: float,
    _relaxation_factor: float = 0.4,
) -> float:
    """
    PHPP V10 | Ground | E128:P128

    =(1-$Q$122)*E128+$Q$122*$P$120*$T135*COS(2*PI()*(E$123-$T136+6+$P$121)/12)

    Units: ?
    """
    return (
        1 - _relaxation_factor
    ) * _previous_iteration_q_pi + _relaxation_factor * _inner_harmonic_conductance * _amplitude * cos(
        2 * pi * (_period_number - _phase_month + 6 + _inner_phase_shift) / 12
    )


def calc_q_ges(
    iteration_period: OpPhCalculationIterationPeriod,
    conductance_to_ground: float,
    outer_harmonic_conductance: float,
    outer_phase_shift: float,
    average_interior_temp: float,
    average_ground_surface_temp_c: float,
    amplitude_theta_e_m_deg_c: float,
    phase_shift_theta_e_months: float,
    period_number: int,
) -> float:
    """
    PHPP V10 | Ground | E128:P128

    =$H$119*($T125-$P$11)+$H$120*$P$12*COS(2*PI()*(E$111-$P$13-$H$121)/12)-E128

    Units: ?
    """

    return (
        conductance_to_ground * (average_interior_temp - average_ground_surface_temp_c)
        + outer_harmonic_conductance
        * amplitude_theta_e_m_deg_c
        * cos(
            2
            * pi
            * (period_number - phase_shift_theta_e_months - outer_phase_shift)
            / 12
        )
        - iteration_period.q_pi
    )


def solve_for_iteration_temperatures(
    _previous_iteration: OpPhCalculationIteration,
    _current_iteration: OpPhCalculationIteration,
    _phpp: "OpPhPHPP",
) -> None:
    """Solve for the ground and interior temperatures for each calculation period."""
    energy_demand = get_openph_energy_demand_solver(_phpp)

    for (
        period_cooling,
        period_heating,
        period_climate,
        period_previous_iteration,
    ) in zip(
        energy_demand.cooling_demand.periods,
        energy_demand.heating_demand.periods,
        _phpp.climate.periods,
        _previous_iteration.periods,
    ):
        new_iteration_period = OpPhCalculationIterationPeriod()
        new_iteration_period.summer_heat_flow_to_ground_w = (
            period_cooling.summer_heat_supply_to_ground_W
        )
        new_iteration_period.winter_ground_temp = calc_winter_ground_temp(
            _phpp, period_heating, period_climate, period_previous_iteration.q_ges
        )
        new_iteration_period.summer_ground_temp = calc_summer_ground_temp(
            _phpp, period_cooling, period_climate, period_previous_iteration.q_ges
        )
        new_iteration_period.interior_air_temp = calc_interior_temperature_C(
            _phpp,
            new_iteration_period.winter_ground_temp,
            new_iteration_period.summer_ground_temp,
        )
        _current_iteration.periods.append(new_iteration_period)


def solve_for_iteration_heat_flows(
    _previous_iteration: OpPhCalculationIteration,
    _current_iteration: OpPhCalculationIteration,
    _phpp: "OpPhPHPP",
) -> None:
    """Solve for the heat-flow to ground for each calculation-period."""
    ground_solver = get_openph_ground_solver(_phpp)
    average_interior_temps = [p.interior_air_temp for p in _current_iteration.periods]
    average_interior_temp = sum(average_interior_temps) / len(average_interior_temps)

    # -- Calculate and store the new heat-flow values for each calc-period
    for period_previous_iteration, period_current_iteration, period_climate in zip(
        _previous_iteration.periods, _current_iteration.periods, _phpp.climate.periods
    ):
        period_current_iteration.cos_amplitude = calc_cos_amplitude(
            average_interior_temps, _phpp.climate.period_numbers
        )
        period_current_iteration.sin_amplitude = calc_sin_amplitude(
            average_interior_temps, _phpp.climate.period_numbers
        )
        period_current_iteration.amplitude = calc_amplitude(
            period_current_iteration.cos_amplitude,
            period_current_iteration.sin_amplitude,
        )
        period_current_iteration.phase_month = calc_phase_month(
            period_current_iteration.amplitude,
            period_current_iteration.cos_amplitude,
            period_current_iteration.sin_amplitude,
        )

        # -- Calculate the new heat-flow value
        period_current_iteration.q_pi = calc_q_pi(
            period_current_iteration.amplitude,
            period_current_iteration.phase_month,
            ground_solver.inner_harmonic_conductance,
            ground_solver.inner_phase_shift,
            period_climate.period_number,
            period_previous_iteration.q_pi,
        )
        period_current_iteration.q_ges = calc_q_ges(
            period_current_iteration,
            ground_solver.conductance_to_ground_W_K,
            ground_solver.outer_harmonic_conductance,
            ground_solver.outer_phase_shift,
            average_interior_temp,
            ground_solver.average_ground_surface_temp_C,
            ground_solver.amplitude_theta_e_m_deg_C,
            ground_solver.phase_shift_theta_e_Months,
            period_climate.period_number,
        )
