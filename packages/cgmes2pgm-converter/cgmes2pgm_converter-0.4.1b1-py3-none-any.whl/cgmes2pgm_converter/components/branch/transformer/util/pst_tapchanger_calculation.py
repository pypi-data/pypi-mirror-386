# Copyright [2025] [SOPTIM AG]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

# calculations from ENTSO-E Phase Shift Transformers Modelling
# α: tapAngle
# r: ratio
# ∂u: voltageStepIncrement
# θ: windingConnectionAngle

deg_to_rad = np.pi / 180


def calc_theta_k_2w(
    trafo: pd.Series, tapside: int, tapside_rtc: int
) -> tuple[float, float]:
    """Calculates theta and k for a 2-winding transformer
    based on the tapchanger type.

    Args:
        trafo (pd.Series): Transformer data
        tapside (int): Tap side (1 or 2)
    Returns:
        tuple: theta and k
    """
    theta, k = 0.0, 1.0
    taptype = trafo[f"taptype{tapside}"]

    if taptype == "PhaseTapChangerAsymmetrical" and tapside_rtc != 0:
        taptype = "InPhaseAndAsymPST"

    if taptype == "PhaseTapChangerTabular" and tapside_rtc != 0:
        taptype = "InPhaseAndTabularPST"

    match taptype:
        case "PhaseTapChangerTabular":
            theta = _calc_theta_tabular(trafo, tapside)
            k = _calc_k_tabular(trafo)
        case "InPhaseAndTabularPST":
            theta = _calc_theta_tabular(trafo, tapside)
            k = calc_k_tabular_in_phase(trafo, tapside, tapside_rtc)
        case "PhaseTapChangerLinear":
            logging.warning("Found Transformer with a PhaseTapChangerLinear.")
            logging.warning("\tElectrical Parameters may be inaccurate.")
            theta = _calc_theta_linear(trafo, tapside)
            k = _calc_k_tabular(trafo)
        case "PhaseTapChangerSymmetrical":
            theta, k = _calc_theta_symmetrical(trafo, tapside)
        case "PhaseTapChangerAsymmetrical":
            theta, k = _calc_theta_k_asymmetrical(trafo, tapside)
        case "PhaseTapChanger" | "PhaseTapChangerNonLinear":
            logging.warning(
                "Tapchanger type %s for transformer %s is an abstract class",
                taptype,
                trafo["name1"],
            )
        case "InPhaseAndAsymPST":
            theta, k = calc_theta_k_asymmetrical_in_phase(trafo, tapside, tapside_rtc)
        case _:
            logging.warning(
                "Unknown tapchanger type %s for transformer %s",
                taptype,
                trafo["name1"],
            )

    return theta, k


def calc_theta_k_3w(trafo, tapside, current_side):
    """Calculates theta and k for a 3-winding transformer

    Args:
        trafo (pd.Series): Transformer data
        tapside (int): Tap side of the transformer
        current_side (int): Current side of the transformer

    Returns:
        tuple: theta and k
    """
    if tapside == current_side:
        tapside_rtc = 0  # TODO: determine tapside_rtc
        return calc_theta_k_2w(trafo, tapside, tapside_rtc)

    # The current 2w is a trafo without a tapchanger
    # TODO: validate call of _calc_k_tabular
    return 0.0, _calc_k_tabular(trafo)


def _calc_theta_tabular(trafo, tapside):

    # --- Shift theta ---
    tc_angle1 = trafo["tcAngle1"]
    tc_angle2 = trafo["tcAngle2"]

    tc_angle = tc_angle1 if not np.isnan(tc_angle1) else tc_angle2

    theta = tc_angle * deg_to_rad

    ## TODO: validate with better network!
    if tapside == 2:
        theta *= -1

    return theta


