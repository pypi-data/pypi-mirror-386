# aemo_to_tariff/energex.py
from datetime import time, datetime
from zoneinfo import ZoneInfo

def time_zone():
    return 'Australia/Brisbane'

def battery_tariffs(customer_type: str):
    """
    Get the battery tariff for a given customer type.

    Parameters:
    - customer_type (str): The customer type ('Residential' or 'Business').

    Returns:
    - str: The battery tariff code.
    """
    if customer_type == 'Residential':
        return {'import': ['6900'], 'export': ['6900X']}
    elif customer_type == 'Business':
        return {'import': ['6800'], 'export': ['6800X']}
    else:
        raise ValueError("Invalid customer type. Must be 'Residential' or 'Business'.")

daily_fees = {
    '8400': 0.556,  # Residential Flat
    '3900': 0.556,  # Residential Transitional Demand
    '3700': 0.556,  # Residential Demand
    '6900': 0.556,  # Residential Time of Use Energy
    '8500': 0.739,  # Small Business Flat
    '3600': 0.739,  # Small Business Demand
    '3800': 0.739,  # Small Business Transitional Demand
    '6000': {        # Small Business Wide IFT
        'band1': 0.739,
        'band2': 1.033,
        'band3': 1.322,
        'band4': 1.608,
        'band5': 1.888
    },
    '6800': {        # Small Business ToU Energy
        'band1': 0.739,
        'band2': 1.041,
        'band3': 1.343,
        'band4': 1.647,
        'band5': 1.950
    },
    '6600': 5.273,  # Large Residential Energy
    '6700': 5.273,  # Large Business Energy
    '7200': 7.665,  # LV Demand Time-of-Use
    '8100': 37.740,  # Demand Large
    '8300': 5.273,  # Demand Small
}

tariffs = {
    '8400': {
        'name': 'Residential Flat',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 9.648)
        ],
        'rate': 9.648
    },
    '3900': {
        'name': 'Residential Transitional Demand',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 4.085)
        ],
        'rate': 4.085
    },
    '3700': {
        'name': 'Residential Demand',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 3.320)
        ],
        'rate': 3.320
    },
    '6900': {
        'name': 'Residential Time of Use Energy',
        'periods': [
            ('Evening', time(16, 0), time(21, 0), 19.367),
            ('Overnight', time(21, 0), time(11, 0), 4.868),
            ('Day', time(11, 0), time(16, 0), 0.00476)
        ],
        'rate': {'Evening': 19.367, 'Overnight': 4.868, 'Day': 0.00476}
    },
    '3600': {
        'name': 'Small Business Demand',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 5.616)
        ],
        'rate': 5.616
    },
    '3800': {
        'name': 'Small Business Transitional Demand',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 6.558)
        ],
        'rate': 6.558
    },
    '6000': {
        'name': 'Small Business Wide IFT',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 10.359)
        ],
        'rate': 10.359
    },
    '8500': {
        'name': 'Small Business Flat',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 10.359)
        ],
        'rate': 10.195
    },
    '8900': {
        'name': 'Small 8900 TOU',
        'periods': [
            ('Evening', time(16, 0), time(21, 0), 22.98),
            ('Overnight', time(21, 0), time(11, 0), 11.02),
            ('Day', time(11, 0), time(16, 0), 8.37)
        ],
        'rate': 10.195
    },
    '8800': {
        'name': 'Small 8800 TOU',
        'periods': [
            ('Evening', time(7, 0), time(21, 0), 14.58),
            ('Overnight', time(21, 0), time(23, 59), 9.59),
            ('Day', time(0, 0), time(7, 0), 9.59)
        ],
        'rate': 10.195
    },
    '6800': {
        'name': 'Small Business ToU Energy',
        'periods': [
            ('Day', time(11, 0), time(16, 0), 4.356),
            ('Evening', time(16, 0), time(21, 0), 19.219),
            ('Overnight', time(21, 0), time(11, 0), 14.097)
        ],
        'rate': {'Day': 4.356, 'Evening': 19.219, 'Overnight': 14.097}
    },
    '6600': {
        'name': 'Large Residential Energy',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 9.648)
        ],
        'rate': 9.648
    },
    '6700': {
        'name': 'Large Business Energy',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 10.195)
        ],
        'rate': 10.195
    },
    '7200': {
        'name': 'LV Demand Time-of-Use',
        'periods': [
            ('Off-Peak', time(11, 0), time(13, 0), 0.00476),
            ('Peak', time(17, 0), time(20, 0), 0.01736),
            ('Shoulder', time(20, 0), time(23, 59), 0.02611),
            ('Shoulder', time(0, 0), time(10, 59), 0.02611),
            ('Shoulder', time(13, 1), time(16, 59), 0.02611),
            ('Shoulder', time(14, 0), time(16, 59), 0.02611)
        ],
        'rate': 2.484
    },
    '8100': {
        'name': 'Demand Large',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 1.301)
        ],
        'rate': 1.301
    },
    '8300': {
        'name': 'SAC Demand Small',
        'periods': [
            ('Anytime', time(0, 0), time(23, 59), 0.01736)
        ],
        'rate': 1.799
    },
    '94300': {
        'name': 'Large TOU Energy',
        'periods': [
            ('Off-Peak', time(11, 0), time(13, 59), 0.00476),
            ('Peak', time(16, 0), time(20, 59), 0.24736),
            ('Shoulder', time(21, 0), time(23, 59), 0.20136),
            ('Shoulder', time(0, 0), time(10, 59), 0.20136)
        ],
    },
}

