import json
import tempfile
from pathlib import Path

from sam2_lab.utils.manifest import append_manifest


def test_append_manifest():
    # 使用临时文件测试写入，避免弄乱你的真实工程数据
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    record = {"image": "test.jpg", "score": 0.99}
    
    # 测试追加记录
    append_manifest(tmp_path, record)
    
    with open(tmp_path, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["image"] == "test.jpg"
        assert "created_at" in data  # 验证是否自动注入了时间戳
        
    Path(tmp_path).unlink()  # 测试完清理临时文件