def calc_k_tabular_in_phase(
    trafo,
    tapside,
    tapside_rtc,
):
    ## RTC
    steps_rtc = trafo[f"step{tapside_rtc}_rtc"] - trafo[f"neutralStep{tapside_rtc}_rtc"]

    voltage_increment_rtc = trafo[f"stepSize{tapside_rtc}"]

    u_netz1 = trafo["nomU1"]
    u_netz2 = trafo["nomU2"]
    u_rated1 = trafo["ratedU1"]
    u_rated2 = trafo["ratedU2"]

    k = calc_k_tabular_in_phase2(
        trafo,
        tapside,
        u_netz1,
        u_netz2,
        u_rated1,
        u_rated2,
        voltage_increment_rtc,
        steps_rtc,
    )

    k = 1 / k

    return k


def calc_k_tabular_in_phase2(
    trafo,
    tapside,
    u_netz1,
    u_netz2,
    u_rated1,
    u_rated2,
    voltage_increment_rtc,
    steps_rtc,
):
    w0 = (u_rated2 / u_netz2) / (u_rated1 / u_netz1)
    if tapside == 1:
        w0 = 1 / w0

    ### PST
    tc_ratio1 = trafo["tcRatio1"]
    tc_ratio2 = trafo["tcRatio2"]
    tc_ratio = 1  ## dummy

    if not np.isnan(tc_ratio1):
        tc_ratio = tc_ratio1
        # tc_ratio = 1 / tc_ratio
    elif not np.isnan(tc_ratio2):
        tc_ratio = tc_ratio2
        # tc_ratio = 1 / tc_ratio

    ### RTC

    k_tap = w0 * (1 + (voltage_increment_rtc / 100 * steps_rtc))

    ## COMBINED
    k = k_tap * tc_ratio

    return k


def _calc_theta_linear(trafo, tapside):
    # s = n-n_0
    # α = s * ∂α
    # r = 1

    # TODO: validate if (step - neutralStep) or (neutralStep - step)
    steps = trafo[f"neutralStep{tapside}"] - trafo[f"step{tapside}"]
    shift_per_step = trafo[f"stepPhaseShift{tapside}"] * deg_to_rad
    theta = steps * shift_per_step

    # TODO: check with an example where tapside == 2
    if tapside == 1:
        theta *= -1

    return theta


def _calc_theta_symmetrical(trafo, tapside):
    # Formula from ENTSO-E "Phase Shift Transformers Modelling", chapter 4.2
    #   s = n-n_0
    #   α = 2 * atan(0.5 * s * ∂u)
    #   r = 1
    steps_current = trafo[f"step{tapside}"]
    steps_neutral = trafo[f"neutralStep{tapside}"]
    steps = steps_current - steps_neutral
    voltage_increment = trafo[f"stepVoltageIncrement{tapside}"]

    # theta = 2.0 * np.arctan(0.5 * steps * voltage_increment/100)
    # if tapside == 1:
    #     theta *= -1

    rated_u1_ = trafo["ratedU1"]
    rated_u2_ = trafo["ratedU2"]
    u_netz2 = trafo["nomU2"]
    u_netz1 = trafo["nomU1"]

    w0 = (rated_u2_ / u_netz2) / (rated_u1_ / u_netz1)
    w0 = 1 / w0

    angle = 90 * deg_to_rad
    nenner_pst = 1 + ((steps / 100) * voltage_increment) * complex(
        np.cos(angle), np.sin(angle)
    )
    t_pst = w0 / nenner_pst

    k = 1 / (abs(t_pst) * w0)

    theta = -np.angle(t_pst)

    #####

    rated_hv = rated_u1_
    rated_lv = rated_u2_
    nom_hv = u_netz1
    nom_lv = u_netz2
    if rated_u1_ < rated_u2_:
        rated_lv = rated_u1_
        rated_hv = rated_u2_
        nom_hv = u_netz2
        nom_lv = u_netz1

    tap_side = "hv" if tapside == 1 else "lv"
    # tap_side = "lv"

    _rated_hv, _rated_lv, theta1 = _calc_pp_shift(
        nom_hv,
        nom_lv,
        rated_hv,
        rated_lv,
        0.0,
        [
            TapChanger(
                tap_type="symmetrical",
                tap_side=tap_side,
                tap_pos=steps_current,
                tap_neutral=steps_neutral,
                tap_step_percent=voltage_increment,
                tap_step_degree=0,  # winding_connection_angle * deg_to_rad,
            )
        ],
    )
    ## better for amp
    k1 = _calc_pp_ratio(_rated_hv, _rated_lv, u_netz1, u_netz2)
    k1 = 1 / k1

    #####

    return theta, k
    # return theta1, k1


