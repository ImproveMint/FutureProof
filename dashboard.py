from datetime import datetime, timezone
import importlib
import inspect
import json
from flask import Flask, render_template, request, redirect, url_for
from src.account import Account
from src.candle_manager import preprocess_candles
import src.simulation
import src.strategy
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo

app = Flask(__name__)

STRATEGIES_FOLDER = 'strategies'

@app.route('/')
def index():
    # List all Python files in the strategies folder
    strategy_files = [f for f in os.listdir(STRATEGIES_FOLDER) if f.endswith('.py')]
    return render_template('index.html', strategy_files=strategy_files)

@app.route('/run_script', methods=['POST'])
def run_script():
    # Read the date and time values from the form
    start_date = request.form['start_date']
    start_time = "00:00"
    
    end_date = request.form['end_date']
    end_time = "00:00"
    
    strategy_file = request.form['strategy_file']
    
    # Combine date and time and convert to UTC timestamp in milliseconds
    start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    
    start_timestamp = int(start_datetime.timestamp() * 1000)
    end_timestamp = int(end_datetime.timestamp() * 1000)
    
    # Here you can call your script or function with these integers
    asset_price, portfolio, metrics = run_simulation(start_timestamp, end_timestamp, strategy_file)
    
    # Generate the plot
    plot_div = plot_floats_over_time(asset_price, portfolio)
    
    return render_template('index.html', plot_div=plot_div, metrics=metrics, strategy_files=os.listdir(STRATEGIES_FOLDER))

def run_simulation(start_ts, end_ts, strategy_file):
    
    filename = "data/candles/SOLUSDT_1m.json"
    strategy_class = get_strategy_class(strategy_file)

    with open(filename, 'r') as f:
        raw_candles = json.load(f)["candles"]
        candles = preprocess_candles(raw_candles)
    
    # binary search refactor
    start_index = next(i for i, candle in enumerate(candles) if candle['start'] >= start_ts)
    end_index = next(i for i, candle in enumerate(candles) if candle['start'] >= end_ts)
    
    candles = candles[start_index: end_index]

    account = Account("SOLPERP", 1000, 0.1, 0.05)
    strategy = strategy_class(account)
    
    _, portfolio, time_series = src.simulation.run_simulation(strategy, candles)
    
    metrics = {
        'end_balance': round(account.collateral_manager.total_collateral, 3),
        'total_trades': strategy.metrics.total_trades,
        'total_longs': strategy.metrics.total_longs,
        'total_shorts': strategy.metrics.total_shorts
    }
    
    return time_series, portfolio, metrics

def get_strategy_class(strategy_file):
    # Dynamically import and the selected strategy
    strategy_module_name = strategy_file.replace('.py', '')
    strategy_module_path = os.path.join(STRATEGIES_FOLDER, strategy_file)
    spec = importlib.util.spec_from_file_location(strategy_module_name, strategy_module_path)
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    
    # Find the only class in the strategy module
    strategy_class = None
    for _, obj in inspect.getmembers(strategy_module, inspect.isclass):
        if issubclass(obj, src.strategy.Strategy) and obj is not src.strategy.Strategy:
            strategy_class = obj
            break
    
    if not strategy_class:
        raise ValueError(f"No subclass of Strategy found in the strategy file {strategy_file}")
    
    return strategy_class
    
def plot_floats_over_time(asset_price, portfolio, title='Equity Curve', xlabel='Timeline', ylabel1='Asset Price', ylabel2='Portfolio'):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=list(range(len(asset_price))), y=asset_price, name='Asset Price', line=dict(color='blue')),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=list(range(len(portfolio))), y=portfolio, name='Portfolio', line=dict(color='orange')),
        secondary_y=True,
    )
    
    # Extract long and short order positions
    # long_positions = [candle for order, candle in metrics.order_history if order.direction == OrderDirection.LONG]
    # short_positions = [candle for order, candle in metrics.order_history if order.direction == OrderDirection.SHORT]

    # # Add long order arrows
    # fig.add_trace(
    #     go.Scatter(
    #         x=long_positions,
    #         y=[values1[pos] for pos in long_positions],
    #         mode='markers',
    #         name='Long Orders',
    #         marker=dict(symbol='arrow-bar-up', color='green', size=10)
    #     ),
    #     secondary_y=False
    # )

    # # Add short order arrows
    # fig.add_trace(
    #     go.Scatter(
    #         x=short_positions,
    #         y=[values1[pos] for pos in short_positions],
    #         mode='markers',
    #         name='Short Orders',
    #         marker=dict(symbol='arrow-bar-down', color='red', size=10)
    #     ),
    #     secondary_y=False
    # )

    # Add figure title
    fig.update_layout(
        title_text=title,
        width=1200,  # set the width of the plot
        height=600   # set the height of the plot
    )

    # Set x-axis title
    fig.update_xaxes(title_text=xlabel)

    # Set y-axes titles
    fig.update_yaxes(title_text=ylabel1, secondary_y=False)
    fig.update_yaxes(title_text=ylabel2, secondary_y=True)

    # Get HTML representation of the plot
    plot_div = pyo.plot(fig, output_type='div', include_plotlyjs=True)

    return plot_div

if __name__ == '__main__':
    app.run(debug=True)