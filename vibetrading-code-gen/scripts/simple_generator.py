#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Strategy Generator - Creates self-contained strategy folders
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.new_code_formatter import NewCodeFormatter
from scripts.template_manager import TemplateManager

def parse_grid_parameters(prompt):
    """Parse grid trading parameters from prompt."""
    params = {
        'symbol': 'HYPE',
        'type': 'grid_trading',
        'parameters': {
            'price_range': [0.1, 0.3],
            'grid_count': 20,
            'grid_size': 1000.0
        }
    }
    
    # Extract symbol
    if '$HYPE' in prompt or 'HYPE' in prompt:
        params['symbol'] = 'HYPE'
    
    # Extract price range
    import re
    price_match = re.search(r'price range\s+([\d.]+)\s*-\s*([\d.]+)', prompt, re.IGNORECASE)
    if price_match:
        params['parameters']['price_range'] = [float(price_match.group(1)), float(price_match.group(2))]
    
    # Extract grid count
    grid_match = re.search(r'(\d+)\s+grids?', prompt, re.IGNORECASE)
    if grid_match:
        params['parameters']['grid_count'] = int(grid_match.group(1))
    
    # Extract grid size
    size_match = re.search(r'(\d+(?:\.\d+)?)\s+HYPE per grid', prompt, re.IGNORECASE)
    if size_match:
        params['parameters']['grid_size'] = float(size_match.group(1))
    
    return params

def generate_strategy(prompt, output_dir="generated_strategies"):
    """Generate a self-contained strategy from prompt."""
    print(f"🔍 分析策略描述: {prompt}")
    
    # Parse parameters
    strategy_info = parse_grid_parameters(prompt)
    
    # Generate session ID
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Load template
    template_manager = TemplateManager()
    template = template_manager.select_template(strategy_info)
    
    if not template:
        print("❌ 未找到合适的模板")
        return None
    
    print(f"📄 使用模板: {template['name']}")
    print(f"📊 策略参数: {json.dumps(strategy_info, indent=2, ensure_ascii=False)}")
    
    # Generate strategy
    formatter = NewCodeFormatter()
    result = formatter.generate(
        template=template,
        strategy_info=strategy_info,
        base_output_dir=output_dir,
        session_id=session_id
    )
    
    return result

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate self-contained trading strategy')
    parser.add_argument('prompt', help='Strategy description prompt')
    parser.add_argument('--output-dir', '-o', default='generated_strategies',
                       help='Output directory (default: generated_strategies)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🚀 开始生成自包含策略...")
    print(f"📁 输出目录: {args.output_dir}")
    
    # Generate strategy
    result = generate_strategy(args.prompt, args.output_dir)
    
    if result:
        print("\n" + "="*60)
        print("✅ 策略生成完成!")
        print("="*60)
        
        print(f"\n📁 策略文件夹: {result['strategy_folder']}")
        print(f"📛 策略名称: {result['strategy_name']}")
        print(f"🔑 Session ID: {result['session_id']}")
        
        print("\n📄 生成的文件:")
        for file_info in result['generated_files']:
            print(f"  • {file_info['type']}: {file_info['path']}")
            if args.verbose:
                print(f"    {file_info['description']}")
        
        print("\n🚀 使用说明:")
        print(f"  1. cd {result['strategy_folder']}")
        print("  2. pip install -r requirements.txt")
        print("  3. 设置环境变量:")
        print("     export HYPERLIQUID_API_KEY='your_api_key'")
        print("     export HYPERLIQUID_ACCOUNT_ADDRESS='your_address'")
        print("  4. python run_strategy.py")
        print("\n📊 运行回测:")
        print("  python run_backtest.py")
        
        print("\n⚠️  重要提示:")
        print("  • 请在模拟交易中充分测试策略")
        print("  • 使用小资金开始实盘交易")
        print("  • 定期监控策略性能")
        
        # Save generation info
        info_file = Path(result['strategy_folder']) / "generation_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 生成信息已保存到: {info_file}")
    else:
        print("❌ 策略生成失败")

if __name__ == "__main__":
    main()