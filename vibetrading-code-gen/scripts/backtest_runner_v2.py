#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Runner v2 - Uses historical data for accurate backtesting

Replaces the old simulated backtest with real historical data backtesting
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest_engine.historical_backtest import HistoricalBacktestEngine
from backtest_engine.data_downloader import HyperliquidDataDownloader
from backtest_engine.strategy_adapter import create_strategy_from_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestRunnerV2:
    """Backtest runner using historical data"""
    
    def __init__(self, use_testnet=False):
        self.use_testnet = use_testnet
        self.data_downloader = HyperliquidDataDownloader(use_testnet=use_testnet)
        logger.info(f"BacktestRunnerV2 initialized (testnet: {use_testnet})")
    
    def run_backtest(self, strategy_path, config=None):
        """
        Run historical backtest
        
        Args:
            strategy_path: Path to strategy file
            config: Backtest configuration
        
        Returns:
            Backtest results
        """
        # Default configuration
        default_config = {
            "symbol": "HYPE",
            "interval": "1h",
            "days": 30,
            "initial_balance": 10000.0,
            "commission_rate": 0.001,
            "slippage": 0.001,
            "force_download": False,
            "testnet": self.use_testnet
        }
        
        if config:
            default_config.update(config)
        config = default_config
        
        print(f"\n🚀 Starting Historical Backtest")
        print(f"📁 Strategy: {strategy_path}")
        print(f"📊 Symbol: {config['symbol']}")
        print(f"📅 Period: Last {config['days']} days")
        print(f"⏱️  Interval: {config['interval']}")
        print(f"💰 Initial Balance: ${config['initial_balance']:,.2f}")
        
        try:
            # Check if config file exists
            strategy_dir = Path(strategy_path).parent
            config_file = None
            
            # Look for config file
            possible_configs = [
                strategy_dir / f"{Path(strategy_path).stem}_config.json",
                strategy_dir / "config.json",
                Path(strategy_path).with_suffix('.json')
            ]
            
            for cfg in possible_configs:
                if cfg.exists():
                    config_file = cfg
                    print(f"📋 Using config: {config_file}")
                    break
            
            # Create backtest engine
            engine = HistoricalBacktestEngine(
                use_testnet=config["testnet"],
                data_dir="data/historical"
            )
            
            # Run backtest
            results = engine.run_backtest(strategy_path, config)
            
            if results:
                print("\n✅ Backtest completed successfully!")
                
                # Save detailed results
                self._save_detailed_results(results, strategy_path, config)
                
                return results
            else:
                print("\n❌ Backtest failed!")
                return None
                
        except Exception as e:
            print(f"\n❌ Backtest error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_detailed_results(self, results, strategy_path, config):
        """Save detailed backtest results"""
        output_dir = Path("backtest_results")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name = Path(strategy_path).stem
        
        # Save JSON results
        json_file = output_dir / f"{strategy_name}_{config['symbol']}_{timestamp}.json"
        
        results_data = {
            "strategy": strategy_name,
            "strategy_path": str(strategy_path),
            "config": config,
            "results": results,
            "generated_at": datetime.now().isoformat(),
            "backtest_version": "v2_historical"
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed results saved to: {json_file}")
        
        # Save summary report
        self._generate_summary_report(results, strategy_name, config, output_dir, timestamp)
    
    def _generate_summary_report(self, results, strategy_name, config, output_dir, timestamp):
        """Generate human-readable summary report"""
        report_file = output_dir / f"{strategy_name}_{config['symbol']}_{timestamp}_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("HISTORICAL BACKTEST REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Strategy: {strategy_name}\n")
            f.write(f"Symbol: {config['symbol']}\n")
            f.write(f"Interval: {config['interval']}\n")
            f.write(f"Period: {results.get('period_start', 'N/A')} to {results.get('period_end', 'N/A')}\n")
            f.write(f"Data Points: {results.get('data_points', 0)}\n\n")
            
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-"*70 + "\n")
            f.write(f"Initial Balance: ${results['initial_balance']:,.2f}\n")
            f.write(f"Final Balance:   ${results['final_balance']:,.2f}\n")
            f.write(f"Total Return:    {results['total_return_pct']:+.2f}%\n\n")
            
            f.write("RISK METRICS\n")
            f.write("-"*70 + "\n")
            f.write(f"Max Drawdown:    {results['max_drawdown_pct']:.2f}%\n")
            f.write(f"Sharpe Ratio:    {results['sharpe_ratio']:.2f}\n")
            f.write(f"Win Rate:        {results['win_rate']:.1f}%\n")
            f.write(f"Total Trades:    {results['total_trades']}\n")
            f.write(f"Winning Trades:  {results['winning_trades']}\n")
            f.write(f"Losing Trades:   {results['losing_trades']}\n")
            f.write(f"Total Commission: ${results['total_commission']:.2f}\n\n")
            
            f.write("FINAL POSITION\n")
            f.write("-"*70 + "\n")
            f.write(f"USDC Balance:    ${results['final_usdc']:,.2f}\n")
            f.write(f"{config['symbol']} Balance: {results['final_asset']:.4f}\n")
            f.write(f"Current Price:   ${results['final_price']:.4f}\n\n")
            
            f.write("BACKTEST CONFIGURATION\n")
            f.write("-"*70 + "\n")
            for key, value in config.items():
                f.write(f"{key}: {value}\n")
            
            f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Backtest Engine: Historical Data v2\n")
        
        print(f"📝 Summary report saved to: {report_file}")
    
    def download_data(self, symbols=None, days=30, intervals=None):
        """Download historical data for backtesting"""
        if symbols is None:
            symbols = ["BTC", "ETH", "HYPE"]
        
        if intervals is None:
            intervals = ["1h", "4h"]
        
        print(f"\n📥 Downloading historical data...")
        print(f"   Symbols: {', '.join(symbols)}")
        print(f"   Days: {days}")
        print(f"   Intervals: {', '.join(intervals)}")
        
        self.data_downloader.download_all_data(
            symbols=symbols,
            intervals=intervals,
            days=days,
            include_funding=True
        )
        
        # Show summary
        summary = self.data_downloader.get_data_summary()
        print(f"\n✅ Data download completed!")
        print(f"   Total files: {summary['file_count']}")
        print(f"   Total size: {summary['total_size_mb']:.2f} MB")
    
    def show_data_summary(self):
        """Show summary of downloaded data"""
        summary = self.data_downloader.get_data_summary()
        
        print(f"\n📊 Data Summary")
        print(f"   Directory: {self.data_downloader.data_dir}")
        print(f"   Total files: {summary['file_count']}")
        print(f"   Total size: {summary['total_size_mb']:.2f} MB")
        
        if summary['files']:
            print(f"\n   Recent files:")
            for file_info in summary['files'][:5]:  # Show first 5 files
                print(f"     • {file_info['name']} ({file_info['size_mb']:.2f} MB)")
        
        # Show available symbols
        symbols = self.data_downloader.get_available_symbols()
        print(f"\n   Available symbols ({len(symbols)}):")
        for i in range(0, len(symbols), 5):
            print(f"     {', '.join(symbols[i:i+5])}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run historical backtests')
    
    # Backtest commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run backtest
    run_parser = subparsers.add_parser('run', help='Run backtest')
    run_parser.add_argument('strategy', help='Path to strategy file')
    run_parser.add_argument('--symbol', default='HYPE', help='Trading symbol')
    run_parser.add_argument('--interval', default='1h', help='Time interval')
    run_parser.add_argument('--days', type=int, default=30, help='Days of data')
    run_parser.add_argument('--balance', type=float, default=10000.0, help='Initial balance')
    run_parser.add_argument('--testnet', action='store_true', help='Use testnet')
    run_parser.add_argument('--force-download', action='store_true', help='Force data download')
    
    # Download data
    download_parser = subparsers.add_parser('download', help='Download historical data')
    download_parser.add_argument('--symbols', nargs='+', default=['BTC', 'ETH', 'HYPE'], help='Symbols to download')
    download_parser.add_argument('--days', type=int, default=30, help='Days of data')
    download_parser.add_argument('--intervals', nargs='+', default=['1h', '4h'], help='Time intervals')
    download_parser.add_argument('--testnet', action='store_true', help='Use testnet')
    
    # Show data
    data_parser = subparsers.add_parser('data', help='Show data summary')
    data_parser.add_argument('--testnet', action='store_true', help='Use testnet')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create runner
    runner = BacktestRunnerV2(use_testnet=getattr(args, 'testnet', False))
    
    if args.command == 'run':
        # Run backtest
        config = {
            "symbol": args.symbol,
            "interval": args.interval,
            "days": args.days,
            "initial_balance": args.balance,
            "force_download": args.force_download,
            "testnet": args.testnet
        }
        
        runner.run_backtest(args.strategy, config)
    
    elif args.command == 'download':
        # Download data
        runner.download_data(
            symbols=args.symbols,
            days=args.days,
            intervals=args.intervals
        )
    
    elif args.command == 'data':
        # Show data summary
        runner.show_data_summary()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required for historical backtesting")
        sys.exit(1)
    
    main()