import datetime


def time_to_seconds(time: datetime.time) -> float:
    return (
        time.hour * 3600 + time.minute * 60 + time.second + time.microsecond / 1000000
    )
