"""
Transient filter: combines a fast rules-based pre-filter (removes obvious
noise/instrument artifacts) with an optional LLM-based triage pass that
gives a human-readable classification + reasoning for candidates that pass
the rules stage. The LLM step is optional and only runs if ANTHROPIC_API_KEY
is set — the rules engine alone is fully functional without it.
"""
import os
import numpy as np

from config import Config


def rules_filter(detection: dict, flux: list) -> dict:
    """Cheap, deterministic checks to reject likely artifacts before any
    expensive model / LLM call."""
    flux = np.array(flux, dtype=np.float32)
    reasons = []
    passed = True

    # Reject flat / near-zero-variance sequences (likely bad data, not a real signal)
    if flux.std() < 1e-6:
        passed = False
        reasons.append("flux variance near zero (likely flatlined/bad data)")

    # Reject single-point spikes (cosmic rays / detector glitches), not real transits
    diffs = np.abs(np.diff(flux))
    if diffs.max() > 6 * (diffs.std() + 1e-8) and detection.get("reconstruction_error", 0) < 3:
        reasons.append("possible single-frame glitch/cosmic ray spike")

    # Require some minimum confidence from the ML stage to bother with LLM triage
    if detection.get("transit_probability", 0) < 0.2 and not detection.get("is_anomaly_autoencoder", False):
        passed = False
        reasons.append("low model confidence, no autoencoder anomaly")

    return {"passed_rules": passed, "rule_reasons": reasons}


def llm_triage(detection: dict, flux_summary: dict, target_name: str = "unknown") -> dict:
    """Optional LLM pass: asks Claude to give a plain-language triage note.
    Requires ANTHROPIC_API_KEY in the environment. Falls back gracefully if
    not configured."""
    if not Config.USE_LLM_FILTER:
        return {"llm_used": False, "note": "ANTHROPIC_API_KEY not set; skipping LLM triage."}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        prompt = (
            f"You are assisting an astronomer triaging a candidate transit/transient "
            f"signal for target '{target_name}'.\n"
            f"Detection stats: {detection}\n"
            f"Flux summary: {flux_summary}\n\n"
            f"In 2-3 sentences, give a plain-language assessment of whether this looks "
            f"like a genuine astrophysical transit/transient vs. an instrument artifact, "
            f"and suggest one concrete next step for verification. Be concise and calibrated."
        )
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        note = "".join(block.text for block in resp.content if block.type == "text")
        return {"llm_used": True, "note": note}
    except Exception as e:
        return {"llm_used": False, "note": f"LLM triage failed: {e}"}


def filter_candidate(detection: dict, flux: list, target_name: str = "unknown") -> dict:
    flux_arr = np.array(flux, dtype=np.float32)
    flux_summary = {
        "mean": float(flux_arr.mean()),
        "std": float(flux_arr.std()),
        "min": float(flux_arr.min()),
        "max": float(flux_arr.max()),
        "n_points": len(flux_arr),
    }

    rules_result = rules_filter(detection, flux)
    result = {**rules_result, "flux_summary": flux_summary}

    if rules_result["passed_rules"]:
        result["llm_triage"] = llm_triage(detection, flux_summary, target_name)
    else:
        result["llm_triage"] = {"llm_used": False, "note": "Skipped — rejected by rules filter."}

    return result
