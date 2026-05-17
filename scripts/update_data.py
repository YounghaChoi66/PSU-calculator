#!/usr/bin/env python3
"""
삼성전자 PSU 계산기 — 시세 데이터 자동 갱신 스크립트
-----------------------------------------------------------
Yahoo Finance에서 삼성전자(005930.KS) 일별 종가·거래량을 받아
1주/1개월/2개월/3개월 거래량가중평균(VWAP)과 PSU 기준주가를
계산하여 data.json 으로 기록한다.

PSU 기준주가 = (1주 VWAP + 1개월 VWAP + 2개월 VWAP) ÷ 3
  · 1주/1개월/2개월: PSU 평가식에 사용되는 공식 구간
  · 3개월: 차트 표시용 추가 지표

GitHub Actions 워크플로우(.github/workflows/update-data.yml)에서
매일(평일) 실행되며, 표준 라이브러리만 사용한다(설치 의존성 없음).
"""

import datetime
import json
import sys
import urllib.request

TICKER = "005930.KS"  # 삼성전자 (KRX) — Yahoo Finance 심볼
# range=6mo 로 넉넉히 받아 2~3개월 구간 VWAP 정확도를 확보한다.
CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/"
    + TICKER
    + "?range=6mo&interval=1d"
)

KST = datetime.timezone(datetime.timedelta(hours=9))


def fetch_bars():
    """Yahoo Finance chart API에서 일별 (날짜, 종가, 거래량)을 가져온다."""
    req = urllib.request.Request(
        CHART_URL,
        headers={"User-Agent": "Mozilla/5.0 (samsung-psu-calculator updater)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    result = raw["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    closes = quote["close"]
    volumes = quote["volume"]

    bars = []
    for ts, close, vol in zip(timestamps, closes, volumes):
        # 결측 봉(휴장 등)은 건너뛴다.
        if close is None or vol is None:
            continue
        # KST 기준으로 거래일을 확정한다 (시간대 오차 방지).
        trade_date = datetime.datetime.fromtimestamp(ts, KST).date()
        bars.append(
            {"date": trade_date.isoformat(), "close": float(close), "volume": float(vol)}
        )
    bars.sort(key=lambda b: b["date"])
    return bars


def vwap(bars, days):
    """최근 `days` 일(달력 기준) 거래량가중평균 주가. 데이터 없으면 None."""
    if not bars:
        return None
    last_date = datetime.date.fromisoformat(bars[-1]["date"])
    cutoff = last_date - datetime.timedelta(days=days)
    numerator = 0.0
    denominator = 0.0
    for b in bars:
        if datetime.date.fromisoformat(b["date"]) >= cutoff:
            numerator += b["close"] * b["volume"]
            denominator += b["volume"]
    if denominator == 0:
        return None
    return numerator / denominator


def main():
    bars = fetch_bars()
    if not bars:
        print("ERROR: no price data returned from Yahoo Finance", file=sys.stderr)
        sys.exit(1)

    current = bars[-1]["close"]
    v1w = vwap(bars, 7)
    v1m = vwap(bars, 30)
    v2m = vwap(bars, 60)
    v3m = vwap(bars, 90)

    # PSU 기준주가 = (1주 + 1개월 + 2개월 VWAP) / 3
    if None in (v1w, v1m, v2m):
        base_price = None
    else:
        base_price = round((v1w + v1m + v2m) / 3)

    # 차트용 히스토리: 최근 90일(달력 기준)
    last_date = datetime.date.fromisoformat(bars[-1]["date"])
    chart_cutoff = last_date - datetime.timedelta(days=90)
    history = [
        {"date": b["date"], "close": round(b["close"])}
        for b in bars
        if datetime.date.fromisoformat(b["date"]) >= chart_cutoff
    ]

    def r(x):
        return round(x) if x is not None else None

    data = {
        "asOf": bars[-1]["date"],
        "ticker": TICKER,
        "sample": False,
        "currentPrice": r(current),
        "vwap1w": r(v1w),
        "vwap1m": r(v1m),
        "vwap2m": r(v2m),  # PSU 기준주가 산식에 사용
        "vwap3m": r(v3m),  # 차트 표시용
        "basePrice": base_price,
        "history": history,
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        "data.json updated | asOf={asOf} current={currentPrice} "
        "base={basePrice} bars={n}".format(n=len(history), **data)
    )


if __name__ == "__main__":
    main()
