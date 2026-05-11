def get_spn(toponym: dict) -> tuple[float, float]:
    """
    Вычисляет spn (span) объекта из ответа геокодера.
    Возвращает (spn_lon, spn_lat) в градусах.
    Если размер не определён — возвращает (0.005, 0.005).
    """
    try:
        envelope = toponym["boundedBy"]["Envelope"]
        lower = envelope["lowerCorner"].split()
        upper = envelope["upperCorner"].split()
        spn_lon = abs(float(upper[0]) - float(lower[0]))
        spn_lat = abs(float(upper[1]) - float(lower[1]))
        spn_lon = max(spn_lon, 0.001)
        spn_lat = max(spn_lat, 0.001)
        return spn_lon, spn_lat
    except (KeyError, ValueError, IndexError):
        return 0.005, 0.005
