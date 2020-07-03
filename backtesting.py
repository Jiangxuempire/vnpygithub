#!/usr/bin/env python
# coding: utf-8

# In[1]:


#%%
from importlib import reload
from datetime import datetime
from vnpy.app.cta_strategy.backtesting import BacktestingEngine

def run_backtesting(
    strategy_class, 
    setting=None,
    vt_symbol="XBTUSD.BITMEX", 
    interval="1m", 
    start=datetime(2017, 1, 1), 
    end=datetime(2021, 12, 31), 
    rate=2/10000, 
    slippage=0.5, 
    size=1, 
    pricetick=0.5, 
    capital=100,
    inverse=False
):
    engine = BacktestingEngine()
    
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital,
        inverse=inverse
    )

    if setting is None:
        setting = {}
    engine.add_strategy(strategy_class, setting)
    
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    engine.calculate_statistics()
    engine.show_chart()
    
    return df

def show_portfolio(df_list):
    portfolio_df = df_list[0]
    for df in df_list[1:]:
        portfolio_df += df
    
    engine = BacktestingEngine()
    engine.calculate_statistics(portfolio_df)
    engine.show_chart(portfolio_df)


# In[2]:


import super_turtle_strategy
reload(super_turtle_strategy)
df1 = run_backtesting(super_turtle_strategy.SuperTurtleStrategy, inverse=True)


# In[3]:


import trend_thrust_strategy
reload(trend_thrust_strategy)
df2 = run_backtesting(trend_thrust_strategy.TrendThrustStrategy)


# In[4]:


import rsi_momentum_strategy
reload(rsi_momentum_strategy)
df3 = run_backtesting(rsi_momentum_strategy.RsiMomentumStrategy)


# In[5]:


import keltner_bandit_strategy
reload(keltner_bandit_strategy)
df4 = run_backtesting(keltner_bandit_strategy.KeltnerBanditStrategy)


# In[6]:


import double_channel_strategy
reload(double_channel_strategy)
df5 = run_backtesting(double_channel_strategy.DoubleChannelStrategy)


# In[ ]:


df_list = [df1, df2, df3, df4, df5]
show_portfolio(df_list)


# In[ ]:





# In[ ]:




