#!/usr/bin/env python3
"""生成 configs/workflows/*.json —— 五个文献落地的实验工作流模板（spec v1.0）。

依据：A-Lab（Szymanski 2023，固相合成三站流程）、目标相 Ba5Y12Zn[O(SiO4)]8 的
高温溶液/Pt 坩埚生长（Ababaikeri 2024）、BaZn2Si2O7 固相反应（Kerstan 2013 / Thieme 2022）、
SafeLab 九类操作语法与安全阈值（Bai 2026）。资产 key 来自 configs/safelab_asset_registry.json。

用法：.venv/bin/python tools/gen_workflow_templates.py [--out configs/workflows]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMB = {"robot": "franka_fr3", "gripper": "franka_hand", "base_pose": [0, 0, 0, 1, 0, 0, 0]}
SAFETY = {"dp_max_mm": 20, "theta_dev_max_rad": 0.25, "f_peak_max_n": 20, "tilt_limit_rad": 0.85}
ON_ERROR = {"retry": 3, "then": "request_user_input"}
HOT = {"f_peak_max_n": 10, "theta_dev_max_rad": 0.15}  # 热坩埚/托盘：更严的倾斜与接触力


# ------------------------------------------------------------- primitive helpers
def pp(obj, to, **s):            return {"op": "pick_place", "object": obj, "to": to, **({"safety": s} if s else {})}
def door(st, open_=True):        return {"op": "open_door" if open_ else "close_door", "station": st}
def lid(st, open_=True):         return {"op": "open_lid" if open_ else "close_lid", "station": st}
def press(st, button):           return {"op": "press_button", "station": st, "button": button}
def wait(sec):                   return {"op": "wait", "seconds": sec}
def weigh(obj, st):              return {"op": "weigh", "object": obj, "station": st}
def uncap(obj):                  return {"op": "uncap", "object": obj}
def cap(obj):                    return {"op": "cap", "object": obj}
def pourp(obj, to):              return {"op": "pour_powder", "object": obj, "to": to}
def pourl(obj, to, ml):          return {"op": "pour_liquid", "object": obj, "to": to, "volume_ml": ml}
def stir(tool, st, sec):         return {"op": "stir", "tool": tool, "station": st, "seconds": sec}
def flatten(obj, tool):          return {"op": "flatten", "object": obj, "tool": tool}
def insert(obj, to, **s):        return {"op": "insert_rack", "object": obj, "to": to, **({"safety": s} if s else {})}
def extract(obj, to, **s):       return {"op": "extract_rack", "object": obj, "to": to, **({"safety": s} if s else {})}
def tongs(tool, obj, to, **s):   return {"op": "grasp_with_tool", "tool": tool, "object": obj, "to": to, **({"safety": s} if s else {})}


def station(id_, instrument, asset, pose):
    return {"id": id_, "instrument": instrument, "asset": asset, "pose": pose}


def obj(id_, labware, asset, pose=None, sample=None):
    d = {"id": id_, "labware": labware, "asset": asset}
    if pose is not None:
        d["pose"] = pose
    if sample:
        d["sample"] = sample
    return d


def task(id_, type_, st, samples, prims, params=None, deps=(), instruction=None, safety=None):
    d = {"id": id_, "type": type_, "station": st, "samples": samples, "depends_on": list(deps),
         "params": params or {}, "primitives": prims, "on_error": ON_ERROR}
    if instruction:
        d["instruction"] = instruction
    if safety:
        d["safety"] = safety
    return d


def dose_sequence(bottle, paper, st_dose, st_rack):
    """称量一种前驱体：取瓶→开盖→倒粉到称量纸→合盖→称重→放回架。"""
    return [pp(bottle, st_dose), uncap(bottle), pourp(bottle, paper), cap(bottle), weigh(paper, st_dose), pp(bottle, st_rack)]


def furnace_cycle(tray, st_furnace, st_out, program="start", hold_s=60, cool_s=30):
    """A-Lab Heating：开门→送架→关门→启动→保温→开门→取架→关门→台面冷却。"""
    return [door(st_furnace), insert(tray, st_furnace, **HOT), door(st_furnace, False), press(st_furnace, program),
            wait(hold_s), door(st_furnace), extract(tray, st_out, **HOT), door(st_furnace, False), wait(cool_s)]


# ------------------------------------------------------------- the five workflows
def wf01():
    """固相法煅烧：BaCO3 + 2 ZnO + 2 SiO2 → BaZn2Si2O7（A-Lab 三站流程的前半段）。"""
    return {
        "spec_version": "1.0", "id": "wf01_solid_state_calcination",
        "title": "Solid-state calcination of BaZn2Si2O7 from carbonate/oxide precursors (A-Lab dosing → grinding → box-furnace cycle)",
        "goal": {"objective": "Prepare a BaZn2Si2O7 pellet-free powder sample by the A-Lab solid-state route: weigh stoichiometric BaCO3/ZnO/SiO2, grind, calcine in a box furnace, recover the crucible for characterization.",
                 "target_phase": "BaZn2Si2O7", "literature": ["kerstan2013bazn2si2o7", "thieme2022solid", "szymanski2023alab"]},
        "embodiment": EMB,
        "samples": [{"name": "s1", "precursors": {"BaCO3": 0.987, "ZnO": 0.814, "SiO2": 0.601}, "labware": ["crucible_s1"],
                     "note": "5 mmol BaZn2Si2O7: 0.987 g BaCO3, 0.814 g ZnO, 0.601 g SiO2"}],
        "stations": [
            station("dosing_1", "dosing_station", "Precision_Electronic_Balance", [0.55, 0.30, 0.0]),
            station("grinder_1", "shaker_grinder", "mortar", [0.50, 0.00, 0.0]),
            station("transfer_1", "transfer_rack", "Test_Tube_Rack", [0.35, -0.30, 0.0]),
            station("furnace_1", "box_furnace", "art:Oven065", [0.75, -0.35, 0.0]),
            station("rack_1", "storage_rack", "Test_Tube_Rack", [0.30, 0.45, 0.0]),
        ],
        "objects": [
            obj("bottle_BaCO3", "precursor_bottle", "brown_reagent_bottle_small", [0.30, 0.55, 0.0]),
            obj("bottle_ZnO", "precursor_bottle", "clear_reagent_bottle_small", [0.38, 0.55, 0.0]),
            obj("bottle_SiO2", "precursor_bottle", "clear_reagent_bottle_large", [0.46, 0.55, 0.0]),
            obj("paper_1", "xrd_holder", "weighing_paper", [0.55, 0.30, 0.02]),
            obj("pestle_1", "tongs", "pestle", [0.42, 0.05, 0.0]),
            obj("crucible_s1", "crucible", "Crucible", [0.40, -0.15, 0.0], sample="s1"),
            obj("tray_1", "crucible_tray", None, [0.35, -0.30, 0.0]),
        ],
        "tasks": [
            task("t_start", "Starting", "rack_1", ["s1"], [], instruction="Register sample s1 and confirm all three precursor bottles are on the rack."),
            task("t_dose", "PowderDosing", "dosing_1", ["s1"],
                 [pp("paper_1", "dosing_1"), press("dosing_1", "tare")]
                 + dose_sequence("bottle_BaCO3", "paper_1", "dosing_1", "rack_1")
                 + dose_sequence("bottle_ZnO", "paper_1", "dosing_1", "rack_1")
                 + dose_sequence("bottle_SiO2", "paper_1", "dosing_1", "rack_1"),
                 params={"powder_dispenses": {"BaCO3": 0.987, "ZnO": 0.814, "SiO2": 0.601}, "tolerance_mg": 5}, deps=["t_start"],
                 instruction="Weigh 0.987 g BaCO3, 0.814 g ZnO and 0.601 g SiO2 onto the weighing paper, taring between reagents."),
            task("t_grind", "Grinding", "grinder_1", ["s1"],
                 [pourp("paper_1", "grinder_1"), pp("pestle_1", "grinder_1"), stir("pestle_1", "grinder_1", 120), pp("pestle_1", "rack_1"),
                  pourp("grinder_1", "crucible_s1")],
                 params={"duration_s": 120}, deps=["t_dose"],
                 instruction="Transfer the weighed powders into the mortar, grind for 2 minutes with the pestle, then pour the mixture into the crucible."),
            task("t_load", "Moving", "transfer_1", ["s1"], [pp("crucible_s1", "tray_1")], params={"destination": "tray_1"}, deps=["t_grind"]),
            task("t_heat", "Heating", "furnace_1", ["s1"], furnace_cycle("tray_1", "furnace_1", "transfer_1", hold_s=60, cool_s=30),
                 params={"heating_temperature": 1000, "heating_time": 240, "profiles": [[2, 300], [15, 1000]], "cooling_rate": None},
                 deps=["t_load"], safety=HOT,
                 instruction="Load the tray into the furnace, run the 2 C/min-to-300 C then 15 C/min-to-1000 C program with a 4 h dwell (time-compressed in simulation), unload after cooling."),
            task("t_store", "Ending", "rack_1", ["s1"], [pp("crucible_s1", "rack_1")], deps=["t_heat"]),
        ],
        "safety_constraints": SAFETY,
        "evidence": [
            {"claim": "The A-Lab heats crucibles in box furnaces at 2 C/min to 300 C, then 15 C/min to the target, with a 4 h dwell and passive cooling to 100 C before robotic unloading.", "cite": "szymanski2023alab"},
            {"claim": "BaZn2Si2O7 is prepared by solid-state reaction of BaCO3, ZnO and SiO2 and studied as an SOFC sealant.", "cite": "kerstan2013bazn2si2o7"},
            {"claim": "BaZn2Si2O7-based solid solutions and their polymorphism have been reviewed; the low-temperature/high-temperature transition motivates controlled calcination.", "cite": "thieme2022solid"},
            {"claim": "Transport tilt limit 0.25 rad and 20 mm spatial tolerance are SafeLab's calibrated safety thresholds.", "cite": "bai2026safelab"},
        ],
    }


def wf02():
    """产物回收 + XRD 制样 + 衍射（A-Lab RecoverPowder / PrepareSampleforXRD / Diffraction）。"""
    return {
        "spec_version": "1.0", "id": "wf02_powder_recovery_xrd",
        "title": "Post-calcination powder recovery, vial transfer and XRD sample preparation (A-Lab characterization station)",
        "goal": {"objective": "Recover the calcined powder from the crucible, grind it, transfer it into a capped vial with mass bookkeeping, prepare a flat XRD specimen and run the scan for phase identification.",
                 "target_phase": "BaZn2Si2O7", "literature": ["szymanski2023alab", "lin1999phase"]},
        "embodiment": EMB,
        "samples": [{"name": "s1", "precursors": {}, "labware": ["crucible_s1", "vial_s1"]}],
        "stations": [
            station("balance_1", "balance", "art:AnalyticalBalance001", [0.55, 0.35, 0.0]),
            station("grinder_1", "shaker_grinder", "mortar", [0.50, 0.00, 0.0]),
            station("prep_1", "xrd_prep", "Funnel_Stand", [0.45, -0.30, 0.0]),
            station("xrd_1", "xrd", "art:PHMeterAcidimeter001", [0.75, -0.40, 0.0]),
            station("rack_1", "storage_rack", "Test_Tube_Rack", [0.30, 0.50, 0.0]),
            station("waste_1", "waste", "glass_beaker_500ml", [0.20, -0.55, 0.0]),
        ],
        "objects": [
            obj("crucible_s1", "crucible", "Crucible", [0.35, 0.20, 0.0], sample="s1"),
            obj("pestle_1", "tongs", "pestle", [0.42, 0.05, 0.0]),
            obj("funnel_1", "funnel", "Funnel", [0.45, -0.30, 0.05]),
            obj("vial_s1", "vial", "Sample_Tube_With_Stopper", [0.30, 0.50, 0.0], sample="s1"),
            obj("holder_1", "xrd_holder", "weighing_paper", [0.45, -0.22, 0.02]),
            obj("disc_1", "acrylic_disc", None, [0.50, -0.22, 0.0]),
        ],
        "tasks": [
            task("t_recover", "RecoverPowder", "grinder_1", ["s1"],
                 [weigh("crucible_s1", "balance_1"), pourp("crucible_s1", "grinder_1"), pp("pestle_1", "grinder_1"), stir("pestle_1", "grinder_1", 120),
                  pp("pestle_1", "rack_1"), uncap("vial_s1"), pp("funnel_1", "vial_s1"), pourp("grinder_1", "funnel_1"), pp("funnel_1", "prep_1"),
                  cap("vial_s1"), weigh("vial_s1", "balance_1"), pp("crucible_s1", "waste_1")],
                 params={"grind_seconds": 120},
                 instruction="Weigh the crucible, grind its contents in the mortar for 2 minutes, funnel the powder into the vial, cap and weigh the vial, discard the crucible."),
            task("t_prep", "PrepareSampleforXRD", "prep_1", ["s1"],
                 [pp("holder_1", "prep_1"), uncap("vial_s1"), pourp("vial_s1", "holder_1"), flatten("holder_1", "disc_1"), weigh("holder_1", "balance_1"),
                  cap("vial_s1"), pp("vial_s1", "rack_1")],
                 params={"target_mass_mg": 100, "max_attempts": 3}, deps=["t_recover"],
                 instruction="Pour about 100 mg of powder onto the holder, flatten it with the disc, weigh, re-cap the vial."),
            task("t_xrd", "Diffraction", "xrd_1", ["s1"],
                 [door("xrd_1"), pp("holder_1", "xrd_1"), door("xrd_1", False), press("xrd_1", "start"), wait(30), door("xrd_1"), pp("holder_1", "rack_1"), door("xrd_1", False)],
                 params={"two_theta_range": [10, 100], "scan_min": 8}, deps=["t_prep"],
                 instruction="Load the holder into the diffractometer, run the 10-100 degree scan, unload the holder."),
            task("t_end", "Ending", "rack_1", ["s1"], [pp("holder_1", "rack_1")], deps=["t_xrd"]),
        ],
        "safety_constraints": SAFETY,
        "evidence": [
            {"claim": "After heating, the A-Lab grinds each crucible with a 10 mm alumina ball in a vertical shaker, pours the powder through a steel mesh onto an XRD holder, flattens it with an acrylic disc and scans 10-100 degrees for 8 minutes.", "cite": "szymanski2023alab"},
            {"claim": "BaZn2Si2O7 has a reversible phase transition and known crystal structures usable as XRD reference phases.", "cite": "lin1999phase"},
            {"claim": "Automated phase identification and Rietveld refinement close the loop on XRD data in the A-Lab.", "cite": "szymanski2023alab"},
        ],
    }


def wf03():
    """湿化学前驱体路线：溶液计量、搅拌、pH 调节、离心分离、干燥（SafeLab 液体域）。"""
    return {
        "spec_version": "1.0", "id": "wf03_wet_chemical_precursor",
        "title": "Wet-chemical (solution) precursor preparation: metering, stirring, pH adjustment, centrifugation and drying",
        "goal": {"objective": "Prepare a mixed Ba/Zn/Si precursor gel from stock solutions with pH control, separate it by centrifugation and dry it, as the alternative low-temperature route feeding the calcination workflow.",
                 "target_phase": "BaZn2Si2O7 precursor gel", "literature": ["szymanski2023alab", "bai2026safelab"]},
        "embodiment": EMB,
        "samples": [{"name": "s1", "precursors": {"Ba/Zn nitrate solution (mL)": 50, "silica sol (mL)": 20, "NH3 aq (mL)": 2}, "labware": ["beaker_1", "tube_1", "dish_1"]}],
        "stations": [
            station("liquid_1", "liquid_station", "art:MagneticStirrer001", [0.55, 0.10, 0.0]),
            station("ph_1", "ph_meter", "art:PHMeterAcidimeter001", [0.60, -0.30, 0.0]),
            station("mixer_1", "mixer", "art:HighSpeedCentrifuge001", [0.75, 0.40, 0.0]),
            station("oven_1", "drying_oven", "art:Oven065", [0.75, -0.45, 0.0]),
            station("rack_1", "storage_rack", "Test_Tube_Rack", [0.30, 0.50, 0.0]),
            station("waste_1", "waste", "glass_beaker_500ml", [0.20, -0.55, 0.0]),
        ],
        "objects": [
            obj("bottle_nitrate", "precursor_bottle", "brown_reagent_bottle_large", [0.30, 0.60, 0.0]),
            obj("bottle_silica", "precursor_bottle", "clear_reagent_bottle_large", [0.40, 0.60, 0.0]),
            obj("bottle_ammonia", "precursor_bottle", "brown_reagent_bottle_small", [0.48, 0.60, 0.0]),
            obj("cyl_1", "cylinder", "glass_cylinder_100ml", [0.45, 0.35, 0.0]),
            obj("beaker_1", "beaker", "glass_beaker_250ml", [0.55, 0.10, 0.0], sample="s1"),
            obj("tube_1", "vial", "Centrifuge_Tube", [0.30, 0.42, 0.0], sample="s1"),
            obj("dish_1", "dish", "glass_beaker_100ml", [0.35, -0.10, 0.0], sample="s1"),
        ],
        "tasks": [
            task("t_meter", "LiquidHandling", "liquid_1", ["s1"],
                 [uncap("bottle_nitrate"), pourl("bottle_nitrate", "cyl_1", 50), cap("bottle_nitrate"), pourl("cyl_1", "beaker_1", 50),
                  pp("beaker_1", "liquid_1"), press("liquid_1", "stir"),
                  uncap("bottle_silica"), pourl("bottle_silica", "cyl_1", 20), cap("bottle_silica"), pourl("cyl_1", "beaker_1", 20), wait(60)],
                 params={"volume_ml": 70, "stir_rpm": 300},
                 instruction="Measure 50 mL nitrate solution and 20 mL silica sol with the cylinder into the beaker on the stirrer; stir for 1 minute."),
            task("t_ph", "Measurement", "ph_1", ["s1"],
                 [pp("beaker_1", "ph_1"), press("ph_1", "measure"), wait(10), uncap("bottle_ammonia"), pourl("bottle_ammonia", "beaker_1", 2), cap("bottle_ammonia"),
                  press("ph_1", "measure"), wait(10), pp("beaker_1", "liquid_1")],
                 params={"quantity": "pH", "target": 9.0}, deps=["t_meter"],
                 instruction="Measure the pH, add 2 mL ammonia solution, re-measure, return the beaker to the stirrer."),
            task("t_spin", "Mixing", "mixer_1", ["s1"],
                 [pourl("beaker_1", "tube_1", 40), cap("tube_1"), lid("mixer_1"), pp("tube_1", "mixer_1"), lid("mixer_1", False), press("mixer_1", "start"), wait(60),
                  lid("mixer_1"), pp("tube_1", "rack_1"), lid("mixer_1", False), uncap("tube_1"), pourl("tube_1", "waste_1", 30)],
                 params={"duration_s": 300, "rpm": 4000}, deps=["t_ph"],
                 instruction="Transfer 40 mL of suspension into the centrifuge tube, spin, then decant the supernatant into the waste beaker."),
            task("t_dry", "Drying", "oven_1", ["s1"],
                 [pourp("tube_1", "dish_1"), door("oven_1"), pp("dish_1", "oven_1"), door("oven_1", False), press("oven_1", "start"), wait(60), door("oven_1"), pp("dish_1", "rack_1"), door("oven_1", False)],
                 params={"temperature_c": 80, "duration_min": 720}, deps=["t_spin"],
                 instruction="Scrape the gel into the dish and dry it at 80 C in the oven."),
        ],
        "safety_constraints": SAFETY,
        "evidence": [
            {"claim": "The A-Lab mixes precursor powders as an ethanol slurry and dries the slurry at 80 C in a closed evaporation system before heating.", "cite": "szymanski2023alab"},
            {"claim": "SafeLab calibrates liquid transport tilt (0.25 rad) and pour-phase ceilings from container geometry and fill level; pouring tasks are evaluated on spillage.", "cite": "bai2026safelab"},
        ],
    }


def wf04():
    """Pt 坩埚高温溶液（助熔剂）法生长目标相晶体 + 助熔剂溶出与过滤回收。"""
    return {
        "spec_version": "1.0", "id": "wf04_flux_growth_pt_crucible",
        "title": "High-temperature solution (flux) growth of Ba5Y12Zn[O(SiO4)]8 crystals in a platinum crucible with flux leaching and filtration",
        "goal": {"objective": "Dose oxide precursors and flux into a Pt crucible, run a melt/slow-cool furnace program, then leach the flux in hot water on a stirrer, filter and collect the crystals.",
                 "target_phase": "Ba5Y12Zn[O(SiO4)]8", "literature": ["ababaikeri2024ba5y12zn", "wierzbickawieczorek2017high", "gulay2024navigation"]},
        "embodiment": EMB,
        "samples": [{"name": "s1", "precursors": {"oxide premix (BaCO3/Y2O3/ZnO/SiO2)": 2.0, "flux": 6.0}, "labware": ["pt_crucible_1", "vial_s1"]}],
        "stations": [
            station("dosing_1", "dosing_station", "Precision_Electronic_Balance", [0.55, 0.30, 0.0]),
            station("furnace_1", "box_furnace", "art:Oven065", [0.75, -0.35, 0.0]),
            station("leach_1", "liquid_station", "art:MagneticStirrer001", [0.55, 0.05, 0.0]),
            station("filter_1", "liquid_station", "Funnel_Stand", [0.45, -0.30, 0.0]),
            station("rack_1", "storage_rack", "Test_Tube_Rack", [0.30, 0.50, 0.0]),
        ],
        "objects": [
            obj("bottle_premix", "precursor_bottle", "clear_reagent_bottle_small", [0.30, 0.58, 0.0]),
            obj("bottle_flux", "precursor_bottle", "brown_reagent_bottle_large", [0.40, 0.58, 0.0]),
            obj("bottle_water", "precursor_bottle", "clear_reagent_bottle_large", [0.48, 0.58, 0.0]),
            obj("paper_1", "xrd_holder", "weighing_paper", [0.55, 0.30, 0.02]),
            obj("pt_crucible_1", "crucible", "Crucible", [0.40, 0.10, 0.0], sample="s1"),
            obj("tray_1", "crucible_tray", None, [0.35, -0.30, 0.0]),
            obj("tongs_1", "tongs", "Crucible_Tong", [0.25, -0.10, 0.0]),
            obj("beaker_1", "beaker", "glass_beaker_250ml", [0.55, 0.05, 0.0]),
            obj("funnel_1", "funnel", "Funnel", [0.45, -0.30, 0.05]),
            obj("flask_1", "flask", "erlenmeyer_flask", [0.45, -0.30, 0.0]),
            obj("vial_s1", "vial", "Sample_Tube_With_Stopper", [0.30, 0.42, 0.0], sample="s1"),
        ],
        "tasks": [
            task("t_dose", "PowderDosing", "dosing_1", ["s1"],
                 [pp("paper_1", "dosing_1"), press("dosing_1", "tare")]
                 + dose_sequence("bottle_premix", "paper_1", "dosing_1", "rack_1")
                 + dose_sequence("bottle_flux", "paper_1", "dosing_1", "rack_1")
                 + [pourp("paper_1", "pt_crucible_1"), pp("pt_crucible_1", "tray_1")],
                 params={"powder_dispenses": {"oxide premix": 2.0, "flux": 6.0}, "flux_ratio": 3.0},
                 instruction="Weigh 2.0 g oxide premix and 6.0 g flux onto the paper, pour both into the platinum crucible and set it on the tray."),
            task("t_grow", "Heating", "furnace_1", ["s1"], furnace_cycle("tray_1", "furnace_1", "rack_1", program="slow_cool", hold_s=120, cool_s=30),
                 params={"heating_temperature": 1250, "heating_time": 600, "profiles": [[5, 1250]], "cooling_rate": 2},
                 deps=["t_dose"], safety=HOT,
                 instruction="Run the melt-and-slow-cool program (1250 C dwell, 2 C/h cooling; time-compressed), unload the tray when cool."),
            task("t_leach", "LiquidHandling", "leach_1", ["s1"],
                 [uncap("bottle_water"), pourl("bottle_water", "beaker_1", 150), cap("bottle_water"), tongs("tongs_1", "pt_crucible_1", "beaker_1", **HOT),
                  pp("beaker_1", "leach_1"), press("leach_1", "stir"), wait(120)],
                 params={"volume_ml": 150, "temperature_c": 80}, deps=["t_grow"],
                 instruction="Fill the beaker with 150 mL water, lower the crucible into it with the tongs and stir on the hot plate to dissolve the flux."),
            task("t_filter", "LiquidHandling", "filter_1", ["s1"],
                 [pp("funnel_1", "flask_1"), pourl("beaker_1", "funnel_1", 150), wait(60), pourp("funnel_1", "vial_s1"), cap("vial_s1"), pp("vial_s1", "rack_1"),
                  tongs("tongs_1", "pt_crucible_1", "rack_1")],
                 params={"volume_ml": 150}, deps=["t_leach"],
                 instruction="Filter the leachate through the funnel into the flask, collect the crystals from the filter into the vial, return the crucible with the tongs."),
        ],
        "safety_constraints": SAFETY,
        "evidence": [
            {"claim": "Ba5Y12Zn[O(SiO4)]8 was obtained by a high-temperature solution method in a platinum crucible.", "cite": "ababaikeri2024ba5y12zn"},
            {"claim": "High-temperature flux growth is a systematic route to mixed-framework metal-Y silicates, with flux choice controlling the product.", "cite": "wierzbickawieczorek2017high"},
            {"claim": "Ba5Y13[SiO4]8O8.5 and Ba3Y2[Si2O7]2 were discovered by navigating Ba-Y-Si-O composition space, giving the neighbour phases to watch for in the product.", "cite": "gulay2024navigation"},
            {"claim": "Box-furnace loading/unloading with a robot arm and crucible racks is the A-Lab heating-station procedure.", "cite": "szymanski2023alab"},
        ],
    }


def wf05():
    """试剂管理与安全闭环：柜取试剂、瓶口分配器定量、归还、废弃物处置（SafeLab actuation 域）。"""
    return {
        "spec_version": "1.0", "id": "wf05_reagent_logistics_safety",
        "title": "Reagent logistics and safe disposal: cabinet retrieval, bottle-top dispensing, return and waste handling",
        "goal": {"objective": "Retrieve an acid bottle from the reagent cabinet, dispense a metered volume with the bottle-top dispenser into a beaker on the balance, return the bottle and dispose of a used crucible and test tube into the waste container without spillage or excessive contact force.",
                 "target_phase": None, "literature": ["bai2026safelab", "szymanski2023alab"]},
        "embodiment": EMB,
        "samples": [{"name": "s1", "precursors": {"HCl 1 M (mL)": 10}, "labware": ["beaker_1"]}],
        "stations": [
            station("cabinet_1", "storage_rack", "art:ReagentCabinet001", [0.80, 0.30, 0.0]),
            station("dispenser_1", "liquid_station", "art:BottleTopDispenser002", [0.55, 0.00, 0.0]),
            station("balance_1", "balance", "art:AnalyticalBalance001", [0.55, -0.35, 0.0]),
            station("rack_1", "storage_rack", "Test_Tube_Rack", [0.30, 0.50, 0.0]),
            station("waste_1", "waste", "glass_beaker_500ml", [0.20, -0.55, 0.0]),
        ],
        "objects": [
            obj("bottle_acid", "precursor_bottle", "brown_reagent_bottle_large", [0.80, 0.30, 0.10]),
            obj("beaker_1", "beaker", "glass_beaker_100ml", [0.40, 0.20, 0.0], sample="s1"),
            obj("crucible_used", "crucible", "Crucible", [0.35, -0.15, 0.0]),
            obj("tube_used", "vial", "glass_test_tube_20ml", [0.30, 0.50, 0.0]),
            obj("tongs_1", "tongs", "Crucible_Tong", [0.25, -0.10, 0.0]),
        ],
        "tasks": [
            task("t_get", "Storage", "cabinet_1", ["s1"], [door("cabinet_1"), pp("bottle_acid", "dispenser_1"), door("cabinet_1", False)],
                 instruction="Open the reagent cabinet, take the acid bottle to the dispenser station, close the cabinet."),
            task("t_dispense", "LiquidHandling", "dispenser_1", ["s1"],
                 [pp("beaker_1", "dispenser_1"), press("dispenser_1", "dispense"), wait(5), weigh("beaker_1", "balance_1"), pp("beaker_1", "rack_1")],
                 params={"volume_ml": 10}, deps=["t_get"],
                 instruction="Place the beaker under the dispenser, dispense 10 mL, weigh the beaker and park it on the rack."),
            task("t_return", "Storage", "cabinet_1", ["s1"], [door("cabinet_1"), pp("bottle_acid", "cabinet_1"), door("cabinet_1", False)], deps=["t_dispense"],
                 instruction="Return the acid bottle to the cabinet and close the door."),
            task("t_dispose", "Disposal", "waste_1", ["s1"], [tongs("tongs_1", "crucible_used", "waste_1"), pp("tongs_1", "rack_1"), pp("tube_used", "waste_1")], deps=["t_return"],
                 instruction="Move the used crucible with the tongs and the used test tube into the waste container."),
        ],
        "safety_constraints": {**SAFETY, "f_peak_max_n": 15},
        "evidence": [
            {"claim": "SafeLab's actuation domain (open/close cabinet, press switch) and spatial domain (pick-and-place, handover) are evaluated by Safe Success Rate with peak-force and 20 mm placement thresholds.", "cite": "bai2026safelab"},
            {"claim": "In the A-Lab, crucibles are disposed of after powder recovery and consumables such as precursor bottles are refilled manually.", "cite": "szymanski2023alab"},
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "configs" / "workflows"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fn in (wf01, wf02, wf03, wf04, wf05):
        spec = fn()
        (out / f"{spec['id']}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {spec['id']}: {len(spec['tasks'])} tasks, {sum(len(t['primitives']) for t in spec['tasks'])} primitives")


if __name__ == "__main__":
    main()
