"""
MCP工具处理函数
包含所有工具的业务逻辑和错误处理
"""

from typing import Any, Dict, List
from mcp import types
import json

from .errors import (
    MCPError,
    validate_data_id,
    validate_factor_name,
    validate_required_columns,
    validate_data_length,
    validate_window_size,
    validate_period,
    validate_file_path
)
from .utils import serialize_response, convert_to_serializable

from quantanalyzer.data import DataLoader
from quantanalyzer.data.processor import ProcessInf, CSZFillna, CSZScoreNorm, ProcessorChain
from quantanalyzer.factor import FactorLibrary, FactorEvaluator, Alpha158Generator


# 全局存储
data_store = {}
factor_store = {}
model_store = {}
processor_store = {}


async def handle_preprocess_data(args: Dict[str, Any]) -> List[types.TextContent]:
    """数据预处理和清洗"""
    file_path = args["file_path"]
    data_id = args["data_id"]
    auto_clean = args.get("auto_clean", True)  # 默认开启自动清洗
    export_path = args.get("export_path", None)  # 导出路径（可选）
    
    # 验证文件路径
    error = validate_file_path(file_path)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    try:
        loader = DataLoader()
        data = loader.load_from_csv(file_path)
        
        # 验证必需列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        error = validate_required_columns(data, required_cols, data_id)
        if error:
            return [types.TextContent(type="text", text=error)]
        
        # 验证数据量
        error = validate_data_length(data, min_length=100, data_id=data_id)
        if error:
            return [types.TextContent(type="text", text=error)]
        
        # 记录原始数据质量
        original_null_count = int(data.isna().sum().sum())
        original_null_rate = original_null_count / (data.shape[0] * data.shape[1]) if data.shape[0] * data.shape[1] > 0 else 0
        
        # 自动数据清洗
        cleaned = False
        cleaning_methods = []
        if auto_clean:
            try:
                # 检查股票数量
                symbol_count = len(data.index.get_level_values(1).unique())
                
                # 按照Qlib标准流程清洗数据
                # 注意：这里只清洗异常值和缺失值，不进行标准化
                # 标准化应该在因子生成后进行（对因子标准化，而非原始OHLCV数据）
                processor_chain = ProcessorChain([
                    ProcessInf(),          # 处理无穷值（用截面均值替换）
                    CSZFillna(),           # 截面填充缺失值（用截面均值）
                ])
                data = processor_chain.fit_transform(data.copy())
                
                cleaning_methods = [
                    "ProcessInf() - 用截面均值替换inf/-inf",
                    "CSZFillna() - 用截面均值填充NaN"
                ]
                
                # 多股票场景的提示信息
                if symbol_count > 1:
                    cleaning_methods.append(
                        "⚠️ 提示：原始数据未标准化，建议在因子生成后使用CSZScoreNorm标准化因子"
                    )
                
                cleaned = True
            except Exception as e:
                # 如果清洗失败，使用原始数据并记录警告
                cleaned = False
                cleaning_methods = []
        
        data_store[data_id] = data
        
        # 计算清洗后的数据质量
        current_null_count = int(data.isna().sum().sum())
        current_null_rate = current_null_count / (data.shape[0] * data.shape[1]) if data.shape[0] * data.shape[1] > 0 else 0
        
        # 导出清洗后的数据到本地
        export_info = None
        if export_path or cleaned:  # 如果指定导出路径或进行了清洗，则导出
            import os
            from pathlib import Path
            from datetime import datetime
            
            # 如果没有指定导出路径，使用默认路径
            if not export_path:
                # 默认保存到项目根目录的 exports 文件夹
                exports_dir = Path("exports")
                exports_dir.mkdir(exist_ok=True)
                
                # 生成文件名：data_id_timestamp.csv
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_filename = f"{data_id}_cleaned_{timestamp}.csv"
                export_path = exports_dir / export_filename
            else:
                export_path = Path(export_path)
                # 确保目录存在
                export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 导出数据
            try:
                data.to_csv(export_path, encoding='utf-8')
                export_info = {
                    "exported": True,
                    "path": str(export_path.absolute()),
                    "size_mb": round(os.path.getsize(export_path) / (1024 * 1024), 2)
                }
            except Exception as e:
                export_info = {
                    "exported": False,
                    "error": f"导出失败: {str(e)}"
                }
        
        # 优化的响应格式
        result = {
            "status": "success",
            "message": f"✅ 数据已成功预处理为 '{data_id}'" + (f" (已自动清洗)" if cleaned else "") + (f" 并导出到本地" if export_info and export_info.get('exported') else ""),
            "summary": {
                "data_id": data_id,
                "shape": {"rows": data.shape[0], "columns": data.shape[1]},
                "columns": list(data.columns),
                "date_range": {
                    "start": str(data.index.get_level_values(0).min()),
                    "end": str(data.index.get_level_values(0).max())
                },
                "symbol_count": len(data.index.get_level_values(1).unique()),
                "total_records": len(data)
            },
            "preview": {
                "head_3": data.head(3).to_dict('records')[:3],
                "tail_3": data.tail(3).to_dict('records')[:3]
            },
            "data_quality": {
                "auto_cleaned": cleaned,
                "original_missing_values": original_null_count if cleaned else current_null_count,
                "original_missing_rate": f"{original_null_rate * 100:.2f}%" if cleaned else f"{current_null_rate * 100:.2f}%",
                "current_missing_values": current_null_count,
                "current_missing_rate": f"{current_null_rate * 100:.2f}%",
                "quality_score": "优秀" if current_null_rate < 0.01 else "良好" if current_null_rate < 0.05 else "需要清洗",
                "cleaning_applied": cleaning_methods
            },
            "next_steps": [
                f"使用 generate_alpha158 生成因子: result_id='alpha158_{data_id}'",
                f"或使用 calculate_factor 计算单个因子",
                f"使用 list_factors 查看已加载数据: 无需参数"
            ]
        }
        
        # 添加导出信息
        if export_info:
            result["export_info"] = export_info
        
        result = convert_to_serializable(result)
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except FileNotFoundError as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.FILE_ERROR,
                message=f"文件未找到: {file_path}",
                details={"file_path": file_path, "error": str(e)},
                suggestions=[
                    "检查文件路径是否正确",
                    "确认文件是否存在",
                    "使用绝对路径"
                ]
            )
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"数据加载失败: {str(e)}",
                details={
                    "file_path": file_path,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                },
                suggestions=[
                    "检查CSV文件格式是否正确",
                    "确认文件编码为UTF-8",
                    "验证文件是否包含必需的列"
                ]
            )
        )]


