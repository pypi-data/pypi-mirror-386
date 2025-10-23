from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from typing import Any, Literal, cast

import networkx as nx

from ..constants import (
    DEFAULTS,
    get_aliases,
)
from ..gamma import _get_gamma_spec, eval_gamma
from ..alias import collect_attr, get_attr, get_attr_str, set_attr, set_attr_str
from ..utils import get_numpy
from ..types import NodeId, TNFRGraph
from .._compat import TypeAlias

ALIAS_VF = get_aliases("VF")
ALIAS_DNFR = get_aliases("DNFR")
ALIAS_DEPI = get_aliases("DEPI")
ALIAS_EPI = get_aliases("EPI")
ALIAS_EPI_KIND = get_aliases("EPI_KIND")
ALIAS_D2EPI = get_aliases("D2EPI")

__all__ = (
    "AbstractIntegrator",
    "DefaultIntegrator",
    "prepare_integration_params",
    "update_epi_via_nodal_equation",
)


GammaMap: TypeAlias = dict[NodeId, float]
"""Γ evaluation cache keyed by node identifier."""

NodeIncrements: TypeAlias = dict[NodeId, tuple[float, ...]]
"""Mapping of nodes to staged integration increments."""

NodalUpdate: TypeAlias = dict[NodeId, tuple[float, float, float]]
"""Mapping of nodes to ``(EPI, dEPI/dt, ∂²EPI/∂t²)`` tuples."""

IntegratorMethod: TypeAlias = Literal["euler", "rk4"]
"""Supported explicit integration schemes for nodal updates."""


_PARALLEL_GRAPH: TNFRGraph | None = None


def _gamma_worker_init(graph: TNFRGraph) -> None:
    """Initialise process-local graph reference for Γ evaluation."""

    global _PARALLEL_GRAPH
    _PARALLEL_GRAPH = graph


def _gamma_worker(task: tuple[list[NodeId], float]) -> list[tuple[NodeId, float]]:
    """Evaluate Γ for ``task`` chunk using process-local graph."""

    chunk, t = task
    if _PARALLEL_GRAPH is None:
        raise RuntimeError("Parallel Γ worker initialised without graph reference")
    return [
        (node, float(eval_gamma(_PARALLEL_GRAPH, node, t))) for node in chunk
    ]


def _normalise_jobs(n_jobs: int | None, total: int) -> int | None:
    """Return an effective worker count respecting serial fallbacks."""

    if n_jobs is None:
        return None
    try:
        workers = int(n_jobs)
    except (TypeError, ValueError):
        return None
    if workers <= 1 or total <= 1:
        return None
    return max(1, min(workers, total))


def _chunk_nodes(nodes: list[NodeId], chunk_size: int) -> Iterable[list[NodeId]]:
    """Yield deterministic chunks from ``nodes`` respecting insertion order."""

    for idx in range(0, len(nodes), chunk_size):
        yield nodes[idx:idx + chunk_size]


def _apply_increment_chunk(
    chunk: list[tuple[NodeId, float, float, tuple[float, ...]]],
    dt_step: float,
    method: str,
) -> list[tuple[NodeId, tuple[float, float, float]]]:
    """Compute updated states for ``chunk`` using scalar arithmetic."""

    results: list[tuple[NodeId, tuple[float, float, float]]] = []
    dt_nonzero = dt_step != 0

    for node, epi_i, dEPI_prev, ks in chunk:
        if method == "rk4":
            k1, k2, k3, k4 = ks
            epi = epi_i + (dt_step / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            dEPI_dt = k4
        else:
            (k1,) = ks
            epi = epi_i + dt_step * k1
            dEPI_dt = k1
        d2epi = (dEPI_dt - dEPI_prev) / dt_step if dt_nonzero else 0.0
        results.append((node, (float(epi), float(dEPI_dt), float(d2epi))))

    return results


def _evaluate_gamma_map(
    G: TNFRGraph,
    nodes: list[NodeId],
    t: float,
    *,
    n_jobs: int | None = None,
) -> GammaMap:
    """Return Γ evaluations for ``nodes`` at time ``t`` respecting parallelism."""

    workers = _normalise_jobs(n_jobs, len(nodes))
    if workers is None:
        return {n: float(eval_gamma(G, n, t)) for n in nodes}

    chunk_size = max(1, math.ceil(len(nodes) / (workers * 4)))
    mp_ctx = get_context("spawn")
    tasks = ((chunk, t) for chunk in _chunk_nodes(nodes, chunk_size))

    results: GammaMap = {}
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=mp_ctx,
        initializer=_gamma_worker_init,
        initargs=(G,),
    ) as executor:
        futures = [executor.submit(_gamma_worker, task) for task in tasks]
        for fut in futures:
            for node, value in fut.result():
                results[node] = value
    return results


