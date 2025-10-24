
"""
MCP工具Schema定义
所有工具的输入schema和description
"""

from mcp import types


def get_preprocess_data_schema():
    """preprocess_data工具Schema"""
    return types.Tool(
        name="preprocess_data",
        description="""
[🧹 数据预处理 | 步骤1/6] 从CSV文件加载并清洗股票行情数据

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

这是使用aigroup-quant-mcp服务的第一步，将CSV格式的股票历史数据加载到内存并进行智能清洗。
系统会自动处理缺失值、异常值，并可选择性地将清洗后的数据导出到本地，便于后续深入分析。
为后续的因子计算、模型训练等操作提供高质量的数据基础。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 量化策略回测
  - 因子挖掘研究
  - 机器学习模型训练
  - 历史数据分析

⚠️ 不适合:
  - 实时行情数据（需要流式数据接口）
  - 非结构化数据（仅支持CSV格式）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 数据格式要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CSV文件必须包含以下列（不区分大小写）：
- datetime: 日期时间（格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
- symbol: 股票代码（如: 000001.SZ, 600000.SH）
- open: 开盘价
- high: 最高价
- low: 最低价
- close: 收盘价
- volume: 成交量

可选列：
- vwap: 成交量加权平均价
- amount: 成交额

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 典型工作流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

preprocess_data 👈 当前步骤（自动清洗+导出）
    ↓
generate_alpha158 或 calculate_factor
    ↓
apply_processor_chain (可选，已清洗可跳过)
    ↓
train_lstm_model / train_gru_model / train_transformer_model
    ↓
predict_with_model

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 数据量 < 10万行: 直接加载
- 数据量 10-100万行: 正常，可能需要10-30秒
- 数据量 > 100万行: 考虑分批处理或数据采样

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 1000条数据: < 1秒
- 1万条数据: 1-3秒
- 10万条数据: 5-15秒
- 100万条数据: 30-60秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 文件路径必须是绝对路径或相对于当前工作目录的路径
2. CSV文件编码建议使用UTF-8
3. 数据会完全加载到内存，注意内存使用
4. data_id必须唯一，重复ID会覆盖之前的数据
5. 加载后的数据会自动转换为MultiIndex格式(datetime, symbol)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": """
CSV文件的完整路径

📌 路径格式:
- Windows: "D:/data/stock_data.csv" 或 "D:\\data\\stock_data.csv"
- Linux/Mac: "/home/user/data/stock_data.csv"
- 相对路径: "./data/stock_data.csv" (相对于当前工作目录)

📌 文件要求:
- 必须是CSV格式（.csv扩展名）
- 文件必须存在且可读
- 建议使用UTF-8编码
- 文件大小建议 < 500MB

❌ 常见错误:
- 路径不存在或拼写错误
- 使用了反斜杠但未转义（Windows）
- 文件权限不足
- 文件正在被其他程序占用

💡 最佳实践:
- 使用绝对路径避免路径问题
- 文件名使用英文和数字，避免特殊字符
- 大文件建议先验证格式再加载
""",
                    "examples": [
                        "D:/data/stock_data_2023.csv",
                        "./data/training_set.csv",
                        "/home/user/quant/backtest_data.csv"
                    ]
                },
                "data_id": {
                    "type": "string",
                    "description": """
数据标识ID - 为加载的数据指定一个唯一标识符

📌 命名规则:
- 只能包含字母、数字、下划线、连字符
- 建议使用有意义的名称，便于后续引用
- 区分大小写
- 长度建议 3-50 个字符

📌 命名建议:
- 包含数据类型: stock_data, index_data
- 包含时间范围: data_2023, data_2020_2023
- 包含用途: training_set, test_set, backtest_data
- 组合命名: stock_training_2023

❌ 常见错误:
- 使用特殊字符（如空格、@、#等）
- ID过于简单（如: data, test）
- 重复使用相同ID（会覆盖之前的数据）

💡 最佳实践:
- 使用项目前缀: project1_stock_data
- 包含版本号: data_v1, data_v2
- 使用时间戳: data_20230101
- 描述性命名: hs300_daily_2023

⚠️ 重要提示:
- 此ID将用于后续所有工具调用
- 如果忘记ID，使用 list_factors 工具查看
- 相同ID会覆盖之前加载的数据
""",
                    "examples": [
                        "stock_data_2023",
                        "training_set",
                        "hs300_backtest",
                        "project1_data_v1"
                    ]
                },
                "auto_clean": {
                    "type": "boolean",
                    "default": True,
                    "description": """
是否自动清洗数据（默认开启）

📌 自动清洗流程（参考Qlib标准）:

多股票场景：
1. ProcessInf() - 处理无穷值（用截面均值替换）
2. CSZFillna() - 截面填充缺失值（用截面均值）
3. CSZScoreNorm() - 截面Z-score标准化

单股票场景：
1. ProcessInf() - 处理无穷值
2. CSZFillna() - 填充缺失值

📌 Qlib清洗策略优势:
- ProcessInf: 用同一时间截面的均值替换inf/-inf，避免异常值
- CSZFillna: 用同一时间截面的均值填充NaN，比固定值更合理
- CSZScoreNorm: 在每个时间截面上标准化，消除量纲差异

📌 清洗效果:
- 妥善处理异常值（inf/-inf）
- 智能填充缺失值（截面均值）
- 统一数据量纲（多股票场景）
- 避免数据泄露（仅使用截面信息）
- 提高模型训练效果

💡 使用建议:
- 默认开启，遵循Qlib最佳实践
- 截面均值填充比固定值或前向填充更科学
- 如需自定义清洗流程，可设为false
- 清洗后的数据直接可用于模型训练

⚠️ 注意:
- 设为false时，原始数据可能包含缺失值和异常值
- 原始数据需要手动处理后才能用于模型
- 自动清洗使用Qlib标准流程，经过大量验证
- 单股票数据不进行标准化（截面标准化需要多个股票）
""",
                    "examples": [True, False]
                },
                "export_path": {
                    "type": "string",
                    "description": """
是否导出清洗后的数据到本地文件（可选）

📌 导出说明:
- 如果指定此参数，数据将导出到指定路径
- 如果不指定但开启了auto_clean，数据将自动导出到 ./exports/ 目录
- 导出文件格式为CSV，编码UTF-8
- 自动创建不存在的目录

📌 路径格式:
- 绝对路径: "D:/data/cleaned/stock_data.csv"
- 相对路径: "./exports/cleaned_data.csv"
- 默认路径: "./exports/{data_id}_cleaned_{timestamp}.csv"

📌 导出优势:
- 保存清洗后的数据，便于后续重复使用
- 避免重复清洗，节省计算时间
- 便于数据审查和质量检查
- 支持外部工具（如Excel）进一步分析
- 数据持久化，不依赖内存

💡 使用建议:
- 清洗后的数据建议导出保存
- 大数据集建议指定具体路径避免文件名冲突
- 导出路径建议使用项目相对路径便于管理

⚠️ 注意:
- 导出会覆盖同名文件
- 确保有足够的磁盘空间
- 大文件导出可能需要较长时间
""",
                    "examples": [
                        "./exports/cleaned_stock_data.csv",
                        "D:/data/processed/hs300_cleaned.csv",
                        "./data/train_set_cleaned.csv"
                    ]
                }
            },
            "required": ["file_path", "data_id"],
            "examples": [
                {
                    "name": "预处理2023年股票数据（自动清洗+自动导出）",
                    "description": "加载并清洗完整年度数据，自动导出到默认路径",
                    "input": {
                        "file_path": "D:/data/stock_data_2023.csv",
                        "data_id": "stock_2023",
                        "auto_clean": True
                    },
                    "expected_output": "数据成功预处理并自动清洗导出，返回数据摘要、清洗详情和导出路径"
                },
                {
                    "name": "预处理训练集数据（指定导出路径）",
                    "description": "加载并清洗训练数据，导出到指定位置",
                    "input": {
                        "file_path": "./data/training_set.csv",
                        "data_id": "training_data",
                        "export_path": "./exports/training_cleaned.csv"
                    },
                    "expected_output": "训练数据预处理完成，已清洗并导出到指定路径"
                },
                {
                    "name": "加载原始数据（不清洗不导出）",
                    "description": "仅加载原始数据用于自定义处理",
                    "input": {
                        "file_path": "/home/user/backtest/hs300_2020_2023.csv",
                        "data_id": "hs300_backtest",
                        "auto_clean": False
                    },
                    "expected_output": "原始数据加载完成，保留缺失值和原始数值，未导出"
                },
                {
                    "name": "预处理并导出大数据集",
                    "description": "处理大型数据集并导出以便重复使用",
                    "input": {
                        "file_path": "D:/bigdata/all_stocks_10years.csv",
                        "data_id": "large_dataset",
                        "auto_clean": True,
                        "export_path": "D:/processed/large_dataset_cleaned.csv"
                    },
                    "expected_output": "大数据集预处理完成，清洗后导出，后续可直接使用清洗后文件"
                }
            ]
        }
    )


def get_calculate_factor_schema():
    """calculate_factor工具Schema"""
    return types.Tool(
        name="calculate_factor",
        description="""
[🔬 单因子计算 | 步骤2/6] 计算单个量化因子

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

计算单个技术指标或量化因子，用于股票价格预测和策略构建。
支持动量、波动率、成交量等多种因子类型。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 单因子策略研究
  - 因子有效性验证
  - 技术指标分析
  - 快速原型验证

⚠️ 不适合:
  - 多因子组合（使用generate_alpha158）
  - 复杂因子计算（需要自定义实现）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 支持的因子类型
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- momentum: 动量因子（价格变化趋势）
- volatility: 波动率因子（价格波动程度）
- volume_ratio: 成交量比率因子
- rsi: 相对强弱指数（14日周期）
- macd: 移动平均收敛散度
- bollinger_bands: 布林带指标

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 典型工作流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

load_csv_data
    ↓
calculate_factor 👈 当前步骤
    ↓
evaluate_factor_ic
    ↓
如果IC有效 → 训练模型
    ↓
如果IC无效 → 尝试其他因子

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 数据量 < 10万行: 1-3秒
- 数据量 10-100万行: 5-15秒
- 数据量 > 100万行: 20-60秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 1000条数据: < 1秒
- 1万条数据: 1-3秒
- 10万条数据: 5-10秒
- 100万条数据: 20-40秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 必须先使用load_csv_data加载数据
2. factor_name必须唯一，重复会覆盖
3. period参数影响因子计算窗口
4. 建议先计算少量因子验证有效性
5. 因子计算后会自动存储，可通过list_factors查看

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {
                "data_id": {
                    "type": "string",
                    "description": """
数据标识ID - 指定要计算因子的数据源

📌 要求:
- 必须是已通过load_csv_data加载的数据ID
- 数据必须包含必需的OHLCV列
- 数据量建议 > 100条

❌ 常见错误:
- 数据ID不存在
- 数据格式不正确
- 数据量不足

💡 最佳实践:
- 使用有意义的data_id便于管理
- 确保数据已正确加载
- 使用list_factors查看可用数据
""",
                    "examples": ["stock_data_2023", "training_set", "backtest_data"]
                },
                "factor_name": {
                    "type": "string",
                    "description": """
因子名称 - 为计算的因子指定唯一标识

📌 命名规则:
- 只能包含字母、数字、下划线
- 建议包含因子类型和周期
- 区分大小写
- 长度建议 3-50 个字符

📌 命名建议:
- 包含因子类型: momentum_20, volatility_30
- 包含用途: signal_factor, alpha_factor
- 组合命名: rsi_14_signal, macd_trend

❌ 常见错误:
- 使用特殊字符
- 名称过于简单
- 重复使用相同名称

💡 最佳实践:
- 使用描述性名称
- 包含周期信息
- 便于后续引用
""",
                    "examples": ["momentum_20", "volatility_30", "rsi_14", "macd_signal"]
                },
                "factor_type": {
                    "type": "string",
                    "enum": ["momentum", "volatility", "volume_ratio", "rsi", "macd", "bollinger_bands"],
                    "description": """
因子类型 - 选择要计算的因子类型

📌 可用类型:
- momentum: 动量因子，衡量价格变化趋势
- volatility: 波动率因子，衡量价格波动程度
- volume_ratio: 成交量比率因子
- rsi: 相对强弱指数（14日周期）
- macd: 移动平均收敛散度
- bollinger_bands: 布林带指标

💡 选择建议:
- 趋势跟踪: momentum, macd
- 均值回归: rsi, bollinger_bands
- 波动率策略: volatility
- 成交量策略: volume_ratio
""",
                    "examples": ["momentum", "volatility", "rsi"]
                },
                "period": {
                    "type": "integer",
                    "default": 20,
                    "description": """
计算周期 - 因子计算的时间窗口（单位：天）

📌 周期范围:
- 建议范围: 5-60天
- 短期因子: 5-20天
- 中期因子: 20-40天
- 长期因子: 40-60天

💡 周期选择:
- 动量因子: 20-30天
- 波动率因子: 10-30天
- RSI: 固定14天
- MACD: 固定参数

⚠️ 注意:
- 周期不能超过数据长度
- 周期越大，数据要求越多
""",
                    "examples": [10, 20, 30, 50]
                }
            },
            "required": ["data_id", "factor_name", "factor_type"],
            "examples": [
                {
                    "name": "计算20日动量因子",
                    "description": "计算20日价格动量因子",
                    "input": {
                        "data_id": "stock_data_2023",
                        "factor_name": "momentum_20",
                        "factor_type": "momentum",
                        "period": 20
                    },
                    "expected_output": "动量因子计算完成，返回因子信息和质量评估"
                },
                {
                    "name": "计算30日波动率因子",
                    "description": "计算30日历史波动率",
                    "input": {
                        "data_id": "training_set",
                        "factor_name": "volatility_30",
                        "factor_type": "volatility",
                        "period": 30
                    },
                    "expected_output": "波动率因子计算完成，包含标准差和波动率指标"
                },
                {
                    "name": "计算RSI指标",
                    "description": "计算14日相对强弱指数",
                    "input": {
                        "data_id": "backtest_data",
                        "factor_name": "rsi_14",
                        "factor_type": "rsi"
                    },
                    "expected_output": "RSI指标计算完成，返回0-100范围内的数值"
                }
            ]
        }
    )


