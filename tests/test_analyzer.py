import io
import unittest

from PIL import Image

from analyzer import AnalysisError, image_to_jpeg, parse_verdict


class ParseVerdictTests(unittest.TestCase):
    def test_fenced_json_with_trailing_comma(self) -> None:
        raw = """
        Voici le résultat :
        ```json
        {
          "is_scam": "true",
          "risk_score": "98%",
          "verdict_title": "Faux transfert",
          "sender_analysis": "Numéro personnel",
          "red_flags": "- Urgence\\n- Mauvais expéditeur",
          "plain_advice": "Vérifiez avec *145#.",
          "whatsapp_alert": "Alerte famille",
        }
        ```
        """
        verdict = parse_verdict(raw)
        self.assertTrue(verdict.is_scam)
        self.assertEqual(verdict.risk_score, 98)
        self.assertEqual(verdict.spoken_sentence, "Vérifiez avec *145#.")
        self.assertEqual(verdict.scene, "autre")
        self.assertEqual(
            verdict.red_flags,
            ["Urgence", "Mauvais expéditeur"],
        )

    def test_scene_and_spoken_sentence(self) -> None:
        raw = """
        {
          "is_scam": true,
          "risk_score": 90,
          "scene": "shop",
          "verdict_title": "Reçu photo",
          "spoken_sentence": "Ne donne pas la marchandise. Tape *145#.",
          "sender_analysis": "Capture WhatsApp",
          "red_flags": ["Image collée"],
          "plain_advice": "Vérifie le solde.",
          "whatsapp_alert": "Alerte marché"
        }
        """
        verdict = parse_verdict(raw)
        self.assertEqual(verdict.scene, "boutique")
        self.assertEqual(
            verdict.spoken_sentence,
            "Ne donne pas la marchandise. Tape *145#.",
        )

    def test_rejects_text_without_object(self) -> None:
        with self.assertRaises(AnalysisError):
            parse_verdict("Je ne peux pas analyser cette image.")


class ImagePrepTests(unittest.TestCase):
    def test_jpeg_bytes_stay_within_edge(self) -> None:
        image = Image.new("RGB", (2000, 1000), color=(20, 40, 60))
        payload = image_to_jpeg(image)
        self.assertLess(len(payload), 200_000)
        opened = Image.open(io.BytesIO(payload))
        self.assertLessEqual(max(opened.size), 1280)
        self.assertEqual(opened.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