def prepare_integration_params(
    G: TNFRGraph,
    dt: float | None = None,
    t: float | None = None,
    method: Literal["euler", "rk4"] | None = None,
) -> tuple[float, int, float, Literal["euler", "rk4"]]:
    """Validate and normalise ``dt``, ``t`` and ``method`` for integration.

    Returns ``(dt_step, steps, t0, method)`` where ``dt_step`` is the
    effective step, ``steps`` the number of substeps and ``t0`` the prepared
    initial time.
    """
    if dt is None:
        dt = float(G.graph.get("DT", DEFAULTS["DT"]))
    else:
        if not isinstance(dt, (int, float)):
            raise TypeError("dt must be a number")
        if dt < 0:
            raise ValueError("dt must be non-negative")
        dt = float(dt)

    if t is None:
        t = float(G.graph.get("_t", 0.0))
    else:
        t = float(t)

    method_value = (
        method
        or G.graph.get(
            "INTEGRATOR_METHOD", DEFAULTS.get("INTEGRATOR_METHOD", "euler")
        )
    ).lower()
    if method_value not in ("euler", "rk4"):
        raise ValueError("method must be 'euler' or 'rk4'")

    dt_min = float(G.graph.get("DT_MIN", DEFAULTS.get("DT_MIN", 0.0)))
    if dt_min > 0 and dt > dt_min:
        steps = int(math.ceil(dt / dt_min))
    else:
        steps = 1
    # ``steps`` is guaranteed to be ≥1 at this point
    dt_step = dt / steps

    return dt_step, steps, t, cast(Literal["euler", "rk4"], method_value)


def _apply_increments(
    G: TNFRGraph,
    dt_step: float,
    increments: NodeIncrements,
    *,
    method: str,
    n_jobs: int | None = None,
) -> NodalUpdate:
    """Combine precomputed increments to update node states."""

    nodes: list[NodeId] = list(G.nodes)
    if not nodes:
        return {}

    np = get_numpy()

    epi_initial: list[float] = []
    dEPI_prev: list[float] = []
    ordered_increments: list[tuple[float, ...]] = []

    for node in nodes:
        nd = G.nodes[node]
        _, _, dEPI_dt_prev, epi_i = _node_state(nd)
        epi_initial.append(float(epi_i))
        dEPI_prev.append(float(dEPI_dt_prev))
        ordered_increments.append(increments[node])

    if np is not None:
        epi_arr = np.asarray(epi_initial, dtype=float)
        dEPI_prev_arr = np.asarray(dEPI_prev, dtype=float)
        k_arr = np.asarray(ordered_increments, dtype=float)

        if method == "rk4":
            if k_arr.ndim != 2 or k_arr.shape[1] != 4:
                raise ValueError("rk4 increments require four staged values")
            dt_factor = dt_step / 6.0
            k1 = k_arr[:, 0]
            k2 = k_arr[:, 1]
            k3 = k_arr[:, 2]
            k4 = k_arr[:, 3]
            epi = epi_arr + dt_factor * (k1 + 2 * k2 + 2 * k3 + k4)
            dEPI_dt = k4
        else:
            if k_arr.ndim == 1:
                k1 = k_arr
            else:
                k1 = k_arr[:, 0]
            epi = epi_arr + dt_step * k1
            dEPI_dt = k1

        if dt_step != 0:
            d2epi = (dEPI_dt - dEPI_prev_arr) / dt_step
        else:
            d2epi = np.zeros_like(dEPI_dt)

        results: NodalUpdate = {}
        for idx, node in enumerate(nodes):
            results[node] = (
                float(epi[idx]),
                float(dEPI_dt[idx]),
                float(d2epi[idx]),
            )
        return results

    payload: list[tuple[NodeId, float, float, tuple[float, ...]]] = list(
        zip(nodes, epi_initial, dEPI_prev, ordered_increments)
    )

    workers = _normalise_jobs(n_jobs, len(nodes))
    if workers is None:
        return dict(_apply_increment_chunk(payload, dt_step, method))

    chunk_size = max(1, math.ceil(len(nodes) / (workers * 4)))
    mp_ctx = get_context("spawn")

    results: NodalUpdate = {}
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp_ctx) as executor:
        futures = [
            executor.submit(
                _apply_increment_chunk,
                chunk,
                dt_step,
                method,
            )
            for chunk in _chunk_nodes(payload, chunk_size)
        ]
        for fut in futures:
            for node, value in fut.result():
                results[node] = value

    return {node: results[node] for node in nodes}


