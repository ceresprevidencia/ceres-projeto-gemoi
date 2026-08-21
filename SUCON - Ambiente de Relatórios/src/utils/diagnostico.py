"""Instrumentacao leve para diagnosticar consumo do app Streamlit."""

from __future__ import annotations

import gc
import os
import pickle
import sys
import time
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any, TypeVar, cast

import pandas as pd
import streamlit as st

F = TypeVar("F", bound=Callable[..., Any])
_REGISTRY: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


def _process_memory_mb() -> tuple[float | None, float | None]:
    """Retorna working set e memoria privada sem exigir psutil."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        if get_memory(process, ctypes.byref(counters), counters.cb):
            return (
                counters.WorkingSetSize / 1024**2,
                counters.PagefileUsage / 1024**2,
            )

    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            value /= 1024**2
        else:
            value /= 1024
        return value, None
    except (ImportError, AttributeError):
        return None, None


def _sizeof(value: Any) -> float | None:
    if isinstance(value, pd.DataFrame):
        return value.memory_usage(index=True, deep=True).sum() / 1024**2
    try:
        return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)) / 1024**2
    except (TypeError, pickle.PickleError, OverflowError):
        return None


def registrar_dataframe(nome: str, dataframe: pd.DataFrame, origem: str = "") -> pd.DataFrame:
    """Registra o ultimo DataFrame produzido por uma consulta ou pagina."""
    tamanho = dataframe.memory_usage(index=True, deep=True).sum() / 1024**2
    with _LOCK:
        _REGISTRY[nome] = {
            "nome": nome,
            "origem": origem,
            "linhas": len(dataframe),
            "colunas": len(dataframe.columns),
            "memoria_mb": tamanho,
            "atualizado_em": time.strftime("%H:%M:%S"),
            "dataframe": dataframe,
        }
    return dataframe


def registrar_consulta(nome: str) -> Callable[[F], F]:
    """Mede tempo e registra DataFrame retornado por uma funcao cacheada."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            inicio = time.perf_counter()
            antes = _process_memory_mb()[0]
            resultado = func(*args, **kwargs)
            depois = _process_memory_mb()[0]
            registro = {
                "nome": nome,
                "origem": "consulta",
                "linhas": len(resultado) if isinstance(resultado, pd.DataFrame) else None,
                "colunas": len(resultado.columns) if isinstance(resultado, pd.DataFrame) else None,
                "memoria_mb": _sizeof(resultado),
                "duracao_s": time.perf_counter() - inicio,
                "delta_memoria_mb": (depois - antes) if antes is not None and depois is not None else None,
                "atualizado_em": time.strftime("%H:%M:%S"),
                "dataframe": resultado if isinstance(resultado, pd.DataFrame) else None,
            }
            with _LOCK:
                _REGISTRY[nome] = registro
            return resultado

        return cast(F, wrapper)
    return decorator


def registros() -> list[dict[str, Any]]:
    with _LOCK:
        return [dict(item) for item in _REGISTRY.values()]


def memoria_sessao_mb() -> float | None:
    try:
        return len(pickle.dumps(dict(st.session_state), protocol=pickle.HIGHEST_PROTOCOL)) / 1024**2
    except (TypeError, pickle.PickleError, OverflowError):
        return None


def coletar_memoria() -> dict[str, float | None]:
    working_set, memoria_privada = _process_memory_mb()
    return {
        "working_set_mb": working_set,
        "memoria_privada_mb": memoria_privada,
        "session_state_mb": memoria_sessao_mb(),
        "objetos_python": float(len(gc.get_objects())),
    }


def limpar_registros() -> None:
    with _LOCK:
        _REGISTRY.clear()


@st.cache_data(ttl="30s")
def snapshot_memoria() -> dict[str, float | None]:
    """Evita recomputar a mesma leitura durante a mesma execucao."""
    return coletar_memoria()