def get_generate_alpha158_schema():
    """generate_alpha158工具Schema"""
    return types.Tool(
        name="generate_alpha158",
        description="""
[🔬 因子生成 | 步骤2/6] 生成Alpha158因子集

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

生成完整的Alpha158因子库，包含158个技术因子，
涵盖K线形态、价格特征、成交量特征和滚动统计特征。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 多因子模型构建
  - 机器学习特征工程
  - 深度学习模型训练
  - 因子挖掘研究

⚠️ 不适合:
  - 单因子策略（使用calculate_factor）
  - 实时计算（计算量较大）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 因子分类
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- K线形态因子 (9个): 开盘、最高、最低、收盘相关特征
- 价格特征因子 (5个): 价格变化、收益率等
- 成交量特征因子 (5个): 成交量变化、成交额等
- 滚动统计因子 (139个): 不同窗口期的统计特征

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 典型工作流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

load_csv_data
    ↓
generate_alpha158 👈 当前步骤
    ↓
apply_processor_chain (可选)
    ↓
train_lstm_model / train_gru_model / train_transformer_model
    ↓
predict_with_model

━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 数据量 < 1万行: 10-30秒
- 数据量 1-10万行: 1-5分钟
- 数据量 > 10万行: 5-30分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 1000条数据: 10-30秒
- 1万条数据: 1-3分钟
- 10万条数据: 5-15分钟
- 100万条数据: 30-60分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 数据量建议 > 1000条，否则因子质量可能不佳
2. 滚动窗口越大，需要的数据越多
3. 生成因子会占用较多内存
4. result_id必须唯一，重复会覆盖
5. 建议使用apply_processor_chain进行数据清洗

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {
                "data_id": {
                    "type": "string",
                    "description": """
数据标识ID - 指定要生成因子的数据源

📌 要求:
- 必须是已通过load_csv_data加载的数据ID
- 数据必须包含必需的OHLCV列
- 数据量建议 > 1000条

❌ 常见错误:
- 数据ID不存在
- 数据格式不正确
- 数据量不足

💡 最佳实践:
- 确保数据已正确加载
- 数据量越大，因子质量越好
- 使用list_factors查看可用数据
""",
                    "examples": ["stock_data_2023", "training_set", "backtest_data"]
                },
                "result_id": {
                    "type": "string",
                    "description": """
结果标识ID - 为生成的Alpha158因子指定唯一标识

📌 命名规则:
- 只能包含字母、数字、下划线
- 建议包含数据类型和用途
- 区分大小写
- 长度建议 3-50 个字符

📌 命名建议:
- 包含数据类型: alpha158_stock, alpha158_index
- 包含用途: alpha158_training, alpha158_test
- 组合命名: alpha158_hs300_2023

❌ 常见错误:
- 使用特殊字符
- 名称过于简单
- 重复使用相同名称

💡 最佳实践:
- 使用描述性名称
- 便于后续引用
- 避免与data_id重复
""",
                    "examples": ["alpha158_stock", "alpha158_training", "alpha158_hs300"]
                },
                "kbar": {
                    "type": "boolean",
                    "default": True,
                    "description": """
是否生成K线形态因子

📌 包含9个因子:
- 开盘价相关特征
- 最高价相关特征
- 最低价相关特征
- 收盘价相关特征

💡 建议:
- 通常建议开启
- 对价格预测很重要
- 占用计算资源较少
""",
                    "examples": [True, False]
                },
                "price": {
                    "type": "boolean",
                    "default": True,
                    "description": """
是否生成价格特征因子

📌 包含5个因子:
- 价格变化特征
- 收益率特征
- 价格动量特征

💡 建议:
- 通常建议开启
- 核心价格特征
- 对趋势预测重要
""",
                    "examples": [True, False]
                },
                "volume": {
                    "type": "boolean",
                    "default": True,
                    "description": """
是否生成成交量特征因子

📌 包含5个因子:
- 成交量变化特征
- 成交额特征
- 量价关系特征

💡 建议:
- 通常建议开启
- 对波动率预测重要
- 提供流动性信息
""",
                    "examples": [True, False]
                },
                "rolling": {
                    "type": "boolean",
                    "default": True,
                    "description": """
是否生成滚动统计因子

📌 包含139个因子:
- 不同窗口期的统计特征
- 移动平均、标准差等
- 技术指标衍生

💡 建议:
- 通常建议开启
- 提供时间序列特征
- 计算量较大
""",
                    "examples": [True, False]
                },
                "rolling_windows": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "default": [5, 10, 20, 30, 60],
                    "description": """
滚动窗口大小列表（单位：天）

📌 窗口范围:
- 建议范围: 5-60天
- 短期窗口: 5-10天
- 中期窗口: 20-30天
- 长期窗口: 40-60天

💡 窗口选择:
- 数据量少时使用较小窗口
- 数据量多时可使用较大窗口
- 建议包含多个时间尺度

⚠️ 注意:
- 窗口越大，需要的数据越多
- 窗口数量影响计算时间
""",
                    "examples": [
                        [5, 10, 20],
                        [5, 10, 20, 30, 60],
                        [10, 20, 30, 50]
                    ]
                }
            },
            "required": ["data_id", "result_id"],
            "examples": [
                {
                    "name": "生成完整Alpha158因子",
                    "description": "生成包含所有158个因子的完整特征集",
                    "input": {
                        "data_id": "stock_data_2023",
                        "result_id": "alpha158_full",
                        "kbar": True,
                        "price": True,
                        "volume": True,
                        "rolling": True,
                        "rolling_windows": [5, 10, 20, 30, 60]
                    },
                    "expected_output": "Alpha158因子生成完成，返回因子数量、质量评估和后续步骤"
                },
                {
                    "name": "生成精简Alpha158因子",
                    "description": "只生成核心因子，减少计算量",
                    "input": {
                        "data_id": "training_set",
                        "result_id": "alpha158_lite",
                        "kbar": True,
                        "price": True,
                        "volume": False,
                        "rolling": True,
                        "rolling_windows": [10, 20, 30]
                    },
                    "expected_output": "精简版Alpha158因子生成完成，包含核心特征"
                },
                {
                    "name": "生成基础因子",
                    "description": "只生成基础K线和价格因子",
                    "input": {
                        "data_id": "backtest_data",
                        "result_id": "alpha158_basic",
                        "kbar": True,
                        "price": True,
                        "volume": False,
                        "rolling": False
                    },
                    "expected_output": "基础Alpha158因子生成完成，包含19个核心因子"
                }
            ]
        }
    )


def get_evaluate_factor_ic_schema():
    """evaluate_factor_ic工具Schema"""
    return types.Tool(
        name="evaluate_factor_ic",
        description="""
[📊 因子评估 | 步骤3/6] 评估因子IC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

评估因子的信息系数（Information Coefficient），
衡量因子对未来收益率的预测能力。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 因子有效性验证
  - 因子筛选
  - 策略优化
  - 模型特征选择

⚠️ 不适合:
  - 实时评估（需要历史数据）
  - 非数值型因子

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 IC指标说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- IC均值: 因子与未来收益的相关性均值
- IC标准差: 因子稳定性的衡量
- ICIR: 信息比率（IC均值/IC标准差）
- 因子质量评级: 基于IC的因子有效性评估

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 典型工作流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

load_csv_data
    ↓
calculate_factor 或 generate_alpha158
    ↓
evaluate_factor_ic 👈 当前步骤
    ↓
如果IC有效 → 训练模型
    ↓
如果IC无效 → 尝试其他因子

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 数据量 < 10万行: 1-5秒
- 数据量 10-100万行: 5-20秒
- 数据量 > 100万行: 20-60秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 1000条数据: < 1秒
- 1万条数据: 1-3秒
- 10万条数据: 5-10秒
- 100万条数据: 20-40秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 因子和价格数据的时间范围必须匹配
2. 数据量建议 > 100条，否则IC不稳定
3. IC绝对值 > 0.03通常认为有效
4. ICIR > 0.5通常认为稳定
5. 建议使用spearman方法（对异常值更稳健）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {
                "factor_name": {
                    "type": "string",
                    "description": """
因子名称 - 指定要评估的因子

📌 要求:
- 必须是已通过calculate_factor或generate_alpha158生成的因子
- 因子数据必须为数值型
- 因子数据不能全为NaN

❌ 常见错误:
- 因子名称不存在
- 因子数据格式不正确
- 因子数据全为NaN

💡 最佳实践:
- 使用有意义的因子名称
- 确保因子已正确生成
- 使用list_factors查看可用因子
""",
                    "examples": ["momentum_20", "alpha158_stock", "volatility_30"]
                },
                "data_id": {
                    "type": "string",
                    "description": """
数据标识ID - 指定价格数据源

📌 要求:
- 必须是已通过load_csv_data加载的数据ID
- 数据必须包含close列
- 数据时间范围与因子匹配

❌ 常见错误:
- 数据ID不存在
- 数据缺少close列
- 时间范围不匹配

💡 最佳实践:
- 使用与因子相同的数据源
- 确保数据包含价格信息
- 时间范围要覆盖因子计算期
""",
                    "examples": ["stock_data_2023", "training_set", "backtest_data"]
                },
                "method": {
                    "type": "string",
                    "enum": ["spearman", "pearson"],
                    "default": "spearman",
                    "description": """
IC计算方法

📌 方法说明:
- spearman: 斯皮尔曼秩相关系数（推荐）
  - 对异常值不敏感
  - 适用于非线性关系
  - 更稳健
- pearson: 皮尔逊相关系数
  - 假设线性关系
  - 对异常值敏感
  - 计算更快

💡 选择建议:
- 通常建议使用spearman
- 如果确定线性关系可使用pearson
- spearman更稳健，推荐使用
""",
                    "examples": ["spearman", "pearson"]
                }
            },
            "required": ["factor_name", "data_id"],
            "examples": [
                {
                    "name": "评估动量因子IC",
                    "description": "评估20日动量因子的预测能力",
                    "input": {
                        "factor_name": "momentum_20",
                        "data_id": "stock_data_2023",
                        "method": "spearman"
                    },
                    "expected_output": "IC评估完成，返回IC均值、ICIR、因子质量评级和后续建议"
                },
                {
                    "name": "评估Alpha158因子IC",
                    "description": "评估Alpha158因子集的整体有效性",
                    "input": {
                        "factor_name": "alpha158_stock",
                        "data_id": "training_set",
                        "method": "spearman"
                    },
                    "expected_output": "Alpha158因子IC评估完成，返回综合IC指标和因子质量分析"
                },
                {
                    "name": "评估波动率因子IC",
                    "description": "评估30日波动率因子的预测能力",
                    "input": {
                        "factor_name": "volatility_30",
                        "data_id": "backtest_data",
                        "method": "pearson"
                    },
                    "expected_output": "波动率因子IC评估完成，返回IC指标和稳定性分析"
                }
            ]
        }
    )


