# aigroup-quant-mcp - Roo-Code量化分析MCP服务

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v1.0.24-blue.svg)](https://pypi.org/project/aigroup-quant-mcp/)

> 🎯 **专为Roo-Code设计的MCP量化分析服务** - 提供LightGBM/XGBoost/sklearn机器学习建模，无需torch依赖

---

## 🚀 快速开始（Roo-Code用户）

### 一键启动MCP服务

```bash
# 使用uvx快速启动（推荐，无需安装）
uvx aigroup-quant-mcp
```

**就这么简单！** MCP服务会自动：
- ✅ 下载最新版本
- ✅ 配置轻量级依赖（仅~50MB）
- ✅ 启动并连接到Roo-Code
- ✅ 提供7个专业量化工具

### 配置Roo-Code

MCP服务已自动配置在Roo-Code中，您可以直接使用以下工具：

| 工具 | 功能 | 用途 |
|-----|------|------|
| `preprocess_data` | 数据预处理 | 加载CSV数据并自动清洗 |
| `generate_alpha158` | Alpha158因子生成 | 生成158个技术指标因子 |
| `calculate_factor` | 单因子计算 | 计算动量、波动率等6种基础因子 |
| `evaluate_factor_ic` | 因子评估 | 评估因子IC并生成报告 |
| `apply_processor_chain` | 数据标准化 | 智能标准化处理（单商品/多商品自动适配） |
| `train_ml_model` | 机器学习训练 | 训练LightGBM/XGBoost/sklearn模型 |
| `predict_ml_model` | 模型预测 | 使用训练好的模型进行预测 |
| `list_factors` | 查看因子 | 列出所有已加载的数据和因子 |

---

## 🎯 典型工作流程

### 场景1：快速因子分析

```json
// 1. 预处理数据
{
  "tool": "preprocess_data",
  "params": {
    "file_path": "./data/stock_data.csv",
    "data_id": "my_stock_data"
  }
}

// 2. 生成Alpha158因子
{
  "tool": "generate_alpha158",
  "params": {
    "data_id": "my_stock_data",
    "result_id": "alpha158_factors"
  }
}

// 3. 评估因子并生成报告
{
  "tool": "evaluate_factor_ic",
  "params": {
    "factor_name": "alpha158_factors",
    "data_id": "my_stock_data",
    "method": "spearman",
    "report_path": "./reports/factor_evaluation.md"
  }
}
```

### 场景2：机器学习建模（推荐）

```json
// 1. 预处理数据
{
  "tool": "preprocess_data",
  "params": {
    "file_path": "./data/stock_data.csv",
    "data_id": "my_stock_data"
  }
}

// 2. 生成Alpha158因子
{
  "tool": "generate_alpha158",
  "params": {
    "data_id": "my_stock_data",
    "result_id": "alpha158_factors"
  }
}

// 3. 数据标准化
{
  "tool": "apply_processor_chain",
  "params": {
    "data_id": "alpha158_factors",
    "result_id": "alpha158_normalized",
    "processors": [{"name": "CSZScoreNorm"}]
  }
}

// 4. 训练LightGBM模型
{
  "tool": "train_ml_model",
  "params": {
    "data_id": "my_stock_data",
    "model_id": "lgb_model_v1",
    "model_type": "lightgbm",
    "train_start": "2023-01-01",
    "train_end": "2023-06-30",
    "test_start": "2023-07-01",
    "test_end": "2023-12-31"
  }
}

// 5. 模型预测
{
  "tool": "predict_ml_model",
  "params": {
    "model_id": "lgb_model_v1",
    "data_id": "alpha158_normalized",
    "export_path": "./exports/predictions.csv"
  }
}
```

**机器学习优势**：
- ✅ 无需安装torch（更轻量）
- ✅ 训练速度更快
- ✅ 模型可解释性强
- ✅ 自动特征重要性分析

---

## 📦 安装方式

### 方式1：uvx（推荐，无需安装）

```bash
# 直接运行最新版本
uvx aigroup-quant-mcp

# 或指定版本
uvx aigroup-quant-mcp@1.0.17
```

**优点**：
- ⚡ 快速启动（几秒钟）
- 🔄 自动获取最新版本
- 💾 无需本地安装
- 🎯 轻量级依赖（~50MB）

### 方式2：pip安装

```bash
# 基础安装（包含机器学习功能，无torch）
pip install aigroup-quant-mcp

# 完整安装（包含深度学习）
pip install aigroup-quant-mcp[full]

# 或只安装深度学习依赖
pip install aigroup-quant-mcp[dl]

# 运行
aigroup-quant-mcp
```

### 依赖说明

- **核心依赖**（默认）：pandas, numpy, scipy, mcp, lightgbm, xgboost, scikit-learn
- `[dl]`：torch（深度学习，需要时再装）
- `[full]`：所有功能（适合完整开发）

**💡 推荐**：直接使用基础安装，包含所有机器学习功能，无需额外安装torch！

---

## ✨ 核心特性

### 1️⃣ 智能数据预处理

- ✅ **自动清洗**：自动处理缺失值和异常值
- ✅ **智能导出**：清洗后数据自动保存
- ✅ **质量评估**：自动生成数据质量报告

### 2️⃣ Alpha158因子库

- 📊 **158个技术指标**：Qlib级专业因子库
- 🎯 **分类清晰**：K线(9) + 价格(5) + 成交量(5) + 滚动统计(139)
- 🔧 **灵活配置**：支持自定义窗口和因子组合
- 💾 **导出支持**：可导出CSV/JSON便于查看

### 3️⃣ 因子评估

- 📈 **IC分析**：Spearman/Pearson相关性分析
- 📊 **ICIR计算**：信息比率评估因子稳定性
- 📝 **报告生成**：自动生成Markdown评估报告
- 🎯 **质量评级**：智能评估因子有效性

### 4️⃣ 智能标准化

- 🤖 **自动识别**：单商品/多商品自动适配
- 🔄 **智能切换**：CSZScoreNorm自动优化
- ✅ **避免NaN**：单商品自动使用ZScoreNorm
- 📊 **透明化**：明确告知调整原因

### 5️⃣ 机器学习建模

- 🤖 **三模型支持**：LightGBM/XGBoost/sklearn
- ⚡ **无需torch**：轻量级机器学习解决方案
- 📊 **完整评估**：MSE/MAE/R²/IC等指标
- 🎯 **特征分析**：自动特征重要性分析
- 🔮 **批量预测**：支持导出预测结果

---

## 📋 工具详细说明

### preprocess_data

加载CSV数据并自动清洗

**参数**：
- `file_path`：CSV文件路径
- `data_id`：数据唯一标识
- `auto_clean`：是否自动清洗（默认true）
- `export_path`：导出路径（可选）

**返回**：
- 数据摘要（行数、列数、日期范围）
- 数据质量评估
- 清洗详情
- 导出信息

### generate_alpha158

生成Alpha158因子集

**参数**：
- `data_id`：数据源ID
- `result_id`：结果ID
- `kbar`：是否生成K线因子（默认true）
- `price`：是否生成价格因子（默认true）
- `volume`：是否生成成交量因子（默认true）
- `rolling`：是否生成滚动统计因子（默认true）
- `rolling_windows`：窗口大小列表
- `export_path`：导出路径（可选）

**返回**：
- 因子数量和分类统计
- 数据质量评估
- 导出信息

### evaluate_factor_ic

评估因子IC并生成报告

**参数**：
- `factor_name`：因子名称
- `data_id`：数据源ID
- `method`：计算方法（spearman/pearson）
- `report_path`：报告保存路径（可选，新增于v1.0.16）

**返回**：
- IC指标（IC均值、IC标准差、ICIR、IC正值占比）
- 因子质量评级
- 预测方向和预测能力分析
- 使用建议

**新增功能（v1.0.16）**：
- ✨ 自动生成Markdown格式评估报告
- 📊 包含详细的指标解读
- 💡 提供后续步骤指引

### apply_processor_chain

智能数据标准化

**参数**：
- `data_id`：数据源ID
- `result_id`：结果ID
- `processors`：处理器配置列表

**特点**：
- 🤖 自动识别单商品/多商品
- 🔄 CSZScoreNorm自动优化
- ✅ 避免单商品100% NaN问题

**推荐用法**：
```json
{
  "processors": [
    {"name": "CSZScoreNorm"}
  ]
}
```
系统会自动判断并选择最佳标准化方法。

### list_factors

列出所有已加载的数据和因子

**参数**：无

**返回**：
- 数据列表
- 因子列表
- 每个因子的类型和形状

### train_ml_model

训练机器学习模型

**参数**：
- `data_id`：数据源ID（必须包含close列）
- `model_id`：模型唯一标识
- `model_type`：模型类型（lightgbm/xgboost/linear）
- `train_start`：训练开始日期
- `train_end`：训练结束日期
- `test_start`：测试开始日期
- `test_end`：测试结束日期
- `params`：模型参数（可选）

**返回**：
- 训练和测试性能指标（MSE/MAE/R²/IC）
- 特征重要性分析
- 模型质量评估

### predict_ml_model

使用训练好的模型进行预测

**参数**：
- `model_id`：模型ID
- `data_id`：预测数据ID
- `export_path`：导出路径（可选）

**返回**：
- 预测结果统计
- 预测值预览
- 导出信息（如果指定）

---

## 🆕 版本更新

### v1.0.24 (2025-01-25) - 机器学习时代

✨ **新增机器学习建模功能**
- 新增LightGBM模型支持（推荐）
- 新增XGBoost模型支持
- 新增sklearn线性回归模型
- 新增train_ml_model训练工具
- 新增predict_ml_model预测工具

🔧 **架构优化**
- 移除torch作为必需依赖
- 机器学习库移至核心依赖
- 更轻量级的基础安装
- 保持向后兼容性

📊 **增强功能**
- 完整的模型评估指标（MSE/MAE/R²/IC）
- 自动特征重要性分析
- 批量预测和结果导出
- 详细的模型性能报告

### v1.0.17 (2024-10-24) - 性能优化

⚡ **解决uvx安装卡住问题**
- 将torch等重量级依赖移到可选依赖
- 基础安装仅需~50MB（原2GB）
- uvx启动从几分钟降至几秒

### v1.0.16 (2024-10-24) - Bug修复与功能增强

🐛 **Critical Bug Fix**
- 修复evaluate_factor_ic返回NoneType错误
- 函数定义与实现分离问题已解决

✨ **新增功能**
- 因子评估报告生成（Markdown格式）
- 支持report_path参数

### v1.0.15 及更早版本

查看 [CHANGELOG.md](CHANGELOG.md) 了解完整更新历史。

---

## 📚 高级使用（Python API）

如果您需要在Python脚本中使用，可以直接导入：

```python
from quantanalyzer.data import DataLoader
from quantanalyzer.factor import Alpha158Generator, FactorEvaluator

# 加载数据
loader = DataLoader()
data = loader.load_from_csv("stock_data.csv")

# 生成因子
generator = Alpha158Generator(data)
factors = generator.generate_all(rolling_windows=[5, 10, 20])

# 评估因子
returns = data['close'].groupby(level=1).pct_change().shift(-1)
evaluator = FactorEvaluator(factors, returns)
ic_metrics = evaluator.calculate_ic(method='spearman')

print(f"IC均值: {ic_metrics['ic_mean']:.4f}")
print(f"ICIR: {ic_metrics['icir']:.4f}")
```

更多Python API示例请查看 [examples/](examples/) 目录。

---

## 📂 项目结构

```
aigroup-quant-mcp/
├── quantanalyzer/              # 核心包
│   ├── mcp/                    # MCP服务
│   │   ├── server.py          # MCP服务器
│   │   ├── handlers.py        # 工具处理函数
│   │   ├── schemas.py         # 工具Schema定义
│   │   └── ...
│   ├── data/                   # 数据层
│   ├── factor/                 # 因子层
│   │   ├── alpha158.py        # Alpha158因子
│   │   ├── evaluator.py       # 因子评估
│   │   └── library.py         # 基础因子
│   ├── model/                  # 模型层
│   └── backtest/               # 回测层
├── examples/                   # 示例脚本
├── exports/                    # 导出数据目录
├── reports/                    # 评估报告目录
├── pyproject.toml             # 项目配置
├── CHANGELOG.md               # 更新日志
└── README.md                  # 本文档
```

---

## 🔧 故障排除

### uvx安装卡住

**问题**：`uvx aigroup-quant-mcp` 卡住不动

**解决**：
1. 确保使用v1.0.17或更高版本
2. 检查网络连接
3. 尝试清除缓存：`uvx --no-cache aigroup-quant-mcp`

### 因子评估返回错误

**问题**：evaluate_factor_ic返回NoneType

**解决**：
1. 升级到v1.0.16或更高版本
2. 确保因子已正确生成
3. 使用list_factors查看可用因子

### 单商品数据标准化后全是NaN

**问题**：使用CSZScoreNorm后数据全是NaN

**解决**：
1. 升级到v1.0.14或更高版本
2. 系统会自动切换为ZScoreNorm
3. 或手动使用ZScoreNorm处理器

### 机器学习模型训练失败

**问题**：train_ml_model返回错误

**解决**：
1. 确保数据包含close列用于生成标签
2. 检查时间范围参数是否正确
3. 确认数据格式与训练时一致
4. 查看详细错误信息和建议

### 模型预测结果异常

**问题**：predict_ml_model返回异常值

**解决**：
1. 确保预测数据特征与训练时一致
2. 检查数据是否正确标准化
3. 确认模型已正确训练
4. 查看模型评估指标判断质量

---

## 📖 文档

- [CHANGELOG.md](CHANGELOG.md) - 完整更新日志
- [RELEASE_v1.0.24.md](RELEASE_v1.0.24.md) - v1.0.24发布说明
- [docs/ML_MODELS_GUIDE.md](docs/ML_MODELS_GUIDE.md) - 机器学习模型使用指南
- [QLIB_WORKFLOW_GUIDE.md](QLIB_WORKFLOW_GUIDE.md) - Qlib工作流程指南
- [examples/](examples/) - 示例代码

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 开启Pull Request

---

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 了解详情

---

## 🙏 鸣谢

- [Qlib](https://github.com/microsoft/qlib) - 量化分析框架
- [MCP](https://modelcontextprotocol.io/) - 模型上下文协议
- [Roo-Code](https://roo.cline.bot/) - AI编程助手

---

## 📞 支持

- 💬 提交 [GitHub Issue](https://github.com/yourusername/aigroup-quant-mcp/issues)
- 📧 邮件：ai.group@example.com
- 📚 文档：查看项目文档和示例

---

**立即开始**: `uvx aigroup-quant-mcp` 🚀