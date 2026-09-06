import unittest

from app import calculate_multiplayer_elo


class EloTests(unittest.TestCase):
    def test_equal_two_players(self):
        rows = [
            {"account_id": 1, "elo_before": 100, "placement": 1},
            {"account_id": 2, "elo_before": 100, "placement": 2},
        ]
        result = calculate_multiplayer_elo(rows)
        self.assertEqual(result[1]["delta"], 16)
        self.assertEqual(result[2]["delta"], -16)

    def test_equal_three_players(self):
        rows = [
            {"account_id": 1, "elo_before": 100, "placement": 1},
            {"account_id": 2, "elo_before": 100, "placement": 2},
            {"account_id": 3, "elo_before": 100, "placement": 3},
        ]
        result = calculate_multiplayer_elo(rows)
        self.assertEqual(result[1]["delta"], 16)
        self.assertEqual(result[2]["delta"], 0)
        self.assertEqual(result[3]["delta"], -16)

    def test_floor_zero(self):
        rows = [
            {"account_id": 1, "elo_before": 0, "placement": 2},
            {"account_id": 2, "elo_before": 1000, "placement": 1},
        ]
        result = calculate_multiplayer_elo(rows)
        self.assertGreaterEqual(result[1]["elo_after"], 0)

    def test_upset_rewards_more(self):
        favorite_loss = [
            {"account_id": 1, "elo_before": 100, "placement": 1},
            {"account_id": 2, "elo_before": 500, "placement": 2},
        ]
        result = calculate_multiplayer_elo(favorite_loss)
        self.assertGreater(result[1]["delta"], 16)
        self.assertLess(result[2]["delta"], -16)


if __name__ == "__main__":
    unittest.main()
