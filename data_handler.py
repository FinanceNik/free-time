import pandas as pd
from datetime import datetime

data = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv")


def time_difference(start_time_str, end_time_str, time_format='%H:%M:%S'):
    """
    Calculate the time difference between two time strings.

    Parameters:
    - start_time_str (str): Start time string in the specified format.
    - end_time_str (str): End time string in the specified format.
    - time_format (str): Format of the time strings (default is '%H:%M:%S').

    Example:
    start_time_str = '08:30:00'
    end_time_str = '17:15:00'

    Returns:
    - timedelta: Time difference as a timedelta object.
    """
    start_time = datetime.strptime(start_time_str, time_format)
    end_time = datetime.strptime(end_time_str, time_format)
    time_diff = str(end_time - start_time)

    return time_diff