def get_list_factors_schema():
    """list_factors工具Schema"""
    return types.Tool(
        name="list_factors",
        description="""
[📋 状态查询 | 辅助工具] 列出所有已加载的数据和因子

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

查看当前内存中所有已加载的数据和因子，
便于管理和引用。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 查看当前工作状态
  - 查找可用的数据和因子
  - 管理内存中的对象
  - 调试和问题排查

⚠️ 不适合:
  - 数据持久化存储
  - 大量历史数据查询

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 返回信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 数据数量和数据ID列表
- 因子数量和因子信息
- 每个因子的类型和形状
- 内存使用情况概览

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 典型工作流
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在任何步骤中都可使用此工具查看当前状态

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 性能建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 瞬时完成，无性能影响

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- < 100毫秒

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 注意事项
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 只显示当前内存中的数据
2. 重启服务后数据会丢失
3. 数据量过大时建议及时清理
4. 可用于检查数据是否正确加载

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {},
            "examples": [
                {
                    "name": "查看当前状态",
                    "description": "查看所有已加载的数据和因子",
                    "input": {},
                    "expected_output": "返回数据数量、因子数量、详细列表和内存使用情况"
                }
            ]
        }
    )


def get_quick_start_lstm_schema():
    """quick_start_lstm工具Schema"""
    return types.Tool(
        name="quick_start_lstm",
        description="""
[🚀 快捷工具] 一键完成LSTM工作流 - 从数据加载到模型训练的自动化流程

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 功能概述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

自动执行完整的LSTM建模流程，包括：
1. 数据加载
2. Alpha158因子生成
3. 数据预处理（标准化）
4. LSTM模型训练

节省时间：从手动4-6步 → 自动1步完成

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 适用场景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 适合:
  - 快速原型验证
  - 标准化工作流程
  - 新手入门学习
  - 批量实验

⚠️ 不适合:
  - 需要自定义因子配置
  - 需要特殊的数据预处理
  - 需要精细调参

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 自动化流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: load_csv_data
  ↓
Step 2: generate_alpha158
  ↓
Step 3: apply_processor (CSZScoreNorm)
  ↓
Step 4: train_lstm_model 👈 全自动
  ↓
完成！返回综合结果

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 预计耗时
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

取决于数据量:
- 1000条: 约1-2分钟
- 10000条: 约5-10分钟
- 100000条: 约30-60分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        inputSchema={
            "type": "object",
            "properties": {
                "data_file": {
                    "type": "string",
                    "description": "CSV数据文件路径",
                    "examples": ["./data/stock_data.csv", "D:/data/hs300_2023.csv"]
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称，用于生成所有ID的前缀",
                    "examples": ["my_project", "hs300_test", "strategy_v1"]
                },
                "model_config": {
                    "type": "object",
                    "description": "LSTM模型配置(可选)",
                    "properties": {
                        "hidden_size": {"type": "integer", "default": 64},
                        "num_layers": {"type": "integer", "default": 2},
                        "n_epochs": {"type": "integer", "default": 50},
                        "batch_size": {"type": "integer", "default": 800},
                        "lr": {"type": "number", "default": 0.001}
                    }
                }
            },
            "required": ["data_file", "project_name"],
            "examples": [
                {
                    "name": "标准LSTM工作流",
                    "description": "使用默认配置快速构建LSTM模型",
                    "input": {
                        "data_file": "./data/stock_data_2023.csv",
                        "project_name": "my_lstm_project"
                    },
                    "expected_output": "自动完成数据加载→因子生成→预处理→模型训练"
                },
                {
                    "name": "自定义模型参数",
                    "description": "使用自定义LSTM参数",
                    "input": {
                        "data_file": "D:/data/hs300.csv",
                        "project_name": "hs300_lstm",
                        "model_config": {
                            "hidden_size": 128,
                            "n_epochs": 100
                        }
                    },
                    "expected_output": "使用128隐藏层、100轮训练的LSTM模型"
                }
            ]
        }
    )


def get_all_tool_schemas():
    """获取所有工具Schema"""
    return [
        get_preprocess_data_schema(),
        get_calculate_factor_schema(),
        get_generate_alpha158_schema(),
        get_evaluate_factor_ic_schema(),
        get_list_factors_schema(),
        get_quick_start_lstm_schema(),
    ]