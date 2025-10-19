import random, string

def generate_token(length=16):
    """Generate a secure random token for streaming"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def parse_caption(caption):
    """
    Extract movie/TV metadata from caption
    Example: "Ghosted 2023 1080p WEBRip x265"
    Returns: dict(name, year, quality)
    """
    parts = caption.split()
    data = {}
    if len(parts) >= 2:
        data["name"] = " ".join(parts[:-2])
        data["year"] = parts[-2] if parts[-2].isdigit() else None
        data["quality"] = parts[-1]
    return data
