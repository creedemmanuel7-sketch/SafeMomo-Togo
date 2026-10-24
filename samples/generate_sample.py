"""Dessine un échantillon synthétique pour la démo.

Le texte reprend le scénario public de l'ANCY Togo : une fausse
notification de transfert, puis une demande de renvoi. Ce n'est pas
une copie d'un SMS réel.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")


def font(path: Path, size: int) -> ImageFont.ImageFont:
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    image = Image.new("RGB", (420, 780), "#101418")
    draw = ImageDraw.Draw(image)
    title = font(FONT_BOLD, 28)
    body = font(FONT, 22)
    small = font(FONT, 16)
    tiny = font(FONT, 14)

    draw.rounded_rectangle((18, 16, 402, 764), radius=36, fill="#F4F1EA")
    draw.rectangle((18, 16, 402, 118), fill="#0E5A58")
    draw.text((36, 36), "Messages", font=title, fill="#F4F7F6")
    draw.text((36, 74), "+228 90 12 34 56", font=small, fill="#D7E6E3")

    draw.rounded_rectangle((36, 146, 384, 560), radius=22, fill="#FFFFFF")
    lines = [
        "Vous avez recu 35 000 FCFA",
        "par TMONEY de KOFFI A.",
        "Ref TX998234.",
        "Nouveau solde 35 250 FCFA.",
        "",
        "Pardon, mauvais numero.",
        "Renvoyez ce montant maintenant.",
        "C'est pour l'hopital.",
    ]
    y = 170
    for line in lines:
        draw.text((54, y), line, font=body, fill="#14201F")
        y += 34

    draw.text((36, 590), "Aujourd'hui, 14 h 08", font=tiny, fill="#4A5B59")
    draw.text((36, 680), "Echantillon synthetique SafeMomo.", font=small, fill="#5C6B68")
    draw.text((36, 708), "Pas un vrai SMS d'operateur.", font=small, fill="#5C6B68")

    ROOT.mkdir(parents=True, exist_ok=True)
    output = ROOT / "fake_tmoney_sample.png"
    image.save(output, format="PNG")
    print(output)


if __name__ == "__main__":
    main()
