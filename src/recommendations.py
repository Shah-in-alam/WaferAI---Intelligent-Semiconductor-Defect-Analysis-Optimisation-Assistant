from typing import Any

DEFECT_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "Center": {
        "severity": "High",
        "root_causes": [
            "Photolithography focus drift",
            "Resist coating non-uniformity at wafer centre",
            "Chamber pressure fluctuation during deposition",
        ],
        "immediate_actions": [
            "Recalibrate stepper focus",
            "Inspect resist dispense nozzle for clogs",
            "Verify chamber pressure sensors against reference",
        ],
        "process_improvements": [
            "Implement closed-loop focus control",
            "Add inline coating-uniformity monitor",
            "Upgrade chamber pressure regulation hardware",
        ],
        "quality_impact": "Centre defects strike high-value die clusters and reduce sellable chips per wafer.",
        "estimated_yield_loss": "8-15%",
    },
    "Donut": {
        "severity": "Medium",
        "root_causes": [
            "Spin-coating rotation speed instability",
            "Edge-bead removal misalignment",
            "Thermal gradient during bake step",
        ],
        "immediate_actions": [
            "Re-baseline spin coater RPM profile",
            "Inspect EBR nozzle alignment",
            "Audit bake plate temperature uniformity",
        ],
        "process_improvements": [
            "Add real-time RPM telemetry",
            "Implement automated EBR alignment check at lot start",
            "Replace bake-plate thermocouples on PM schedule",
        ],
        "quality_impact": "Ring-shaped yield loss reduces mid-radius dies.",
        "estimated_yield_loss": "5-10%",
    },
    "Edge-Loc": {
        "severity": "Medium",
        "root_causes": [
            "Edge-handler contamination",
            "Wafer carrier misalignment in cassette",
            "Localised plasma non-uniformity at edge",
        ],
        "immediate_actions": [
            "Clean edge-handling robotics",
            "Verify cassette mapping and slot alignment",
            "Inspect plasma source RF balance",
        ],
        "process_improvements": [
            "Schedule shorter PM intervals for edge handlers",
            "Add cassette slot integrity check before lot start",
            "Tune plasma RF for edge uniformity",
        ],
        "quality_impact": "Localised edge defects can be screened, but indicate broader tooling drift.",
        "estimated_yield_loss": "3-7%",
    },
    "Edge-Ring": {
        "severity": "High",
        "root_causes": [
            "Edge-ring temperature non-uniformity in deposition chamber",
            "Worn-out focus ring",
            "Backside cooling leak around wafer perimeter",
        ],
        "immediate_actions": [
            "Replace focus ring",
            "Verify backside helium cooling flow",
            "Run temperature uniformity test on the chamber",
        ],
        "process_improvements": [
            "Reduce focus-ring replacement interval",
            "Install per-chamber temperature mapping",
            "Tighten He-cooling leak-rate spec",
        ],
        "quality_impact": "Ring-shaped exclusion at wafer edge — predictable yield loss but persistent.",
        "estimated_yield_loss": "6-12%",
    },
    "Loc": {
        "severity": "Low",
        "root_causes": [
            "Random particulate contamination",
            "Localised handling damage",
            "Single-point chamber defect",
        ],
        "immediate_actions": [
            "Sample airborne particle counts at the toolset",
            "Inspect end-effector pads for residue",
            "Run pattern recognition against historical Loc maps",
        ],
        "process_improvements": [
            "Increase mini-environment HEPA cycling",
            "Schedule preventative replacement of end-effector pads",
        ],
        "quality_impact": "Low-magnitude — usually a single tool / single shift issue.",
        "estimated_yield_loss": "1-3%",
    },
    "Random": {
        "severity": "Low",
        "root_causes": [
            "Stochastic particulate contamination",
            "Random pattern fluctuation from EUV",
            "Resist sensitivity variation lot-to-lot",
        ],
        "immediate_actions": [
            "Review cleanroom particle log for the shift",
            "Audit resist lot QC data",
        ],
        "process_improvements": [
            "Tighten incoming-resist QC sampling",
            "Trend particle counts vs. yield monthly",
        ],
        "quality_impact": "Baseline noise — improvements come from cleanroom discipline, not single fixes.",
        "estimated_yield_loss": "1-4%",
    },
    "Scratch": {
        "severity": "High",
        "root_causes": [
            "End-effector or handling robot contact damage",
            "Cassette slot misalignment causing wafer rub",
            "CMP pad debris dragging across surface",
        ],
        "immediate_actions": [
            "Quarantine the suspect handler and inspect for sharp edges",
            "Re-teach robot positions for the affected loadlock",
            "Inspect CMP pad and slurry filter immediately",
        ],
        "process_improvements": [
            "Add automated wafer-edge scratch detection at FOUP load",
            "Reduce CMP pad replacement interval",
            "Install handler-contact sensors on at-risk transfer arms",
        ],
        "quality_impact": "Linear defects propagate across many die — severe per-wafer loss.",
        "estimated_yield_loss": "10-20%",
    },
    "Near-full": {
        "severity": "Critical",
        "root_causes": [
            "Major equipment malfunction (lithography, deposition, or etch tool down)",
            "Process recipe error or wrong recipe applied",
            "Severe contamination event",
        ],
        "immediate_actions": [
            "Halt the lot and notify the area engineer",
            "Pull the tool from service",
            "Audit recipe management system for the last 24h of changes",
        ],
        "process_improvements": [
            "Add automated recipe-checksum verification before each lot",
            "Tighten SPC limits to flag drift earlier",
        ],
        "quality_impact": "Entire wafer scrap. Catastrophic per-wafer loss.",
        "estimated_yield_loss": "70-100%",
    },
    "None": {
        "severity": "Low",
        "root_causes": ["No defect pattern detected"],
        "immediate_actions": ["Continue normal processing"],
        "process_improvements": ["Maintain existing controls"],
        "quality_impact": "No measurable impact.",
        "estimated_yield_loss": "0%",
    },
}


def fallback_recommendations(defect_type: str) -> dict[str, Any]:
    """Rules-based recommendations when the LLM is unavailable."""
    if defect_type in DEFECT_KNOWLEDGE:
        return {"defect_type": defect_type, **DEFECT_KNOWLEDGE[defect_type]}
    return {"defect_type": "None", **DEFECT_KNOWLEDGE["None"]}
