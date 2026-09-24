"""Bundles a finished project's guide + media into a single zip, ready
to hand off to a client instead of sending a loose folder."""
import os
import zipfile


def package_for_delivery(project_dir: str) -> str:
    """Zips every file directly inside project_dir into a sibling
    `<project_dir>.zip` (kept outside the folder so the zip never
    contains itself). Returns the zip's path."""
    project_dir = os.path.normpath(project_dir)
    zip_path = project_dir + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in os.listdir(project_dir):
            file_path = os.path.join(project_dir, filename)
            if os.path.isfile(file_path):
                zf.write(file_path, arcname=filename)
    return zip_path
