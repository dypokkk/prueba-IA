import os
import zipfile
from pathlib import Path

def create_deliverable_zip():
    root_dir = Path(__file__).resolve().parent.parent
    output_zip = root_dir / "customer_support_rag_assistant.zip"

    print("=" * 60)
    print("📦 PACKAGING DELIVERABLE ZIP BUNDLE")
    print("=" * 60)
    print(f"Source: {root_dir}")
    print(f"Output: {output_zip}")

    excluded_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
    excluded_files = {".env", "customer_support_rag_assistant.zip"}

    file_count = 0
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                if file in excluded_files or file.endswith(".pyc"):
                    continue

                full_path = Path(root) / file
                rel_path = full_path.relative_to(root_dir)
                zipf.write(full_path, arcname=str(rel_path))
                file_count += 1

    zip_size_kb = output_zip.stat().st_size / 1024
    print(f"\n✅ Packaged {file_count} files into '{output_zip.name}' ({zip_size_kb:.1f} KB)")
    print("Deliverable is ready for submission!")

if __name__ == "__main__":
    create_deliverable_zip()