def _calc_theta_k_asymmetrical(trafo, tapside: int):
    steps_current = trafo[f"step{tapside}"]
    steps_neutral = trafo[f"neutralStep{tapside}"]
    steps = steps_current - steps_neutral
    voltage_increment = trafo[f"stepVoltageIncrement{tapside}"]
    winding_connection_angle = trafo[f"windingConnectionAngle{tapside}"]

    u_netz1 = trafo["nomU1"]
    u_netz2 = trafo["nomU2"]
    u_rated1 = trafo["ratedU1"]
    u_rated2 = trafo["ratedU2"]

    theta, k = calc_theta_k_generic(
        rtc_tapside=0,
        rtc_step=0,
        rtc_voltage_increment=0,
        pst_tapside=tapside,
        pst_step=steps,
        pst_voltage_increment=voltage_increment,
        winding_connection_angle=winding_connection_angle,
        u_rated1=u_rated1,
        u_rated2=u_rated2,
        u_netz1=u_netz1,
        u_netz2=u_netz2,
    )

    #####

    rated_hv = u_rated1
    rated_lv = u_rated2
    nom_hv = u_netz1
    nom_lv = u_netz2
    if u_rated1 < u_rated2:
        rated_lv = u_rated1
        rated_hv = u_rated2
        nom_hv = u_netz2
        nom_lv = u_netz1

    tap_side = "hv" if tapside == 1 else "lv"
    tap_side = "lv"

    # tap_step *= -1
    # tap_side = "lv"

    _rated_hv, _rated_lv, theta1 = _calc_pp_shift(
        nom_hv,
        nom_lv,
        rated_hv,
        rated_lv,
        0.0,
        [
            TapChanger(
                tap_type="asymmetrical",
                tap_side=tap_side,
                tap_pos=steps_current,
                tap_neutral=steps_neutral,
                tap_step_percent=voltage_increment,
                tap_step_degree=winding_connection_angle * deg_to_rad,
            )
        ],
    )
    k1 = _calc_pp_ratio(_rated_hv, _rated_lv, u_netz1, u_netz2)

    #####

    return theta, k
    # return theta1, k1