def _collect_nodal_increments(
    G: TNFRGraph,
    gamma_maps: tuple[GammaMap, ...],
    *,
    method: str,
) -> NodeIncrements:
    """Combine node base state with staged Γ contributions.

    ``gamma_maps`` must contain one entry for Euler integration and four for
    RK4. The helper merges the structural frequency/ΔNFR base contribution
    with the supplied Γ evaluations.
    """

    nodes: list[NodeId] = list(G.nodes())
    if not nodes:
        return {}

    if method == "rk4":
        expected_maps = 4
    elif method == "euler":
        expected_maps = 1
    else:
        raise ValueError("method must be 'euler' or 'rk4'")

    if len(gamma_maps) != expected_maps:
        raise ValueError(f"{method} integration requires {expected_maps} gamma maps")

    np = get_numpy()
    if np is not None:
        vf = collect_attr(G, nodes, ALIAS_VF, 0.0, np=np)
        dnfr = collect_attr(G, nodes, ALIAS_DNFR, 0.0, np=np)
        base = vf * dnfr

        gamma_arrays = [
            np.fromiter((gm.get(n, 0.0) for n in nodes), float, count=len(nodes))
            for gm in gamma_maps
        ]
        if gamma_arrays:
            gamma_stack = np.stack(gamma_arrays, axis=1)
            combined = base[:, None] + gamma_stack
        else:
            combined = base[:, None]

        return {
            node: tuple(float(value) for value in combined[idx])
            for idx, node in enumerate(nodes)
        }

    increments: NodeIncrements = {}
    for node in nodes:
        nd = G.nodes[node]
        vf, dnfr, *_ = _node_state(nd)
        base = vf * dnfr
        gammas = [gm.get(node, 0.0) for gm in gamma_maps]

        if method == "rk4":
            k1, k2, k3, k4 = gammas
            increments[node] = (
                base + k1,
                base + k2,
                base + k3,
                base + k4,
            )
        else:
            (k1,) = gammas
            increments[node] = (base + k1,)

    return increments


def _build_gamma_increments(
    G: TNFRGraph,
    dt_step: float,
    t_local: float,
    *,
    method: str,
    n_jobs: int | None = None,
) -> NodeIncrements:
    """Evaluate Γ contributions and merge them with ``νf·ΔNFR`` base terms."""

    if method == "rk4":
        gamma_count = 4
    elif method == "euler":
        gamma_count = 1
    else:
        raise ValueError("method must be 'euler' or 'rk4'")

    gamma_spec = G.graph.get("_gamma_spec")
    if gamma_spec is None:
        gamma_spec = _get_gamma_spec(G)

    gamma_type = ""
    if isinstance(gamma_spec, Mapping):
        gamma_type = str(gamma_spec.get("type", "")).lower()

    if gamma_type == "none":
        gamma_maps: tuple[GammaMap, ...] = tuple(
            cast(GammaMap, {}) for _ in range(gamma_count)
        )
        return _collect_nodal_increments(G, gamma_maps, method=method)

    nodes: list[NodeId] = list(G.nodes)
    if not nodes:
        gamma_maps = tuple(cast(GammaMap, {}) for _ in range(gamma_count))
        return _collect_nodal_increments(G, gamma_maps, method=method)

    if method == "rk4":
        t_mid = t_local + dt_step / 2.0
        t_end = t_local + dt_step
        g1_map = _evaluate_gamma_map(G, nodes, t_local, n_jobs=n_jobs)
        g_mid_map = _evaluate_gamma_map(G, nodes, t_mid, n_jobs=n_jobs)
        g4_map = _evaluate_gamma_map(G, nodes, t_end, n_jobs=n_jobs)
        gamma_maps = (g1_map, g_mid_map, g_mid_map, g4_map)
    else:  # method == "euler"
        gamma_maps = (
            _evaluate_gamma_map(G, nodes, t_local, n_jobs=n_jobs),
        )

    return _collect_nodal_increments(G, gamma_maps, method=method)


