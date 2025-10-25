from dataclasses import dataclass
from typing import Optional

from zervedataplatform.model_transforms.db.PipelineRunConfig import PipelineRunConfig
from zervedataplatform.model_transforms.db.Sites import Sites
from zervedataplatform.model_transforms.db.abstractions.ModelBase import ModelBase
from zervedataplatform.model_transforms.db.helpers.data_class_helpers import primary_key, foreign_key


@dataclass
class SelectorsBase(ModelBase):
    ID: Optional[int] = primary_key()  # Primary key field
    site_id: int = foreign_key(Sites, "ID")
    identifier_path: str = ""
    UpdatedPipelineRunConfig_id: int = foreign_key(PipelineRunConfig, "ID")

