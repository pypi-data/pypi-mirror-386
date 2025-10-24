# -*- coding: utf-8 -*-
"""
本模块功能：演示量化投资案例
所属工具包：证券投资分析工具SIAT 
SIAT：Security Investment Analysis Tool
创建日期：2025年8月27日
最新修订日期：2025年8月28日
作者：王德宏 (WANG Dehong, Peter)
作者单位：北京外国语大学国际商学院
作者邮件：wdehong2000@163.com
版权所有：王德宏
用途限制：仅限研究与教学使用，不可商用！商用需要额外授权。
特别声明：作者不对使用本工具进行证券投资导致的任何损益负责！
"""

#==============================================================================
#关闭所有警告
import warnings; warnings.filterwarnings('ignore')
from siat.common import *
from siat.translate import *
from siat.security_trend2 import *
from siat.grafix import *

#==============================================================================
import pandas as pd
import numpy as np
#==============================================================================

#==============================================================================

def add_slippage(price, slippage=0.001):
    """
    模拟滑点，返回加入滑点后的价格，通用。
    参数:
    - price: 当前价格
    - slippage: 滑点的幅度，默认为0.1%（即0.001）
    
    返回：
    - 加入滑点后的价格
    """
    seed = 42
    np.random.seed(seed)
    
    slippage_factor = 1 + slippage * np.random.randn()  # 使用正态分布模拟滑点
    return price * slippage_factor

#==============================================================================

def calculate_transaction_fee(price, position, fee_rate=0.0005):
    """
    计算交易费用：含手续费、佣金、过户费和印花税，通用。
    参数:
    - price: 当前价格
    - position: 当前持仓量
    - fee_rate: 交易费率（默认为0.05%）
    
    返回：
    - 交易费用
    """
    return abs(position * price) * fee_rate  # 计算买入或卖出所需的交易费用

#==============================================================================
# 高低点策略
# 注意：本策略中的price_type可以使用Close、Adj Close或Open
#==============================================================================
if __name__=='__main__':
    ticker="600519.SS"
    
    # 样本期间
    fromdate="2010-1-1"
    todate="2025-6-30"
    
    prices,found=get_price_1ticker(ticker,fromdate,todate)
    
    signals=strategy_highlow(prices, window=252, price_type="Close")
    print(signals[signals != 0])
    signals.loc["2010-03-01":"2010-03-10"]
    signals.loc["2010-3-1":"2010-3-10"]

def strategy_highlow(prices, window=252, \
                     
                     strategy_name="", \
                     stop_loss=0.1, take_profit=0.2,mdd_limit=0, 
                     initial_balance=1000000, slippage=0.001, fee_rate=0.0005, \
                     min_shares=100, \
                     price_type="Close"):
    """
    专用策略名称：高低点策略，对于每个交易日产生三种信号：不操作0，买入1，卖出-1
    观察窗口期：window
    策略函数：当股价不高于最近窗口期最低点时买入，不低于最近窗口期最高点时卖出
    参数:
    - prices: 收盘价数据，pandas DataFrame
    - window: 计算窗口期的滑动窗口，默认为252个交易日（52周）
    - price_type: 可用收盘价Close、调整收盘价Adj Close或开盘价Open
    
    返回:
    - signals: 序列，买入卖出信号的Series，1为买入，-1为卖出，0为不操作
    """
    # 计算窗口期的最高价和最低价
    prices['window_high'] = prices[price_type].rolling(window=window).max()
    prices['window_low'] = prices[price_type].rolling(window=window).min()
    
    # 初始化信号列
    signals = np.zeros(len(prices))
    
    # 买入信号：收盘价低于最近窗口期最低价
    signals[prices[price_type] <= prices['window_low']] = 1  # 买入信号
    
    # 卖出信号：收盘价高于最近窗口期最高价
    signals[prices[price_type] >= prices['window_high']] = -1  # 卖出信号
    
    return pd.Series(signals, index=prices.index)

#==============================================================================
# 金叉死叉策略
# 注意：本策略中的price_type可以使用Close、Open和Adj Close，但需要对KDJ进行处理
#==============================================================================

# 计算MACD
def calculate_macd(prices, short_window=12, long_window=26, signal_window=9, \
                   price_type="Close"):
    short_ema = prices[price_type].ewm(span=short_window, adjust=False).mean()
    long_ema = prices[price_type].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

# 计算RSI
def calculate_rsi(prices, window=14, price_type="Close"):
    delta = prices[price_type].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 计算KDJ：有分红时需要特别处理
