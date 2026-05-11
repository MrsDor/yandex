import sys
sys.stdout.reconfigure(encoding="utf-8")

import requests

API_KEY = "bef8e409-21c9-4478-a91f-3dc865c12e24"
API_URL = "https://api.rasp.yandex.net/v3.0/search/"


def find_trains(from_code: str, to_code: str, date: str) -> list[str]:
    titles = set()
    page = 1

    while True:
        params = {
            "apikey": API_KEY,
            "from": from_code,
            "to": to_code,
            "date": date,
            "transport_types": "train",
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

        for segment in segments:
            title = segment.get("thread", {}).get("title", "").strip()
            if title:
                titles.add(title)

        total = data.get("pagination", {}).get("total", 0)
        limit = data.get("pagination", {}).get("limit", 100)
        if page * limit >= total:
            break
        page += 1

    return sorted(titles)


def main():
    args = input().split()
    if len(args) != 2:
        print("Введите два кода: откуда и куда")
        sys.exit(1)
    from_code, to_code = args

    date = input().strip()

    trains = find_trains(from_code, to_code, date)

    if not trains:
        print("Поезда не найдены.")
    else:
        for title in trains:
            print(title)


if __name__ == "__main__":
    main()
