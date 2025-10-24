import sys
from pathlib import Path
import traceback
import functools
from typing import Callable, Any

from loguru import logger

# Try to import OpenAI if available
try:
    from openai import OpenAI, AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LogWrapper:
    def __init__(self, logs_dir: str = "logs", log_level: str = "DEBUG",
                 api_key: str = "",
                 base_url: str = "",
                 model_path: str = '',
                 temperature: float = 0.6,
                 top_p: float = 0.95,
                 ai_flag: bool = False):
        self.logger = logger
        self.logger.remove()

        # 初始化AI相关属性
        self.ai_enabled = False
        self.client = None
        self.async_client = None
        self.model_path = model_path
        self.temperature = temperature
        self.top_p = top_p

        # AI功能总开关（控制error日志）
        self.ai_flag = ai_flag

        # 只有当标志位开启时才尝试初始化AI客户端
        if self.ai_flag and OPENAI_AVAILABLE and api_key and base_url and model_path:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                self.ai_enabled = True
            except Exception as e:
                self.logger.warning(f"Failed to initialize AI client: {e}")
                self.ai_enabled = False

        # 创建日志目录
        Path(logs_dir).mkdir(parents=True, exist_ok=True)

        # 配置控制台输出
        self.logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYYMMDD HH:mm:ss.SSS}</green> | "
                "{process.name} | "
                "{thread.name} | "
                "<cyan>{module}</cyan>.<cyan>{function}</cyan>:"
                "<cyan>{line}</cyan> | "
                "<level>{level}</level>: "
                "<level>{message}</level>"
            ),
            level=log_level
        )

        # 配置文件输出
        log_file_path = Path(logs_dir) / "{time:YYYY-MM-DD}.log"
        self.logger.add(
            log_file_path,
            level=log_level,
            format=(
                "{time:YYYYMMDD HH:mm:ss} - "
                "{process.name} | "
                "{thread.name} | "
                "{module}.{function}:{line} - {level} - {message}"
            ),
            rotation="10 MB",
            encoding="utf-8"
        )

        # 重写error方法，添加AI功能
        self._original_error = self.logger.error
        self.logger.error = self._ai_enhanced_error

        # 创建错误分析装饰器
        self.analyze_errors = self._create_error_analyzer_decorator()

    def set_ai_flag(self, value: bool):
        """动态设置error日志的AI功能开关"""
        self.ai_flag = value

    def get_ai_flag(self) -> bool:
        """获取当前error日志的AI功能开关状态"""
        return self.ai_flag

    def _get_code_context(self, filename: str, line_number: int, context_lines: int = 10) -> str:
        """获取错误行周围的代码上下文"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 调整行号为0基索引
            start_line = max(0, line_number - 1 - context_lines)
            end_line = min(len(lines), line_number + context_lines)

            context = []
            for i in range(start_line, end_line):
                line_num = i + 1
                marker = "->" if line_num == line_number else "  "
                context.append(f"{marker} {line_num}: {lines[i].rstrip()}")

            return "\n".join(context)
        except Exception as e:
            self.logger.debug(f"Failed to get code context: {e}")
            return "Code context unavailable"

    def _analyze_error_with_ai(self, exc_type: type, exc_value: BaseException,
                               exc_traceback: traceback.StackSummary) -> str:
        """使用AI模型分析错误"""
        # 双重检查：标志位和AI客户端都正常才执行
        if not (self.ai_flag and self.ai_enabled and self.client):
            return "AI analysis disabled"

        try:
            # 获取错误信息
            error_type = exc_type.__name__
            error_message = str(exc_value)

            # 获取堆栈跟踪信息
            tb = traceback.extract_tb(exc_traceback)

            # 准备完整的堆栈跟踪信息
            stack_trace_info = []
            full_code_context = []

            if tb:
                # 添加堆栈跟踪摘要
                stack_trace_summary = "Stack Trace:\n"
                for i, frame in enumerate(tb):
                    stack_trace_summary += f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.name}\n"
                    if frame.line:
                        stack_trace_summary += f"    {frame.line.strip()}\n"

                stack_trace_info.append(stack_trace_summary)

                # 获取每个堆栈帧的代码上下文
                for i, frame in enumerate(tb):
                    filename = frame.filename
                    line_number = frame.lineno
                    function_name = frame.name

                    # 为上层帧减少上下文行数以避免过多信息
                    context_lines = 5 if i < len(tb) - 1 else 10  # 实际错误帧更多上下文
                    code_context = self._get_code_context(filename, line_number, context_lines)

                    if code_context and code_context != "Code context unavailable":
                        frame_header = f"\n{'=' * 50}"
                        frame_header += f"\nFrame {i + 1}/{len(tb)}: {function_name} at {filename}:{line_number}"
                        frame_header += f"\n{'=' * 50}"
                        full_code_context.append(f"{frame_header}\n{code_context}")

            # 准备AI提示
            prompt = f"""
            Analyze the following Python error and provide a solution:

            Error Type: {error_type}
            Error Message: {error_message}

            {''.join(stack_trace_info)}

            Code Context for All Stack Frames:
            {''.join(full_code_context) if full_code_context else 'No code context available'}

            Please provide:
            1. A brief explanation of the error
            2. The likely cause (considering the entire call stack)
            3. A suggested solution or fix
            4. If applicable, corrected code snippet

            Keep your response concise and focused on solving the problem.
            Please Answer in Chinese.
            """

            # 调用AI模型
            response = self.client.chat.completions.create(
                model=self.model_path,
                messages=[
                    {"role": "system",
                     "content": "You are a Python error analysis assistant. Help developers understand and fix Python errors."},
                    {"role": "user", "content": prompt.strip()}
                ],
                temperature=0.7,
                max_tokens=10000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.logger.debug(f"AI error analysis failed: {e}")
            return "AI analysis failed"

    def _ai_enhanced_error(self, message: str, *args, **kwargs):
        """增强的error日志，带AI分析功能"""
        # 先记录原始error日志
        self._original_error(message, *args, **kwargs)

        # 如果AI功能未开启，直接返回
        if not self.ai_flag:
            return

        # 获取当前异常（如果有的话）
        exc_type, exc_value, exc_traceback = sys.exc_info()

        # 只有存在异常且AI可用时才进行分析
        if exc_type and exc_value and exc_traceback and self.ai_enabled:
            try:
                # 获取AI分析结果
                ai_analysis = self._analyze_error_with_ai(exc_type, exc_value, exc_traceback)

                # 记录AI分析结果
                if ai_analysis and ai_analysis not in ["AI analysis disabled", "AI analysis failed"]:
                    self.logger.warning(f"\nAI Error Analysis:\n{ai_analysis}\n")
                elif ai_analysis == "AI analysis failed":
                    self.logger.debug("AI error analysis attempted but failed")

            except Exception as e:
                self.logger.debug(f"Error in AI enhanced logging: {e}")

    def _create_error_analyzer_decorator(self) -> Callable:
        """创建函数错误分析装饰器"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 记录错误
                    self._original_error(f"Error in function {func.__name__}")

                    # 如果AI功能开启，提供额外分析
                    if self.ai_flag and self.ai_enabled:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        ai_analysis = self._analyze_error_with_ai(exc_type, exc_value, exc_traceback)

                        if ai_analysis and ai_analysis not in ["AI analysis disabled", "AI analysis failed"]:
                            self.logger.warning(f"\nDetailed AI Analysis for {func.__name__}:\n{ai_analysis}\n")

                    raise  # 记录后重新抛出异常

            return wrapper

        return decorator

    def get_logger(self):
        return self.logger


def create_logger(**kwargs):
    wrapper = LogWrapper(**kwargs)
    new_logger = wrapper.get_logger()
    return new_logger


# 便捷函数
def setup_logger(**kwargs) -> LogWrapper:
    """创建带有自定义配置的新日志器实例"""
    return LogWrapper(**kwargs)


def get_default_logger():
    """获取默认日志器实例"""
    return logger


# # 导出装饰器以便快速访问
# analyze_errors = default_logger.analyze_errors