def calculate_adj_high_low(prices):
    """
    核心逻辑是：
    同一时间点的复权比例对所有价格（开盘价、最高价、最低价、收盘价）是相同的，
    因此可以通过 Adj Close 与 Close 的比值得到复权系数，
    再应用到 High 和 Low 上
    """
    """
    计算前复权最高价(Adj High)和前复权最低价(Adj Low)
    
    参数:
        prices: pandas DataFrame，需包含以下列：
            - Close: 原始收盘价
            - Adj Close: 前复权收盘价
            - High: 原始最高价
            - Low: 原始最低价
    
    返回:
        新增 Adj High 和 Adj Low 列的 DataFrame
    """
    # 复制原始数据避免修改源数据
    df = prices.copy()
    
    # 计算复权系数：前复权收盘价 / 原始收盘价
    # 处理除数为0的情况（极少数极端情况）
    df['adj_factor'] = df['Adj Close'] / df['Close'].replace(0, pd.NA)
    
    # 计算前复权最高价和最低价
    df['Adj High'] = df['High'] * df['adj_factor']
    df['Adj Low'] = df['Low'] * df['adj_factor']
    
    # 移除临时计算的复权系数列（可选）
    df = df.drop(columns=['adj_factor'])
    
    return df 
   

def calculate_kdj(prices, window=14, price_type="Close"):
    
    # 不使用调整收盘价
    if not ("Adj" in price_type):
        low_min = prices['Low'].rolling(window=window).min()
        high_max = prices['High'].rolling(window=window).max()
        rsv = (prices[price_type] - low_min) / (high_max - low_min) * 100
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
    
    # 使用调整收盘：考虑红利再投资
    else:
        prices=calculate_adj_high_low(prices)
        low_min = prices['Adj Low'].rolling(window=window).min()
        high_max = prices['Adj High'].rolling(window=window).max()
        rsv = (prices[price_type] - low_min) / (high_max - low_min) * 100
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
        
            
    return k, d, j


def strategy_cross(prices, MACD=True, RSI=True, KDJ=True):
    # 金叉死叉策略
    # 计算指标：MACD、RSI、KDJ必须至少有一个为True
    
    macd, signal, histogram = calculate_macd(prices)
    rsi = calculate_rsi(prices)
    k, d, j = calculate_kdj(prices)
    
    # 策略条件：MACD、RSI和KDJ出现低位金叉时买入
    buy_signal = True
    if MACD:
        buy_signal = buy_signal & (macd > signal)
    if RSI:
        buy_signal = buy_signal & (rsi < 30)
    if KDJ:
        buy_signal = buy_signal & (k > d) & (j > k)
    #buy_signal = (macd > signal) & (rsi < 30) & (k > d) & (j > k)


    # MACD、RSI和KDJ出现高位死叉时卖出
    sell_signal = True
    if MACD:
        sell_signal = sell_signal & (macd < signal)
    if RSI:
        sell_signal = sell_signal & (rsi > 70)
    if KDJ:
        sell_signal = sell_signal & (k < d) & (j < k)

    #sell_signal = (macd < signal) & (rsi > 70) & (k < d) & (j < k)
    
    signals = pd.Series(0, index=prices.index)  # 初始化信号列
    signals[buy_signal] = 1  # 买入信号
    signals[sell_signal] = -1  # 卖出信号
    
    return signals

#==============================================================================
#==============================================================================
#==============================================================================
if __name__=='__main__':
    
    
    # 回测期间
    start="2015-1-1"
    end  ="2024-12-31"
    
    price_type="Close"
    initial_balance=1000000
    slippage=0.001
    fee_rate=0.0005
    min_shares=100
    printout=True
    
    equity_curve=backtest(prices, signals, start, end)


