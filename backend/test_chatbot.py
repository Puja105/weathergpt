
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
            intent = chatbot._understand_question(
                "ಬೆಂಗಳೂರಿನಲ್ಲಿ ನಾಳೆ ಮಳೆ ಬರುತ್ತದೆಯೇ?"
            )

        self.assertEqual(intent.cities, ["Bengaluru"])
        self.assertEqual(intent.date, date(2026, 10, 10))
        self.assertEqual(intent.query_type, "daily")
        self.assertEqual(intent.language, "Kannada")

    def test_current_weather_uses_existing_weather_data_schema(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            (1, "Bengaluru", "Karnataka", "India")
        ]
        cursor.fetchone.return_value = (
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
        )

        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(
            chatbot, "get_connection", return_value=connection
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    cities=["Bengaluru"],
                    query_type="current",
                )
            )

        result = context["weather_results"][0]

        self.assertEqual(result["location"]["city"], "Bengaluru")
        self.assertEqual(result["weather"]["temperature_c"], 24.5)

        self.assertIn(
            "FROM weather_data",
            cursor.execute.call_args_list[1].args[0],
        )
        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            (1,),
        )

        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_multiple_cities_return_independent_weather_data(self):
        cursor = MagicMock()

        cursor.fetchall.return_value = [
            (1, "Bengaluru", "Karnataka", "India"),
            (2, "Mumbai", "Maharashtra", "India"),
        ]

        cursor.fetchone.side_effect = [
            (
                datetime(2026, 11, 2, 18),
                20.5, 99, 23.3, 0.4, 0.4, 51, 96, 8.0, 70
            ),
            (
                datetime(2026, 11, 2, 18),
                30.9, 54, 34.2, 0.0, 0.0, 0, 1, 4.9, 4
            ),
        ]

        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(
            chatbot, "get_connection", return_value=connection
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    cities=["Bengaluru", "Mumbai"],
                    query_type="current",
                )
            )

        results = context["weather_results"]

        self.assertEqual(len(results), 2)

        self.assertEqual(
            results[0]["location"]["city"],
            "Bengaluru",
        )
        self.assertEqual(
            results[0]["weather"]["temperature_c"],
            20.5,
        )

        self.assertEqual(
            results[1]["location"]["city"],
            "Mumbai",
        )
        self.assertEqual(
            results[1]["weather"]["temperature_c"],
            30.9,
        )

        self.assertEqual(cursor.execute.call_count, 3)

    def test_current_heavy_rain_question_uses_existing_model_features(self):
        cursor = MagicMock()

        cursor.fetchall.return_value = [
            (1, "Bengaluru", "Karnataka", "India")
        ]

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
            patch.object(
                chatbot, "get_connection", return_value=connection
            ),
            patch.object(
                chatbot, "estimate_heavy_rain", return_value=estimate
            ) as predict,
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    cities=["Bengaluru"],
                    include_heavy_rain_risk=True,
                )
            )

        result = context["weather_results"][0]

        self.assertEqual(
            result["heavy_rain_model_estimate"],
            estimate,
        )

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
            [
                (
                    datetime(2026, 10, 10, 9),
                    25.0,
                    60,
                    0.0,
                    0.0,
                    1,
                    5.0,
                    90,
                )
            ],
        ]

        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(
            chatbot, "get_connection", return_value=connection
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    cities=["Bengaluru"],
                    date=date(2026, 10, 10),
                    query_type="hourly",
                )
            )

        result = context["weather_results"][0]

        self.assertEqual(
            result["weather"][0]["temperature_c"],
            25.0,
        )

        self.assertIn(
            "FROM hourly_forecast",
            cursor.execute.call_args_list[1].args[0],
        )

        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            (1, date(2026, 10, 10)),
        )

    def test_daily_forecast_uses_existing_daily_forecast_schema(self):
        cursor = MagicMock()

        cursor.fetchall.return_value = [
            (1, "Bengaluru", "Karnataka", "India")
        ]

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

        with patch.object(
            chatbot, "get_connection", return_value=connection
        ):
            context = chatbot._get_weather_context(
                chatbot.WeatherIntent(
                    cities=["Bengaluru"],
                    date=date(2026, 10, 10),
                    query_type="daily",
                )
            )

        result = context["weather_results"][0]

        self.assertEqual(
            result["weather"]["temperature_max_c"],
            29.0,
        )

        self.assertIn(
            "FROM daily_forecast",
            cursor.execute.call_args_list[1].args[0],
        )

        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            (1, date(2026, 10, 10)),
        )

    def test_database_failure_returns_service_unavailable(self):
        with (
            patch.object(
                chatbot,
                "get_connection",
                side_effect=chatbot.psycopg2.OperationalError(
                    "unavailable"
                ),
            ),
            patch.object(chatbot.logger, "exception"),
        ):
            with self.assertRaises(HTTPException) as error:
                chatbot._get_weather_context(
                    chatbot.WeatherIntent(cities=["Bengaluru"])
                )

        self.assertEqual(error.exception.status_code, 503)

    def test_answer_generation_includes_data_and_returns_model_text(self):
        intent = chatbot.WeatherIntent(
            cities=["Bengaluru"],
            language="Hindi",
        )

        weather_context = {
            "weather_results": [
                {
                    "location": {"city": "Bengaluru"},
                    "weather": {"temperature_c": 24},
                }
            ]
        }

        with patch.object(
            chatbot,
            "_request_openai",
            return_value=" Bengaluru में तापमान 24°C है। ",
        ) as request:
            answer = chatbot._generate_answer(
                "मौसम कैसा है?",
                intent,
                weather_context,
            )

        self.assertEqual(
            answer,
            "Bengaluru में तापमान 24°C है।",
        )

        self.assertIn(
            '"temperature_c": 24',
            request.call_args.args[0][1]["content"],
        )

    def test_rain_risk_model_uses_training_features_and_threshold(self):
        model = MagicMock()
        model.classes_ = [0, 1]
        model.predict_proba.return_value = [[0.65, 0.35]]

        with patch.object(
            rain_risk, "_load_model", return_value=model
        ):
            result = rain_risk.estimate_heavy_rain(
                temperature=24.5,
                humidity=70,
                cloud_cover=10,
                wind_speed=8,
                previous_rain=1.5,
                month=10,
                hour=6,
            )

        self.assertEqual(
            result["heavy_rain_probability"],
            0.35,
        )
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
