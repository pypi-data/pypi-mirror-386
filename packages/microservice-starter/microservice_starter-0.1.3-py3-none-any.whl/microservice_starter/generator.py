import os
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates" / "microservice_template"

def _replace_placeholders(dest: Path, service_name: str):
    for path in dest.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            updated = text.replace("{{SERVICE_NAME}}", service_name)
            if updated != text:
                path.write_text(updated, encoding="utf-8")

def create_microservice(name: str):
    dest = Path.cwd() / name
    if dest.exists():
        raise FileExistsError(f"Folder '{name}' already exists.")

    # Create all directories and files (even empty ones)
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        rel_path = Path(root).relative_to(TEMPLATE_DIR)
        target_dir = dest / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in files:
            src_file = Path(root) / file_name
            dst_file = target_dir / file_name
            shutil.copy2(src_file, dst_file)

    # Replace placeholders inside files
    _replace_placeholders(dest, name)