def backtest(prices, signals,
             start, end,
             RF=0,
             strategy_name="",
             stop_loss=0.1, take_profit=0.2,   # 止损，止盈
             mdd_limit=0,                      # 最大回撤控制
             initial_balance=1000000, slippage=0.001, fee_rate=0.0005,
             min_shares=100,
             
             price_type="Close",
             printout=True,printout_result=True):

    if signals.empty:
        print(text_lang("交易信号为空，无法回测","Trading signals are empty, backtest cannot be performed."))
        return [initial_balance]
    
    prices2 = prices[start:end]
    signals2 = signals[start:end]

    balance = initial_balance
    position = 0
    entry_price = 0  # 记录买入价格
    equity_curve = []
    trade_records = []  # 记录每笔交易盈亏

    trade_activity = False
    first_trade = True
    peak_equity = initial_balance   # 新增：跟踪历史最高净值

    for i in range(1, len(prices2)):
        current_price = prices2[price_type].iloc[i]
        price_with_slippage = add_slippage(current_price, slippage)
        transaction_fee = calculate_transaction_fee(price_with_slippage, position, fee_rate)
        trddate = prices2.index[i].strftime("%Y-%m-%d")

        # === 买入逻辑 ===
        if signals2[i] == 1 and position == 0:
            max_shares_to_buy = balance / price_with_slippage
            shares_to_buy = max(int(max_shares_to_buy), min_shares)

            if shares_to_buy * price_with_slippage + transaction_fee <= balance:
                position = shares_to_buy
                entry_price = price_with_slippage
                balance -= shares_to_buy * price_with_slippage + transaction_fee
                trade_activity = True
                
                if printout:
                    if first_trade:
                        first_trade = False
                        activitytxt=text_lang("交易活动","Trading activities")
                        totxt=text_lang("至"," to ")
                        slippagetxt=text_lang("滑点比例","slippage ")
                        fee_ratetxt=text_lang("交易费率","fee rate ")
                        print(f"*** {activitytxt}: {start}{totxt}{end}, {slippagetxt}{slippage}, {fee_ratetxt}{fee_rate}")
                    buytxt=text_lang("买入","Buy")
                    pricetxt=text_lang("价格","price")
                    sharestxt=text_lang("买入股数","shares bought")
                    balancetxt=text_lang("余额","balance")
                    positiontxt=text_lang("持仓","position")
                    print(f"  {buytxt}: {trddate}, {pricetxt}: {current_price:.2f}, {sharestxt}: {shares_to_buy}, {balancetxt}: {balance:.2f}, {positiontxt}: {position}")

        # === 卖出逻辑（信号、止损、止盈） ===
        elif position > 0:
            sell_flag = False
            reason = ""

            # 策略信号卖出
            if signals2[i] == -1:
                sell_flag = True
                reason = text_lang("信号卖出","signal exit")

            # 止损卖出
            elif (stop_loss != 0) and ((current_price - entry_price) / entry_price <= -stop_loss):
                sell_flag = True
                reason = text_lang("止损","stop loss")

            # 止盈卖出
            elif (take_profit != 0) and (current_price - entry_price) / entry_price >= take_profit:
                sell_flag = True
                reason = text_lang("止盈","take profit")

            if sell_flag:
                balance += position * price_with_slippage - transaction_fee
                pnl = (price_with_slippage - entry_price) * position
                trade_records.append(pnl)
                trade_activity = True
                
                if printout:
                    
                    selltxt=text_lang("卖出","Sell")
                    pricetxt=text_lang("价格","price")
                    sharestxt=text_lang("卖出股数","shares sold")
                    balancetxt=text_lang("余额","balance")
                    positiontxt=text_lang("持仓","position")                    
                    print(f"  {selltxt}({reason}): {trddate}, {pricetxt}: {current_price:.2f}, {sharestxt}: {position}, {balancetxt}: {balance:.2f}, {positiontxt}: 0")

                position = 0
                entry_price = 0

        # === 计算净值 ===
        equity = balance + position * price_with_slippage
        equity_curve.append(equity)

        # === 更新最大净值 & 计算回撤 ===
        if equity > peak_equity:
            peak_equity = equity
        current_mdd = equity / peak_equity - 1

        # === 检查是否超过最大回撤限制 ===
        if (mdd_limit > 0) and (current_mdd <= -mdd_limit) and (position > 0):
            balance += position * price_with_slippage - transaction_fee
            pnl = (price_with_slippage - entry_price) * position
            trade_records.append(pnl)
            trade_activity = True
            
            if printout:
                selltxt=text_lang("卖出","Sell")
                pricetxt=text_lang("价格","price")
                sharestxt=text_lang("卖出股数","shares sold")
                balancetxt=text_lang("余额","balance")
                positiontxt=text_lang("持仓","position")
                reasontxt=text_lang("最大回撤限制","MDD limit")
                print(f"  {selltxt}({reasontxt}): {trddate}, {pricetxt}: {current_price:.2f}, {sharestxt}: {position}, {balancetxt}: {balance:.2f}, {positiontxt}: 0")
            
            position = 0
            entry_price = 0

    equity_curve = pd.Series(equity_curve, index=prices2.index[1:])

    metrics=None
    if trade_activity:
    #if len(equity_curve) > 0:
        if printout_result:
            print("")
            
        metrics = calculate_metrics(prices, equity_curve, trade_records,
                                    start, end, RF=RF,
                                    strategy_name=strategy_name,
                                    initial_balance=initial_balance,
                                    slippage=slippage, fee_rate=fee_rate,
                                    min_shares=min_shares, price_type=price_type,
                                    printout=printout_result)
    else:
        if printout_result:
            msgtxt=text_lang("无交易活动，无法进行回测","No trading activity, backtest cannot be performed.")
            print(msgtxt)

    if printout_result:
        return equity_curve
    else:
        return equity_curve, metrics

