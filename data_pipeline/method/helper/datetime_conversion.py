import datetime as dt
from logging import raiseExceptions

datetime_format = "%Y%m%d"


def dt_to_str(obj: dt.datetime) -> str:
    return obj.strftime(datetime_format)


def str_to_dt(obj: str) -> dt.datetime:
    return dt.datetime.strptime(obj, datetime_format)


def get_component(obj, component: str) -> str:
    if isinstance(obj, str):
        obj = dt.datetime.strptime(obj, datetime_format)

    component = component.lower()
    if component in ["d", "day"]:
        return str(obj.day)
    elif component in ["m", "month"]:
        return str(obj.month)
    elif component in ["y", "year"]:
        return str(obj.year)
    else:
        return "Invalid/Unsupported type"
