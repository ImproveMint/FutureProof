from itertools import product
from typing import List
import numpy as np

def preprocess_candles(candles: List[dict]) -> np.ndarray:
    dtype = np.dtype([
        ('start', 'i8'),
        ('open', 'f8'),
        ('high', 'f8'),
        ('low', 'f8'),
        ('close', 'f8')
    ])

    preprocessed = np.array([
        (   
            int(k["start"]),
            float(k["open"]),
            float(k["high"]),
            float(k["low"]),
            float(k["close"])
        )
        for k in candles
    ], dtype=dtype)

    return preprocessed

def is_candle_bullish(candle):
    return candle['close'] > candle['open']

def is_candle_bearish(candle):
    return candle['close'] < candle['open']

def search_for_candle_pattern(candles, pattern = [1, 0, 1, 1, 1]):
    
    total_patterns = 0
    bullish_next_candles = 0
    bearish_next_candles = 0

    for i in range(len(candles) - len(pattern)):
        is_pattern = True
        for j in range(len(pattern)):
            if pattern[j] == 0 and not is_candle_bearish(candles[i+j]):
                is_pattern = False
                break
            elif pattern[j] == 1 and not is_candle_bullish(candles[i+j]):
                is_pattern = False
                break
        if is_pattern:
            total_patterns += 1
            if is_candle_bullish(candles[i + len(pattern)]):
                bullish_next_candles += 1
            else:
                bearish_next_candles += 1

    results = {
        "total_patterns": total_patterns,
        "bullish_next_percentage": (bullish_next_candles / total_patterns * 100) if total_patterns > 0 else 0,
        "bearish_next_percentage": (bearish_next_candles / total_patterns * 100) if total_patterns > 0 else 0
    }

    return results

def analyze_patterns(candles, pattern_length: int):
    patterns = list(product([0, 1], repeat=pattern_length))
    best_patterns = []

    for pattern in patterns:
        result = search_for_candle_pattern(candles, pattern)
        best_patterns.append((pattern, result))

    # Sort by bullish_next_percentage and total_patterns to find the most predictive patterns
    best_patterns.sort(key=lambda x: (x[1]['bullish_next_percentage'], x[1]['total_patterns']), reverse=True)

    for pattern, result in best_patterns[:10]:  # Print top 10 patterns for brevity
        print(f"Pattern: {pattern}, Total Patterns: {result['total_patterns']}, "
            f"Bullish Next %: {result['bullish_next_percentage']:.2f}, "
            f"Bearish Next %: {result['bearish_next_percentage']:.2f}")