#==============================================================================


def calculate_metrics(prices, equity_curve, trade_records,
                      start, end,
                      RF=0,
                      strategy_name="",
                      initial_balance=1000000, slippage=0.001, fee_rate=0.0005,
                      min_shares=100,
                      price_type="Close",
                      printout=True):

    prices2 = prices[start:end]
    start_date = pd.to_datetime(start)
    end_date = pd.to_datetime(end)
    period_years = (end_date - start_date).days / 365.25

    cumulative_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    cagr = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / period_years) - 1

    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = drawdown.min()

    periods_per_year = 252

    daily_returns = equity_curve.pct_change().dropna()
    excess_returns = daily_returns - RF / periods_per_year
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(periods_per_year)
    
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std(ddof=0)
    sortino_ratio = np.sqrt(periods_per_year) * excess_returns.mean() / downside_std if downside_std != 0 else np.nan

    calmar_ratio = cagr / abs(max_drawdown) if max_drawdown < 0 else np.nan

    # === 修复：基于交易盈亏计算胜率和盈亏比 ===
    wins = [p for p in trade_records if p > 0]
    losses = [p for p in trade_records if p < 0]

    win_rate = len(wins) / len(trade_records) if trade_records else 0
    if losses:
        profit_loss_ratio = np.mean(wins) / abs(np.mean(losses)) if wins else 0
    else:
        #profit_loss_ratio = text_lang("没有亏损交易，无盈亏比","No losing trades, no profit-loss ratio")
        if win_rate == 1:
            profit_loss_ratio = text_lang("无亏损交易","No losing trades")
        if win_rate == 0:
            profit_loss_ratio = text_lang("无盈利交易","No winning trades")

    metrics = {
        text_lang('累计收益率','Cumulative return'): cumulative_return,
        text_lang('年化收益率','Annualized return'): cagr,
        text_lang('最大回撤','Max drawdown'): max_drawdown,
        text_lang('夏普比率','Sharpe'): sharpe_ratio,
        text_lang('索替诺比率','Sortino'): sortino_ratio,
        text_lang('卡玛比率','Calmar'): calmar_ratio,
        text_lang('胜率','Win rate'): win_rate,
        text_lang('盈亏比','Profit-loss ratio'): profit_loss_ratio
    }

    if printout:
        titletxt=text_lang("量化策略回测结果","Backtest Results")
        print(f"*** {titletxt}: {strategy_name}")
        ticker = prices2['ticker'].values[0]
        
        totxt=text_lang("至"," to ")
        print(f"  {ticker_name(ticker)}，{start}{totxt}{end}")
        for metric, value in metrics.items():
            if isinstance(value, float):
                if metric in [text_lang('夏普比率','Sharpe'),text_lang('索替诺比率','Sortino'),text_lang('卡玛比率','Calmar')]:
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value*100:.2f}%")
            else:
                print(f"  {metric}: {value}")

    return metrics


if __name__ =="__main__":
    # 示例数据
    prices = pd.Series([100, 105, 110, 115, 120])  # 假设的股价数据
    equity_curve = pd.Series([100, 110, 120, 115, 125])  # 假设的回测资产值
    start = '2020-01-01'
    end = '2023-01-01'
    RF = 0.02  # 无风险利率 (年化)
    
    # 计算绩效指标
    metrics = calculate_metrics(start_date, end_date, prices, equity_curve, RF)
    
    # 输出结果
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

#==============================================================================
if __name__ =="__main__":
    
    df=strategy_trend(ticker, prices, equity_curve, 
                    start, end, \
                    twinx=True, strategy_name="高低点策略")
    
