import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import interp1d
import logging
from utils import get_current_price

logger = logging.getLogger(__name__)

def filter_dates(dates):
    today = datetime.today().date()
    cutoff_date = today + timedelta(days=45)
    
    sorted_dates = sorted(datetime.strptime(date, "%Y-%m-%d").date() for date in dates)

    arr = []
    for i, date in enumerate(sorted_dates):
        if date >= cutoff_date:
            arr = [d.strftime("%Y-%m-%d") for d in sorted_dates[:i+1]]  
            break
    
    if len(arr) > 0:
        if arr[0] == today.strftime("%Y-%m-%d"):
            return arr[1:]
        return arr

    raise ValueError("No date 45 days or more in the future found.")


def yang_zhang(price_data, window=30, trading_periods=252, return_last_only=True):
    log_ho = (price_data['High'] / price_data['Open']).apply(np.log)
    log_lo = (price_data['Low'] / price_data['Open']).apply(np.log)
    log_co = (price_data['Close'] / price_data['Open']).apply(np.log)
    
    log_oc = (price_data['Open'] / price_data['Close'].shift(1)).apply(np.log)
    log_oc_sq = log_oc**2
    
    log_cc = (price_data['Close'] / price_data['Close'].shift(1)).apply(np.log)
    log_cc_sq = log_cc**2
    
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    
    close_vol = log_cc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    open_vol = log_oc_sq.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    window_rs = rs.rolling(
        window=window,
        center=False
    ).sum() * (1.0 / (window - 1.0))

    k = 0.34 / (1.34 + ((window + 1) / (window - 1)) )
    result = (open_vol + k * close_vol + (1 - k) * window_rs).apply(np.sqrt) * np.sqrt(trading_periods)

    if return_last_only:
        return result.iloc[-1]
    else:
        return result.dropna()
    

def build_term_structure(days, ivs):
    days = np.array(days)
    ivs = np.array(ivs)

    sort_idx = days.argsort()
    days = days[sort_idx]
    ivs = ivs[sort_idx]

    spline = interp1d(days, ivs, kind='linear', fill_value="extrapolate")

    def term_spline(dte):
        if dte < days[0]:  
            return ivs[0]
        elif dte > days[-1]:
            return ivs[-1]
        else:  
            return float(spline(dte))

    return term_spline


def compute_recommendation(tickers):
    if isinstance(tickers, str):
        tickers = [tickers]
    
    recommendations = {}
    
    for ticker in tickers:
        try:
            ticker = ticker.strip().upper()
            if not ticker:
                recommendations[ticker] = "No stock symbol provided."
                continue
            
            try:
                stock = yf.Ticker(ticker)
                if len(stock.options) == 0:
                    raise KeyError()
            except KeyError:
                recommendations[ticker] = f"Error: No options found for stock symbol '{ticker}'."
                continue
            
            exp_dates = list(stock.options)
            try:
                exp_dates = filter_dates(exp_dates)
            except Exception as e:
                logger.error(f"Error filtering dates for {ticker}: {e}")
                recommendations[ticker] = "Error: Not enough option data."
                continue
            
            options_chains = {}
            for exp_date in exp_dates:
                options_chains[exp_date] = stock.option_chain(exp_date)
            
            try:
                underlying_price = get_current_price(stock)
                if underlying_price is None:
                    raise ValueError("No market price found.")
            except Exception as e:
                logger.error(f"Error retrieving underlying stock price for {ticker}: {e}")
                recommendations[ticker] = "Error: Unable to retrieve underlying stock price."
                continue
            
            atm_iv = {}
            straddle = None 
            i = 0
            for exp_date, chain in options_chains.items():
                calls = chain.calls
                puts = chain.puts

                if calls.empty or puts.empty:
                    continue

                call_diffs = (calls['strike'] - underlying_price).abs()
                call_idx = call_diffs.idxmin()
                call_iv = calls.loc[call_idx, 'impliedVolatility']

                put_diffs = (puts['strike'] - underlying_price).abs()
                put_idx = put_diffs.idxmin()
                put_iv = puts.loc[put_idx, 'impliedVolatility']

                atm_iv_value = (call_iv + put_iv) / 2.0
                atm_iv[exp_date] = atm_iv_value

                if i == 0:
                    call_bid = calls.loc[call_idx, 'bid']
                    call_ask = calls.loc[call_idx, 'ask']
                    put_bid = puts.loc[put_idx, 'bid']
                    put_ask = puts.loc[put_idx, 'ask']
                    
                    if call_bid is not None and call_ask is not None:
                        call_mid = (call_bid + call_ask) / 2.0
                    else:
                        call_mid = None

                    if put_bid is not None and put_ask is not None:
                        put_mid = (put_bid + put_ask) / 2.0
                    else:
                        put_mid = None

                    if call_mid is not None and put_mid is not None:
                        straddle = (call_mid + put_mid)

                i += 1
            
            if not atm_iv:
                recommendations[ticker] = "Error: Could not determine ATM IV for any expiration dates."
                continue
            
            today = datetime.today().date()
            dtes = []
            ivs = []
            for exp_date, iv in atm_iv.items():
                exp_date_obj = datetime.strptime(exp_date, "%Y-%m-%d").date()
                days_to_expiry = (exp_date_obj - today).days
                dtes.append(days_to_expiry)
                ivs.append(iv)
            
            term_spline = build_term_structure(dtes, ivs)
            
            ts_slope_0_45 = (term_spline(45) - term_spline(dtes[0])) / (45-dtes[0])
            
            price_history = stock.history(period='3mo')
            iv30_rv30 = term_spline(30) / yang_zhang(price_history)

            avg_volume = price_history['Volume'].rolling(30).mean().dropna().iloc[-1]

            expected_move = round(straddle / underlying_price * 100,2) if straddle else None

            avg_volume_bool = avg_volume >= 1500000
            iv30_rv30_bool = iv30_rv30 >= 1.25
            ts_slope_bool = ts_slope_0_45 <= -0.00406

            if avg_volume_bool and iv30_rv30_bool and ts_slope_bool:
                recommendations[ticker] = {"Recommendation": "Recommended", "Expected Move": expected_move}
            elif ts_slope_bool and (avg_volume_bool or iv30_rv30_bool):
                recommendations[ticker] = {"Recommendation": "Consider", "Expected Move": expected_move}
            else:
                recommendations[ticker] = None
                
        except Exception as e:
            logger.error(f"Error occurred processing {ticker}: {str(e)}")
            recommendations[ticker] = f'Error occurred processing {ticker}: {str(e)}'
    
    return recommendations
    
def process_tickers(df):
    logger.info(f"Processing tickers: {df['Ticker']}")
    results = compute_recommendation(df['Ticker'])
    for ticker, result in results.items():
        if result is None:
            df = df[df['Ticker'] != ticker]
        else:
            df.loc[df['Ticker'] == ticker, 'Recommendation'] = result['Recommendation']
            df.loc[df['Ticker'] == ticker, 'Expected Move'] = result['Expected Move']
        
    return df
