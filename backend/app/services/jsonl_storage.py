import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class JSONLStorageService:
    """
    Manages append-only JSONL files for verbose evaluation outputs,
    preventing SQLite database bloat.
    """

    @staticmethod
    def append_record(file_path: Path | str, record: Dict[str, Any]) -> int:
        """
        Appends a record to a JSONL file and returns the 0-based line index.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        line_idx = 0
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                line_idx = sum(1 for _ in f)

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return line_idx

    @staticmethod
    def read_line(file_path: Path | str, line_index: int) -> Optional[Dict[str, Any]]:
        """Reads a specific line from a JSONL file by line index."""
        path = Path(file_path)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx == line_index:
                    return json.loads(line)
        return None

    @staticmethod
    def read_all(file_path: Path | str) -> List[Dict[str, Any]]:
        """Reads all records from a JSONL file."""
        path = Path(file_path)
        if not path.exists():
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

jsonl_storage = JSONLStorageService()