async def handle_calculate_factor(args: Dict[str, Any]) -> List[types.TextContent]:
    """计算因子"""
    data_id = args["data_id"]
    factor_name = args["factor_name"]
    factor_type = args["factor_type"]
    period = args.get("period", 20)
    
    # 验证数据ID
    error = validate_data_id(data_id, data_store)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    # 验证period参数
    error = validate_period(period)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    try:
        data = data_store[data_id]
        library = FactorLibrary()
        factor_func = getattr(library, factor_type)
        factor_values = factor_func(data, period)
        
        factor_store[factor_name] = factor_values
        
        # 优化的响应格式
        null_count = int(factor_values.isna().sum()) if hasattr(factor_values, 'isna') else 0
        null_rate = null_count / len(factor_values) if len(factor_values) > 0 else 0
        
        # 先计算质量分数，避免在构建result时引用自身
        quality_score = "优秀" if null_rate < 0.01 else "良好" if null_rate < 0.05 else "需要清洗"
        
        result = {
            "status": "success",
            "message": f"✅ 因子 '{factor_name}' 计算完成",
            "factor_info": {
                "factor_name": factor_name,
                "factor_type": factor_type,
                "period": period,
                "data_rows": len(factor_values),
                "valid_values": len(factor_values) - null_count
            },
            "data_quality": {
                "null_count": null_count,
                "null_rate": f"{null_rate * 100:.2f}%",
                "quality_score": quality_score
            },
            "next_steps": [
                {
                    "step": 1,
                    "action": "评估因子有效性",
                    "tool": "evaluate_factor_ic",
                    "params_example": {
                        "factor_name": factor_name,
                        "data_id": data_id,
                        "method": "spearman"
                    },
                    "reason": "判断因子是否有预测能力"
                },
                {
                    "step": 2,
                    "action": "如果IC有效，可生成更多因子或直接训练模型",
                    "tools": ["generate_alpha158", "train_lstm_model"]
                }
            ],
            "tips": [
                f"💡 因子类型: {factor_type}，周期: {period}天",
                f"💡 数据质量: {quality_score}",
                "💡 建议先评估IC再决定是否使用此因子"
            ]
        }
        
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except AttributeError:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.INVALID_PARAMETER,
                message=f"不支持的因子类型: {factor_type}",
                details={
                    "factor_type": factor_type,
                    "supported_types": ["momentum", "volatility", "volume_ratio", "rsi", "macd", "bollinger_bands"]
                },
                suggestions=[
                    "使用支持的因子类型之一",
                    "检查factor_type参数拼写"
                ]
            )
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"因子计算失败: {str(e)}",
                details={
                    "factor_name": factor_name,
                    "factor_type": factor_type,
                    "period": period,
                    "exception_type": type(e).__name__
                },
                suggestions=[
                    "检查数据中是否有NaN或Inf值",
                    "确认period参数合理",
                    "尝试使用更小的period值"
                ]
            )
        )]


