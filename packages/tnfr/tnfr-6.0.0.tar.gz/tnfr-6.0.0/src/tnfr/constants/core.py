"""Core constants."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Mapping
from types import MappingProxyType


SELECTOR_THRESHOLD_DEFAULTS: Mapping[str, float] = MappingProxyType(
    {
        "si_hi": 0.66,
        "si_lo": 0.33,
        "dnfr_hi": 0.50,
        "dnfr_lo": 0.10,
        "accel_hi": 0.50,
        "accel_lo": 0.10,
    }
)


@dataclass(frozen=True, slots=True)
class CoreDefaults:
    """Default parameters for the core engine.

    The fields are exported via :data:`CORE_DEFAULTS` and may therefore appear
    unused to static analysis tools such as Vulture.
    """

    DT: float = 1.0
    INTEGRATOR_METHOD: str = "euler"
    DT_MIN: float = 0.1
    EPI_MIN: float = -1.0
    EPI_MAX: float = 1.0
    VF_MIN: float = 0.0
    VF_MAX: float = 1.0
    THETA_WRAP: bool = True
    DNFR_WEIGHTS: dict[str, float] = field(
        default_factory=lambda: {
            "phase": 0.34,
            "epi": 0.33,
            "vf": 0.33,
            "topo": 0.0,
        }
    )
    SI_WEIGHTS: dict[str, float] = field(
        default_factory=lambda: {"alpha": 0.34, "beta": 0.33, "gamma": 0.33}
    )
    PHASE_K_GLOBAL: float = 0.05
    PHASE_K_LOCAL: float = 0.15
    PHASE_ADAPT: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "R_hi": 0.90,
            "R_lo": 0.60,
            "disr_hi": 0.50,
            "disr_lo": 0.25,
            "kG_min": 0.01,
            "kG_max": 0.20,
            "kL_min": 0.05,
            "kL_max": 0.25,
            "up": 0.10,
            "down": 0.07,
        }
    )
    UM_COMPAT_THRESHOLD: float = 0.75
    UM_CANDIDATE_MODE: str = "sample"
    UM_CANDIDATE_COUNT: int = 0
    GLYPH_HYSTERESIS_WINDOW: int = 7
    AL_MAX_LAG: int = 5
    EN_MAX_LAG: int = 3
    GLYPH_SELECTOR_MARGIN: float = 0.05
    VF_ADAPT_TAU: int = 5
    VF_ADAPT_MU: float = 0.1
    GLYPH_FACTORS: dict[str, float] = field(
        default_factory=lambda: {
            "AL_boost": 0.05,
            "EN_mix": 0.25,
            "IL_dnfr_factor": 0.7,
            "OZ_dnfr_factor": 1.3,
            "UM_theta_push": 0.25,
            "RA_epi_diff": 0.15,
            "SHA_vf_factor": 0.85,
            "VAL_scale": 1.15,
            "NUL_scale": 0.85,
            "THOL_accel": 0.10,
            "ZHIR_theta_shift": 1.57079632679,
            "NAV_jitter": 0.05,
            "NAV_eta": 0.5,
            "REMESH_alpha": 0.5,
        }
    )
    GLYPH_THRESHOLDS: dict[str, float] = field(
        default_factory=lambda: {"hi": 0.66, "lo": 0.33, "dnfr": 1e-3}
    )
    NAV_RANDOM: bool = True
    NAV_STRICT: bool = False
    RANDOM_SEED: int = 0
    JITTER_CACHE_SIZE: int = 256
    OZ_NOISE_MODE: bool = False
    OZ_SIGMA: float = 0.1
    GRAMMAR: dict[str, Any] = field(
        default_factory=lambda: {
            "window": 3,
            "avoid_repeats": ["ZHIR", "OZ", "THOL"],
            "force_dnfr": 0.60,
            "force_accel": 0.60,
            "fallbacks": {"ZHIR": "NAV", "OZ": "ZHIR", "THOL": "NAV"},
        }
    )
    SELECTOR_WEIGHTS: dict[str, float] = field(
        default_factory=lambda: {"w_si": 0.5, "w_dnfr": 0.3, "w_accel": 0.2}
    )
    SELECTOR_THRESHOLDS: dict[str, float] = field(
        default_factory=lambda: dict(SELECTOR_THRESHOLD_DEFAULTS)
    )
    GAMMA: dict[str, Any] = field(
        default_factory=lambda: {"type": "none", "beta": 0.0, "R0": 0.0}
    )
    CALLBACKS_STRICT: bool = False
    VALIDATORS_STRICT: bool = False
    PROGRAM_TRACE_MAXLEN: int = 50
    HISTORY_MAXLEN: int = 0


@dataclass(frozen=True, slots=True)
class RemeshDefaults:
    """Default parameters for the remeshing subsystem.

    As with :class:`CoreDefaults`, the fields are exported via
    :data:`REMESH_DEFAULTS` and may look unused to static analysers.
    """

    EPS_DNFR_STABLE: float = 1e-3
    EPS_DEPI_STABLE: float = 1e-3
    FRACTION_STABLE_REMESH: float = 0.80
    REMESH_COOLDOWN_WINDOW: int = 20
    REMESH_COOLDOWN_TS: float = 0.0
    REMESH_REQUIRE_STABILITY: bool = True
    REMESH_STABILITY_WINDOW: int = 25
    REMESH_MIN_PHASE_SYNC: float = 0.85
    REMESH_MAX_GLYPH_DISR: float = 0.35
    REMESH_MIN_SIGMA_MAG: float = 0.50
    REMESH_MIN_KURAMOTO_R: float = 0.80
    REMESH_MIN_SI_HI_FRAC: float = 0.50
    REMESH_LOG_EVENTS: bool = True
    REMESH_MODE: str = "knn"
    REMESH_COMMUNITY_K: int = 2
    REMESH_TAU_GLOBAL: int = 8
    REMESH_TAU_LOCAL: int = 4
    REMESH_ALPHA: float = 0.5
    REMESH_ALPHA_HARD: bool = False

_core_defaults = asdict(CoreDefaults())
_remesh_defaults = asdict(RemeshDefaults())

CORE_DEFAULTS = MappingProxyType(_core_defaults)
REMESH_DEFAULTS = MappingProxyType(_remesh_defaults)