def _integrate_euler(
    G: TNFRGraph,
    dt_step: float,
    t_local: float,
    *,
    n_jobs: int | None = None,
) -> NodalUpdate:
    """One explicit Euler integration step."""
    increments = _build_gamma_increments(
        G,
        dt_step,
        t_local,
        method="euler",
        n_jobs=n_jobs,
    )
    return _apply_increments(
        G,
        dt_step,
        increments,
        method="euler",
        n_jobs=n_jobs,
    )


def _integrate_rk4(
    G: TNFRGraph,
    dt_step: float,
    t_local: float,
    *,
    n_jobs: int | None = None,
) -> NodalUpdate:
    """One Runge–Kutta order-4 integration step."""
    increments = _build_gamma_increments(
        G,
        dt_step,
        t_local,
        method="rk4",
        n_jobs=n_jobs,
    )
    return _apply_increments(
        G,
        dt_step,
        increments,
        method="rk4",
        n_jobs=n_jobs,
    )


class AbstractIntegrator(ABC):
    """Abstract base class encapsulating nodal equation integration."""

    @abstractmethod
    def integrate(
        self,
        graph: TNFRGraph,
        *,
        dt: float | None,
        t: float | None,
        method: str | None,
        n_jobs: int | None,
    ) -> None:
        """Advance ``graph`` coherence states according to the nodal equation."""


class DefaultIntegrator(AbstractIntegrator):
    """Explicit integrator combining Euler and RK4 step implementations."""

    def integrate(
        self,
        graph: TNFRGraph,
        *,
        dt: float | None,
        t: float | None,
        method: str | None,
        n_jobs: int | None,
    ) -> None:
        if not isinstance(
            graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
        ):
            raise TypeError("G must be a networkx graph instance")

        dt_step, steps, t0, resolved_method = prepare_integration_params(
            graph, dt, t, cast(IntegratorMethod | None, method)
        )

        t_local = t0
        for _ in range(steps):
            if resolved_method == "rk4":
                updates: NodalUpdate = _integrate_rk4(
                    graph, dt_step, t_local, n_jobs=n_jobs
                )
            else:
                updates = _integrate_euler(graph, dt_step, t_local, n_jobs=n_jobs)

            for n, (epi, dEPI_dt, d2epi) in updates.items():
                nd = graph.nodes[n]
                epi_kind = get_attr_str(nd, ALIAS_EPI_KIND, "")
                set_attr(nd, ALIAS_EPI, epi)
                if epi_kind:
                    set_attr_str(nd, ALIAS_EPI_KIND, epi_kind)
                set_attr(nd, ALIAS_DEPI, dEPI_dt)
                set_attr(nd, ALIAS_D2EPI, d2epi)

            t_local += dt_step

        graph.graph["_t"] = t_local


def update_epi_via_nodal_equation(
    G: TNFRGraph,
    *,
    dt: float | None = None,
    t: float | None = None,
    method: Literal["euler", "rk4"] | None = None,
    n_jobs: int | None = None,
) -> None:
    """TNFR nodal equation.

    Implements the extended nodal equation:
        ∂EPI/∂t = νf · ΔNFR(t) + Γi(R)

    Where:
      - EPI is the node's Primary Information Structure.
      - νf is the node's structural frequency (Hz_str).
      - ΔNFR(t) is the nodal gradient (reorganisation need), typically a mix
        of components (e.g. phase θ, EPI, νf).
      - Γi(R) is the optional network coupling as a function of Kuramoto order
        ``R`` (see :mod:`gamma`), used to modulate network integration.

    TNFR references: nodal equation (manual), νf/ΔNFR/EPI glossary, Γ operator.
    Side effects: caches dEPI and updates EPI via explicit integration.
    """
    DefaultIntegrator().integrate(
        G,
        dt=dt,
        t=t,
        method=method,
        n_jobs=n_jobs,
    )


def _node_state(nd: dict[str, Any]) -> tuple[float, float, float, float]:
    """Return common node state attributes.

    Extracts ``νf``, ``ΔNFR``, previous ``dEPI/dt`` and current ``EPI``
    using alias helpers, providing ``0.0`` defaults when attributes are
    missing.
    """

    vf = get_attr(nd, ALIAS_VF, 0.0)
    dnfr = get_attr(nd, ALIAS_DNFR, 0.0)
    dEPI_dt_prev = get_attr(nd, ALIAS_DEPI, 0.0)
    epi_i = get_attr(nd, ALIAS_EPI, 0.0)
    return vf, dnfr, dEPI_dt_prev, epi_i
