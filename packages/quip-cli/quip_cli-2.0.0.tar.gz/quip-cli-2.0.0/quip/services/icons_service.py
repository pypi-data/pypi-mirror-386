import logging
import os
import re
import shutil


def update_icon(q):
    """Resize source images under src/templates/ to 48x48 and update template_icon.png.
    Mirrors legacy behavior; expects Pillow installed.
    """
    from PIL import Image
    import PIL

    logging.info(f"Updating icon for {q.template_name}")
    template_path = q.join_path("src", "templates")
    converted = []
    for path in os.scandir(template_path):
        logging.debug(f"Scanning file : {path}")
        if not path.is_file():
            continue
        if path.name in ["template_icon.png"]:
            continue
        if path.name.lower().endswith("48x48.png"):
            continue
        filename = q.join_path("src", "templates", path.name)
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
            logging.debug(f"Image file : {filename}")
            output_file = os.path.splitext(filename)[0] + "_48x48.png"
            converted.append(output_file)
            logging.debug(f"Output Image file : {output_file}")
            with Image.open(filename) as im:
                im_resized = im.resize((48, 48), resample=PIL.Image.LANCZOS)
                im_resized.save(output_file, "PNG")

    if len(converted) == 1:
        logging.debug(f"Updating icon file {converted[0]} => template_icon.png")
        shutil.copy2(converted[0], os.path.join(template_path, "template_icon.png"))
    elif len(converted) == 0:
        logging.debug(
            "Nothing to convert. Put an image file under templates folder and make sure the file name is not 'template_icon.png'"
        )


def create_icon_safe(q, message=None):
    try:
        create_icon(q, message=message)
    except Exception as ex:
        logging.error("WARNING: Couldn't create a new ICON")
        font_name = q._global_conf_defaults.get("icon_font", "cour.ttf")
        logging.error(
            "WARNING: Check the icon_font in the quip config. You may need to install a TrueTypeFont to your system. Current value is %s",
            font_name,
        )
        logging.error("Error: %s", ex)
        return


def create_icon(q, message=None):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        logging.error("WARNING: PIL module is missing. Install it using 'pip install Pillow'")
        logging.error("WARNING: Couldn't create a new ICON")
        return

    logging.info("Creating a new icon based on the name of the template/extension.")

    width = 48
    height = 48
    # Determine message to render
    if message is None:
        message = get_icon_message(q, q.template_name)
    else:
        message = str(message).strip()
        if len(message) == 0:
            message = get_icon_message(q, q.template_name)
        if len(message) > 3:
            logging.debug("Provided TEXT is longer than 3 characters; truncating to first 3.")
            message = message[:3]
    message = message.upper()
    logging.debug("Text in the ICON will be '%s'", message)

    font_size = 38
    correction_x = 3
    correction_y = -5
    if len(message) == 1:
        font_size = 38
        correction_x = 3
        correction_y = -7
    elif len(message) == 2:
        font_size = 24
        correction_x = 3
        correction_y = -5
    elif len(message) == 3:
        font_size = 18
        correction_x = 3
        correction_y = -5

    font_name = q._global_conf_defaults.get("icon_font", "cour.ttf")
    font = ImageFont.truetype(font_name, size=font_size)
    img = Image.new("RGBA", (width, height), (255, 0, 0, 0))
    imgDraw = ImageDraw.Draw(img)

    textWidth = font.getbbox(message)[2]
    textHeight = font.getbbox(message)[3]
    xText = (width - textWidth + correction_x) / 2
    yText = (height - textHeight + correction_y) / 2

    imgDraw.ellipse((4, 4, 44, 44), outline=(50, 110, 230), fill=(50, 110, 230))
    imgDraw.text((xText, yText), message, font=font, fill="white", stroke_width=1)

    template_path = q.join_path("src", "templates")
    img.save(os.path.join(template_path, "template_icon.png"))


def get_icon_message(q, message):
    result = []
    message = message.upper()
    message = message.replace("-", " ")
    message = message.replace("  ", " ")
    words = message.split(" ")
    if words and words[0] in ["UT", "UE"]:
        words = words[1:]

    prefix = getattr(q, "project_prefix", None)
    if prefix is not None and words and words[0] == prefix.upper():
        words = words[1:]

    # Build initials from each word (use first alphabetic char if available)
    for word in words:
        if not word:
            continue
        initial = None
        for ch in word:
            if ch.isalpha():
                initial = ch
                break
        if initial is None:
            initial = word[0]
        result.append(initial)

    if len("".join(result)) < 2 and words:
        match = re.search("(\d+)$", words[-1])
        if match is not None:
            result.append(match.group(0))

    return "".join(result)[:3]
