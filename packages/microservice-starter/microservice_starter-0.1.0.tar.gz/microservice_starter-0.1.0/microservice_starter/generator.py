# microservice_starter/generator.py
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates" / "microservice_template"

def _replace_placeholders(dest: Path, service_name: str):
    for path in dest.rglob("*"):
        if path.is_file():
            # only replace in text files (common extensions)
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
    shutil.copytree(TEMPLATE_DIR, dest)
    _replace_placeholders(dest, name)
