"""
KOSPI 시가총액 상위 10종목 월별 리밸런싱 전략 분석
- 시작: 2010년 1월 2일
- 전략: 매월 말 시가총액 상위 10위 종목 유지
  - 탈락 종목: 매도
  - 신규 진입 종목: 100만원 매수
- 기존 보유 종목은 그대로 유지 (수량 유지)
"""

import pandas as pd
import numpy as np
from pykrx import stock
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_last_trading_day_of_month(year, month):
    """해당 월의 마지막 거래일 반환"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    date_str = last_day.strftime('%Y%m%d')
    return date_str

def get_first_trading_day_of_month(year, month):
    """해당 월의 첫 거래일 반환"""
    first_day = datetime(year, month, 1)
    date_str = first_day.strftime('%Y%m%d')
    return date_str

print("=" * 60)
print("KOSPI 시가총액 상위 10종목 월별 리밸런싱 전략 분석")
print("=" * 60)
print()

# 전략 파라미터
INITIAL_BUY_AMOUNT = 1_000_000  # 100만원
START_DATE = '20100102'
END_YEAR = 2025
END_MONTH = 12

# ─── 월별 시가총액 상위 10종목 수집 ───────────────────────────
print("월별 KOSPI 시가총액 데이터 수집 중...")
print("(2010년 ~ 2025년, 약 192개월, 시간이 걸릴 수 있습니다)")
print()

monthly_top10 = {}  # {YYYYMM: [(ticker, name, market_cap), ...]}
monthly_prices = {}  # {YYYYMM: {ticker: close_price}}

years = range(2010, 2026)
months = range(1, 13)

for year in years:
    for month in months:
        ym_key = f"{year}{month:02d}"

        # 2025년 5월 이후는 스킵 (데이터 없을 수 있음)
        if year == 2026 or (year == 2025 and month > 4):
            break

        # 해당 월의 마지막 거래일 구하기
        date_str = get_last_trading_day_of_month(year, month)

        try:
            # KOSPI 시가총액 데이터 조회
            df = stock.get_market_cap(date_str, market="KOSPI")
            if df is None or df.empty:
                # 하루씩 앞당겨서 재시도
                for delta in range(1, 10):
                    alt_date = (datetime.strptime(date_str, '%Y%m%d') - timedelta(days=delta))
                    alt_str = alt_date.strftime('%Y%m%d')
                    df = stock.get_market_cap(alt_str, market="KOSPI")
                    if df is not None and not df.empty:
                        date_str = alt_str
                        break

            if df is None or df.empty:
                print(f"  {ym_key}: 데이터 없음 스킵")
                continue

            # 시가총액 기준 정렬, 상위 10개
            df = df.sort_values('시가총액', ascending=False)
            top10 = df.head(10)

            top10_list = []
            price_dict = {}
            for ticker in top10.index:
                try:
                    name = stock.get_market_ticker_name(ticker)
                except:
                    name = ticker
                mktcap = top10.loc[ticker, '시가총액']
                close = top10.loc[ticker, '종가'] if '종가' in top10.columns else 0
                top10_list.append((ticker, name, mktcap, close))
                price_dict[ticker] = close

            monthly_top10[ym_key] = top10_list
            monthly_prices[ym_key] = price_dict

            if month == 1 or month == 7:
                top_names = [t[1] for t in top10_list[:3]]
                print(f"  {year}년 {month:02d}월: {', '.join(top_names)} ...")

        except Exception as e:
            print(f"  {ym_key}: 오류 - {e}")
            continue

print()
print(f"수집 완료: {len(monthly_top10)}개월 데이터")
print()

# ─── 투자 시뮬레이션 ───────────────────────────────────────────
print("=" * 60)
print("투자 시뮬레이션 시작")
print("=" * 60)

# 포트폴리오: {ticker: {'shares': 수량, 'buy_price': 매수단가, 'name': 종목명}}
portfolio = {}
total_invested = 0  # 총 투자금액
total_cash_from_sales = 0  # 매도로 회수한 현금
cumulative_invested = 0  # 누적 순투자금 (투자 - 회수)

trade_log = []

sorted_months = sorted(monthly_top10.keys())

for i, ym_key in enumerate(sorted_months):
    top10_data = monthly_top10[ym_key]
    prices = monthly_prices[ym_key]

    current_top10_tickers = set(t[0] for t in top10_data)
    held_tickers = set(portfolio.keys())

    # 탈락 종목 매도
    to_sell = held_tickers - current_top10_tickers
    sell_proceeds = 0
    for ticker in to_sell:
        if ticker in prices:
            sell_price = prices[ticker]
        else:
            # 가격 정보 없으면 매수가로 처리
            sell_price = portfolio[ticker]['buy_price']

        shares = portfolio[ticker]['shares']
        proceeds = shares * sell_price
        sell_proceeds += proceeds
        total_cash_from_sales += proceeds

        trade_log.append({
            'month': ym_key,
            'action': 'SELL',
            'ticker': ticker,
            'name': portfolio[ticker]['name'],
            'shares': shares,
            'price': sell_price,
            'amount': proceeds
        })
        del portfolio[ticker]

    # 신규 진입 종목 매수 (첫 달은 전체 10종목 매수)
    new_tickers = current_top10_tickers - held_tickers

    for td in top10_data:
        ticker, name, mktcap, close_price = td
        if ticker in new_tickers:
            if close_price <= 0:
                continue

            shares = INITIAL_BUY_AMOUNT / close_price
            cost = shares * close_price
            total_invested += cost
            cumulative_invested += cost

            portfolio[ticker] = {
                'shares': shares,
                'buy_price': close_price,
                'name': name
            }

            trade_log.append({
                'month': ym_key,
                'action': 'BUY',
                'ticker': ticker,
                'name': name,
                'shares': shares,
                'price': close_price,
                'amount': cost
            })

    # 매도 대금 차감 (누적 순투자금 계산)
    cumulative_invested -= sell_proceeds

# ─── 최종 포트폴리오 가치 계산 ────────────────────────────────
print()
print("최종 포트폴리오 평가 중...")
latest_ym = sorted_months[-1]
print(f"마지막 평가 기준월: {latest_ym}")
print()

final_prices = monthly_prices.get(latest_ym, {})
final_value = 0
portfolio_detail = []

for ticker, info in portfolio.items():
    if ticker in final_prices and final_prices[ticker] > 0:
        current_price = final_prices[ticker]
    else:
        current_price = info['buy_price']

    current_value = info['shares'] * current_price
    cost_basis = info['shares'] * info['buy_price']
    gain = current_value - cost_basis
    gain_pct = (gain / cost_basis) * 100 if cost_basis > 0 else 0

    final_value += current_value
    portfolio_detail.append({
        'ticker': ticker,
        'name': info['name'],
        'shares': info['shares'],
        'buy_price': info['buy_price'],
        'current_price': current_price,
        'cost_basis': cost_basis,
        'current_value': current_value,
        'gain': gain,
        'gain_pct': gain_pct
    })

# ─── 결과 출력 ────────────────────────────────────────────────
print("=" * 60)
print("분석 결과")
print("=" * 60)

total_revenue = final_value + total_cash_from_sales
net_return = total_revenue - total_invested
net_return_pct = (net_return / total_invested) * 100 if total_invested > 0 else 0

# 연환산 수익률 계산 (2010.01 ~ 2025.04 = 약 15.3년)
years_elapsed = (datetime.strptime(latest_ym + "01", "%Y%m%d") - datetime.strptime("20100102", "%Y%m%d")).days / 365.25
cagr = ((total_revenue / total_invested) ** (1 / years_elapsed) - 1) * 100 if total_invested > 0 and years_elapsed > 0 else 0

print(f"\n📌 투자 기간: 2010년 1월 ~ {latest_ym[:4]}년 {latest_ym[4:]}월 ({years_elapsed:.1f}년)")
print(f"\n💰 투자 내역")
print(f"   총 매수 금액 (누계):   {total_invested:>15,.0f} 원")
print(f"   총 매도 회수 금액:     {total_cash_from_sales:>15,.0f} 원")
print(f"   현재 보유 평가금액:    {final_value:>15,.0f} 원")
print(f"\n📈 수익 분석")
print(f"   총 투자 대비 총 회수:  {total_revenue:>15,.0f} 원")
print(f"   순 손익:               {net_return:>15,.0f} 원")
print(f"   총 수익률:             {net_return_pct:>14.2f} %")
print(f"   연환산 수익률 (CAGR):  {cagr:>14.2f} %")

print(f"\n📊 현재 보유 포트폴리오 (상위 10종목 기준 {latest_ym})")
print(f"{'종목명':<12} {'매수가':>10} {'현재가':>10} {'수익률':>8}")
print("-" * 45)
for p in sorted(portfolio_detail, key=lambda x: x['gain_pct'], reverse=True):
    print(f"{p['name']:<12} {p['buy_price']:>10,.0f} {p['current_price']:>10,.0f} {p['gain_pct']:>7.1f}%")

# 거래 요약
buy_trades = [t for t in trade_log if t['action'] == 'BUY']
sell_trades = [t for t in trade_log if t['action'] == 'SELL']
print(f"\n📋 거래 요약")
print(f"   총 매수 거래: {len(buy_trades)}건")
print(f"   총 매도 거래: {len(sell_trades)}건")
print(f"   분석 기간 총 월수: {len(sorted_months)}개월")

# 연도별 상위 10 종목 변화
print(f"\n📅 연도별 시가총액 1위 종목 변화")
for year in [2010, 2013, 2016, 2019, 2022, 2025]:
    for month in [1]:
        ym = f"{year}{month:02d}"
        if ym in monthly_top10:
            top3 = [t[1] for t in monthly_top10[ym][:3]]
            print(f"   {year}년 1월: {' > '.join(top3)}")

print()
print("=" * 60)
print("분석 완료")
print("=" * 60)
