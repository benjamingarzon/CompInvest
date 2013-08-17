# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

# Third Party Imports
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import sys
import numpy as np 
from scipy.optimize import fmin_powell

print "Pandas Version", pd.__version__


def simulate(startdate, enddate, ls_symbols, allocations):

    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(startdate, enddate, dt_timeofday)

    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo', cachestalltime = 0)

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']

    # Reading the data, now d_data is a dictionary with the keys above.
    # Timestamps and symbols are the ones that were specified before.
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    print type(d_data['open'])

    # Filling the data for NAN
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    # Getting the numpy ndarray of close prices.
    na_price = d_data['close'].values

    # Calculate cumulative returns
    na_cum = na_price / na_price[0,:]

    # Calculate fund
    fund_cum =  np.dot(na_cum, np.array(allocations))

    # Calculate daily returns
    # Copy the normalized prices to a new ndarry to find returns.
    fund_rets = fund_cum.copy()

    # Calculate the daily returns of the prices. (Inplace calculation)
    # returnize0 works on ndarray and not dataframes.
    tsu.returnize0(fund_rets)
    
    # Calculate std and mean of returns
    fund_std = np.std(fund_rets)

    fund_mean = np.mean(fund_rets)

    # Calculate Sharpe ratio
    fund_sharpe = fund_mean / fund_std

    return(fund_std, fund_mean, fund_sharpe, fund_cum[-1])

def calc_sharpe(allocations, startdate, enddate, ls_symbols):

    ''' Just a wrapper for simulate '''
    allocationsX = np.concatenate((allocations, [1 - sum(allocations)]))
    vol, daily_ret, sharpe, cum_ret = simulate(startdate, enddate, ls_symbols, allocationsX)

    max_alloc = np.max(allocations)
    min_alloc = np.min(allocations)

# let's discourage values outside of the simplex
    if max_alloc > 1:
        sharpe = sharpe*(1 - 1000*(max_alloc - 1))

    if min_alloc < 0:
        sharpe = sharpe*(1 - 1000*(1 - min_alloc))
    print allocationsX
    print sharpe
    return -sharpe 

def main():

    ''' Main Function'''

    # List of symbols
    ls_symbols = [ "AAPL", "GLD", "GOOG", "XOM"]

    # Start and End date of the charts
    startdate = dt.datetime(2011, 1, 1)
    enddate = dt.datetime(2011, 12, 31)

    allocations0 = np.array([0.25, 0.25, 0.25])
    max_allocations = fmin_powell(calc_sharpe, allocations0, args = (startdate, enddate, ls_symbols))   
    max_allocationsX = np.concatenate((max_allocations, [1 - sum(max_allocations)]))

    print max_allocationsX
    vol, daily_ret, sharpe, cum_ret = simulate(startdate, enddate, ls_symbols, max_allocationsX)
    print sharpe, cum_ret

if __name__ == '__main__':
    main()





