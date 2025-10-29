import re

def drive_direct_download_url(url: str) -> str:
    """Convierte link de Google Drive a descarga directa"""
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        return url
    file_id = match.group(1)
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def transform_dropbox_link(url: str) -> str:
    """
    Convierte enlaces de Dropbox a descarga directa (funciona con enlaces tipo /scl/fi/ o /s/).
    """
    if not url:
        return url

    if "dropbox.com" in url:
        # Si ya tiene un parámetro dl=0, lo cambia a dl=1
        if "dl=0" in url:
            url = url.replace("dl=0", "dl=1")
        # Si no, agrega dl=1 al final
        elif "?" in url:
            url += "&dl=1"
        else:
            url += "?dl=1"

    return url

