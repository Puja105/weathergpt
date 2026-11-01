import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from backend import chatbot
from backend import rain_risk


class ChatbotTests(unittest.TestCase):
    def test_understand_question_parses_multilingual_intent(self):
        with patch.object(
            chatbot,
            "_request_openai",
            return_value=(
                '{"city":"Bengaluru","date":"2026-10-10",'
                '"query_type":"daily","language":"Kannada"}'
            ),
        ):
            intent = chatbot._understand_question("ಬೆಂಗಳೂರಿನಲ್ಲಿ ನಾಳೆ ಮಳೆ ಬರುತ್ತದೆಯೇ?")

        self.assertEqual(intent.city, "Bengaluru")
        self.assertEqual(intent.date, date(2026, 10, 10))
        self.assertEqual(intent.query_type, "daily")
        self.assertEqual(intent.language, "Kannada")

    def test_current_weather_uses_existing_weather_data_schema(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [(1, "Bengaluru", "Karnataka", "India")]
        cursor.fetchone.return_value = (
            "2026-10-09 06:00",
            24.5,
            70,
            25.0,
            0.0,
            0.0,
            2,
            10,
            8.0,
            180,
        )
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(chatbot, "get_connection", return_value=connection):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(city="Bengaluru", query_type="current")
            )

        self.assertEqual(context["location"]["city"], "Bengaluru")
        self.assertEqual(context["weather"]["temperature_c"], 24.5)
        self.assertIn("FROM weather_data", cursor.execute.call_args_list[1].args[0])
        self.assertEqual(cursor.execute.call_args_list[1].args[1], (1,))
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_current_heavy_rain_question_uses_existing_model_features(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [(1, "Bengaluru", "Karnataka", "India")]
        cursor.fetchone.side_effect = [
            (
                datetime(2026, 10, 9, 6),
                24.5,
                70,
                25.0,
                0.0,
                0.0,
                2,
                10,
                8.0,
                180,
            ),
            (1.5,),
        ]
        connection = MagicMock()
        connection.cursor.return_value = cursor
        estimate = {
            "heavy_rain_probability": 0.4,
            "risk": "High",
            "threshold": 0.3,
            "meaning": "Current estimate",
        }

        with (
            patch.object(chatbot, "get_connection", return_value=connection),
            patch.object(
                chatbot, "estimate_heavy_rain", return_value=estimate
            ) as predict,
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    city="Bengaluru",
                    include_heavy_rain_risk=True,
                )
            )

        self.assertEqual(context["heavy_rain_model_estimate"], estimate)
        predict.assert_called_once_with(
            temperature=24.5,
            humidity=70,
            cloud_cover=10,
            wind_speed=8.0,
            previous_rain=1.5,
            month=10,
            hour=6,
        )

    def test_hourly_forecast_is_filtered_by_city_location_and_date(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [(1, "Bengaluru", "Karnataka", "India")],
            [("2026-10-10 09:00", 25.0, 60, 0.0, 0.0, 1, 5.0, 90)],
        ]
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(chatbot, "get_connection", return_value=connection):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    city="Bengaluru",
                    date=date(2026, 10, 10),
                    query_type="hourly",
                )
            )

        self.assertEqual(context["weather"][0]["temperature_c"], 25.0)
        self.assertIn("FROM hourly_forecast", cursor.execute.call_args_list[1].args[0])
        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            (1, date(2026, 10, 10)),
        )

    def test_daily_forecast_uses_existing_daily_forecast_schema(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [(1, "Bengaluru", "Karnataka", "India")]
        cursor.fetchone.return_value = (
            date(2026, 10, 10),
            29.0,
            20.0,
            30.0,
            21.0,
            2.5,
            2.0,
            61,
        )
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(chatbot, "get_connection", return_value=connection):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    city="Bengaluru",
                    date=date(2026, 10, 10),
                    query_type="daily",
                )
            )

        self.assertEqual(context["weather"]["temperature_max_c"], 29.0)
        self.assertIn("FROM daily_forecast", cursor.execute.call_args_list[1].args[0])
        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            (1, date(2026, 10, 10)),
        )

    def test_database_failure_returns_service_unavailable(self):
        with (
            patch.object(
                chatbot,
                "get_connection",
                side_effect=chatbot.psycopg2.OperationalError("unavailable"),
            ),
            patch.object(chatbot.logger, "exception"),
        ):
            with self.assertRaises(HTTPException) as error:
                chatbot._get_weather_context(chatbot.WeatherIntent(city="Bengaluru"))

        self.assertEqual(error.exception.status_code, 503)

    def test_answer_generation_includes_data_and_returns_model_text(self):
        intent = chatbot.WeatherIntent(city="Bengaluru", language="Hindi")
        weather_context = {"weather": {"temperature_c": 24}}
        with patch.object(
            chatbot,
            "_request_openai",
            return_value=" Bengaluru में तापमान 24°C है। ",
        ) as request:
            answer = chatbot._generate_answer(
                "मौसम कैसा है?", intent, weather_context
            )

        self.assertEqual(answer, "Bengaluru में तापमान 24°C है।")
        self.assertIn('"temperature_c": 24', request.call_args.args[0][1]["content"])

    def test_rain_risk_model_uses_training_features_and_threshold(self):
        model = MagicMock()
        model.classes_ = [0, 1]
        model.predict_proba.return_value = [[0.65, 0.35]]

        with patch.object(rain_risk, "_load_model", return_value=model):
            result = rain_risk.estimate_heavy_rain(
                temperature=24.5,
                humidity=70,
                cloud_cover=10,
                wind_speed=8,
                previous_rain=1.5,
                month=10,
                hour=6,
            )

        self.assertEqual(result["heavy_rain_probability"], 0.35)
        self.assertEqual(result["risk"], "High")
        self.assertEqual(
            list(model.predict_proba.call_args.args[0].columns),
            [
                "temperature_2m",
                "relative_humidity_2m",
                "cloud_cover",
                "wind_speed_10m",
                "previous_rain",
                "month",
                "hour",
            ],
        )


if __name__ == "__main__":
    unittest.main()
