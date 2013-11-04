#! /usr/bin/env python

''' Market analyzer 
@summary: Compute statistics for the time series in VALUES_FILE and compare to S&P index 
@usage:
analyze.py VALUES_FILE
'''

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

print "Pandas Version", pd.__version__


def read_values(values_file):

    ''' read the values and save them in a data frame'''
    f = open(values_file, 'rU')
    
    values = list()
   
    for line in f:
	split_line = line.strip("\n").split(",")
	date = dt.datetime(int(split_line[0]), int(split_line[1]),int(split_line[2])) + dt.timedelta(hours=16)
	new_value = [date, split_line[3]]
        values.append(new_value)	

    f.close()

    values_df = pd.DataFrame(values, columns = ('date','value'), dtype=np.dtype('f8'))
    nrows = len(values_df.index)

    start_date = values_df['date'][0]
    end_date = values_df['date'][nrows - 1] + dt.timedelta(days = 1)

    return(values_df, start_date, end_date)

def read_reference(start_date, end_date, ls_symbol):
    ''' Read the reference symbol values and save them as a series'''

    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(start_date, end_date, dt_timeofday)

    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo', cachestalltime = 0)

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['close']

    # Reading the data, now d_data is a dictionary with the keys above.
    # Timestamps and symbols are the ones that were specified before.
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbol, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
  
    # Filling the data for NAN
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    # Getting the numpy ndarray of close prices.
    na_price = d_data['close'].values
    na_price_df = pd.DataFrame(na_price, columns = ls_symbol, index = d_data['close'].index) 
    return(na_price_df)


def compute_stats(na_price):

    ''' Compute Sharpe etc '''
    # Calculate cumulative returns
    na_cum = na_price / na_price[0]

    # Calculate total returns
    na_total = na_price[-1] - na_price[0]

    # Calculate daily returns
    # Copy the normalized prices to a new ndarry to find returns.
    na_rets = na_cum.copy()

    # Calculate the daily returns of the prices. (Inplace calculation)
    # returnize0 works on ndarray and not dataframes.
    tsu.returnize0(na_rets)
    
    # Calculate std and mean of returns
    na_std = np.std(na_rets)

    na_mean = np.mean(na_rets)

    # Calculate Sharpe ratio
    na_sharpe = na_mean / na_std
    
    return(na_sharpe, na_total, na_std, na_mean, na_cum)


def main():

#print "Data Range :  %s  to  %s"
#print "Sharpe Ratio of Fund : $d"
#print "Total Return of Fund : $d"
#print "Standard Deviation of Fund : $d"
#print "Average Daily Return of Fund :$d"

    ''' Main Function'''
    values_file = sys.argv[1]
    symbol = sys.argv[2]

    # Start and End date of the charts
    startdate = dt.datetime(2011, 1, 1)
    enddate = dt.datetime(2011, 1, 31)

    fund_df, start_date, end_date = read_values(values_file)
    market_df = read_reference(start_date, end_date, [symbol])
    
    fund_values = fund_df['value'].values
    market_values = market_df[symbol].values

    fund_sharpe, fund_total, fund_std, fund_mean, fund_cum = compute_stats(fund_values)
    market_sharpe, market_total, market_std, market_mean, market_cum = compute_stats(market_values)

    print "Sharpe Ratio of Fund : %f"%(fund_sharpe)
    print "Sharpe Ratio of Market : %f"%(market_sharpe)

    print "Total Return of Fund : %f"%(fund_total)
    print "Total Return of Market : %f"%(market_total)

    print "Standard Deviation of Fund : %f"%(fund_std)
    print "Standard Deviation of Market : %f"%(market_std)

    print "Average Daily Return of Fund : %f"%(fund_mean)
    print "Average Daily Return of Market %f"%(market_mean)

    plt.clf()
    plt.plot(range(0, len(fund_df.index)), fund_cum, label="ValueF")
    plt.plot(range(0, len(market_df.index)), market_cum,label="Value")
    plt.legend(['Fund', 'Market'])
    plt.ylabel('Values')
    #plt.xticks(rotation=70)

    plt.savefig("analysis.png", format='png')

if __name__ == '__main__':
    main()




    


