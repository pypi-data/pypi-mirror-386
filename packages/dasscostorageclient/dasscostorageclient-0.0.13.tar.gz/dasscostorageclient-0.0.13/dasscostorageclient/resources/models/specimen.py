from pydantic import BaseModel
from typing import Dict, Optional

class SpecimenModel(BaseModel):
    institution: str | None
    collection: str | None
    barcode: str | None
    specimen_pid: str | None
    preparation_types: list[str]
    specimen_id: int | None
    role_restrictions: Optional[list[Dict[str, str]]] = []

class AssetSpecimenModel(BaseModel):
    specimen_id: int | None
    asset_guid: str | None
    specimen_pid: str | None
    asset_specimen_id: int | None
    asset_preparation_type: str | None
    specify_collection_object_attachment_id: int | None
    asset_detached: bool
    specimen: SpecimenModel | None