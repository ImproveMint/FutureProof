from src.strategy import Strategy
from src.account import Account
from src.order import *

import optuna

def objective(trial, candles, warmup_candles):
    params = {}
    account = Account("SOLPERP", 1000, 0.1, 0.05)
    strategy = Strategy(account)
    
    # Suggest values for each hyperparameter
    for param in strategy.hyperparameters():
        if param['type'] == float:
            params[param['name']] = trial.suggest_float(param['name'], param['min'], param['max'])
        elif param['type'] == int:
            params[param['name']] = trial.suggest_int(param['name'], param['min'], param['max'])
    
    strategy.hp = params
    run_simulation(strategy, candles, warmup_candles)
    
    return account.collateral_manager.total_collateral

def optimize_hyperparameters(candles, warmup_candles, n_trials=50):
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction='maximize')
    study.optimize(lambda trial: objective(trial, candles, warmup_candles), n_trials=n_trials, )

    return study.best_params, study.best_value

def dynamic_optimization(candles, trials, test_start, test_end, look_back_period, update_period, warmup_candles=0):
    
    param_list = []
    
    # Optimize parameters
    for i in range(test_start - look_back_period, test_end - look_back_period, update_period):
        start_candle = i - warmup_candles
        end_candle = i + look_back_period
        optimization_candles = candles[start_candle : end_candle]
        print(f"Optimizing range: {start_candle + warmup_candles} - {end_candle}")
        results, _ = optimize_hyperparameters(optimization_candles, warmup_candles, trials)
        param_list.append(results)
    
    return param_list

def run_dynamic_params(candles, param_list, test_start, test_end, look_back_period, update_period, warmup_candles=0):
    overall_balance_time_series = []
    overall_asset_price_time_series = []
    
    account = Account("SOLUSDT", 1000, 0.1, 0.05)
    strategy = Strategy(account)
    
    for idx, params in enumerate(param_list):
        start = test_start + (idx * update_period) - warmup_candles
        
        end = min(start + update_period + warmup_candles, test_end)
        test_candles = candles[start : end]
        
        strategy.hp = params
        _, balance_time_series, asset_price_time_series = run_simulation(strategy, account, test_candles, warmup_candles)
        print(f"Testing optimized params on range: {start + warmup_candles} - {end}. PNL:", strategy.account.collateral_manager.total_collateral)
        
        overall_balance_time_series.extend(balance_time_series)
        overall_asset_price_time_series.extend(asset_price_time_series)
    
def run_simulation(strategy: Strategy, candles, warmup_candles = 0):
    
    portfoilio = []
    time_series = []
    
    for i in range(warmup_candles, len(candles)):
        current_candle = candles[i]
        candle_open = current_candle["open"]
        
        ###### Should only have access to the open. Prevent look ahead bias. #######
        strategy.account.update_pnl(candle_open)
        candles_available_this_loop = candles[0 : i + 1]
        strategy.new_candle(candles_available_this_loop)
        #######################################################################
        
        strategy.account.check_for_filled_orders(current_candle["low"], current_candle["high"])
        
        portfoilio.append(strategy.account.collateral_manager.total_collateral)
        time_series.append(candle_open)

    return strategy, portfoilio, time_series