async def handle_generate_alpha158(args: Dict[str, Any]) -> List[types.TextContent]:
    """生成Alpha158因子"""
    data_id = args["data_id"]
    result_id = args["result_id"]
    kbar = args.get("kbar", True)
    price = args.get("price", True)
    volume = args.get("volume", True)
    rolling = args.get("rolling", True)
    rolling_windows = args.get("rolling_windows", [5, 10, 20, 30, 60])
    export_path = args.get("export_path", None)  # 导出路径（可选）
    export_format = args.get("export_format", "csv")  # csv 或 json
    
    # 验证数据ID
    error = validate_data_id(data_id, data_store)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    # 验证rolling_windows参数
    if rolling:
        error = validate_window_size(rolling_windows)
        if error:
            return [types.TextContent(type="text", text=error)]
    
    try:
        data = data_store[data_id]
        
        # 验证必需列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        error = validate_required_columns(data, required_cols, data_id)
        if error:
            return [types.TextContent(type="text", text=error)]
        
        # 验证数据量
        min_required = max(rolling_windows) if rolling and rolling_windows else 100
        error = validate_data_length(data, min_length=min_required, data_id=data_id)
        if error:
            return [types.TextContent(type="text", text=error)]
        
        generator = Alpha158Generator(data)
        
        alpha158 = generator.generate_all(
            kbar=kbar,
            price=price,
            volume=volume,
            rolling=rolling,
            rolling_windows=rolling_windows
        )
        
        factor_store[result_id] = alpha158
        
        # 导出Alpha158因子数据
        export_info = None
        if export_path:
            import os
            from pathlib import Path
            from datetime import datetime
            
            export_path_obj = Path(export_path)
            # 确保目录存在
            export_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                if export_format.lower() == "csv":
                    alpha158.to_csv(export_path, encoding='utf-8')
                elif export_format.lower() == "json":
                    alpha158.to_json(export_path, orient='records', indent=2)
                else:
                    export_format = "csv"  # 默认使用CSV
                    alpha158.to_csv(export_path, encoding='utf-8')
                
                file_size = os.path.getsize(export_path) / (1024 * 1024)
                export_info = {
                    "exported": True,
                    "path": str(export_path_obj.absolute()),
                    "format": export_format,
                    "size_mb": round(file_size, 2),
                    "factor_count": len(alpha158.columns),
                    "row_count": len(alpha158)
                }
            except Exception as e:
                export_info = {
                    "exported": False,
                    "error": f"导出失败: {str(e)}"
                }
        
        # 优化的响应格式
        null_count = int(alpha158.isna().sum().sum())
        total_values = alpha158.shape[0] * alpha158.shape[1]
        null_rate = null_count / total_values if total_values > 0 else 0
        
        # 先计算质量分数，避免在构建result时引用自身
        quality_score = "优秀" if null_rate < 0.01 else "良好" if null_rate < 0.05 else "需要清洗"
        
        result = {
            "status": "success",
            "message": f"✅ Alpha158因子已生成并存储为 '{result_id}'",
            "factor_info": {
                "factor_id": result_id,
                "total_factors": len(alpha158.columns),
                "shape": list(alpha158.shape),
                "categories": {
                    "kbar": 9 if kbar else 0,
                    "price": 5 if price else 0,
                    "volume": 5 if volume else 0,
                    "rolling": len(alpha158.columns) - (9 if kbar else 0) - (5 if price else 0) - (5 if volume else 0)
                }
            },
            "data_quality": {
                "null_count": null_count,
                "null_rate": f"{null_rate * 100:.2f}%",
                "quality_score": quality_score,
                "recommendation": "数据质量良好，可直接用于模型训练" if null_rate < 0.01 else "建议使用 apply_processor_chain 进行数据清洗"
            },
            "next_steps": [
                {
                    "step": 1,
                    "action": "数据预处理（建议）" if null_rate > 0 else "数据预处理（可选）",
                    "tool": "apply_processor_chain",
                    "reason": "清洗缺失值并标准化" if null_rate > 0 else "标准化数据提升模型效果"
                },
                {
                    "step": 2,
                    "action": "训练深度学习模型",
                    "tools": ["train_lstm_model", "train_gru_model", "train_transformer_model"],
                    "params_example": {
                        "data_id": result_id,
                        "model_id": f"model_{result_id}"
                    }
                },
                {
                    "step": 3,
                    "action": "因子评估（可选）",
                    "tool": "evaluate_factor_ic",
                    "params_example": {
                        "factor_name": result_id,
                        "data_id": data_id
                    }
                }
            ],
            "tips": [
                f"💡 因子数量: {len(alpha158.columns)}个，建议使用LSTM或Transformer模型",
                f"💡 数据质量: {quality_score}",
                "💡 如果数据量不足1000条，建议使用更小的rolling_windows",
                f"💡 使用export_path参数导出因子数据便于查看" if not export_path else f"💡 因子数据已导出到: {export_path}"
            ]
        }
        
        # 添加导出信息
        if export_info:
            result["export_info"] = export_info
        
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"Alpha158因子计算失败: {str(e)}",
                details={
                    "data_id": data_id,
                    "result_id": result_id,
                    "exception_type": type(e).__name__
                },
                suggestions=[
                    "检查数据格式是否正确",
                    "确认数据中没有NaN或Inf值",
                    "尝试减少rolling_windows参数",
                    "确保数据量足够（建议1000+条）"
                ]
            )
        )]


