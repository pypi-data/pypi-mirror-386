from __future__ import annotations

from typing import Sequence, Type

from simforge.core.asset.asset import Asset, AssetRegistry
from simforge.core.asset.asset_type import AssetType


class Geometry(Asset, asset_entrypoint=AssetType.GEOMETRY):
    @classmethod
    def registry(cls) -> Sequence[Type[Geometry]]:
        return AssetRegistry.registry.get(AssetType.GEOMETRY, [])  # type: ignore
