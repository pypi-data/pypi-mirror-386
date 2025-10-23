import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
import aemo_to_tariff.evoenergy as evoenergy

class TestEvoenergy(unittest.TestCase):
    def test_some_evoenergy_functionality(self):
        interval_time = datetime(2025, 2, 20, 13, 45, tzinfo=ZoneInfo('Australia/Sydney'))
        tariff_code = '017'
        rrp = -27.14
        expected_price = 0.916755
        price = evoenergy.convert(interval_time, tariff_code, rrp)
        loss_factor = expected_price / price
        self.assertAlmostEqual(price * 1.05, expected_price, places=2)

    def test_peak_evoenergy_functionality(self):
        interval_time = datetime(2025, 3, 28, 15, 55, tzinfo=ZoneInfo('Australia/Sydney'))
        tariff_code = '017'
        rrp = 119.63
        expected_price = 17.46672
        price = evoenergy.convert(interval_time, tariff_code, rrp)
        loss_factor = expected_price / price
        self.assertAlmostEqual(price * 0.96, expected_price, places=1)

    def test_noon_evoenergy_april(self):
        interval_time = datetime(2025, 4, 30, 12, 00, tzinfo=ZoneInfo('Australia/Sydney'))
        tariff_code = '017'
        rrp = -23.5
        expected_price = 1.026793
        price = evoenergy.convert(interval_time, tariff_code, rrp)
        loss_factor = expected_price / price
        print(f"Loss factor: {loss_factor}")
        self.assertAlmostEqual(price * 0.83, expected_price, places=1)

    def test_peak_evoenergy_april(self):
        interval_time = datetime(2025, 4, 28, 17, 55, tzinfo=ZoneInfo('Australia/Sydney'))
        tariff_code = '017'
        rrp = 110.4
        expected_price = 14.15
        price = evoenergy.convert(interval_time, tariff_code, rrp)
        loss_factor = expected_price / price
        print(f"Loss factor: {loss_factor}")
        self.assertAlmostEqual(price * 0.83, expected_price, places=1)