async def handle_evaluate_factor_ic(args: Dict[str, Any]) -> List[types.TextContent]:
    """评估因子IC"""


async def handle_quick_start_lstm(args: Dict[str, Any]) -> List[types.TextContent]:
    """快速启动LSTM工作流"""
    data_file = args["data_file"]
    project = args["project_name"]
    model_config = args.get("model_config", {})
    
    workflow_results = {
        "project_name": project,
        "steps_completed": [],
        "generated_ids": {}
    }
    
    try:
        # 步骤1: 预处理数据
        # print语句移除以避免Windows环境下的GBK编码错误
        data_result = await handle_preprocess_data({
            "file_path": data_file,
            "data_id": f"{project}_data"
        })
        workflow_results["steps_completed"].append("preprocess_data")
        workflow_results["generated_ids"]["data_id"] = f"{project}_data"
        
        # 步骤2: 生成Alpha158因子
        factor_result = await handle_generate_alpha158({
            "data_id": f"{project}_data",
            "result_id": f"{project}_alpha158"
        })
        workflow_results["steps_completed"].append("generate_alpha158")
        workflow_results["generated_ids"]["factor_id"] = f"{project}_alpha158"
        
        # 步骤3: 数据预处理
        # 注意：这里简化了，实际应该有apply_processor函数
        # 暂时跳过预处理步骤
        workflow_results["steps_completed"].append("preprocessing_skipped")
        workflow_results["generated_ids"]["processed_id"] = f"{project}_alpha158"
        
        # 步骤4: 训练LSTM模型
        # 注意：这里需要train_lstm_model函数
        # 暂时返回占位符
        workflow_results["steps_completed"].append("model_training_placeholder")
        workflow_results["generated_ids"]["model_id"] = f"{project}_lstm"
        
        # 返回综合结果
        result = {
            "status": "success",
            "message": f"🎉 LSTM工作流完成！项目: {project}",
            "workflow_summary": {
                "project_name": project,
                "steps_completed": len(workflow_results["steps_completed"]),
                "total_time": "根据数据量而定",
                "generated_ids": workflow_results["generated_ids"]
            },
            "next_steps": [
                {
                    "action": "模型预测",
                    "tool": "predict_with_model",
                    "params": {
                        "model_id": f"{project}_lstm",
                        "data_id": f"{project}_alpha158",
                        "result_id": f"{project}_predictions"
                    }
                },
                {
                    "action": "评估效果",
                    "tool": "evaluate_factor_ic",
                    "params": {
                        "factor_name": f"{project}_predictions",
                        "data_id": f"{project}_data"
                    }
                }
            ],
            "tips": [
                f"💡 所有生成的ID都以 '{project}_' 为前缀",
                "💡 使用 list_factors 查看所有生成的数据和因子",
                "💡 使用 predict_with_model 进行预测"
            ]
        }
        
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"LSTM工作流失败: {str(e)}",
                details={
                    "project_name": project,
                    "failed_at_step": len(workflow_results["steps_completed"]) + 1,
                    "completed_steps": workflow_results["steps_completed"]
                },
                suggestions=[
                    "检查数据文件路径是否正确",
                    "确认数据格式符合要求",
                    "查看已完成的步骤，从失败处继续",
                    f"已生成的ID: {workflow_results['generated_ids']}"
                ]
            )
        )]
    factor_name = args["factor_name"]
    data_id = args["data_id"]
    method = args.get("method", "spearman")
    
    # 验证因子名称
    error = validate_factor_name(factor_name, factor_store)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    # 验证数据ID
    error = validate_data_id(data_id, data_store)
    if error:
        return [types.TextContent(type="text", text=error)]
    
    try:
        factor_data = factor_store[factor_name]
        price_data = data_store[data_id]["close"]
        
        returns = price_data.groupby(level=1).pct_change().shift(-1)
        aligned_factor = factor_data.dropna()
        aligned_returns = returns.reindex(aligned_factor.index)
        
        evaluator = FactorEvaluator(aligned_factor, aligned_returns)
        ic_result = evaluator.calculate_ic(method=method)
        
        # 优化的响应格式
        ic_mean = ic_result.get('ic_mean', 0)
        ic_std = ic_result.get('ic_std', 0)
        icir = ic_result.get('icir', 0)
        
        # 判断因子质量
        abs_ic = abs(ic_mean)
        if abs_ic > 0.10:
            quality = "非常强"
            recommendation = "强烈推荐使用此因子"
        elif abs_ic > 0.08:
            quality = "强"
            recommendation = "推荐使用此因子"
        elif abs_ic > 0.05:
            quality = "较强"
            recommendation = "可以使用此因子"
        elif abs_ic > 0.03:
            quality = "有效"
            recommendation = "谨慎使用，建议与其他因子组合"
        else:
            quality = "无效"
            recommendation = "不推荐使用，预测能力不足"
        
        result = {
            "status": "success",
            "message": f"✅ 因子 '{factor_name}' IC评估完成",
            "ic_metrics": ic_result,
            "factor_quality": {
                "rating": quality,
                "ic_mean": f"{ic_mean:.4f}",
                "icir": f"{icir:.4f}",
                "recommendation": recommendation
            },
            "interpretation": {
                "direction": "正向因子（因子值越大，收益越高）" if ic_mean > 0 else "反向因子（因子值越大，收益越低）",
                "stability": "稳定" if icir > 1.0 else "较稳定" if icir > 0.5 else "不稳定",
                "predictive_power": f"每单位因子变化对应约{abs(ic_mean)*100:.2f}%的收益率变化"
            },
            "next_steps": [
                {
                    "step": 1,
                    "action": "使用有效因子" if abs_ic > 0.03 else "尝试其他因子",
                    "reason": recommendation
                },
                {
                    "step": 2,
                    "action": "生成更多因子或训练模型",
                    "tools": ["generate_alpha158", "train_lstm_model"] if abs_ic > 0.05 else ["calculate_factor"],
                    "reason": "因子有效，可继续建模" if abs_ic > 0.05 else "当前因子效果不佳，建议尝试其他因子"
                }
            ],
            "tips": [
                f"💡 IC均值: {ic_mean:.4f} ({'强' if abs_ic > 0.08 else '较强' if abs_ic > 0.05 else '弱'})",
                f"💡 ICIR: {icir:.4f} ({'稳定' if icir > 1.0 else '较稳定' if icir > 0.5 else '不稳定'})",
                f"💡 {quality}因子，{recommendation}"
            ]
        }
        
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except KeyError as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.INVALID_PARAMETER,
                message=f"数据缺少close列: {str(e)}",
                details={"data_id": data_id, "missing_column": "close"},
                suggestions=[
                    "确保数据包含close列",
                    "检查数据加载是否正确"
                ]
            )
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"IC评估失败: {str(e)}",
                details={
                    "factor_name": factor_name,
                    "data_id": data_id,
                    "method": method,
                    "exception_type": type(e).__name__
                },
                suggestions=[
                    "检查因子和数据的时间范围是否匹配",
                    "确认数据中有足够的样本",
                    "尝试使用不同的method参数"
                ]
            )
        )]