def calc_theta_k_asymmetrical_in_phase(
    trafo,
    tapside_pst,
    tapside_rtc,
):
    ## PST
    steps_current_pst = trafo[f"step{tapside_pst}"]
    steps_neutral_pst = trafo[f"neutralStep{tapside_pst}"]
    steps_pst = steps_current_pst - steps_neutral_pst

    voltage_increment_pst = trafo[f"stepVoltageIncrement{tapside_pst}"]
    winding_connection_angle = trafo[f"windingConnectionAngle{tapside_pst}"]

    ## RTC

    steps_current_rtc = trafo[f"step{tapside_rtc}_rtc"]
    steps_neutral_rtc = trafo[f"neutralStep{tapside_rtc}_rtc"]
    steps_rtc = steps_current_rtc - steps_neutral_rtc
    voltage_increment_rtc = trafo[f"stepSize{tapside_rtc}"]

    u_netz1 = trafo["nomU1"]
    u_netz2 = trafo["nomU2"]
    u_rated1 = trafo["ratedU1"]
    u_rated2 = trafo["ratedU2"]

    theta, k = calc_theta_k_generic(
        rtc_tapside=tapside_rtc,
        rtc_step=steps_rtc,
        rtc_voltage_increment=voltage_increment_rtc,
        pst_tapside=tapside_pst,
        pst_step=steps_pst,
        pst_voltage_increment=voltage_increment_pst,
        winding_connection_angle=winding_connection_angle,
        u_rated1=u_rated1,
        u_rated2=u_rated2,
        u_netz1=u_netz1,
        u_netz2=u_netz2,
    )

    #####

    rated_hv = u_rated1
    rated_lv = u_rated2
    nom_hv = u_netz1
    nom_lv = u_netz2
    if u_rated1 < u_rated2:
        rated_lv = u_rated1
        rated_hv = u_rated2
        nom_hv = u_netz2
        nom_lv = u_netz1

    _rated_hv, _rated_lv, theta1 = _calc_pp_shift(
        nom_hv,
        nom_lv,
        rated_hv,
        rated_lv,
        0.0,
        [
            TapChanger(
                tap_type="asymmetrical",
                tap_side="hv" if tapside_pst == 1 else "lv",
                tap_pos=steps_pst,
                tap_neutral=steps_neutral_pst,
                tap_step_percent=voltage_increment_pst,
                tap_step_degree=winding_connection_angle * deg_to_rad,
            ),
            TapChanger(
                tap_type="ratio",
                tap_side="hv" if tapside_rtc == 1 else "lv",
                tap_pos=steps_rtc,
                tap_neutral=steps_neutral_rtc,
                tap_step_percent=voltage_increment_rtc,
                tap_step_degree=0.0,
            ),
        ],
    )
    k1 = _calc_pp_ratio(_rated_hv, _rated_lv, u_netz1, u_netz2)
    k1r = 1 / k1

    _rated_hv2, _rated_lv2, theta2 = _calc_pp_shift(
        nom_hv,
        nom_lv,
        rated_hv,
        rated_lv,
        0.0,
        [
            TapChanger(
                tap_type="ratio",
                tap_side="lv",  # "hv" if tapside_rtc == 1 else "lv",
                tap_pos=steps_rtc,
                tap_neutral=steps_neutral_rtc,
                tap_step_percent=voltage_increment_rtc,
                tap_step_degree=0.0,
            ),
            TapChanger(
                tap_type="asymmetrical",
                tap_side="hv",  # "hv" if tapside_pst == 1 else "lv",
                tap_pos=steps_pst,
                tap_neutral=steps_neutral_pst,
                tap_step_percent=voltage_increment_pst,
                tap_step_degree=winding_connection_angle * deg_to_rad,
            ),
        ],
    )
    k2 = _calc_pp_ratio(_rated_hv2, _rated_lv2, u_netz1, u_netz2)
    k2r = 1 / k2

    #####

    return theta, k
    # return theta1, k1 ## better for amp
    # return theta2, k2r


def calc_theta_k_generic(
    rtc_tapside,
    rtc_step,
    rtc_voltage_increment,
    pst_tapside,
    pst_step,
    pst_voltage_increment,
    winding_connection_angle,
    u_rated1,
    u_rated2,
    u_netz1,
    u_netz2,
):
    angle = winding_connection_angle * deg_to_rad
    w0 = (u_rated2 / u_netz2) / (u_rated1 / u_netz1)

    #
    # RTC
    #
    if rtc_tapside == 0:
        t_rtc = 1
    else:

        if rtc_tapside == pst_tapside:
            rtc_step = -rtc_step

        nenner_rtc = 1 + ((rtc_step / 100) * rtc_voltage_increment) * complex(
            np.cos(0), np.sin(0)
        )
        t_rtc = w0 / nenner_rtc

    w0 = w0 * abs(t_rtc)

    ## TODO: dependent on rtc_tapside or pst_tapside?
    w0 = 1 / w0

    #
    # PST
    #
    nenner_pst = 1 + ((pst_step / 100) * pst_voltage_increment) * complex(
        np.cos(angle), np.sin(angle)
    )
    t_pst = w0 / nenner_pst

    ## ----------------------

    if rtc_tapside == 0:
        k = abs(t_pst)
        theta = np.angle(t_pst)
    else:
        k = 1 / abs(t_pst)
        theta = -np.angle(t_pst)

    return theta, k


