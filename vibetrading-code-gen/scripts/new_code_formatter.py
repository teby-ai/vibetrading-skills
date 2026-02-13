#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
New Code Formatter - Creates self-contained strategy folders
"""

import os
import re
import json
import shutil
from datetime import datetime
from pathlib import Path

class NewCodeFormatter:
    """Creates self-contained strategy folders with all dependencies."""
    
    def __init__(self):
        """Initialize code formatter."""
        pass
    
    def generate(self, template, strategy_info, base_output_dir, session_id=None):
        """
        Generate complete strategy in a self-contained folder.
        
        Args:
            template: Template dictionary
            strategy_info: Strategy information from prompt parser
            base_output_dir: Base output directory
            session_id: Optional session ID
            
        Returns:
            Dictionary with generated files info
        """
        # Generate strategy name and folder
        strategy_name = self._generate_strategy_name(strategy_info)
        folder_name = strategy_name.lower().replace(' ', '_').replace('-', '_')
        
        # Create strategy folder
        strategy_folder = Path(base_output_dir) / folder_name
        strategy_folder.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (strategy_folder / "backtest_results").mkdir(exist_ok=True)
        (strategy_folder / "logs").mkdir(exist_ok=True)
        (strategy_folder / "configs").mkdir(exist_ok=True)
        
        # Add session info
        if session_id:
            strategy_info['session_id'] = session_id
        
        generated_files = []
        
        # 1. Generate main strategy file
        strategy_file = self._generate_strategy_file(
            template=template,
            strategy_info=strategy_info,
            strategy_folder=strategy_folder,
            strategy_name=strategy_name
        )
        generated_files.append(strategy_file)
        
        # 2. Generate configuration file
        config_file = self._generate_config_file(
            strategy_info=strategy_info,
            strategy_folder=strategy_folder,
            strategy_name=strategy_name
        )
        generated_files.append(config_file)
        
        # 3. Generate requirements file
        requirements_file = self._generate_requirements_file(strategy_folder)
        generated_files.append(requirements_file)
        
        # 4. Generate instructions file
        instructions_file = self._generate_instructions_file(
            strategy_info=strategy_info,
            strategy_folder=strategy_folder,
            strategy_name=strategy_name
        )
        generated_files.append(instructions_file)
        
        # 5. Copy API wrappers
        api_wrappers_copied = self._copy_api_wrappers(strategy_folder)
        if api_wrappers_copied:
            generated_files.append({
                'type': 'api_wrappers',
                'path': str(strategy_folder / "api_wrappers"),
                'description': 'Hyperliquid API wrapper files'
            })
        
        # 6. Create run script
        run_script = self._create_run_script(strategy_folder, strategy_name)
        generated_files.append(run_script)
        
        # 7. Create backtest script
        backtest_script = self._create_backtest_script(strategy_folder, strategy_name)
        generated_files.append(backtest_script)
        
        return {
            'strategy_folder': str(strategy_folder),
            'strategy_name': strategy_name,
            'generated_files': generated_files,
            'session_id': session_id
        }
    
    def _generate_strategy_name(self, strategy_info):
        """Generate strategy name from strategy info."""
        symbol = strategy_info.get('symbol', 'HYPE')
        strategy_type = strategy_info.get('type', 'grid')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{symbol}_{strategy_type}_strategy_{timestamp}"
    
    def _generate_strategy_file(self, template, strategy_info, strategy_folder, strategy_name):
        """Generate main strategy file."""
        # Get template content
        template_content = template['content']
        
        # Replace template variables
        content = self._replace_template_variables(template_content, strategy_info)
        
        # Remove sys.path.insert and fix imports
        content = self._fix_imports(content, strategy_folder)
        
        # Write strategy file
        strategy_file_path = strategy_folder / f"{strategy_name}.py"
        with open(strategy_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            'type': 'strategy',
            'path': str(strategy_file_path),
            'description': 'Main strategy Python file'
        }
    
    def _replace_template_variables(self, content, strategy_info):
        """Replace template variables with actual values."""
        # Replace basic variables
        replacements = {
            '{symbol}': strategy_info.get('symbol', 'HYPE'),
            '{strategy_type}': strategy_info.get('type', 'grid'),
            '{timestamp}': datetime.now().strftime('%Y%m%d_%H%M%S'),
        }
        
        # Add parameter replacements
        params = strategy_info.get('parameters', {})
        if 'price_range' in params:
            replacements['{lower_bound}'] = str(params['price_range'][0])
            replacements['{upper_bound}'] = str(params['price_range'][1])
        
        if 'grid_count' in params:
            replacements['{grid_count}'] = str(params['grid_count'])
        
        if 'grid_size' in params:
            replacements['{grid_size}'] = str(params['grid_size'])
        
        # Apply replacements
        for key, value in replacements.items():
            content = content.replace(key, value)
        
        return content
    
    def _fix_imports(self, content, strategy_folder):
        """Fix imports to use local api_wrappers."""
        # Remove sys.path.insert lines
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'sys.path.insert' in line and 'api_wrappers' in line:
                # Replace with local import
                new_lines.append('# Local API wrappers are in the api_wrappers folder')
            elif 'from hyperliquid_api import' in line or 'import hyperliquid_api' in line:
                # Keep the import - it will work with local api_wrappers folder
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _generate_config_file(self, strategy_info, strategy_folder, strategy_name):
        """Generate configuration file."""
        config = {
            'strategy': {
                'name': strategy_name,
                'type': strategy_info.get('type', 'grid'),
                'symbol': strategy_info.get('symbol', 'HYPE'),
                'generated_at': datetime.now().isoformat()
            },
            'parameters': strategy_info.get('parameters', {}),
            'risk_management': {
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'max_position': 1000.0,
                'max_daily_loss': 0.10
            },
            'execution': {
                'check_interval': 60,
                'order_type': 'limit',
                'slippage': 0.001
            }
        }
        
        # Add session info if available
        if 'session_id' in strategy_info:
            config['session_id'] = strategy_info['session_id']
        
        config_file_path = strategy_folder / "configs" / "strategy_config.json"
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return {
            'type': 'config',
            'path': str(config_file_path),
            'description': 'Strategy configuration file'
        }
    
    def _generate_requirements_file(self, strategy_folder):
        """Generate requirements.txt file."""
        requirements = [
            'requests>=2.28.0',
            'websocket-client>=1.5.0',
            'python-dotenv>=1.0.0',
            'pandas>=1.5.0',
            'numpy>=1.24.0',
            'matplotlib>=3.7.0',
            'scipy>=1.10.0'
        ]
        
        req_file_path = strategy_folder / "requirements.txt"
        with open(req_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        
        return {
            'type': 'requirements',
            'path': str(req_file_path),
            'description': 'Python dependencies'
        }
    
    def _generate_instructions_file(self, strategy_info, strategy_folder, strategy_name):
        """Generate instructions file."""
        symbol = strategy_info.get('symbol', 'HYPE')
        strategy_type = strategy_info.get('type', 'grid')
        
        instructions = f"""# {strategy_name} - 使用说明