# Add this to your existing code

demand_charges = {
    '3700': { 'Peak': 8.998},  # Residential Demand
    '3900': { 'Peak': 5.127},  # Residential Transitional Demand
    '3600': { 'Peak': 10.289},  # Small Business Demand
    '3800': { 'Peak': 4.975},  # Small Business Transitional Demand
    '7200': {
        'Off-Peak': 0.000,    # 11:00 to 13:00
        'Peak': 14.919,       # 17:00 to 20:00
        'Shoulder': 3.333     # Other times
    },
    '8100': 15.773,  # Demand Large
    '8300': 15.704,  # Demand Small
}

def translate_tariff(tariff_code: str):
    """
    Translate a tariff code to its canonical form for lookup.

    Parameters:
    - tariff_code (str): The input tariff code.

    Returns:
    - str: The canonical tariff code for lookup.
    """
    code = str(tariff_code)
    if len(code) == 4:
        prefix = code[:2]
        return prefix + '00'
    return code

def days_in_month(interval_time: datetime) -> int:
    year = interval_time.year
    month = interval_time.month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    days_in_month = (datetime(next_year, next_month, 1) - datetime(year, month, 1)).days
    return days_in_month


def estimate_demand_fee(interval_time: datetime, tariff_code: str, demand_kw: float):
    """
    Estimate the demand fee for a given tariff code, demand amount, and time period.

    Parameters:
    - interval_time (datetime): The interval datetime.
    - tariff_code (str): The tariff code.
    - demand_kw (float): The maximum demand in kW (or kVA for 8100 and 8300 tariffs).

    Returns:
    - float: The estimated demand fee in dollars.
    """
    tariff_code = translate_tariff(str(tariff_code))
    time_of_day = interval_time.astimezone(ZoneInfo(time_zone())).time()
    
    if tariff_code not in demand_charges:
        return 0.0  # Return 0 if the tariff doesn't have a demand charge

    charge = demand_charges[tariff_code]
    if isinstance(charge, dict):
        # Determine the time period
        if 'Peak' in charge and time(17, 0) <= time_of_day < time(20, 0):
            charge_per_kw_per_month = charge['Peak']
        elif 'Off-Peak' in charge and time(11, 0) <= time_of_day < time(13, 0):
            charge_per_kw_per_month = charge['Off-Peak']
        else:
            charge_per_kw_per_month = charge.get('Shoulder', 0.0)
    else:
        charge_per_kw_per_month = charge

    return charge_per_kw_per_month * demand_kw