def strategy_trend(prices, equity_curve, 
                    start, end, \
                    twinx=True, \
                    loc1='upper left',loc2='upper right', \
                    facecolor='whitesmoke', \
                     
                     strategy_name="", \
                     stop_loss=0.1, take_profit=0.2,mdd_limit=0, \
                     initial_balance=1000000, slippage=0.001, fee_rate=0.0005, \
                     min_shares=100, \
                     price_type="Close"):
    """
    可视化回测结果：绘制账户余额的变化曲线
    参数:
    - prices: 收盘价数据
    - equity_curve: 回测的账户余额曲线
    """
    ticker=prices['ticker'].values[0]
    titletxt=text_lang("量化策略回测：","Backtest Results: ")+ticker_name(ticker)
    
    footnote1=text_lang("注：资产净值横线表示持币观望","Note: A flat net asset line indicates holding cash (no trades)")
    if strategy_name != "":
        titletxt=titletxt + "，"+strategy_name
    
    ending_balance=round(equity_curve[-1],2)
    if ending_balance > initial_balance:
        sign='▲'
    elif ending_balance < initial_balance:
        sign='▼'
    else:
        sign=''
        
    change=str(round(abs(ending_balance/initial_balance-1)*100,2))+'%'
    footnote2=text_lang("价格滑点比例","slippage rate ")+str(slippage*100)+"%"+ \
              text_lang(", 交易费率",", fee rate ")+str(fee_rate*100)+"%"+ \
              text_lang(", 最小交易股数",", minimum trading shares ")+str(min_shares)
    footnote3=text_lang("期初资金量","Initial investment ")+str(initial_balance)+ \
              text_lang(", 期末资产净值",", ending net assets ")+str(ending_balance)+" ("+sign+change+")"
              
    footnote='\n' + footnote1 + '\n' + footnote2 + '\n' + footnote3

    df1=pd.DataFrame(equity_curve)
    ticker1=""
    colname1=0
    label1=text_lang("资产净值","Net assets")
    
    df2=prices[start:end]
    ticker2=''
    colname2=price_type
    label2=text_lang("证券价格","Security price")
    
    ylabeltxt=''
    
    plot_line2(df1,ticker1,colname1,label1, \
                   df2,ticker2,colname2,label2, \
                   ylabeltxt,titletxt,footnote, \
                   twinx=twinx, \
                   loc1=loc1,loc2=loc2, \
                   facecolor=facecolor)
    
    return df1, df2
#==============================================================================

def month_count(start, end):
    # 计算期间的月数
    
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return months

if __name__ =="__main__":
    # 示例
    month_count("2007-01-01", "2025-06-30") #222
    month_count("2023-01-01", "2025-06-30") #30
    month_count("2018-01-01", "2023-12-31") #72
    month_count("2016-01-01", "2022-12-31") #84
    month_count("2019-01-01", "2024-12-31") #72
    month_count("2021-09-01", "2022-06-30") #10

#==============================================================================


# =============== 绘制净值曲线 ===============
def plot_equity_curve(prices, equity_curve, start, end, price_type="Close"):
    """
    绘制净值曲线：策略 vs 买入持有
    
    策略净值曲线：
        根据交易信号计算出来的策略资金曲线，反映“如果按照策略买卖”，资金如何变化
    买入持有曲线：
        假设在回测区间 一开始全仓买入并一直持有，不做任何操作，然后到期末卖出。
        这个曲线用来作为最简单的“参考基准”。
    """
    prices2 = prices[start:end]
    
    # 策略净值
    strategy_curve = equity_curve / equity_curve.iloc[0]

    # 买入持有净值
    buyhold_curve = prices2[price_type] / prices2[price_type].iloc[0]

    plt.figure(figsize=(12,6))
    plt.plot(strategy_curve.index, strategy_curve, label="策略净值", linewidth=2)
    plt.plot(buyhold_curve.index, buyhold_curve, label="买入持有", linestyle="--", alpha=0.7)

    plt.title("净值曲线对比", fontsize=14)
    plt.xlabel("日期")
    plt.ylabel("净值（归一化）")
    plt.legend()
    plt.grid(True)
    plt.show()


# =============== 绘制回撤曲线 ===============
def plot_drawdown(equity_curve):
    """
    绘制回撤曲线
    
    为什么要看回撤曲线？
        回撤衡量的是 风险，而不是收益。
        策略可能赚钱，但如果中途有 −50% 的回撤，投资者可能撑不到翻盘。
        净值曲线告诉你赚了多少钱；回撤曲线告诉你中途可能亏了多少。
    """
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak

    plt.figure(figsize=(12,4))
    plt.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.4)
    plt.plot(drawdown.index, drawdown, color="red", linewidth=1.5)
    
    plt.title("回撤曲线", fontsize=14)
    plt.xlabel("日期")
    plt.ylabel("回撤比例")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # 下载贵州茅台近5年数据
    ticker = "600519.SS"
    prices,found=get_price_1ticker(ticker,fromdate,todate)
    # 策略信号
    signals = strategy_highlow(prices, window=60)

    # 回测
    equity_curve = backtest(prices, signals,
                            start="2019-01-01", end="2023-12-31",
                            strategy_name="高低点突破策略",
                            stop_loss=0.2, take_profit=0.3)

    # 绘制净值曲线
    plot_equity_curve(prices, equity_curve, "2019-01-01", "2023-12-31")

    # 绘制回撤曲线
    plot_drawdown(equity_curve)

