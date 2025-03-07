import datetime

def message(indent : int, message : str, flush=False):
    bullet_points = ['', '->', '-+', '>>']
    print(f"{get_datetime_string()} | {' ' * ((indent - 1) * 2)}{bullet_points[indent]} {message}", flush=flush)


def get_datetime_string():
    return datetime.datetime.today().strftime('%d-%m-%Y %H:%M:%S')