def calculate_demand_fee(tariff_code: str, demand_kw: float, days: int = 30, tou='peak'):
    """
    Calculate the demand fee for a given tariff code, demand amount, and time period.

    Parameters:
    - tariff_code (str): The tariff code.
    - demand_kw (float): The maximum demand in kW (or kVA for 8100 and 8300 tariffs).
    - days (int): The number of days for the billing period (default is 30).

    Returns:
    - float: The demand fee in dollars.
    """
    tariff_code = translate_tariff(str(tariff_code))

    if tariff_code not in demand_charges:
        return 0.0  # Return 0 if the tariff doesn't have a demand charge

    charge = demand_charges[tariff_code]
    if isinstance(charge, dict):
        charge_per_kw_per_month = charge.get(tou, 0.0)
    else:
        charge_per_kw_per_month = charge

    # Convert the charge to a daily rate and then calculate for the given number of days
    daily_rate = charge_per_kw_per_month / days
    total_charge = demand_kw * daily_rate * days

    return total_charge

def get_daily_fee(tariff_code: str, annual_usage: float = None):
    """
    Calculate the daily fee for a given tariff code.

    Parameters:
    - tariff_code (str): The tariff code.
    - annual_usage (float): Annual usage in kWh, required for Wide IFT and ToU Energy tariffs.

    Returns:
    - float: The daily fee in dollars.
    """
    tariff_code = translate_tariff(str(tariff_code))
    fee = daily_fees.get(tariff_code)

    if isinstance(fee, dict):
        if annual_usage is None:
            raise ValueError("Annual usage is required for this tariff.")

        if annual_usage <= 20000:
            return fee['band1']
        elif annual_usage <= 40000:
            return fee['band2']
        elif annual_usage <= 60000:
            return fee['band3']
        elif annual_usage <= 80000:
            return fee['band4']
        else:
            return fee['band5']

    return fee


def get_periods(tariff_code: str):
    tariff_code = translate_tariff(str(tariff_code))
    tariff = tariffs.get(tariff_code)
    if not tariff:
        raise ValueError(f"Unknown tariff code: {tariff_code}")

    return tariff['periods']

def convert_feed_in_tariff(interval_datetime: datetime, tariff_code: str, rrp: float):
    """
    Convert RRP from $/MWh to c/kWh for SA Power Networks.

    Parameters:
    - interval_datetime (datetime): The interval datetime.
    - tariff_code (str): The tariff code.
    - rrp (float): The Regional Reference Price in $/MWh.

    Returns:
    - float: The price in c/kWh.
    """
    rrp_c_kwh = rrp / 10
    
    return rrp_c_kwh

def convert(interval_datetime: datetime, tariff_code: str, rrp: float):
    """
    Convert RRP from $/MWh to c/kWh for Energex.

    Parameters:
    - interval_time (str): The interval time.
    - tariff (str): The tariff code.
    - rrp (float): The Regional Reference Price in $/MWh.

    Returns:
    - float: The price in c/kWh.
    """
    tariff_code = translate_tariff(str(tariff_code))
    interval_time = interval_datetime.astimezone(ZoneInfo(time_zone())).time()
    rrp_c_kwh = rrp / 10

    tariff_code = str(tariff_code)[:4]
    tariff = tariffs.get(tariff_code)

    if not tariff:
        # Handle unknown tariff codes
        slope = 1.037869032618134
        intercept = 5.586606750833143
        return rrp_c_kwh * slope + intercept

    # Find the applicable period and rate
    for period, start, end, rate in tariff['periods']:
        if start <= interval_time < end or (start > end and (interval_time >= start or interval_time < end)):
            total_price = rrp_c_kwh + rate
            return total_price

    # If no period is found, use the default rate
    if isinstance(tariff['rate'], dict):
        # For Time-of-Use tariffs, use the first rate as default
        rate = list(tariff['rate'].values())[0]
    else:
        rate = tariff['rate']

    return rrp_c_kwh + rate