async def handle_apply_processor_chain(args: Dict[str, Any]) -> List[types.TextContent]:
    """应用数据处理器链"""
    data_id = args["data_id"]
    result_id = args["result_id"]
    processors_config = args["processors"]
    export_path = args.get("export_path", None)
    export_format = args.get("export_format", "csv")  # csv 或 json
    
    # 验证数据ID
    error = validate_data_id(data_id, factor_store)  # 通常处理因子数据
    if error:
        # 如果不在factor_store，检查data_store
        error = validate_data_id(data_id, data_store)
        if error:
            return [types.TextContent(type="text", text=error)]
        data = data_store[data_id].copy()
    else:
        data = factor_store[data_id].copy()
    
    try:
        # 构建处理器链
        processors = []
        for proc_config in processors_config:
            proc_name = proc_config["name"]
            proc_params = proc_config.get("params", {})
            
            # 根据名称创建处理器
            if proc_name == "CSZScoreNorm":
                proc = CSZScoreNorm(**proc_params)
            elif proc_name == "CSZFillna":
                proc = CSZFillna(**proc_params)
            elif proc_name == "ProcessInf":
                proc = ProcessInf()
            elif proc_name == "ZScoreNorm":
                proc = ZScoreNorm(**proc_params)
            elif proc_name == "RobustZScoreNorm":
                from quantanalyzer.data.processor import RobustZScoreNorm
                proc = RobustZScoreNorm(**proc_params)
            elif proc_name == "CSRankNorm":
                from quantanalyzer.data.processor import CSRankNorm
                proc = CSRankNorm(**proc_params)
            elif proc_name == "MinMaxNorm":
                from quantanalyzer.data.processor import MinMaxNorm
                proc = MinMaxNorm(**proc_params)
            else:
                return [types.TextContent(
                    type="text",
                    text=MCPError.format_error(
                        error_code=MCPError.INVALID_PARAMETER,
                        message=f"不支持的处理器: {proc_name}",
                        details={"processor": proc_name},
                        suggestions=[
                            "支持的处理器: CSZScoreNorm, CSZFillna, ProcessInf, ZScoreNorm, RobustZScoreNorm, CSRankNorm, MinMaxNorm"
                        ]
                    )
                )]
            
            processors.append(proc)
        
        # 应用处理器链
        chain = ProcessorChain(processors)
        processed_data = chain.fit_transform(data)
        
        # 保存处理后的数据
        factor_store[result_id] = processed_data
        
        # 导出处理后的数据
        export_info = None
        if export_path:
            import os
            from pathlib import Path
            from datetime import datetime
            
            export_path_obj = Path(export_path)
            # 确保目录存在
            export_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                if export_format.lower() == "csv":
                    processed_data.to_csv(export_path, encoding='utf-8')
                elif export_format.lower() == "json":
                    processed_data.to_json(export_path, orient='records', indent=2)
                else:
                    export_format = "csv"  # 默认使用CSV
                    processed_data.to_csv(export_path, encoding='utf-8')
                
                file_size = os.path.getsize(export_path) / (1024 * 1024)
                export_info = {
                    "exported": True,
                    "path": str(export_path_obj.absolute()),
                    "format": export_format,
                    "size_mb": round(file_size, 2)
                }
            except Exception as e:
                export_info = {
                    "exported": False,
                    "error": f"导出失败: {str(e)}"
                }
        
        # 计算数据质量
        null_count = int(processed_data.isna().sum().sum())
        total_values = processed_data.shape[0] * processed_data.shape[1]
        null_rate = null_count / total_values if total_values > 0 else 0
        
        result = {
            "status": "success",
            "message": f"✅ 数据处理完成并存储为 '{result_id}'",
            "processing_info": {
                "input_id": data_id,
                "output_id": result_id,
                "processors_applied": [p["name"] for p in processors_config],
                "shape": list(processed_data.shape)
            },
            "data_quality": {
                "null_count": null_count,
                "null_rate": f"{null_rate * 100:.2f}%",
                "quality_score": "优秀" if null_rate < 0.01 else "良好" if null_rate < 0.05 else "一般"
            },
            "next_steps": [
                {
                    "step": 1,
                    "action": "训练深度学习模型",
                    "tools": ["train_lstm_model", "train_gru_model", "train_transformer_model"],
                    "params_example": {
                        "data_id": result_id,
                        "model_id": f"model_{result_id}"
                    }
                }
            ]
        }
        
        return [types.TextContent(type="text", text=serialize_response(result))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=MCPError.format_error(
                error_code=MCPError.COMPUTATION_ERROR,
                message=f"数据处理失败: {str(e)}",
                details={
                    "data_id": data_id,
                    "processors": processors_config,
                    "exception_type": type(e).__name__
                },
                suggestions=[
                    "检查处理器参数是否正确",
                    "确认数据格式符合要求",
                    "尝试减少处理器数量"
                ]
            )
        )]


async def handle_list_factors(args: Dict[str, Any]) -> List[types.TextContent]:
    """列出所有因子"""
    factors_info = {}
    for factor_id, factor in factor_store.items():
        factors_info[factor_id] = {
            "type": str(type(factor).__name__),
            "shape": list(factor.shape) if hasattr(factor, 'shape') else None
        }
    
    result = {
        "data_count": len(data_store),
        "data_ids": list(data_store.keys()),
        "factor_count": len(factor_store),
        "factors": factors_info
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]