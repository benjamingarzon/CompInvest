#! /usr/bin/env python

'''
(c) 2011, 2012 Georgia Tech Research Corporation
Modified from Event profiler Tutorial 
@summary: create matrix of buy/sell events with bollinger bands

@usage: events_output ORDERS_FILE
'''

import sys
import pandas as pd
import numpy as np
import math
import copy
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep

"""
Accepts a list of symbols along with start and end date
Returns the Event Matrix which is a pandas Datamatrix
Event matrix has the following structure :
    |IBM |GOOG|XOM |MSFT| GS | JP |
(d1)|nan |nan | 1  |nan |nan | 1  |
(d2)|nan | 1  |nan |nan |nan |nan |
(d3)| 1  |nan | 1  |nan | 1  |nan |
(d4)|nan | 2 |nan | 1  |nan |nan |
...................................
...................................
Also, d1 = start date
nan = no information about any event.
1 = Buy order
2 = Sell order
"""
N_PERIODS = 20

def compute_bollinger(prices):
    ''' Computing Bollinger values '''
    print "Computing Bollinger values"
    means = pd.rolling_mean(prices,N_PERIODS,min_periods=N_PERIODS)
    stds = pd.rolling_std(prices,N_PERIODS,min_periods=N_PERIODS)
    bollinger_vals = ( prices - means ) / stds
    print bollinger_vals
    return bollinger_vals

def find_events(ls_symbols, d_data, start_date, end_date):
    ''' Finding the event dataframe '''
    print "Finding Events"
    df_close = d_data['actual_close'] 
#    ts_market = df_close['SPY']

    # Creating an empty dataframe
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    # Compute Bollinger bands
    df_bollinger_complete = compute_bollinger(df_close)

    # Select adequate dates
    df_bollinger = df_bollinger_complete.ix[start_date:end_date]

    # Time stamps for the event range
    ldt_timestamps = df_bollinger.index
	    
    for s_sym in ls_symbols:
        print "Calculating values for %s"%(s_sym)
	last_order = 2	  
        for i in range(1, len(ldt_timestamps)):

            # Calculating the returns for this timestamp
	    f_symprice_today = df_close[s_sym].ix[ldt_timestamps[i]]
            f_symprice_yest = df_close[s_sym].ix[ldt_timestamps[i - 1]]
            f_symbollinger_today = df_bollinger[s_sym].ix[ldt_timestamps[i]]
            f_symbollinger_yest = df_bollinger[s_sym].ix[ldt_timestamps[i - 1]]

            # 1 = 'Buy' event if symbol crosses lower bollinger 
            # 2 = 'Sell' event if symbol crosses upper bollinger 
	    # only possible to sell we bought before and viceversa
            if f_symbollinger_today <= -2 and f_symbollinger_yest > -2 and last_order == 2:
                df_events[s_sym].ix[ldt_timestamps[i]] = 1
  		last_order = 1
            # sell if you are holding equity
            if f_symbollinger_today >= 2 and f_symbollinger_yest < 2 and last_order == 1:
                df_events[s_sym].ix[ldt_timestamps[i]] = 2
		last_order = 2

    return df_events

if __name__ == '__main__':

    orders_file = sys.argv[1]
# start computing N_PERIODS earlier ?
    dt_start = dt.datetime(2012, 1, 1)
    dt_start_real = dt_start - dt.timedelta(days=N_PERIODS*2)
    dt_end = dt.datetime(2012, 6, 30)
    ldt_timestamps = du.getNYSEdays(dt_start_real, dt_end, dt.timedelta(hours=16))

    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    #ls_symbols = ['AAPL']
    #ls_symbols.append('SPY')

    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
   
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    df_events = find_events(ls_symbols, d_data, dt_start, dt_end)

    # write out to a file
    f = open(orders_file, 'w')

    for ind in range(0, len(df_events.index)): 
        d = df_events.index[ind]
	row = df_events.iloc[ind]
        buy_symbols = row[row==1].index
        sell_symbols = row[row==2].index

	# place buy orders
	for symbol in buy_symbols:
	    f.write('%d,%d,%d,%s,Buy,100\n'%(d.year, d.month, d.day, symbol ))
	# place sell orders
	for symbol in sell_symbols:
	    f.write('%d,%d,%d,%s,Sell,100\n'%(d.year, d.month, d.day, symbol ))

    f.close()

