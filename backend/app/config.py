from pydantic import BaseModel
from pathlib import Path

class Settings(BaseModel):
    data_dir: Path = Path("data")
    uploads_dir: Path = Path("data/uploads")
    outputs_dir: Path = Path("data/outputs")
    db_path: Path = Path("data/app.sqlite")

settings = Settings()
