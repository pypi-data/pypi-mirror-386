# test/test_convert.py
import unittest
from datetime import datetime
from aemo_to_tariff import spot_to_tariff, get_daily_fee, calculate_demand_fee, spot_to_feed_in_tariff

class TestTariffConversions(unittest.TestCase):

    def test_energex_tariff_6970(self):
        # Off peak
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Energex', '6900', 100, 1, 1), 10.159, 2)

        # Peak
        interval_time = datetime.strptime('2024-07-05 18:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Energex', '6970', 100, 1, 1), 29.521, 2)

        # Shoulder
        interval_time = datetime.strptime('2024-07-05 02:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Energex', '6900', 100, 1, 1), 15.022, 2)

        # With loss factor
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Energex', '6900', 200, 1.05, 1.01), 21.541, 2)

    def test_evoenergy_tariff_017(self):
        # Off peak
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Evoenergy', '017', 100, 1, 1), 13.7411, 2)

        # Peak
        interval_time = datetime.strptime('2024-07-05 17:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Evoenergy', '017', 100, 1, 1), 27.9564, 2)

        # Shoulder
        interval_time = datetime.strptime('2024-07-05 02:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Evoenergy', '017', 100, 1, 1), 16.3855, 2)

        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Evoenergy', '017', 200), 25.4255, 2)

    def test_ausgrid_tariff_EA116(self):
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Ausgrid', 'EA116', 100, 1, 1), 12.491, 2)
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Ausgrid', 'EA116', 200, 1, 1), 22.645, 2)

    def test_energex_daily_fee(self):
        self.assertAlmostEqual(get_daily_fee('Energex', '3900'), 0.556, 3)
        self.assertAlmostEqual(get_daily_fee('Energex', '7200'), 7.665, 3)
        self.assertAlmostEqual(get_daily_fee('Energex', '6000', annual_usage=15000), 0.739, 3)
        self.assertAlmostEqual(get_daily_fee('Energex', '6000', annual_usage=30000), 1.033, 3)

    def test_energex_demand_fee(self):
        self.assertAlmostEqual(calculate_demand_fee('Energex', '3700', 5.5, 31), 0.0, 2)
        self.assertAlmostEqual(calculate_demand_fee('Energex', '3900', 5.5, 31), 0.0, 2)

    def test_ausgrid_daily_fee(self):
        # Placeholder test - update when Ausgrid is implemented
        self.assertEqual(get_daily_fee('Ausgrid', 'EA116'), 0.6)

    def test_ausgrid_demand_fee(self):
        # Placeholder test - update when Ausgrid is implemented
        self.assertAlmostEqual(calculate_demand_fee('Ausgrid', 'EA116', 5.5, 31), 56.76, 1)

    def test_evoenergy_daily_fee(self):
        # Placeholder test - update when Evoenergy is implemented
        self.assertEqual(get_daily_fee('Evoenergy', '017'), 0.0)

    def test_evoenergy_demand_fee(self):
        # Placeholder test - update when Evoenergy is implemented
        self.assertEqual(calculate_demand_fee('Evoenergy', '017', 5.5, 31), 0.0)

    def test_sapn_daily_fee(self):
        self.assertAlmostEqual(get_daily_fee('SAPN', 'RTOU'), 64.4, 4)
        self.assertAlmostEqual(get_daily_fee('SAPN', 'SBTOU'), 72.59, 4)

    def test_evo_battery_trial(self):
        interval_time = datetime.strptime('2024-07-05 14:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'Evoenergy', '026', 100), 14.506, 2)
        self.assertAlmostEqual(spot_to_feed_in_tariff(interval_time, 'Evoenergy', '026', 200), 20.84, 2)
        interval_time = datetime.strptime('2024-07-05 19:00+10:00', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_feed_in_tariff(interval_time, 'Evoenergy', '026', 200), 34.2, 2)

    def test_sapn_demand_fee(self):
        self.assertAlmostEqual(calculate_demand_fee('SAPN', 'RTOU', 5.5, 31), 0, 4)
        self.assertAlmostEqual(calculate_demand_fee('SAPN', 'SBTOU', 5.5, 31), 0, 4)

    def test_sapn_tariff_RTOU(self):
        # Peak
        interval_time = datetime.strptime('2024-07-05 18:00+09:30', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'SAPN', 'RTOU', 100), 29.8692, 2)

        # Off-peak
        interval_time = datetime.strptime('2024-07-05 02:00+09:30', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'SAPN', 'RTOU', 100), 20.3892, 2)

    def test_tasnetworks_daily_fee(self):
        self.assertAlmostEqual(get_daily_fee('tasnetworks', 'TAS93'), 70.032, 2)
        self.assertAlmostEqual(get_daily_fee('tasnetworks', 'TAS94'), 83.78, 2)

    def test_tasnetworks_demand_fee(self):
        self.assertAlmostEqual(calculate_demand_fee('tasnetworks', '75', 5.5, 31), 0.0, 2)
        self.assertAlmostEqual(calculate_demand_fee('tasnetworks', '31', 5.5, 31), 0.0, 2)

    def test_tasnetworks_tariff_93(self):
        # Peak
        interval_time = datetime.strptime('2024-07-05 18:00+09:30', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'tasnetworks', 'TAS93', 100), 28.148, 2)

        # Off-peak
        interval_time = datetime.strptime('2024-07-05 02:00+09:30', '%Y-%m-%d %H:%M%z')
        self.assertAlmostEqual(spot_to_tariff(interval_time, 'tasnetworks', 'TAS93', 100), 14.537, 2)


if __name__ == '__main__':
    unittest.main()
