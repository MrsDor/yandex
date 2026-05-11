import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests

API_KEY = "fa0f11a5-fd86-48c2-b07f-ef6e45a933a8"
API_URL = "https://api.weather.yandex.ru/v2/climate"


def get_monthly_temps(lat: float, lon: float) -> list[int]:
    params = {"lat": lat, "lon": lon}
    headers = {"X-Yandex-Weather-Key": API_KEY}
    response = requests.get(API_URL, params=params, headers=headers)
    if not response:
        print(f"Ошибка API: {response.status_code} {response.reason}", file=sys.stderr)
        sys.exit(1)
    months = response.json() 
    return [round(m["avg_day_t"]) for m in months]


def draw_chart(temps: list[int]) -> None:
    min_temp = min(temps)
    max_neg = abs(min_temp) if min_temp < 0 else 0  

    print("Среднемесячные температуры:")
    for t in temps:
        if t >= 0:
            left = " " * max_neg
            right = "*" * t
        else:
            stars = "*" * abs(t)
            left = stars.rjust(max_neg)
            right = ""
        print(f"{left}|{right}")


def main():
    parts = input().split()
    if len(parts) != 2:
        print("Введите: широта долгота")
        sys.exit(1)
    lat, lon = float(parts[0]), float(parts[1])

    temps = get_monthly_temps(lat, lon)
    draw_chart(temps)


if __name__ == "__main__":
    main()
