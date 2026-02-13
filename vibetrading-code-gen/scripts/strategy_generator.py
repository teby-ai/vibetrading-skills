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
import uuid
from datetime import datetime
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from scripts directory
from scripts.template_manager import TemplateManager
from scripts.prompt_parser import PromptParser
from scripts.code_formatter import CodeFormatter

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate Hyperliquid trading strategy code from prompts')
    parser.add_argument('prompt', help='Natural language prompt describing the strategy')
    parser.add_argument('--output-dir', '-o', default='sessions',
                       help='Output directory for generated files (default: sessions)')
    parser.add_argument('--session-id', help='Session ID for organizing files (default: auto-generated)')
    parser.add_argument('--strategy-name', '-n', help='Custom strategy name')
    parser.add_argument('--symbol', '-s', help='Trading symbol (overrides auto-detection)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return parser.parse_args()

def ensure_output_dir(output_dir, session_id=None):
    """Ensure output directory exists with session structure."""
    if session_id:
        # Create sessions/{session_id} directory
        session_dir = Path(output_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (session_dir / "strategies").mkdir(exist_ok=True)
        (session_dir / "backtest_results").mkdir(exist_ok=True)
        (session_dir / "logs").mkdir(exist_ok=True)
        (session_dir / "configs").mkdir(exist_ok=True)
        
        return str(session_dir / "strategies")
    else:
        # Legacy behavior
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

def generate_strategy_code(prompt, output_dir, session_id=None, strategy_name=None, symbol=None, verbose=False):
    """Generate strategy code from prompt."""
    
    print(f"🔍 分析策略描述: {prompt}")
    
    # Parse the prompt
    parser = PromptParser()
    strategy_info = parser.parse(prompt)
    
    # Override with command line arguments if provided
    if symbol:
        strategy_info['symbol'] = symbol
    if strategy_name:
        strategy_info['name'] = strategy_name
    
    # Add session info
    if session_id:
        strategy_info['session_id'] = session_id
    
    # Select appropriate template
    template_manager = TemplateManager()
    template = template_manager.select_template(strategy_info)
    
    if verbose:
        print(f"📋 解析结果: {json.dumps(strategy_info, indent=2, ensure_ascii=False)}")
        print(f"📄 选择模板: {template['name']}")
        if session_id:
            print(f"📁 Session ID: {session_id}")
    
    # Generate code
    code_formatter = CodeFormatter()
    generated_files = code_formatter.generate(
        template=template,
        strategy_info=strategy_info,
        output_dir=output_dir,
        session_id=session_id
    )
    
    return generated_files, strategy_info

def print_summary(generated_files, strategy_info, session_id=None):
    """Print generation summary."""
    print("\n" + "="*60)
    print("✅ 策略代码生成完成!")
    print("="*60)
    
    if session_id:
        print(f"📁 Session: {session_id}")
    
    print("\n📊 策略信息:")
    print(f"  名称: {strategy_info.get('name', '未命名策略')}")
    print(f"  类型: {strategy_info.get('type', '未知')}")
    print(f"  交易品种: {strategy_info.get('symbol', '未指定')}")
    
    if 'parameters' in strategy_info:
        print(f"  参数: {json.dumps(strategy_info['parameters'], indent=2, ensure_ascii=False)}")
    
    print("\n📁 生成的文件:")
    for file_info in generated_files:
        file_path = file_info['path']
        file_type = file_info['type']
        description = file_info.get('description', '')
        
        # Make path relative for display
        rel_path = os.path.relpath(file_path)
        print(f"  📄 {file_type}: {rel_path}")
        if description:
            print(f"     {description}")
    
    # Show session directory structure
    if session_id:
        print(f"\n📂 Session目录结构:")
        print(f"  sessions/{session_id}/")
        print(f"  ├── strategies/     # 策略文件")
        print(f"  ├── backtest_results/ # 回测结果")
        print(f"  ├── logs/          # 日志文件")
        print(f"  └── configs/       # 配置文件")
    
    print("\n🚀 使用说明:")
    print("  1. 设置环境变量:")
    print("     export HYPERLIQUID_API_KEY='你的API密钥'")
    print("     export HYPERLIQUID_ACCOUNT_ADDRESS='你的账户地址'")
    print("  2. 安装依赖:")
    main_file = next((f for f in generated_files if f['type'] == 'strategy'), None)
    if main_file:
        req_path = os.path.join(os.path.dirname(main_file['path']), 'requirements.txt')
        print(f"     pip install -r {req_path}")
    print("  3. 运行策略:")
    if main_file:
        print(f"     python {os.path.relpath(main_file['path'])}")
    
    print("\n⚠️  风险提示:")
    print("  • 请在模拟交易中充分测试策略")
    print("  • 使用小资金开始实盘交易")
    print("  • 设置合理的止损和仓位管理")
    print("  • 定期监控策略性能")
    
    print("\n" + "="*60)

def ask_for_backtest(strategy_path, session_id=None):
    """Ask user if they want to run a backtest."""
    print("\n🤔 是否需要运行回测评估策略效果?")
    print("   1. 是 - 运行回测 (推荐)")
    print("   2. 否 - 跳过回测")
    
    try:
        # In a real implementation, this would get user input
        # For now, we'll just show the command
        print(f"\n💡 要运行回测，请使用:")
        print(f"   python scripts/backtest_runner.py {strategy_path}")
        
        if session_id:
            print(f"\n💡 回测结果将保存到:")
            print(f"   sessions/{session_id}/backtest_results/")
        
        print(f"\n💡 示例命令:")
        print(f"   python scripts/backtest_runner.py {strategy_path} \\")
        print(f"     --start-date 2025-01-01 \\")
        print(f"     --end-date 2025-03-01 \\")
        print(f"     --initial-balance 10000 \\")
        print(f"     --interval 1h")
        
        # Return False to indicate we're not running backtest automatically
        return False
        
    except Exception as e:
        print(f"⚠️  回测询问失败: {e}")
        return False

def main():
    """Main function."""
    args = parse_arguments()
    
    try:
        # Check Python version first
        from check_python_version import check_python_version
        if not check_python_version():
            print("\n❌ 请升级Python到3.6或更高版本后再试")
            return 1
        
        # Generate or use session ID
        session_id = args.session_id or str(uuid.uuid4())[:8]
        print(f"📁 Session ID: {session_id}")
        
        # Ensure output directory exists with session structure
        strategies_dir = ensure_output_dir(args.output_dir, session_id)
        
        # Generate strategy code
        generated_files, strategy_info = generate_strategy_code(
            prompt=args.prompt,
            output_dir=strategies_dir,
            session_id=session_id,
            strategy_name=args.strategy_name,
            symbol=args.symbol,
            verbose=args.verbose
        )
        
        # Print summary with session info
        print_summary(generated_files, strategy_info, session_id)
        
        # Ask about backtest
        main_file = next((f for f in generated_files if f['type'] == 'strategy'), None)
        if main_file:
            ask_for_backtest(main_file['path'], session_id)
        
        return 0
        
    except Exception as e:
        sys.stderr.write(f"❌ Generation failed: {e}\n")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())