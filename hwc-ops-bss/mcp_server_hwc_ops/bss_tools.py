"""BSS (billing/cost) tools para el MCP hwc-ops — extensión de la imagen base.

Registra tools de costos sobre la MISMA instancia `mcp` de server.py usando
`huaweicloudsdkbssintl` (GlobalCredentials, región global ap-southeast-1).
Se importa como side-effect desde entrypoint.py antes de arrancar el server.

Tools:
  - bss_list_resource_records: fee-records crudos de un ciclo (todos o por svc).
  - bss_total_cost: total facturado del ciclo + breakdown por servicio.
  - bss_cycle_breakdown: breakdown por servicio y por recurso (incluye dados
    de baja; usage_measure_id=6 → segundos → hours=usage/3600).
"""
from __future__ import annotations

import json
import os
import datetime as _dt
from typing import Optional

from .per_request_creds import account_fingerprint
from .server import mcp, _get_credentials

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkbssintl.v2 import BssintlClient, ListCustomerselfResourceRecordsRequest
from huaweicloudsdkbssintl.v2.region.bssintl_region import BssintlRegion

# BSS es un servicio global; la región del endpoint no es la del recurso.
_BSS_REGION = "ap-southeast-1"

# --- Cache de records BSS ---
# La paginación hasta 5000 records tarda ~90s. In-memory para repetir en el
# mismo proceso (instantáneo) + disco para ciclos cerrados (inmutables) que
# sobrevive restarts del contenedor. Toda key lleva huella de cuenta: ver
# _cache_key.
_MEM_CACHE: dict[tuple, list[dict]] = {}
_DISK_CACHE_DIR = os.environ.get("BSS_CACHE_DIR", "/tmp/bss_cache")


def _is_closed_cycle(cyc: str) -> bool:
    """True si el ciclo YYYY-MM ya terminó (mes < mes corriente)."""
    try:
        y, m = int(cyc[:4]), int(cyc[5:7])
        now = _dt.datetime.now(_dt.timezone.utc)
        return (y, m) < (now.year, now.month)
    except Exception:
        return False


def _cache_key(cycle: str, cst: Optional[str]) -> tuple:
    # La huella de cuenta es OBLIGATORIA en la key. Con credenciales por request
    # el contenedor sirve a varios tenants: sin esa dimensión, el primero que
    # consulta un ciclo le entrega su factura a todos los demás — y para meses
    # cerrados queda además escrita en el cache de disco.
    return (account_fingerprint(), cycle, cst or "all")


