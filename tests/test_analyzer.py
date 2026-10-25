import io
import unittest

from PIL import Image

from analyzer import AnalysisError, ScreenReading, decide, image_to_jpeg, parse_verdict


class ParseVerdictTests(unittest.TestCase):
    def test_fenced_json_with_trailing_comma(self) -> None:
        raw = """
        ```json
        {
          "sender_label": "+228 91 23 45 67",
          "message_text": "Vous avez reçu un transfert de 25 000 FCFA. Référence : 584216.",
          "reply_blocked": false,
          "in_whatsapp": false,
          "asks_to_send_back": false,
        }
        ```
        """
        verdict = parse_verdict(raw)
        self.assertTrue(verdict.is_scam)
        self.assertIn("*145#", verdict.spoken_sentence)

    def test_rejects_text_without_object(self) -> None:
        with self.assertRaises(AnalysisError):
            parse_verdict("Je ne peux pas analyser cette image.")


class RuleTests(unittest.TestCase):
    def test_real_moovmoney_notice_is_not_a_scam(self) -> None:
        verdict = decide(
            ScreenReading(
                sender_label="MoovMoney",
                message_text=(
                    "Transfert recu.\n"
                    "Montant: 18 500,00 FCFA\n"
                    "Nouveau solde Moov Money: 22 140,00 FCFA.\n"
                    "Txn ID: 7712048831"
                ),
                reply_blocked=True,
            )
        )
        self.assertFalse(verdict.is_scam)
        self.assertIn("*155#", verdict.spoken_sentence)

    def test_movemoney_spelling_is_accepted(self) -> None:
        verdict = decide(
            ScreenReading(
                sender_label="Movemoney",
                message_text="Votre solde Movemoney est de 12 450 FCFA.",
                reply_blocked=True,
            )
        )
        self.assertFalse(verdict.is_scam)

    def test_phone_copying_operator_notice_is_a_scam(self) -> None:
        verdict = decide(
            ScreenReading(
                sender_label="+228 91 23 45 67",
                message_text=(
                    "Vous avez reçu un transfert de 25 000 FCFA à 14:32. "
                    "Référence : 584216."
                ),
                reply_blocked=False,
            )
        )
        self.assertTrue(verdict.is_scam)
        self.assertGreaterEqual(verdict.risk_score, 90)

    def test_ordinary_personal_sms_is_not_a_scam(self) -> None:
        verdict = decide(
            ScreenReading(
                sender_label="+228 90 12 34 56",
                message_text="Salut, tu passes à la maison ce soir ?",
            )
        )
        self.assertFalse(verdict.is_scam)
        self.assertIn("pas un avis", verdict.spoken_sentence.lower())


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
