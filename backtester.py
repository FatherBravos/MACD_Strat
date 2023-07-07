

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 13:21:59 2022

@author: Admin
"""
import datetime

import altair as alt
import math
import pandas as pd
import numpy as np
from image_transformer import image_transformer







#import time as ti
alt.data_transformers.enable('default')

class position():
    idd=0
    def __init__(self,time,entry_price,typee,spent,tp,sl):

        self.id=position.idd
        position.idd +=1 ##position.idd+1 if position.idd<2 else 0
        self.time=time
        self.close_time=None
        self.spent=spent
        self.entry_price=entry_price
        self.last_mark=entry_price
        self.type=typee
        self.bought_qte=spent/entry_price

        self.tp=tp
        self.sl=sl
        self.closing_price=None
        self.slippage=0
        self.commission=0
        self.atr=None
        self.maintenance_margin_rate=0
        self.maintainance_amount = 0
        self.initial_margin=0
        self.maintainance_margin = 0
        self.pnl=0
        self.entry_mark_price=None
    def update_pnl(self,update_price):
        if self.type=='long':
            self.pnl=self.bought_qte*(update_price-self.entry_mark_price)

        else:
            self.pnl = ((self.entry_mark_price-update_price)/self.entry_mark_price)*self.spent
        self.maintainance_margin = self.maintainance_margin_rate * self.bought_qte * update_price - self.maintainance_amount
        return
    def return_profit(self,exit_price):
        if self.type=='long':
            return self.bought_qte*(exit_price-self.entry_price)-self.slippage-self.commission
        elif self.type=='short':
            return ((self.entry_price-exit_price)/self.entry_price)*self.spent-self.slippage-self.commission
    def return_perc_profit(self,exit_price):
        if self.type=='long':
            return (exit_price-self.entry_price)/self.entry_price
        elif self.type=='short':
            return (self.entry_price-exit_price)/self.entry_price
    def get_duration(self):
        return (self.close_time-self.time).total_seconds()
    def actual_loss(self,actual_price):
        return min(self.return_profit(actual_price),0)



    def __str__(self):
        return 'p'+str(self.id)


class backtester():
    def __init__(self,settings):

        for key in settings:
            setattr(self,key,settings[key])

        self.balance=self.initial_balance
        self.r_balance=self.initial_balance

        self.resize = alt.selection_interval(bind='scales')
        self.pnf_basic_chart=None
        self.backtest_chart=None

        #self.metrics_data=pd.DataFrame(columns=(['total_net_profit','total_net_profit_perc','gross_profit','gross_profit_perc','gross_loss','gross_loss_perc','profit_factor','total_number_of_trades','percent_profitable','winning_trades','losing_trades','average_winning_trade','average_winning_trade_perc','average_losing_trade','average_losing_trade_perc','risk_reward_ratio','expectancy','average_return','average_return_perc','largest_win','largest_win_perc','largest_loss','largest_loss_perc','max_consecutive_win','max_consecutive_win_perc','max_consecutive_losses','max_consecutive_losses_perc','Max_Drawdown']))
        self.backtest_data={}#pd.DataFrame(columns=['position','time','close','action','spent','balance','profit','profit_perc','col_id','plot_lvl'])
        self.image_transformer=image_transformer()

        self.positions={'long':[],'short':[]}
        self.relations_mapping={'and': lambda x,y:x and y,'or':lambda x,y:x or y}




        self.market_close=(self.df_min['time']).dt.time.max()



        self.orders_map={'long_tp_market':'price_last','long_sl_market':'price_last','long_tp_limit':'high_last','long_sl_limit':'low_last','short_tp_market':'price_last','short_sl_market':'price_last','short_tp_limit':'low_last','short_sl_limit':'high_last'}
        self.fee_map={'limit':self.market_taker_fee,'market':self.market_taker_fee}
        self.slippage_map={'limit':lambda x,y:0,'market':self.price_slippage}
        self.logs={}
        self.index,self.hour_index=0,0

    def price_slippage(self, pos):
        return self.tick_size * pos.bought_qte * self.tick_slippage

    def trade_slippage(self):
        positions = set([value['position'] for value in self.backtest_data.values()])
        positions_to_drop = random.choices(list(positions), k=int(len(positions) * self.trade_slippage_percentage))
        self.backtest_data = {key: value for key, value in self.backtest_data.items() if
                                  value['position'] not in positions_to_drop}
    def reset(self):
        self.balance=self.initial_balance
        self.r_balance=self.initial_balance
        self.buy_lvl=100000
        self.buy_short_lvl=0
        self.pnf_basic_chart=None
        self.backtest_chart=None


        self.backtest_data={}
        self.positions={'long':[],'short':[]}
        self.logs={}
        self.direction='all'

    def trailing_volatility_stop(self,index,position, price, initial_value):



        if position.sl in [0, 100000]:

            indicator_value = self.df_min['atr'][index]
            position.sl = \
            {0: lambda x: x - initial_value * indicator_value, 100000: lambda x: x + initial_value * indicator_value}[
                position.sl](position.entry_price)

        elif position.type == 'long' and price > position.last_mark:

            position.sl += (price - position.last_mark)
            position.last_mark = price
            # if self.bkt.return_calculation == 'compound':
            # print(f'{time} update{position.__str__()},price:{high},sl:{position.sl},mark:{position.last_mark},atr:{indicator_value}')

        elif position.type == 'short' and price < position.last_mark:
            position.sl -= (position.last_mark - price)
            position.last_mark = price

    def classic_position_sizing(self, index,entry_price, sl, position_type, risk_per_trade):

        investing_balance = self.r_balance * self.leverage
        if position_type == 'long' and sl != 0:
            return investing_balance * risk_per_trade * entry_price / abs(sl - entry_price)

        elif position_type == 'long' and sl == 0:
            atr=self.df_min['atr'][index]
            return investing_balance * risk_per_trade * entry_price / abs(atr*2)

        if position_type == 'short' and sl != 100000:
            return investing_balance * risk_per_trade * entry_price / abs(sl - entry_price)

        elif position_type == 'short' and sl == 100000:
            atr=self.df_min['atr'][index]
            return investing_balance * risk_per_trade * entry_price / abs(atr)

    def find_margin_info(self,position_size):

        try:
            return [value for key,value in self.margin_map.items() if key[0]<position_size<=key[1]][0]
        except Exception:
            return {'a':0,'b':0}

    def open_position(self,index,entry_price,time,position_type,mark_price):
        #try:

            sl=0 if position_type=='long' else 100000

            p = position(time, entry_price, position_type, 0, None, sl)
            try:
                method_name,method_args=next(iter(self.trailing_stop.items()))
                self.__getattribute__(method_name)(index=index,position=p,price=entry_price,**method_args)
                sl=p.sl
            except StopIteration:
                pass

            key=list(self.position_sizing_model.keys())[0]
            position_size=self.__getattribute__(key)(index=index,sl=sl,entry_price=entry_price,position_type=position_type,**self.position_sizing_model[key])
            amount_to_spend=min(self.balance*self.leverage,position_size) if self.return_calculation=='compound' else self.balance*self.leverage

            if amount_to_spend>0:
                p.spent=amount_to_spend
                p.atr=None
                p.entry_mark_price=mark_price
                p.bought_qte=p.spent/p.entry_price
                p.slippage,p.commission=self.slippage_map['market'](p),self.fee_map['market']*p.spent
                p.maintainance_margin_rate,p.maintainance_amount=self.find_margin_info(p.spent).values()
                p.initial_margin,p.maintainance_margin,p.pnl=(p.bought_qte*mark_price) / self.leverage , p.maintainance_margin_rate*p.bought_qte*mark_price-p.maintainance_amount , -p.slippage-p.commission
                self.positions[position_type].append(p)#
                #print(f'{time} make {p.__str__()},atr:{p.atr}')


                self.balance =self.balance-amount_to_spend if self.return_calculation=='compound' else 0
                #self.last_buying_col=col

                self.backtest_data.update({len(self.backtest_data):dict(zip(['position','time','price','action','spent','balance','profit','profit_perc'],[p.__str__(),time,entry_price,f'buy_{position_type}',amount_to_spend,self.r_balance,0,0]))})
            else:
                del p
                position.idd-=1
        #except Exception as e:
            #print('exception in open pos',e)



    def close_position(self,closing_price,time,pos,status='closed'):

        pos.close_time=time
        profit=pos.return_profit(closing_price)
        perc_profit=(profit/pos.spent)*100


        self.balance = self.balance+profit+pos.spent if self.return_calculation=='compound' else self.initial_balance

        self.r_balance+=profit
        self.backtest_data.update({len(self.backtest_data):dict(zip(['position','time','price','action','spent','balance','profit','profit_perc','duration','slippage','commission'],[pos.__str__(),time,closing_price,f'sell_{pos.type}',pos.spent,self.r_balance,profit,perc_profit,pos.get_duration(),pos.slippage,pos.commission]))})
        mask = (self.df_min['time'] >=pos.time) & (self.df_min['time'] <= pos.close_time)

        p_runup=(self.df_min.loc[mask])['price'].min() if pos.type=='short' else (self.df_min.loc[mask])['price'].max()
        p_drawdown=(self.df_min.loc[mask])['price'].max() if pos.type=='short' else (self.df_min.loc[mask])['price'].min()
        if pos.closing_price is None:
            pos.closing_price=closing_price
        self.logs.update({len(self.logs):dict(zip(['direction','entry_date','entry_time','entry_price','exit_date','exit_time','exit_price','position_size','status','profit_loss','profit_loss_percent','running_profit_loss','sl_price','drawdown','runup','slippage','commission'],[pos.type,pos.time.date(),pos.time.time(),pos.entry_price,pos.close_time.date(),pos.close_time.time(),pos.closing_price,pos.spent,status,profit,perc_profit,self.r_balance,pos.sl,p_drawdown,p_runup,pos.slippage,pos.commission]))})
        self.positions[pos.type].remove(pos)
        return

    def check_to_liquidate(self,price,time):
        updated_pnl=[pos.update_pnl(price) for pos in self.positions['short']+self.positions['long']]
        positions_to_liquidate=[self.close_position(price,time,pos,status='liquidated') for pos in self.positions['short']+self.positions['long'] if pos.initial_margin+pos.pnl<=pos.maintainance_margin]



    def macd_crossover(self,index):
        try:

            return self.df_min['macd'][index]>self.df_min['signal_macd'][index] and self.df_min['macd'][index-60]<=self.df_min['signal_macd'][index-60]
        except IndexError as e:

            return False
    def macd_crossdown(self,index):
        try:
            return self.df_min['macd'][index]<self.df_min['signal_macd'][index] and self.df_min['macd'][index-60]>=self.df_min['signal_macd'][index-60]
        except KeyError:
            return False


    def check_to_close_position(self,price,index,position_type):


        positions_to_sl=[pos for pos in self.positions[position_type] if (position_type=='long' and price<=pos.sl) or (position_type=='short' and price>=pos.sl)]
        positions_to_close_by_conditions=[pos for pos in self.positions[position_type] if (self.check_entry_exit_condition(index,'exit',position_type) and pos not in positions_to_sl)]
        for pos in positions_to_sl:
            pos.closing_price=pos.sl if self.sl_orders=='limit' else price

            pos.slippage+=self.slippage_map[self.sl_orders](pos)
            pos.commission+=self.fee_map[self.sl_orders]*pos.spent
        for pos in positions_to_close_by_conditions:
            pos.closing_price=price

            pos.slippage+=self.slippage_map['market'](pos)
            pos.commission+=self.fee_map['market']*pos.spent
        return positions_to_sl+positions_to_close_by_conditions

    def check_filtration_tools(self,index,pos_type):

        if bool(self.filtration_tools):
            try:
                v=self.filtration_tools['adx']['value']
                adx,p_di,m_di=self.df_min['ADX'][index],self.df_min['P_DI'][index],self.df_min['M_DI'][index]
                decision= adx>v and p_di>m_di if pos_type=='long' else adx>v and p_di<m_di
                return decision
            except Exception as e:
                print(e)
                return False
        else:
            return True



    def check_entry_exit_condition(self,index,action,position_type):
        try:
            conditions=self.__getattribute__(f'{position_type}_{action}_conditions')

            method_name, method_args = next(iter(conditions.items()))
            return self.__getattribute__(method_name)(index=index,**method_args)
        except StopIteration as e:
            print(e)
            return False


    def update_positions_by_trailing(self,index,price):

        for key in self.trailing_stop:

            for pos in self.positions['long']+self.positions['short']:
                self.__getattribute__(key)(index=index,position=pos,price=price,**self.trailing_stop[key])

    def decide(self,index,price,time):

        self.check_to_liquidate(price,time)
        self.update_positions_by_trailing(index,price)

        long_pos_to_close=self.check_to_close_position(price,index,'long')
        short_pos_to_close = self.check_to_close_position(price, index, 'short')

        if bool(long_pos_to_close) :#and self.check_exit_filtration_tools('long_exit') :
           for position in long_pos_to_close:
               self.close_position(position.closing_price,time,position)

        if bool(short_pos_to_close) :#and self.check_exit_filtration_tools('short_exit') :
           for position in short_pos_to_close:
               self.close_position(position.closing_price,time,position)

        if self.check_entry_exit_condition(index,'entry','long') and self.check_filtration_tools(index,'long'): #and self.check_entry_filtration_tools('long_entry') :

           self.open_position(index,price,time,'long',price)

        if self.check_entry_exit_condition(index,'entry','short') and self.check_filtration_tools(index,'short') :# and self.check_entry_filtration_tools('short_entry'):

            self.open_position(index,price,time,'short',price)


    def backtest_long_short(self):

        end=len(self.df_min)-1
        #dicc={'daily':lambda x:x.hour==0 and x.minute==0,'hourly':lambda x:x.minute==0,'minute':lambda x :True}

        for row in self.df_min.itertuples():

            index,time,price=row.Index,row.time,row.price
            self.decide(index,price,time)

        for position in self.positions['long']+self.positions['short']:

            self.close_position(self.df_min['price'][end],self.df_min['time'][end],position)


    def low_point(self,df,idx):
        if df['Daily_Drawdown'][idx]<0:
            return df['balance'][idx]
        elif df['Daily_Drawdown'][idx]==0:
            return 1
    def runup(self,df,idx):
        if idx ==0:
            return 0
        else:
            return max(0,df['balance'][idx]-df['LP'][idx-1])


    def make_metrics(self):

        df=pd.DataFrame.from_dict(self.backtest_data,orient='index')
        df=df[df['action'].str.contains('sell')]


        df.reset_index(drop=True, inplace=True)


        df['rollmax'] = df['balance'].rolling(len(df), min_periods=1).max()

        df['Daily_Drawdown'] = df['balance']/df['rollmax'] - 1.0
        Daily_Drawdown_dollars=df['balance']-df['rollmax']
        df['Daily_Drawdown_dollars']=Daily_Drawdown_dollars
        Max_Daily_Drawdown = df['Daily_Drawdown'].min()
        index_of_mdd=df['Daily_Drawdown'].idxmin()
        date_of_mdd=df['time'][index_of_mdd]####
        Max_Drawdown=(Max_Daily_Drawdown)*100
        MDD=Daily_Drawdown_dollars.min()





        df.reset_index(drop=True, inplace=True)
        df['index']=df.index

        df['LP']=df['index'].apply(lambda x:self.low_point(df,x))
        df['LP'][0]=df['balance'][0]
        for i in range(1,len(df)):
            if df['LP'][i]==1:
                df['LP'][i]=df['LP'][i-1]
        df['equity_runup']=df['index'].apply(lambda x:self.runup(df,x))

        gross_profit=df.loc[df['profit']>0,'profit'].sum()




        gross_loss=abs(df.loc[df['profit']<0,'profit'].sum())



        total_net_profit=gross_profit-gross_loss
        recovery_factor=abs(total_net_profit/MDD)####
        return_on_initial_capital=100*(total_net_profit/self.initial_balance)#####

        buyandhold_return=100*(self.df_min['close'][len(self.df_min)-1]/self.df_min['close'][0]-1)####



        df2=df.groupby([df['time'].dt.strftime('%m-%y')],as_index=False).agg(total_profit_perc = ('profit_perc' , 'sum'),total_profit = ('profit' , 'sum'),first_balance=('balance' , 'first'),first_profit=('profit' , 'first'),VAMI=('balance' , 'last'))

        df2['first_balance']=df2['first_balance']-df2['first_profit']
        df2['monthly_return']=(df2['total_profit']/df2['first_balance']) * 100
        df2['c_m_r'] = df2['monthly_return'] + 100
        avg_monthly_return = ((df2['c_m_r'].prod()) ** (1 / len(df2)) - 100)
        # avg_monthly_return=df2['monthly_return'].mean()
        sharpe_ratio=(avg_monthly_return-self.free_rate/12)/df2['monthly_return'].std()

        #avg_monthly_return=df2['monthly_return'].mean()


        percent_of_time_in_market=100*(df['duration'].sum()/(self.df_min['time'][len(self.df_min)-1]-self.df_min['time'][0]).total_seconds())

        max_position_held=df['spent'].max()
        total_commission=df['commission'].sum()
        total_slippage=df['slippage'].sum()

        winning_trades=df.loc[df['profit']>0,'profit'].count()
        average_winning_trade=df.loc[df['profit']>0,'profit'].mean()
        losing_trades=df.loc[df['profit']<0,'profit'].count()
        average_losing_trade=df.loc[df['profit']<0,'profit'].mean()

        adjusted_gross_profit=(winning_trades-math.sqrt(winning_trades))*average_winning_trade

        adjusted_gross_loss=abs((losing_trades-math.sqrt(losing_trades))*average_losing_trade)
        adjusted_net_profit=adjusted_gross_profit-adjusted_gross_loss


        profit_factor=gross_profit/gross_loss
        adjusted_profit_factor=adjusted_gross_profit/adjusted_gross_loss


        index_of_runup=df['equity_runup'].idxmax()

        date_of_max_runup=df['time'][index_of_runup]####

        max_equity_runup_percent=float((100*df['equity_runup']/df['LP']).max())
        max_equity_runup_dollars=float(df['equity_runup'].max())###
        years=((self.df_min['time'][len(self.df_min)-1]-self.df_min['time'][0]).days/365)+1
        compounded_annual_return=(df['balance'][len(df)-1]/self.initial_balance)**(1/years)-1

        cagr_over_max_dd=abs(compounded_annual_return/Max_Drawdown)

        largest_win=df.loc[df['profit']>0,'profit'].max()
        largest_win_perc=df.loc[df['profit_perc']>0,'profit_perc'].max()

        total_number_of_trades=df.loc[df['profit']!=0,'profit'].count()



        lose_rate=100*losing_trades/total_number_of_trades
        win_rate=100*winning_trades/total_number_of_trades
        #percent_profitable=100*winning_trades/total_number_of_trades




        average_profit_dollars=df.loc[df['profit']!=0,'profit'].mean()
        average_profit_percent=df.loc[df['profit']!=0,'profit_perc'].mean()

        average_winning_trade_perc=df.loc[df['profit_perc']>0,'profit_perc'].mean()

        average_losing_trade_perc=df.loc[df['profit_perc']<0,'profit_perc'].mean()

        risk_reward_ratio=abs(total_net_profit/MDD)

        expectancy=((average_winning_trade*win_rate/100)+(average_losing_trade)*lose_rate/100)/(-average_losing_trade)

        #average_return=df.loc[df['profit']!=0,'profit'].mean()

        average_return_perc=df.loc[df['profit_perc']!=0,'profit_perc'].mean()





        largest_loss=df.loc[df['profit']<0,'profit'].min()

        largest_loss_perc=df.loc[df['profit_perc']<0,'profit_perc'].min()


        first,first_perc=df['profit'][0],df['profit_perc'][0]
        cnt=1
        cnt2=-1
        cnt_list=[]
        #lis=[]
        lis_perc=[]
        for i in range(1,len(df)):
            if (first>0 and df['profit'][i]>0) or (first<0 and df['profit'][i]<0):
                first=first+df['profit'][i]
                if df['profit'][i]>0:
                    cnt+=1
                else :
                    cnt2-=1
                first_perc=first_perc+df['profit_perc'][i]
            elif (first<0 and df['profit'][i]>0) or (first>0 and df['profit'][i]<0):
                #lis.append(first)
                lis_perc.append(first_perc)
                first=df['profit'][i]
                first_perc=df['profit_perc'][i]
                cnt_list.append(cnt)
                cnt_list.append(cnt2)
                cnt=1
                cnt2=-1

        cnt_list.append(cnt)
        cnt_list.append(cnt2)
        lis_perc.append(first_perc)

        max_consecutive_win=max(cnt_list)
        max_consecutive_win_perc=max(lis_perc)

        max_consecutive_losses=abs(min(cnt_list))
        max_consecutive_losses_perc=min(lis_perc)

        variance_returns=df.loc[df['profit_perc']!=0,'profit_perc'].var()#sum([((x-average_return_perc)**2)/(total_number_of_trades-1) for x in df['profit_perc'] if x!=0])
        std_returns=math.sqrt(variance_returns)

        monthly_variance_returns=df2.loc[df2['monthly_return']!=0,'monthly_return'].var()#sum([((x-avg_monthly_return)**2)/(len(df2)-1) for x in df2['monthly_return']])

        std_monthly_returns=math.sqrt(monthly_variance_returns)
        std_monthly_returns=std_monthly_returns

        df_drawdown=df.groupby(df['rollmax'],as_index=False).agg(drawdown = ('Daily_Drawdown' , 'min'))
        df_drawdown['drawdown']=100*df_drawdown['drawdown']
        df_drawdown=df_drawdown[df_drawdown['drawdown']!=0]

        average_DD=df.loc[df['Daily_Drawdown']!=0,'Daily_Drawdown'].mean()


        average_DD_dollars=df.loc[df['Daily_Drawdown_dollars']!=0,'Daily_Drawdown_dollars'].mean()
        cagr_over_avg_dd=abs(compounded_annual_return/average_DD)
        min_drawdown=df.loc[df['Daily_Drawdown']!=0,'Daily_Drawdown'].max()

        min_drawdown_dollars=df.loc[df['Daily_Drawdown_dollars']!=0,'Daily_Drawdown_dollars'].max()


        variance_drawdown=df.loc[df['Daily_Drawdown']!=0,'Daily_Drawdown'].var()#sum([((x-average_DD)**2)/(len(df)-1) for x in list(df['Daily_Drawdown'])])

        std_drawdown=math.sqrt(variance_drawdown)

        df_equity=df[df['profit']!=0]
        df_equity.reset_index(inplace=True)
        df_equity['trades']=df_equity.index+1
        df_equity=df_equity[['trades','balance']]

        new_row = pd.DataFrame({'trades':0, 'balance':1000}, index=[0])

        df_equity = pd.concat([new_row,df_equity.loc[:]]).reset_index(drop=True)

        tetha=np.polyfit(df_equity['trades'],df_equity['balance'],1)
        df_equity['y_line']=tetha[1]+tetha[0]*df_equity['trades']

        correlation_coefficient_equity_curve=df_equity['balance'].corr(df_equity['y_line'])

        coefficient_of_determination=correlation_coefficient_equity_curve**2

        df2.reset_index(inplace=True)
        df2['months']=df2.index

        df2['VAMI']=df2['VAMI'].apply(lambda x:math.log(abs(x)))
        try:
            reg_line,V=np.polyfit(df2['months'],df2['VAMI'],1,cov=True)
            std_error=np.sqrt(V[0][0])
            k_ratio=reg_line[0]/std_error
        except ValueError:
            k_ratio=float(1)


        metrics={'results':{'return_on_initial_capital':return_on_initial_capital,'buyandhold_return':buyandhold_return,'max_drawdown_percent':Max_Drawdown,'recovery_factor':recovery_factor,'sharpe_ratio':sharpe_ratio,'percent_of_time_in_market':percent_of_time_in_market,'max_position_held':max_position_held,'total_commission':total_commission,'total_slippage':total_slippage,'date_of_mdd':date_of_mdd},
                 'return_profiles':{'net_profit':total_net_profit,'adjusted_net_profit':adjusted_net_profit,'compounded_annual_return':compounded_annual_return,'avg_monthly_return':avg_monthly_return,'gross_profit':gross_profit,'adjusted_gross_profit':adjusted_gross_profit,'gross_loss':gross_loss,'adjusted_gross_loss':adjusted_gross_loss,'profit_factor':profit_factor,'adjusted_profit_factor':adjusted_profit_factor,'max_equity_runup_dollars':max_equity_runup_dollars,'max_equity_runup_percent':max_equity_runup_percent,'date_of_max_runup':date_of_max_runup,'max_con_winning_trades_percent':max_consecutive_win_perc,'max_con_winning_trades':max_consecutive_win,'largest_win_dollars':largest_win,'largest_win_percent':largest_win_perc},
                 'risk_profiles':{'risk_reward_ratio':risk_reward_ratio,'cagr_over_avg_dd':cagr_over_avg_dd,'cagr_over_max_dd':cagr_over_max_dd,'max_drawdown_dollars':MDD,'max_drawdown_percent':Max_Drawdown,'avg_drawdown_dollars':average_DD_dollars,'avg_drawdown_percent':average_DD,'min_drawdown_dollars':min_drawdown_dollars,'min_drawdown_percent':min_drawdown,'max_con_losing_trades':max_consecutive_losses,'max_con_losing_trades_percent':max_consecutive_losses_perc,'largest_single_loss_dollars':largest_loss,'largest_single_loss_percent':largest_loss_perc,'max_position_held':max_position_held},
                 'expectancy_profiles':{'number_of_trades':int(total_number_of_trades),'expectancy':expectancy,'win_rate':win_rate,'lose_rate':lose_rate,'average_profit_dollars':average_profit_dollars,'average_profit_percent':average_profit_percent,'average_winning_dollars':average_winning_trade,'average_winning_percent':average_winning_trade_perc,'average_losing_dollars':average_losing_trade,'average_losing_percent':average_losing_trade_perc},
                 'consistency_profiles':{'k_ratio':k_ratio,'variance_returns':variance_returns,'std_returns':std_returns,'std_monthly_returns':std_monthly_returns,'variance_drawdown':variance_drawdown,'std_drawdown':std_drawdown,'correlation_coefficient_equity_curve':correlation_coefficient_equity_curve,'coefficient_of_determination':coefficient_of_determination,'sharpe_ratio':sharpe_ratio}
                 }



        #row=[total_net_profit,total_net_profit_perc,gross_profit,gross_profit_perc,gross_loss,gross_loss_perc,profit_factor,total_number_of_trades,percent_profitable,winning_trades,losing_trades,average_winning_trade,average_winning_trade_perc,average_losing_trade,average_losing_trade_perc,risk_reward_ratio,expectancy,average_return,average_return_perc,largest_win,largest_win_perc,largest_loss,largest_loss_perc,max_consecutive_win,max_consecutive_win_perc,max_consecutive_losses,max_consecutive_losses_perc,Max_Drawdown]
        #self.metrics_data.loc[len(self.metrics_data)] =row
        return metrics



    def plot_buy_long(self):

        image_dict=self.image_transformer.transform_img(['buy_long.png','sell_long.png','buy_short.png','sell_short.png'])
        # mx=int(self.cols_data['ADX'].max())


        plot_dataframe=pd.DataFrame.from_dict(self.backtest_data,orient='index')



        plot_dataframe['plot_image']=plot_dataframe['action']+'.png'

        plot_dataframe['plot_image']=plot_dataframe['plot_image'].map(image_dict)


        chart=alt.Chart(plot_dataframe).mark_image(width=30,height=10).encode(

        alt.X('time'),
        alt.Y('price'),

        url='plot_image',
        tooltip=['time','price','spent','balance','profit','profit_perc','position'],

        ).properties(
            width=1500,
            height=600
        )


        self.backtest_chart=chart

    def plot_basic_chart(self) :

       source = self.df_hours.copy()
       source['plot_time']=source['time'].astype(str)

       open_close_color = alt.condition(
           "datum.open <= datum.close",
           alt.value("#06982d"),
           alt.value("#ae1325")
       )

       base = alt.Chart(source).encode(
           alt.X('time:T')
           .axis(format='%m/%d/%H:%m', labelAngle=-45)
           .title('time'),
           color=open_close_color
       )

       rule = base.mark_rule().encode(
           alt.Y('low:Q')
           .title('Price')
           .scale(zero=False),
           alt.Y2('high:Q')
       ).properties(
            width=1500,
            height=600)

       bar = base.mark_bar().encode(
           alt.Y('open:Q'),
           alt.Y2('close:Q'),
           tooltip = ['plot_time', 'open','high','low','close','macd','signal_macd']
       ).properties(
            width=1500,
            height=600
        ).add_selection(self.resize)

       chart=rule + bar
       self.pnf_basic_chart=chart

    def plot_macd(self):
       dataframe=self.df_min[['time','macd','signal_macd']]
       dataframe.dropna(inplace=True)

       #image_dic=self.image_transformer.transform_img(['x.jpg','o.jpg'])
       #dataframe['plot_image']=dataframe['sign']+'.jpg'
       #dataframe['plot_image']=dataframe['plot_image'].map(image_dic)

       end=max(dataframe['macd'].max(),dataframe['signal_macd'].max())
       start=min(dataframe['macd'].min(),dataframe['signal_macd'].min())

       chart=alt.Chart(dataframe).mark_line().encode(

       alt.X('time'),
       alt.Y('macd',scale=alt.Scale(domain=[-5, 5])).title('MACD'),

       #url='plot_image',
       tooltip=['time',"macd","signal_macd"],
       color=alt.value('#2387A0'),
        ).properties(
            width=1500,
            height=200
        ).add_selection(self.resize)

       chart2=alt.Chart(dataframe).mark_line().encode(

       alt.X('time'),
       alt.Y('signal_macd'),

       #url='plot_image',
       tooltip=['time','macd',"signal_macd"],
       color=alt.value('#FE4A49'),
        ).properties(
            width=1500,
            height=200
        ).add_selection(self.resize)



       return chart+chart2

    def plot_adx(self):
       dataframe=self.df_min[['time','adx','p_di','m_di']]
       dataframe.dropna(inplace=True)

       #image_dic=self.image_transformer.transform_img(['x.jpg','o.jpg'])
       #dataframe['plot_image']=dataframe['sign']+'.jpg'
       #dataframe['plot_image']=dataframe['plot_image'].map(image_dic)


       chart=alt.Chart(dataframe).mark_line().encode(

       alt.X('time'),
       alt.Y('adx').title('ADX'),

       #url='plot_image',
       tooltip=['time',"adx","p_di","m_di"],
       color=alt.value('#2a0f3f'),
        ).properties(
            width=1500,
            height=200
        ).add_selection(self.resize)

       chart2=alt.Chart(dataframe).mark_line().encode(

       alt.X('time'),
       alt.Y('p_di'),

       #url='plot_image',
       tooltip=['time',"adx","p_di","m_di"],
       color=alt.value('#10dc40'),
        ).properties(
            width=1500,
            height=200
        ).add_selection(self.resize)

       chart3 = alt.Chart(dataframe).mark_line().encode(

           alt.X('time'),
           alt.Y('m_di'),

           # url='plot_image',
           tooltip=['time', "adx","p_di","m_di"],
           color=alt.value('#f70084'),
       ).properties(
           width=1500,
           height=200
       ).add_selection(self.resize)



       return chart+chart2+chart3

    def plot_atr(self):
       dataframe=self.df_min[['time','atr']]
       dataframe.dropna(inplace=True)

       #image_dic=self.image_transformer.transform_img(['x.jpg','o.jpg'])
       #dataframe['plot_image']=dataframe['sign']+'.jpg'
       #dataframe['plot_image']=dataframe['plot_image'].map(image_dic)


       chart=alt.Chart(dataframe).mark_line().encode(

       alt.X('time'),
       alt.Y('atr').title('ATR'),

       #url='plot_image',
       tooltip=['time',"atr"],
       color=alt.value('#000033'),
        ).properties(
            width=1500,
            height=200
        ).add_selection(self.resize)





       return chart

    def plot_equity_curve(self):
        plot_dataframe = pd.DataFrame.from_dict(self.backtest_data, orient='index')[['action', 'balance']]
        plot_dataframe = plot_dataframe[plot_dataframe['action'].str.contains('sell')]
        plot_dataframe['trade'] = plot_dataframe.index
        equity_chart = alt.Chart(plot_dataframe).mark_line().encode(

            alt.X('trade'),
            alt.Y('balance'),

            tooltip=['balance'],

        ).properties(
            width=600,
            height=600
        ).interactive()

        return equity_chart













