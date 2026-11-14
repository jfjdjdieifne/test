#!/usr/bin/env python3
"""
Engine V6 - Main Runner
Run backtest on single day or full month
"""

import sys
import argparse
from tests.test_single_day import test_single_day
from tests.test_full_month import test_full_month

def main():
    parser = argparse.ArgumentParser(description='Engine V6 Backtest Runner')
    parser.add_argument('--mode', choices=['single', 'month'], default='single',
                       help='Test mode: single day or full month')
    parser.add_argument('--year', type=int, default=2026, help='Year')
    parser.add_argument('--month', type=int, default=6, help='Month')
    parser.add_argument('--day', type=int, default=15, help='Day (for single mode)')
    parser.add_argument('--balance', type=float, default=109.0, help='Starting balance')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        test_single_day(args.year, args.month, args.day, args.balance)
    else:
        test_full_month(args.year, args.month, args.balance)

if __name__ == '__main__':
    main()
