import base64


def b64_to_bytes(imagen_base64: str) -> bytes:
    if "," in imagen_base64:
        imagen_base64 = imagen_base64.split(",", 1)[1]
    return base64.b64decode(imagen_base64)


def crop(imagen_base64: str, bounding_box: dict) -> bytes:
    from PIL import Image
    from io import BytesIO

    image_bytes = b64_to_bytes(imagen_base64)
    image = Image.open(BytesIO(image_bytes))

    x = int(bounding_box.get("x", 0))
    y = int(bounding_box.get("y", 0))
    w = int(bounding_box.get("width", 0))
    h = int(bounding_box.get("height", 0))

    left = x - w // 2
    top = y - h // 2
    right = left + w
    bottom = top + h

    cropped = image.crop((left, top, right, bottom))
    if cropped.mode in ("RGBA", "P"):
        cropped = cropped.convert("RGB")
    buffer = BytesIO()
    cropped.save(buffer, format="JPEG")
    return buffer.getvalue()
