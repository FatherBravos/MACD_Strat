# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 14:37:51 2022

@author: Admin
"""
import datetime
import talib
import pandas as pd
from candles_backtester import backtester
import itertools
import numpy as np
import os
import time
import warnings
import json
from pymongo import MongoClient
import altair as alt

class data_generator:
    def __init__(self,**kwargs):
        for key in kwargs:
            setattr(self,key,kwargs[key])
        self.shift_dic={'1hour':60,'3hours':180,'1d':1440,'1min':1}
    def get_ohlc_data(self,timeframe):
        data = market_db.find(
            {"timestamp": {"$gte": self.gte, "$lte": self.lt}, "granularity": timeframe,
             'market_type': self.market_type, 'price_type': self.price_type})

        data = pd.DataFrame(list(data))[['timestamp', 'open', 'high', 'low', 'close']]
        data.columns = ['time', 'open', 'high', 'low', 'close']
        return data
    def macd(self,timeframe,fast_macd,slow_macd,signal_macd):
        data=self.get_ohlc_data(timeframe)
        data['macd'], data['signal_macd'], data['hist'] = talib.MACD(np.array(data['close']), fastperiod=fast_macd,slowperiod=slow_macd,signalperiod=signal_macd)
        data['macd'], data['signal_macd']=data['macd'].shift(1), data['signal_macd'].shift(1)
        data.dropna(inplace=True)
        return data[['time','macd','signal_macd']]
    def atr(self,timeframe,lookback):
        data = self.get_ohlc_data(timeframe)
        data['atr'] = talib.ATR(np.array(data['high']),np.array(data['low']),np.array(data['close']),timeperiod=lookback)
        data['atr']=data['atr'].shift(1)
        data.dropna(inplace=True)
        return data[['time','atr']]
    def adx(self,timeframe,lookback):
        data = self.get_ohlc_data(timeframe)
        data['P_DI'] = talib.PLUS_DI(np.array(data['high']),np.array(data['low']),np.array(data['close']),timeperiod=lookback)
        data['M_DI'] = talib.MINUS_DI(np.array(data['high']), np.array(data['low']), np.array(data['close']),timeperiod=lookback)

        data['ADX'] = talib.ADX(np.array(data['high']), np.array(data['low']), np.array(data['close']), timeperiod=lookback)
        data['ADX'],data['P_DI'],data['M_DI']=data['ADX'].shift(1),data['P_DI'].shift(1),data['M_DI'].shift(1)
        data.dropna(inplace=True)
        return data[['time','P_DI','M_DI','ADX']]

    def generate_data(self,timeframe,indicators_dic):
        data=self.get_ohlc_data(timeframe)
        for indicator,arg in indicators_dic.items():
            data=pd.merge(data,self.__getattribute__(indicator)(**arg),how='left',on='time')
        data.reset_index(drop=True, inplace=True)
        data.time = pd.to_datetime(data.time)
        return data

def resolve(indics):
    val = []
    vals = [list(val.values()) for val in indics.values()]
    vals = [i for sublist in vals for i in sublist]

    combs = itertools.product(*vals)

    for comb in combs:
        tr, dicc = 0, {}
        for k, v in indics.items():
            dicc.update({k: dict(zip([e for e in v.keys()], [e for e in comb][tr:tr + len(v)]))})
            tr = tr + len(v)
        val.append(dicc)
    return val


# Base.metadata.drop_all(bind=engine)
# s.close()

warnings.filterwarnings('ignore')

mongo_host='localhost:27017'

plot_equity_curve = False
plot_chart = False
plot_entries = False
plot_indicators = []


granularity_map = {'hours': '1hour', 'days': '1day', 'minutes': '1min'}

######  params

pair = 'USDT'

start_date, end_date = '2021-01-01T0000', '2022-12-31T0000'

grid = {
    ##### point and figure variables ######

    'coin': [('darwinex', 'GBPJPY','spot','ask'),
             ('darwinex', 'AUDJPY','spot','ask'),
             ('darwinex', 'EURUSD','spot','ask'),
             ('darwinex', 'GBPCAD','spot','ask'),
             ('darwinex', 'USDMXN','spot','ask'),
             ('darwinex', 'XAUUSD','spot','ask'),
             ('darwinex', 'NFLX','spot','ask'),
             ('darwinex', 'TSLA','spot','ask'),
             ('darwinex', 'NVDA','spot','ask'),
             ],

    'timeframe':['1min'],

    'indicators': {'macd': {'timeframe': ['1hour'], 'fast_macd': list(map(int, np.arange(8, 16, 2))),
                            'slow_macd': list(map(int, np.arange(20, 31, 2))),
                            'signal_macd': list(map(int, np.arange(9, 10, 1)))},

                   'atr': {'timeframe': ['1hour'], 'lookback': [14]},

                   'adx': {'timeframe': ['1hour'], 'lookback': list(map(int, np.arange(10, 20, 4)))}

                   },

    'initial_balance': [float(1000)],

    ##### Entry rules ######

    'long_entry_conditions': [{'macd_crossover': {}}],

    'long_exit_conditions': [{'macd_crossdown': {}}],

    'short_entry_conditions': [{'macd_crossdown': {}}],

    'short_exit_conditions': [{'macd_crossover': {}}],

    ####### Exit rules #######

    ####### Filtration tools #########

    'trailing_stop': [{}],

    'filtration_tools': [{'adx':{'value':15}}],

    'position_sizing_model': [{'classic_position_sizing': {'risk_per_trade': 1 / 100}}],

    ######## Transaction cost #########

    'tick_slippage': [1],

    'trade_slippage_percentage': [1 / 100],

    ######## Return Calculation #########

    'return_calculation': ['compound'],

    ####### Orders type #######

    'sl_orders': ['market'],

    'free_rate': [2],

    'leverage': [5]
}

grid['indicators']=resolve(grid['indicators'])

def check_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        pass


possible_combinations = 1
for key in grid.keys():
    possible_combinations *= len(grid[
                                     key])

print(f'there are {possible_combinations} possible combination')




client = MongoClient(mongo_host)
db = client.get_database("market_data")

timeseries_db = db['exchange_rules']
combs_map={}
for c_id,comb in enumerate(itertools.product(*grid.values())):

    ###                   params

    dic_comb = dict(zip(grid.keys(), comb))
    combs_map.update({c_id:dict(zip(grid.keys(), [json.dumps(x) for x in comb]))})
    start_time = time.time()
    market_key = f"{dic_comb['coin'][0]}_{dic_comb['coin'][1]}"
    market_db = db[market_key]

    ## backtest dataframe



    argmts={
        'gte':pd.Timestamp(start_date).to_pydatetime(),
        'lt':pd.Timestamp(end_date).to_pydatetime(),
        'market_type':dic_comb['coin'][2],
        'price_type':dic_comb['coin'][3],
    }
    dg=data_generator(**argmts)
    backtest_data=dg.generate_data(dic_comb['timeframe'],dic_comb['indicators'])


    backtest_data['price']=backtest_data['close'].shift(1)
    backtest_data.to_csv('test.csv')
    # data_min=market_db.find({"timestamp":{"$gte":gte,"$lte":lt},"granularity":granularity_map[dic_comb['decider_timeframe']] ,'market_type':market_type})



    hours_data=dg.get_ohlc_data(dic_comb['indicators']['macd']['timeframe'])
    hours_data['macd'], hours_data['signal_macd'], hours_data['hist'] = talib.MACD(np.array(hours_data['close']),
                                                                                   fastperiod=
                                                                                   dic_comb['indicators']['macd'][
                                                                                       'fast_macd'],
                                                                                   slowperiod=
                                                                                   dic_comb['indicators']['macd'][
                                                                                       'slow_macd'], signalperiod=
                                                                                   dic_comb['indicators']['macd'][
                                                                                       'signal_macd'])
    hours_data['macd'], hours_data['signal_macd'] = hours_data['macd'].shift(1), hours_data['signal_macd'].shift(1)

    hours_data.dropna(inplace=True)

    settings = {

        'start_date': pd.Timestamp(start_date),

        'end_date': pd.Timestamp(end_date),

        'df_min': backtest_data,
        'df_hours':hours_data
    }

    settings.update(dic_comb)

    tick_size = timeseries_db.find({'ticker': settings['coin'][1]}, {'tick_size': 1})
    tick_size = float(tick_size[0]['tick_size'])

    makercommission = timeseries_db.find({'ticker': settings['coin'][1]}, {'maker_fee': 1, '_id': 0})
    makercommission = float(makercommission[0]['maker_fee'])

    takercommission = timeseries_db.find({'ticker': settings['coin'][1]}, {'taker_fee': 1, '_id': 0})
    takercommission = float(takercommission[0]['taker_fee'])

    margin_t = timeseries_db.find({'ticker': settings['coin'][1]}, {'margin_tiers': 1, '_id': 0})
    margin_t = margin_t[0]['margin_tiers']
    margin_map = {(d['position_bracket']['start'], d['position_bracket']['end']): {
        'maintenance_margin_rate': d['maintenance_margin_rate'], 'maintenance_amount': d['maintenance_amount']} for d in
                  margin_t}

    settings.update({'margin_map': margin_map, 'tick_size': tick_size, 'market_maker_fee': makercommission,
                     'market_taker_fee': takercommission})


    back1 = backtester(settings)
    back1.backtest_long_short()

    metrics = back1.make_metrics()


    res = pd.DataFrame.from_dict(metrics['results'], orient='index')
    return_p = pd.DataFrame.from_dict(metrics['return_profiles'], orient='index')
    risk_p = pd.DataFrame.from_dict(metrics['risk_profiles'], orient='index')
    expectancy_p = pd.DataFrame.from_dict(metrics['expectancy_profiles'], orient='index')
    consistency_p = pd.DataFrame.from_dict(metrics['consistency_profiles'], orient='index')
    logs = pd.DataFrame.from_dict(back1.logs, orient='index')

    for datafr, name in zip([res, return_p, risk_p, expectancy_p, consistency_p, logs],
                            ['res', 'return_p', 'risk_p', 'expectancy_p', 'consistency_p', 'logs']):
        check_directory('metrics')

        datafr.to_csv(f'metrics//{name}_{c_id}.csv')


    if plot_equity_curve:

        e_curve=back1.plot_equity_curve()
        check_directory('archived_charts')
        e_curve.save(f'archived_charts//equity_curve_{c_id}.html')


    if plot_chart:

        back1.plot_basic_chart()
        chart= back1.pnf_basic_chart
    if plot_entries:

        back1.plot_buy_long()
        chart=chart+back1.backtest_chart


    if bool(plot_indicators):
        charts=[getattr(back1,f'plot_{indic}')() for indic in plot_indicators ]
        chart=alt.vconcat(chart,*charts)

    try:
        check_directory('archived_charts')
        chart.save(f'archived_charts//backtest_chart_{c_id}.html')

    except NameError:
        pass




    exec_time = time.time() - start_time

    print(comb, f'executed in {exec_time}')




