import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests

API_KEY = "bef8e409-21c9-4478-a91f-3dc865c12e24"
API_URL = "https://api.rasp.yandex.net/v3.0/search/"


def get_schedule(from_code: str, to_code: str, date: str) -> list[tuple[str, str]]:
    result = []
    page = 1

    while True:
        params = {
            "apikey": API_KEY,
            "from": from_code,
            "to": to_code,
            "date": date,
            "transport_types": "suburban",
            "lang": "ru_RU",
            "format": "json",
            "page": page,
        }
        response = requests.get(API_URL, params=params)
        if not response:
            print(f"Ошибка API: {response.status_code} {response.reason}", file=sys.stderr)
            break

        data = response.json()
        segments = data.get("segments", [])
        if not segments:
            break

        for seg in segments:
            departure = seg.get("departure", "") or ""
            arrival = seg.get("arrival", "") or ""
            dep_time = departure.split("T")[-1][:8] if "T" in departure else departure[:8]
            arr_time = arrival.split("T")[-1][:8] if "T" in arrival else arrival[:8]
            result.append((dep_time, arr_time))

        total = data.get("pagination", {}).get("total", 0)
        limit = data.get("pagination", {}).get("limit", 100)
        if page * limit >= total:
            break
        page += 1

    return result


def print_direction(label: str, trips: list[tuple[str, str]]) -> None:
    print(label)
    print("Отправление\tПрибытие")
    for dep, arr in trips:
        print(f"{dep}\t{arr}")


def main():
    parts = input().split()
    if len(parts) != 3:
        print("Введите: код_откуда код_куда YYYY-MM-DD")
        sys.exit(1)
    from_code, to_code, date = parts

    there = get_schedule(from_code, to_code, date)
    back = get_schedule(to_code, from_code, date)

    print_direction("Туда:", there)
    print("-" * 20)
    print_direction("Обратно:", back)


if __name__ == "__main__":
    main()