def _cache_get(cycle: str, cst: Optional[str]) -> list[dict] | None:
    key = _cache_key(cycle, cst)
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]
    if _is_closed_cycle(cycle):
        try:
            path = os.path.join(_DISK_CACHE_DIR, f"{key[0]}_{key[1]}_{key[2]}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    recs = json.load(f)
                _MEM_CACHE[key] = recs
                return recs
        except Exception:
            pass
    return None


def _cache_set(cycle: str, cst: Optional[str], recs: list[dict]) -> None:
    key = _cache_key(cycle, cst)
    _MEM_CACHE[key] = recs
    if _is_closed_cycle(cycle):
        try:
            os.makedirs(_DISK_CACHE_DIR, exist_ok=True)
            path = os.path.join(_DISK_CACHE_DIR, f"{key[0]}_{key[1]}_{key[2]}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(recs, f, ensure_ascii=False)
        except Exception:
            pass

_SVC_LABEL: dict[str, str] = {
    "hws.service.type.ec2": "ECS",
    "hws.service.type.ebs": "EVS (discos)",
    "hws.service.type.vpc": "VPC (red/bandwidth)",
    "hws.service.type.modelarts": "ModelArts / MaaS",
    "hws.service.type.dms": "DMS (Kafka/RabbitMQ)",
    "hws.service.type.rds": "RDS",
    "hws.service.type.cbr": "CBR (backups)",
    "hws.service.type.obs": "OBS",
    "hws.service.type.cce": "CCE",
    "hws.service.type.nat": "NAT",
    "hws.service.type.elb": "ELB",
    "hws.service.type.kms": "KMS",
    "hws.service.type.lts": "LTS (logs)",
    "hws.service.type.ces": "CES",
    "hws.service.type.ims": "IMS (imágenes)",
    "hws.service.type.functionstage": "FunctionGraph",
    "hws.service.type.devcloud": "CodeArts",
    "hws.service.type.dcs": "DCS (Redis)",
    "hws.service.type.sfs": "SFS (file storage)",
}


def _bss_client() -> BssintlClient:
    ak, sk = _get_credentials()
    creds = GlobalCredentials(ak=ak, sk=sk)
    region = BssintlRegion.value_of(_BSS_REGION)
    return BssintlClient.new_builder().with_credentials(creds).with_region(region).build()


def _cycle(cycle: Optional[str]) -> str:
    return cycle or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m")


def _fetch_records(cycle: str, cloud_service_type: Optional[str] = None,
                   max_records: int = 5000) -> list[dict]:
    cached = _cache_get(cycle, cloud_service_type)
    if cached is not None:
        return cached[:max_records] if max_records < 5000 else cached
    client = _bss_client()
    out: list[dict] = []
    off = 0
    for _ in range(50):  # tope 5000 records
        kwargs: dict = {"cycle": cycle, "limit": 100, "offset": off}
        if cloud_service_type:
            kwargs["cloud_service_type"] = cloud_service_type
        req = ListCustomerselfResourceRecordsRequest(**kwargs)
        resp = client.list_customerself_resource_records(req)
        page = getattr(resp, "fee_records", None) or []
        for r in page:
            out.append({
                "resource_id": getattr(r, "resource_id", None),
                "resource_name": getattr(r, "resource_name", None),
                "cloud_service_type": getattr(r, "cloud_service_type", None),
                "cloud_service_type_name": getattr(r, "cloud_service_type_name", None),
                "amount": float(getattr(r, "amount", 0) or 0),
                "usage": float(getattr(r, "usage", 0) or 0),
                "usage_measure_id": getattr(r, "usage_measure_id", None),
                "unit_price": (float(r.unit_price) if getattr(r, "unit_price", None) else None),
                "unit": getattr(r, "unit", None),
                "region": getattr(r, "region", None),
                "region_name": getattr(r, "region_name", None),
                "resource_type": getattr(r, "resource_type", None),
                "resource_type_name": getattr(r, "resource_type_name", None),
            })
        if len(page) < 100 or len(out) >= max_records:
            break
        off += 100
    _cache_set(cycle, cloud_service_type, out)
    return out


@mcp.tool()
def bss_list_resource_records(
    cycle: Optional[str] = None,
    cloud_service_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """List BSS billing fee-records for a cycle (YYYY-MM, default current month).
    Optional cloud_service_type filter (e.g. 'hws.service.type.ec2' for ECS,
    'hws.service.type.obs' for OBS). Returns raw records: resource_id,
    resource_name, cloud_service_type, amount, usage, region, region_name, etc."""
    cyc = _cycle(cycle)
    recs = _fetch_records(cyc, cloud_service_type, max_records=limit or 5000)
    return json.dumps({"cycle": cyc, "count": len(recs), "records": recs},
                      indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def bss_total_cost(cycle: Optional[str] = None) -> str:
    """Total billed spend for a cycle (YYYY-MM, default current month) broken down
    by service. Returns {cycle, total, by_service:[{service_type, label, amount,
    resource_count}]}. Useful for 'cuánto gasté este mes'."""
    cyc = _cycle(cycle)
    recs = _fetch_records(cyc)
    by: dict = {}
    for r in recs:
        svc = r["cloud_service_type"] or "unknown"
        if r["amount"] == 0.0 and not r["usage"]:
            continue
        s = by.setdefault(svc, {
            "service_type": svc,
            "label": _SVC_LABEL.get(svc, r["cloud_service_type_name"] or svc),
            "amount": 0.0, "resource_count": 0, "_rids": set(),
        })
        s["amount"] += r["amount"]
        if r["resource_id"] and r["resource_id"] not in s["_rids"]:
            s["_rids"].add(r["resource_id"])
            s["resource_count"] += 1
    services, total = [], 0.0
    for s in by.values():
        s["amount"] = round(s["amount"], 2)
        total += s["amount"]
        del s["_rids"]
        services.append(s)
    services.sort(key=lambda x: x["amount"], reverse=True)
    return json.dumps({"cycle": cyc, "total": round(total, 2), "by_service": services},
                      indent=2, ensure_ascii=False, default=str)


@mcp.tool()
def bss_cycle_breakdown(cycle: Optional[str] = None) -> str:
    """Full billing breakdown for a cycle (YYYY-MM, default current month): by
    service AND by resource. Includes deleted resources (BSS keeps historical
    names). usage_measure_id=6 → seconds → hours=usage/3600. Returns
    {cycle, total, by_service:[{service_type, label, amount, resource_count,
    resources:[{id,name,amount,hours,region,resource_type}]}]}."""
    cyc = _cycle(cycle)
    recs = _fetch_records(cyc)
    by_svc: dict = {}
    for r in recs:
        svc = r["cloud_service_type"] or "unknown"
        if r["amount"] == 0.0 and not r["usage"]:
            continue
        s = by_svc.setdefault(svc, {
            "service_type": svc,
            "label": _SVC_LABEL.get(svc, r["cloud_service_type_name"] or svc),
            "amount": 0.0, "resource_count": 0, "_rids": set(), "resources": [],
        })
        s["amount"] += r["amount"]
        rid = r["resource_id"]
        if rid and rid not in s["_rids"]:
            s["_rids"].add(rid)
            s["resource_count"] += 1
            hours = round(r["usage"] / 3600.0, 1) if r["usage_measure_id"] == 6 and r["usage"] else None
            s["resources"].append({
                "id": rid,
                "name": r["resource_name"] or rid,
                "amount": 0.0,
                "hours": hours,
                "unit_price": r["unit_price"],
                "unit": r["unit"],
                "region": r["region"],
                "region_name": r["region_name"],
                "resource_type": r["resource_type_name"] or r["resource_type"],
            })
        if rid:
            for res in s["resources"]:
                if res["id"] == rid:
                    res["amount"] = round(res["amount"] + r["amount"], 2)
                    break
    services, total = [], 0.0
    for s in by_svc.values():
        s["amount"] = round(s["amount"], 2)
        total += s["amount"]
        s["resources"].sort(key=lambda x: x["amount"], reverse=True)
        del s["_rids"]
        services.append(s)
    services.sort(key=lambda x: x["amount"], reverse=True)
    return json.dumps({"cycle": cyc, "total": round(total, 2), "by_service": services},
                      indent=2, ensure_ascii=False, default=str)
