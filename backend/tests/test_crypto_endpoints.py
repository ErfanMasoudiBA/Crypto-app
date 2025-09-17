from fastapi.testclient import TestClient
import types

import main as app_main


client = TestClient(app_main.app)


def _sample_coins_page(page: int, per_page: int):
    base_rank = (page - 1) * per_page
    result = []
    for i in range(per_page):
        idx = base_rank + i + 1
        result.append(
            {
                "market_cap_rank": idx,
                "symbol": f"C{idx}",
                "id": f"coin-{idx}",
                "name": f"Coin {idx}",
                "current_price": 100.0 + idx,
                "market_cap": 1_000_000.0 * idx,
                "price_change_percentage_24h": 1.0,
                "total_volume": 10_000.0 * idx,
                "last_updated": "2025-01-01T00:00:00Z",
            }
        )
    return result


def test_get_cryptos_paginated(monkeypatch):
    # Monkeypatch the imported functions inside backend.main
    def fake_fetch_paginated(page: int = 1, per_page: int = 10):
        return _sample_coins_page(page, per_page)

    def fake_transform(coin):
        # Minimal transform consistent with models.CryptoCoin
        return app_main.models.CryptoCoin(
            rank=coin.get("market_cap_rank"),
            symbol=coin.get("symbol", "").upper(),
            id=coin.get("id", ""),
            name=coin.get("name", ""),
            price_usd=coin.get("current_price"),
            market_cap_usd=coin.get("market_cap"),
            change_24h_pct=coin.get("price_change_percentage_24h"),
            total_volume_usd=coin.get("total_volume"),
            last_updated=coin.get("last_updated"),
        )

    monkeypatch.setattr(app_main, "fetch_coins_from_coingecko_paginated", fake_fetch_paginated)
    monkeypatch.setattr(app_main, "transform_coin_data", fake_transform)

    resp = client.get("/cryptos", params={"page": 2, "per_page": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["per_page"] == 5
    assert isinstance(data["coins"], list) and len(data["coins"]) == 5
    first = data["coins"][0]
    assert first["rank"] == 6  # page 2, per_page 5 => ranks start at 6
    assert first["symbol"] == "C6"


def test_get_top_cryptos(monkeypatch):
    def fake_fetch_all():
        # return 20 coins
        return _sample_coins_page(page=1, per_page=20)

    def fake_transform(coin):
        return app_main.models.CryptoCoin(
            rank=coin.get("market_cap_rank"),
            symbol=coin.get("symbol", "").upper(),
            id=coin.get("id", ""),
            name=coin.get("name", ""),
            price_usd=coin.get("current_price"),
            market_cap_usd=coin.get("market_cap"),
            change_24h_pct=coin.get("price_change_percentage_24h"),
            total_volume_usd=coin.get("total_volume"),
            last_updated=coin.get("last_updated"),
        )

    monkeypatch.setattr(app_main, "fetch_coins_from_coingecko", fake_fetch_all)
    monkeypatch.setattr(app_main, "transform_coin_data", fake_transform)

    resp = client.get("/cryptos/top/10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 10
    assert len(data["coins"]) == 10
    assert data["coins"][0]["rank"] == 1