## 策略概述
- **交易品种**: {symbol}
- **策略类型**: {strategy_type}交易
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文件夹结构
```
{strategy_name}/
├── {strategy_name}.py      # 主策略文件
├── requirements.txt        # Python依赖
├── run_strategy.py        # 运行脚本
├── run_backtest.py        # 回测脚本
├── api_wrappers/          # API封装库
├── configs/               # 配置文件
├── backtest_results/      # 回测结果
└── logs/                 # 日志文件
```

## 快速开始

### 1. 安装依赖
```bash
cd {strategy_name}
pip install -r requirements.txt
```

### 2. 设置环境变量
```bash
# 创建.env文件或直接设置环境变量
export HYPERLIQUID_API_KEY="your_api_key"
export HYPERLIQUID_ACCOUNT_ADDRESS="your_address"
```

### 3. 运行策略
```bash
# 运行主策略
python run_strategy.py

# 或直接运行
python {strategy_name}.py
```

### 4. 运行回测
```bash
# 运行回测
python run_backtest.py

# 带参数的回测
python run_backtest.py --start-date 2025-01-01 --end-date 2025-03-01
```

## 配置说明

### 策略参数
编辑 `configs/strategy_config.json` 文件调整策略参数。

### 风险控制
- 默认止损: 5%
- 默认止盈: 10%
- 最大仓位: 1000 {symbol}

## 监控与日志
- 日志文件保存在 `logs/` 目录
- 回测结果保存在 `backtest_results/` 目录
- 策略运行时会在控制台输出关键信息

## 注意事项
1. 请在模拟交易中充分测试策略
2. 使用小资金开始实盘交易
3. 定期检查策略性能
4. 加密货币交易具有高风险

## 故障排除
1. API连接问题: 检查环境变量和网络连接
2. 导入错误: 确保已安装所有依赖
3. 交易失败: 检查账户余额和权限

## 联系方式
如有问题，请参考原始生成会话ID: {strategy_info.get('session_id', 'N/A')}
"""
        
        instructions_file_path = strategy_folder / "README.md"
        with open(instructions_file_path, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        return {
            'type': 'instructions',
            'path': str(instructions_file_path),
            'description': 'Strategy instructions and documentation'
        }
    
    def _copy_api_wrappers(self, strategy_folder):
        """Copy API wrappers to strategy folder."""
        source_api_dir = Path(__file__).parent.parent / "api_wrappers"
        target_api_dir = strategy_folder / "api_wrappers"
        
        if source_api_dir.exists():
            # Create target directory
            target_api_dir.mkdir(exist_ok=True)
            
            # Copy all .py files
            for py_file in source_api_dir.glob("*.py"):
                shutil.copy2(py_file, target_api_dir)
            
            # Copy __init__.py if exists
            init_file = source_api_dir / "__init__.py"
            if init_file.exists():
                shutil.copy2(init_file, target_api_dir)
            
            return True
        else:
            # Create minimal API wrapper
            self._create_minimal_api_wrapper(target_api_dir)
            return True
    
    def _create_minimal_api_wrapper(self, target_dir):
        """Create minimal API wrapper if original doesn't exist."""
        target_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_content = """# API Wrappers Package
from .hyperliquid_api import HyperliquidClient

__all__ = ['HyperliquidClient']
"""
        
        with open(target_dir / "__init__.py", 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        # Create hyperliquid_api.py
        api_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
        
        with open(target_dir / "hyperliquid_api.py", 'w', encoding='utf-8') as f:
            f.write(api_content)
    
    def _create_run_script(self, strategy_folder, strategy_name):
        """Create run script."""
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
        
        run_script_path = strategy_folder / "run_strategy.py"
        with open(run_script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable
        run_script_path.chmod(0o755)
        
        return {
            'type': 'run_script',
            'path': str(run_script_path),
            'description': 'Script to run the strategy'
        }
    
    def _create_backtest_script(self, strategy_folder, strategy_name):
        """Create backtest script."""
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
        
        backtest_script_path = strategy_folder / "run_backtest.py"
        with open(backtest_script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable
        backtest_script_path.chmod(0o755)
        
        return {
            'type': 'backtest_script',
            'path': str(backtest_script_path),
            'description': 'Script to run backtests'
        }