def _calc_k_tabular(trafo):
    nominal_ratio_ = trafo["nomU1"] / trafo["nomU2"]
    rated_u1_ = trafo["ratedU1"]
    rated_u2_ = trafo["ratedU2"]

    tc_ratio1 = trafo["tcRatio1"]
    tc_ratio2 = trafo["tcRatio2"]

    corr_u1_ = rated_u1_
    corr_u2_ = rated_u2_
    if not np.isnan(tc_ratio1):
        corr_u1_ *= tc_ratio1
    elif not np.isnan(tc_ratio2):
        corr_u2_ *= tc_ratio2

    k = (corr_u1_ / corr_u2_) / nominal_ratio_
    k = 1 / k

    return k


@dataclass
class TapChanger:
    tap_type: Literal["ratio", "asymmetrical", "symmetrical"]
    tap_side: Literal["hv", "lv"]
    tap_pos: int
    tap_neutral: int
    tap_step_percent: float
    tap_step_degree: float


def _calc_pp_shift(
    nom_hv: float,
    nom_lv: float,
    rated_hv: float,
    rated_lv: float,
    base_shift: float,  # in rad, from one PST (can't have multiple PSTs on one transformer)
    tap_changer: list[TapChanger],
):
    shift = base_shift

    for tap in tap_changer:
        direction = 1 if tap.tap_side == "hv" else -1
        tap_diff = tap.tap_pos - tap.tap_neutral

        if tap.tap_type == "ratio" or tap.tap_type == "asymmetrical":
            steps = tap.tap_step_percent * tap_diff / 100
            angle = tap.tap_step_degree

            if tap.tap_side == "lv":
                _rated_u, _shift = _rated_u_steps(direction, rated_lv, steps, angle)
                rated_lv = _rated_u
                shift += _shift
            elif tap.tap_side == "hv":
                _rated_u, _shift = _rated_u_steps(direction, rated_hv, steps, angle)
                rated_hv = _rated_u
                shift += _shift
            else:
                logging.warning("Unknown tap changer side: %s", tap.tap_side)
                continue

        elif tap.tap_type == "symmetrical":

            if tap.tap_side == "lv":
                shift += 1 * tap_diff * tap.tap_step_degree
            elif tap.tap_side == "hv":
                shift -= 1 * tap_diff * tap.tap_step_degree

            ## arcsin(x) ~~ arctan(x) for small x
            shift2 = (
                direction
                * 2
                # * np.rad2deg(np.arcsin(tap_diff * tap.tap_step_percent / 100 / 2))
                * np.arcsin(tap_diff * tap.tap_step_percent / 100 / 2)
            )
            shift += (
                direction * 2 * np.arctan(0.5 * tap_diff * tap.tap_step_percent / 100)
            )
            wait = 1

        else:
            ratio = 1.0
            logging.warning("Unknown tap changer type: %s", tap.tap_type)

    return rated_hv, rated_lv, shift


def _rated_u_steps(direction, rated_u, steps_percent, angle):
    _du = rated_u * steps_percent
    _rated_u = np.sqrt(
        (rated_u + _du * np.cos(angle)) ** 2 + (_du * np.sin(angle)) ** 2
    )
    _shift = np.arctan(
        direction * _du * np.sin(angle) / (rated_u + _du * np.cos(angle))
    )
    _shift2 = np.arctan2(
        direction * _du * np.sin(angle), (rated_u + _du * np.cos(angle))
    )
    return _rated_u, _shift


def _calc_pp_ratio(rated_hv, rated_lv, nom_hv, nom_lv):
    tap_ratio = rated_hv / rated_lv
    nom_ratio = nom_hv / nom_lv
    return tap_ratio / nom_ratio
