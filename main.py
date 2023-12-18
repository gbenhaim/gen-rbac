#!/usr/bin/env python3
from yaml import safe_load_all, safe_dump
from click import command, option
import click
from pathlib import Path
from itertools import chain
from typing import NamedTuple, Any, Mapping, Iterable
from concurrent.futures import ProcessPoolExecutor
from functools import reduce
from operator import ior
from more_itertools import bucket
import sys

class GVK(NamedTuple):
    group: str
    version: str
    kind: str
    raw_api_version: str

@command()
@option("--dir", default=".", type=click.Path(dir_okay=True, path_type=Path))
@option("--out", default="role.yaml", type=click.File("wt")
)
def main(dir: Path, out: Path) -> None:
    files = chain(dir.rglob("*.yaml"), dir.rglob("*.yml"))
    gvks = get_gvks(files)
    gvk_buckets = bucket(gvks, lambda g: g.group)
    role = generate_cluster_role(gvk_buckets)
    safe_dump(role, out)

def get_gvks(files: Iterable[Path]) -> set[GVK]:
    with ProcessPoolExecutor() as pool:
        ret =  pool.map(
            handle_file,
            files
        )
        return reduce(ior, ret)

def handle_file(path: Path) -> set[GVK]:
    resources = safe_load_file(path)
    return {create_gvk(r) for r in resources}


def safe_load_file(path: Path) -> Any:
    with path.open() as f:
        yield from safe_load_all(f)


def create_gvk(r: Mapping) -> GVK:
    gv: str = r["apiVersion"]
    if "/" in gv:
        group, version = gv.split("/")
    else:
        group, version = "", gv

    return GVK(
        kind=r["kind"],
        group=group,
        version=version,
        raw_api_version=gv,
    )


def generate_cluster_role(gvk_buckets: bucket, name="appstudio-mgmt-argocd") -> Mapping:
    role = {
        "kind": "ClusterRole",
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "metadata": {
            "name": name,
        },
        "rules": []
    }

    for group in sorted(gvk_buckets):
        bucket: Iterable[GVK] = gvk_buckets[group]
        role["rules"].append(
            {
                "apiGroups": [group],
                "resources": sorted([gvk.kind for gvk in bucket]),
                "verbs": ["*"],
            }
        )

    return role


if __name__ == "__main__":
    main()
