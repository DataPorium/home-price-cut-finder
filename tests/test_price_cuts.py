import pytest

import price_cuts as pc


def home(i, cut):
    return {"property_id": str(i), "address": f"{i} Main St", "price": 800000 - cut,
            "price_cut": {"total": cut, "last_date": "2026-11-01"}, "beds": 3, "tags": ["pool", "view"]}


class FakeClient:
    def __init__(self):
        self.calls = []

    def properties(self, **params):
        self.calls.append(params)
        homes = [home(i, 50000 - i * 1000) for i in range(5)]
        start = params["offset"]
        page = homes[start:start + params["limit"]]
        nxt = start + len(page) if start + len(page) < len(homes) else None
        return {"total_matches": 5, "summary": {"count": 5}, "homes": page, "next_offset": nxt,
                "website_link": "https://dataporium.tech/x"}


def test_homes_found_at_any_level():
    assert len(pc.homes_in({"summary": {"count": 1}, "homes": [home(1, 5)]})) == 1
    assert len(pc.homes_in({"data": {"results": [home(1, 5), home(2, 5)]}})) == 2
    assert pc.homes_in([home(1, 5)])[0]["property_id"] == "1"


def test_flatten_and_columns():
    row = pc.flatten(home(1, 5000))
    assert row["price_cut_total"] == 5000 and row["tags"] == "pool; view"
    assert pc.columns_for([row])[:3] == ["address", "price", "beds"]
    assert pc.pick(row, "total_price_cut", "price_cut") == 5000


def test_main_pages_and_writes(tmp_path, monkeypatch, capsys):
    fake = FakeClient()
    monkeypatch.setattr(pc, "DataPorium", lambda: fake)
    monkeypatch.setattr(pc, "PAGE", 2)
    out = tmp_path / "cuts.csv"
    assert pc.main(["--zip", "92602", "--within-days", "7", "--out", str(out)]) == 0
    assert len(out.read_text().splitlines()) == 6
    assert [c["offset"] for c in fake.calls] == [0, 2, 4]
    assert fake.calls[0]["price_cut"] is True and fake.calls[0]["sort"] == "biggest_cut"
    assert "cut $50,000" in capsys.readouterr().out


def test_needs_a_place():
    with pytest.raises(SystemExit):
        pc.main([])


REAL = {"mode": "search", "total_matches": 33, "summary": {"count": 33},
        "area_market": [{"level": "zip", "name": "92602", "for_sale": {"homes": 77}}],
        "website_link": "https://dataporium.tech/real-estate?zip=92602",
        "homes": [{"property_id": "9131968575", "address": "166 Villa Rdg, Irvine, CA 92602", "price": 2250000,
                   "beds": 4, "total_cut": -640000, "total_cut_pct": -22.15,
                   "nearby_2_miles": {"homes": 143, "median_price": 2238000}}],
        "next_offset": None}


def test_real_answer_shape(tmp_path, monkeypatch, capsys):
    class Real:
        def properties(self, **params):
            return REAL
    monkeypatch.setattr(pc, "DataPorium", lambda: Real())
    out = tmp_path / "real.csv"
    assert pc.main(["--zip", "92602", "--out", str(out)]) == 0
    header = out.read_text().splitlines()[0].split(",")
    assert header[:3] == ["address", "price", "total_cut"] and "nearby_2_miles_median_price" in header
    printed = capsys.readouterr().out
    assert "cut $640,000" in printed and "(33 match in all)" in printed
