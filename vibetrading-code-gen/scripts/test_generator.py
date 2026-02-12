#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for VibeTrading Code Generator
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prompt_parser import PromptParser
from template_manager import TemplateManager
from code_formatter import CodeFormatter

def test_prompt_parser():
    """Test prompt parser with various inputs."""
    print("🧪 测试Prompt解析器...")
    
    parser = PromptParser()
    
    test_prompts = [
        "生成HYPE的网格策略",
        "生成一个BTC的网格交易策略，价格区间50000-60000，10个网格，每个网格0.01 BTC",
        "ETH的RSI策略，低于30买入，高于70卖出",
        "基于VibeTrading信号的SOL交易策略"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 测试Prompt: {prompt}")
        result = parser.parse(prompt)
        
        print(f"  解析结果:")
        print(f"    策略类型: {result.get('type')}")
        print(f"    交易品种: {result.get('symbol')}")
        print(f"    参数数量: {len(result.get('parameters', {}))}")
        
        if result.get('parameters'):
            print(f"    参数: {result.get('parameters')}")

def test_template_manager():
    """Test template manager."""
    print("\n🧪 测试模板管理器...")
    
    manager = TemplateManager()
    
    # List available templates
    templates = manager.list_templates()
    print(f"找到 {sum(len(t) for t in templates.values())} 个模板:")
    
    for category, template_list in templates.items():
        print(f"\n  📁 {category}:")
        for template in template_list:
            print(f"    • {template['name']}: {template['description']}")

def test_code_generation():
    """Test complete code generation."""
    print("\n🧪 测试代码生成...")
    
    # Test prompt
    prompt = "生成HYPE的网格策略"
    
    # Parse prompt
    parser = PromptParser()
    strategy_info = parser.parse(prompt)
    
    print(f"📝 解析Prompt: {prompt}")
    print(f"  策略类型: {strategy_info.get('type')}")
    print(f"  交易品种: {strategy_info.get('symbol')}")
    
    # Select template
    manager = TemplateManager()
    template = manager.select_template(strategy_info)
    
    print(f"📄 选择模板: {template.get('name')}")
    
    # Generate code
    formatter = CodeFormatter()
    
    # Create test output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    generated_files = formatter.generate(
        template=template,
        strategy_info=strategy_info,
        output_dir=str(output_dir)
    )
    
    print(f"✅ 生成 {len(generated_files)} 个文件:")
    for file_info in generated_files:
        print(f"  📄 {file_info['type']}: {file_info['path']}")

def main():
    """Main test function."""
    print("🚀 VibeTrading Code Generator 测试")
    print("=" * 50)
    
    try:
        # Test prompt parser
        test_prompt_parser()
        
        # Test template manager
        test_template_manager()
        
        # Test code generation
        test_code_generation()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成!")
        
        # Show generated files
        test_dir = Path("test_output")
        if test_dir.exists():
            print(f"\n📁 生成的测试文件在: {test_dir.absolute()}")
            for file in test_dir.glob("*"):
                print(f"  • {file.name}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())