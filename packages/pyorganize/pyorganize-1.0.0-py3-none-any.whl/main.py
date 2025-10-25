#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

# Define categories and their file extensions
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Scripts": [".py", ".sh", ".js", ".php", ".rb", ".pl"],
    "Code": [".html", ".css", ".json", ".xml", ".yml", ".yaml", ".ini", ".cfg"],
    "Other": []  # fallback folder
}


def organize_files(folder: Path):
    """Organize files in subfolders based on file type."""
    print(f"📁 Starting organization of: {folder}")

    for item in folder.iterdir():
        if item.is_file():
            moved = False
            # Determine the correct category for the file
            for category, extensions in FILE_CATEGORIES.items():
                if item.suffix.lower() in extensions:
                    target_dir = folder / category
                    target_dir.mkdir(exist_ok=True)
                    shutil.move(str(item), str(target_dir / item.name))
                    print(f"  ➜ {item.name} → {category}/")
                    moved = True
                    break

            # If no category matches, move to "Other"
            if not moved:
                other_dir = folder / "Other"
                other_dir.mkdir(exist_ok=True)
                shutil.move(str(item), str(other_dir / item.name))
                print(f"  ➜ {item.name} → Other/")

    print("✅ Done organizing!")


def main():
    """Main function: read the argument and organize the specified folder."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <path_to_folder>")
        sys.exit(1)

    folder = Path(sys.argv[1]).expanduser().resolve()

    if not folder.exists() or not folder.is_dir():
        print(f"❌ The specified path does not exist or is not a directory: {folder}")
        sys.exit(1)

    print(f"📂 Organizing folder: {folder}")
    organize_files(folder)


if __name__ == "__main__":
    main()

