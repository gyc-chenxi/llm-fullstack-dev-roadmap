from pathlib import Path
from diffusers_lab.config import load_yaml

def test_load_sd15_config():
    cfg = load_yaml(Path("configs/sd15_txt2img.yaml"))
    assert cfg["task"] == "txt2img"
    assert cfg["dtype"] == "float32"
    assert cfg["model_id"] == "models/sd15"