#==============================================================================
if __name__ == "__main__":
    
    ticker='601398.SS'
    start="L10Y"
    end="today"
    test_periods=[("L5Y","today")]
    window=21
    RF=0 
    stop_loss=0.1
    take_profit=0.2
    mdd_limit=0
    initial_balance=10000
    slippage=0.001
    fee_rate=0.0005
    min_shares=100
    price_type="Adj Close"
    printout=True
    
    
    
    

def backtest_highlow(ticker,start="L5Y",end="today", \
                     test_periods=[("L5Y","today")], \
                     window=21,
                     RF=0,
                     strategy_name="高低点突破策略",
                     stop_loss=0.1, take_profit=0.3,   # 止损，止盈
                     mdd_limit=0,                      # 最大回撤控制
                     initial_balance=1000000, slippage=0.001, fee_rate=0.0005,
                     min_shares=100,
                     price_type="Adj Close",
                     facecolor='whitesmoke'):
    
    """
    功能：策略套装回测，高低点突破策略
    """
    # 获取证券价格数据
    start,end=start_end_preprocess(start,end)
    prices,found=get_price_1ticker(ticker,start,end)
    if found != "Found":
        print(f"Price info not found for {ticker} from {start} to {end}")
        return None

    # 定义公共参数
    strategy_name=text_lang("高低点突破策略","High-low Breakout Strategy")
    com_settings = {
                 "strategy_name":strategy_name,
                 "stop_loss":stop_loss, 
                 "take_profit":take_profit,
                 "mdd_limit":mdd_limit,
                 "initial_balance":initial_balance, 
                 "slippage":slippage, 
                 "fee_rate":fee_rate,
                 "min_shares":min_shares,
                 "price_type":price_type, 
                }

        
    # 生成交易信号
    signals=strategy_highlow(prices, window, **com_settings)
    
    # 循环测试各个回测期间
    equity_curve_list=[]
    metric_list=[]
    for tperiod in test_periods:
        tpos=test_periods.index(tperiod) + 1
        tstart,tend,description=tperiod
        tstart,tend=start_end_preprocess(tstart,tend)
        
        # 回测
        equity_curve, metric=backtest(prices, signals, tstart, tend, **com_settings,
                              printout=False, printout_result=False)
        equity_curve_list=equity_curve_list + [equity_curve]
        
        if not (metric is None): 
            metric_new = {
                          text_lang("回测","Test"): tpos,
                          text_lang("描述","Description"): description,
                          text_lang("开始日期","Start"): tstart,
                          text_lang("结束日期","End"): tend,
                          **metric
                        }
        else:
            metric_new = {
                          text_lang("回测","Test"): tpos,
                          text_lang("描述","Description"): description,
                          text_lang("开始日期","Start"): tstart,
                          text_lang("结束日期","End"): tend,
                        }
        
        metric_list=metric_list + [metric_new]

    # 将回测结果转换，便于集中输出
    metric_df = pd.DataFrame(metric_list)
    metric_df = metric_df.fillna('-')
    
    # 转换为百分比
    cols_zh = ['累计收益率', '年化收益率', '最大回撤', '胜率', '盈亏比']
    cols_en = ['Cumulative return','Annualized return','Max drawdown','Win rate','Profit-loss ratio']
    for col in cols_zh+cols_en:
        if col in metric_df.columns:
            metric_df[col] = metric_df[col].apply(lambda x: f"{x*100:.2f}%" if pd.api.types.is_number(x) else x)
    """
    # 产生的style对象无法直接用于CSS
    metric_df_styled=metric_df.style.format({
                    text_lang('累计收益率','Cumulative return'): "{:.2%}",
                    text_lang('年化收益率','Annualized return'): "{:.2%}",
                    text_lang('最大回撤','Max drawdown'): "{:.2%}",
                    text_lang('胜率','Win rate'): "{:.2%}",
                    text_lang('盈亏比','Profit-loss ratio'): "{:.2%}"
                })
    """
    
    titletxt=text_lang("回测结果对比：","Backtest Results: ")+ticker_name(ticker)+", "+strategy_name
    ft_zh="注：" + "窗口期天数" + str(window) + \
          "，止损" + ((str(stop_loss*100)+"%") if stop_loss != 0 else "无") + \
          "，止盈" + ((str(take_profit*100)+"%") if take_profit != 0 else "无") + \
          "，最大回撤控制" + ((str(mdd_limit*100)+"%") if mdd_limit != 0 else "无") + \
          "，滑点" + (str(slippage*100)+"%") + "，费率" + (str(fee_rate*100)+"%") + \
          "，基于" + ("前复权价" if price_type == "Adj Close" else "收盘价")

    ft_en="Note: " + "window days "+str(window) + \
          ", stop loss " + ((str(stop_loss*100)+"%") if stop_loss !=0 else "no") + \
          ", take profit " + ((str(take_profit*100)+"%") if take_profit != 0 else "no") + \
          ", max drawdown control " + ((str(mdd_limit*100)+"%") if mdd_limit !=0 else "no") + \
          ", slippage " + (str(slippage*100)+"%") + ", fee rate " + (str(fee_rate*100)+"%") + \
          ", based on " + ("adjusted price" if price_type=="Adj Close" else "close price")
    
    footnote1=text_lang(ft_zh,ft_en)
    
    ind_notes_zh="最大回撤 = 投资期间内资产净值从最高点到之后最低点的最大跌幅百分比，衡量最糟糕情况下可能遭受的资金损失幅度" + \
                 '\n'+ \
                 "卡玛比率 = 年化收益率与最大回撤的比值，衡量单位回撤风险所获得的收益能力，可精准评估其风险调整后收益能力" + \
                 "\n" \
                 "胜率 = 盈利交易数量占总交易数量的比例；盈亏比 = 所有盈利交易的平均盈利金额与所有亏损交易的平均亏损金额的比值"
    ind_notes_en1="Max drawdown = The largest drop from an investment’s peak to its subsequent trough during a given period"
    ind_notes_en2="Calmar = A risk-adjusted return metric calculated as the annualized return divided by the max drawdown"
    ind_notes_en3="Win rate = The percentage of trades that end in profit out of the total number of trades in a given period"
    ind_notes_en4="Profit-loss ratio = The ratio of average profit per winning trade to the average loss per losing trade"
    ind_notes_en =ind_notes_en1 + '\n' +ind_notes_en2 + '\n' +ind_notes_en3 + '\n' +ind_notes_en4
    footnote2=text_lang(ind_notes_zh,ind_notes_en)
    
    footnote = footnote1 + '\n' + footnote2
    
    df_display_CSS(metric_df,titletxt=titletxt,footnote=footnote, \
                   facecolor=facecolor,decimals=4, \
                       hide_columns=False,
                       first_col_align='center',second_col_align='center', \
                       last_col_align='center',other_col_align='center', \
                       titile_font_size='14px',heading_font_size='12px', \
                       data_font_size='12px',footnote_font_size='12px')
    
    return equity_curve_list, metric_list



