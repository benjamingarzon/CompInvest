#! /usr/bin/env python

''' Market simulator 
@summary: Returns values for the portfolio resulting from the orders in VALUES_FILE, with an initial amount of CASH
@usage:
marketsym.py CASH ORDERS_FILE VALUES_FILE
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

def read_orders(orders_file):

    ''' read the trades and save them in an array'''
    f = open(orders_file, 'rU')
    
    orders = list()
   
    for line in f:
	split_line = line.strip("\n").split(",")
	date = dt.datetime(int(split_line[0]), int(split_line[1]),int(split_line[2])) + dt.timedelta(hours=16)
	new_order = [date, split_line[3], split_line[4], int(split_line[5])]
        orders.append(new_order)	
 
    f.close()

    orders_df = pd.DataFrame(orders, columns = ('date','symbol','type','amount'))

    nrows = len(orders_df.index)

    # sort the frame by date
    sorted_orders_df = orders_df.sort('date')
    sorted_orders_df.index = range(nrows)
    start_date = sorted_orders_df['date'][0]
    end_date = sorted_orders_df['date'][nrows - 1] + dt.timedelta(days = 1)
    sym_list = list(set(orders_df['symbol']))

    return(sorted_orders_df, start_date, end_date, sym_list)

def read_data(start_date, end_date, ls_symbols):
    ''' read the prices for the specified symbols'''
  
    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(start_date, end_date, dt_timeofday)
    
    print "Reading data"
    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo', cachestalltime = 0)

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['close']

    # Reading the data, now d_data is a dictionary with the keys above.
    # Timestamps and symbols are the ones that were specified before.
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    print "Done"
    
    d_data = dict(zip(ls_keys, ldf_data))
  
    # Filling the data for NAN
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    # Getting the numpy ndarray of close prices.
    na_price = d_data['close'].values
    na_price_df = pd.DataFrame(na_price, columns = ls_symbols, index = d_data['close'].index) 
    return(na_price_df)

def calculate_portfolio(cash, orders, prices):
    ''' calculate portfolio values given the specified orders '''
  
    order_n = 0
    amounts = prices*0
    
    for current_day in prices.index:
 	while (order_n < len(orders.index)) and (orders['date'][order_n]==current_day):            
	    symbol = orders['symbol'][order_n]
	    # increment cash when selling
		
	    sign = -1 if orders['type'][order_n]=='Sell' else 1
	    amount = orders['amount'][order_n]
	    amounts[symbol][current_day] = sign*amount
	    order_n += 1	   
    print "amounts" 
    print amounts
    cum_amounts = amounts.copy()*0

    cash_n = pd.Series(cash, amounts.index)
    portfolio = pd.Series(cash, amounts.index)
    for ind in range(0, len(amounts.index)-1): 
        total = sum(prices.iloc[ind]*amounts.iloc[ind])
	# don't allow cash to be negative, stop buying and recover cash
	new_cash = cash_n[ind] - total
        
	if new_cash > 0 : 
	    cash_n[ind+1] = new_cash
	    cum_amounts.iloc[ind+1] = cum_amounts.iloc[ind] + amounts.iloc[ind]
	    
	else:
            amounts.iloc[ind][amounts.iloc[ind]>0] = 0        
	    total = sum(prices.iloc[ind]*amounts.iloc[ind])
	    cash_n[ind+1] = cash_n[ind] - total        
	    
	cum_amounts.iloc[ind+1] = cum_amounts.iloc[ind] + amounts.iloc[ind]    
        portfolio[ind+1] = sum(prices.iloc[ind+1]*cum_amounts.iloc[ind+1]) + cash_n[ind+1]
	#print (cash_n[ind+1], -total)


    return portfolio, cash_n

def main():

    ''' Main Function'''

    cash = float(sys.argv[1])
    orders_file = sys.argv[2]
    values_file = sys.argv[3]

    # Read the orders
    orders, start_date, end_date, sym_list = read_orders(orders_file)
    print "Orders: "
    print orders

    # Read dates
    prices = read_data(start_date, end_date, sym_list)
    
    print prices
    portfolio, cash = calculate_portfolio(cash, orders, prices)
    print "Portfolio"
    print portfolio
    print "Cash: "
    print cash

    f = open(values_file, 'w')
    for ind in range(0, len(portfolio.index)): 
        d = portfolio.index[ind]
	f.write('%d, %d, %d, %d \n'%(d.year, d.month, d.day, portfolio.iloc[ind] ))

    f.close()

if __name__ == '__main__':
    main()


