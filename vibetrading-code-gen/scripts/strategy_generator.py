# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
VibeTrading Code Generator - Main Strategy Generator Script

This script generates executable Hyperliquid trading strategy code
from natural language prompts.
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from templates.template_manager import TemplateManager
from templates.prompt_parser import PromptParser
from code_formatter import CodeFormatter

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate Hyperliquid trading strategy code from prompts')
    parser.add_argument('prompt', help='Natural language prompt describing the strategy')
    parser.add_argument('--output-dir', '-o', default='generated_strategies',
                       help='Output directory for generated files (default: generated_strategies)')
    parser.add_argument('--strategy-name', '-n', help='Custom strategy name')
    parser.add_argument('--symbol', '-s', help='Trading symbol (overrides auto-detection)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return parser.parse_args()

def ensure_output_dir(output_dir):
    """Ensure output directory exists."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir

def generate_strategy_code(prompt, output_dir, strategy_name=None, symbol=None, verbose=False):
    """Generate strategy code from prompt."""
    
    print("🔍 分析策略描述: {prompt}")
    
    # Parse the prompt
    parser = PromptParser()
    strategy_info = parser.parse(prompt)
    
    # Override with command line arguments if provided
    if symbol:
        strategy_info['symbol'] = symbol
    if strategy_name:
        strategy_info['name'] = strategy_name
    
    # Select appropriate template
    template_manager = TemplateManager()
    template = template_manager.select_template(strategy_info)
    
    if verbose:
        print("📋 解析结果: {json.dumps(strategy_info, indent=2, ensure_ascii=False)}")
        print("📄 选择模板: {template['name']}")
    
    # Generate code
    code_formatter = CodeFormatter()
    generated_files = code_formatter.generate(
        template=template,
        strategy_info=strategy_info,
        output_dir=output_dir
    )
    
    return generated_files, strategy_info

def print_summary(generated_files, strategy_info):
    """Print generation summary."""
    print("\n" + "="*60)
    print("✅ 策略代码生成完成!")
    print("="*60)
    
    print("\n📊 策略信息:")
    print("  名称: {strategy_info.get('name', '未命名策略')}")
    print("  类型: {strategy_info.get('type', '未知')}")
    print("  交易品种: {strategy_info.get('symbol', '未指定')}")
    
    if 'parameters' in strategy_info:
        print("  参数: {json.dumps(strategy_info['parameters'], indent=2, ensure_ascii=False)}")
    
    print("\n📁 生成的文件:")
    for file_info in generated_files:
        file_path = file_info['path']
        file_type = file_info['type']
        description = file_info.get('description', '')
        
        # Make path relative for display
        rel_path = os.path.relpath(file_path)
        print("  📄 {file_type}: {rel_path}")
        if description:
            print("     {description}")
    
    print("\n🚀 使用说明:")
    print("  1. 设置环境变量:")
    print("     export HYPERLIQUID_API_KEY='你的API密钥'")
    print("     export HYPERLIQUID_ACCOUNT_ADDRESS='你的账户地址'")
    print("  2. 安装依赖:")
    print("     pip install -r {os.path.join(os.path.relpath(generated_files[0]['path']), '../requirements.txt')}")
    print("  3. 运行策略:")
    main_file = next((f for f in generated_files if f['type'] == 'strategy'), None)
    if main_file:
        print("     python {os.path.relpath(main_file['path'])}")
    
    print("\n⚠️  风险提示:")
    print("  • 请在模拟交易中充分测试策略")
    print("  • 使用小资金开始实盘交易")
    print("  • 设置合理的止损和仓位管理")
    print("  • 定期监控策略性能")
    
    print("\n" + "="*60)

def main():
    """Main function."""
    args = parse_arguments()
    
    try:
        # Ensure output directory exists
        output_dir = ensure_output_dir(args.output_dir)
        
        # Generate strategy code
        generated_files, strategy_info = generate_strategy_code(
            prompt=args.prompt,
            output_dir=output_dir,
            strategy_name=args.strategy_name,
            symbol=args.symbol,
            verbose=args.verbose
        )
        
        # Print summary
        print_summary(generated_files, strategy_info)
        
        return 0
        
    except Exception as e:
        sys.stderr.write("❌ Generation failed: {}\n".format(e))
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())