#==============================================================================


def backtest_cross(ticker,start="L5Y",end="today", \
                     test_periods=[("L5Y","today")], \
                     MACD=True, RSI=True, KDJ=True,
                     RF=0,
                     strategy_name="金叉死叉策略",
                     stop_loss=0.1, take_profit=0.3,   # 止损，止盈
                     mdd_limit=0,                      # 最大回撤控制
                     initial_balance=1000000, slippage=0.001, fee_rate=0.0005,
                     min_shares=100,
                     price_type="Adj Close",
                     facecolor='whitesmoke'):
    
    """
    功能：策略套装回测，高低点突破策略，多个回测期间
    """
    # 获取证券价格数据
    start,end=start_end_preprocess(start,end)
    prices,found=get_price_1ticker(ticker,start,end)
    if found != "Found":
        print(f"Price info not found for {ticker} from {start} to {end}")
        return None

    # 定义公共参数
    strategy_name=text_lang("金叉死叉策略","Golden/Death Cross Strategy")
    com_settings = {
                 "strategy_name":strategy_name,
                 "stop_loss":stop_loss, 
                 "take_profit":take_profit,
                 "mdd_limit":mdd_limit,
                 "initial_balance":initial_balance, 
                 "slippage":slippage, 
                 "fee_rate":fee_rate,
                 "min_shares":min_shares,
                 "price_type":price_type, 
                }

        
    # 生成交易信号
    signals=strategy_cross(prices, MACD=MACD, RSI=RSI, KDJ=KDJ)
    
    # 循环测试各个回测期间
    equity_curve_list=[]
    metric_list=[]
    for tperiod in test_periods:
        tpos=test_periods.index(tperiod) + 1
        tstart,tend,description=tperiod
        tstart,tend=start_end_preprocess(tstart,tend)
        
        # 回测
        equity_curve, metric=backtest(prices, signals, tstart, tend, **com_settings,
                              printout=False, printout_result=False)
        equity_curve_list=equity_curve_list + [equity_curve]
        
        if not (metric is None):
            metric_new = {
                          text_lang("回测","Test"): tpos,
                          text_lang("描述","Description"): description,
                          text_lang("开始日期","Start"): tstart,
                          text_lang("结束日期","End"): tend,
                          **metric 
                        }
        else:
            metric_new = {
                          text_lang("回测","Test"): tpos,
                          text_lang("描述","Description"): description,
                          text_lang("开始日期","Start"): tstart,
                          text_lang("结束日期","End"): tend,
                        }
        
        metric_list=metric_list + [metric_new]

    # 将回测结果转换，便于集中输出
    metric_df = pd.DataFrame(metric_list)
    metric_df = metric_df.fillna('-')
    
    # 转换为百分比
    cols_zh = ['累计收益率', '年化收益率', '最大回撤', '胜率', '盈亏比']
    cols_en = ['Cumulative return','Annualized return','Max drawdown','Win rate','Profit-loss ratio']
    for col in cols_zh+cols_en:
        if col in metric_df.columns:
            metric_df[col] = metric_df[col].apply(lambda x: f"{x*100:.2f}%" if pd.api.types.is_number(x) else x)
    """
    # 产生的style对象无法直接用于CSS
    metric_df_styled=metric_df.style.format({
                    text_lang('累计收益率','Cumulative return'): "{:.2%}",
                    text_lang('年化收益率','Annualized return'): "{:.2%}",
                    text_lang('最大回撤','Max drawdown'): "{:.2%}",
                    text_lang('胜率','Win rate'): "{:.2%}",
                    text_lang('盈亏比','Profit-loss ratio'): "{:.2%}"
                })
    """
    sub_strategy = ("MACD + " if MACD else "") + ("RSI + " if RSI else "") + ("KDJ" if KDJ else "")
    if sub_strategy.endswith(" + "):
        sub_strategy = sub_strategy[:-3]   # 去掉最后两个字符
    
    titletxt=text_lang("回测结果对比：","Backtest Results: ")+ticker_name(ticker)+ \
                        ", "+strategy_name+" ("+sub_strategy+")"
    
    ft_zh="注：" + \
          "止损" + ((str(stop_loss*100)+"%") if stop_loss != 0 else "无") + \
          "，止盈" + ((str(take_profit*100)+"%") if take_profit != 0 else "无") + \
          "，最大回撤控制" + ((str(mdd_limit*100)+"%") if mdd_limit != 0 else "无") + \
          "，滑点" + (str(slippage*100)+"%") + "，费率" + (str(fee_rate*100)+"%") + \
          "，基于" + ("前复权价" if price_type == "Adj Close" else "收盘价") + \
              "，空白行表示期间内无交易活动"

    ft_en="Note: " + \
          "stop loss " + ((str(stop_loss*100)+"%") if stop_loss !=0 else "no") + \
          ", take profit " + ((str(take_profit*100)+"%") if take_profit != 0 else "no") + \
          ", max drawdown control " + ((str(mdd_limit*100)+"%") if mdd_limit !=0 else "no") + \
          ", slippage " + (str(slippage*100)+"%") + ", fee rate " + (str(fee_rate*100)+"%") + \
          ", based on " + ("adjusted price" if price_type=="Adj Close" else "close price") + \
              ", a blank line means no trades in period"
    
    footnote1=text_lang(ft_zh,ft_en)
    
    ind_notes_zh="最大回撤 = 投资期间内资产净值从最高点到之后最低点的最大跌幅百分比，衡量最糟糕情况下可能遭受的资金损失幅度" + \
                 '\n'+ \
                 "卡玛比率 = 年化收益率与最大回撤的比值，衡量单位回撤风险所获得的收益能力，可精准评估其风险调整后收益能力" + \
                 "\n" \
                 "胜率 = 盈利交易数量占总交易数量的比例；盈亏比 = 所有盈利交易的平均盈利金额与所有亏损交易的平均亏损金额的比值"
    ind_notes_en1="Max drawdown = The largest drop from an investment’s peak to its subsequent trough during a given period"
    ind_notes_en2="Calmar = A risk-adjusted return metric calculated as the annualized return divided by the max drawdown"
    ind_notes_en3="Win rate = The percentage of trades that end in profit out of the total number of trades in a given period"
    ind_notes_en4="Profit-loss ratio = The ratio of average profit per winning trade to the average loss per losing trade"
    ind_notes_en =ind_notes_en1 + '\n' +ind_notes_en2 + '\n' +ind_notes_en3 + '\n' +ind_notes_en4
    footnote2=text_lang(ind_notes_zh,ind_notes_en)
    
    footnote = footnote1 + '\n' + footnote2
    
    df_display_CSS(metric_df,titletxt=titletxt,footnote=footnote, \
                   facecolor=facecolor,decimals=4, \
                       hide_columns=False,
                       first_col_align='center',second_col_align='center', \
                       last_col_align='center',other_col_align='center', \
                       titile_font_size='14px',heading_font_size='12px', \
                       data_font_size='12px',footnote_font_size='12px')
    
    return equity_curve_list, metric_list

#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================


















