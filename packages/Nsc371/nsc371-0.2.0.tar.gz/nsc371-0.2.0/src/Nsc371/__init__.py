from .core import (
    # 编译器核心
    Compiler, Compiler_Code,
    
    # 配置函数
    set_func, set_block_handler,
    
    # 主函数和命令行
    main,
    
    # 表达式计算
    safe_eval, Cexal,
    
    # 对象系统
    String, Int, Bool, Any, string, Int as IntObj, Bool as BoolObj, Any as AnyObj,
    
    # 表达式解析
    expr_format, optional, r_input, endl,
    
    # 类系统
    ClassObject, InstanceObject, parse_class,
    
    # 条件处理
    h_if,
    
    # 注释处理
    add_comment_handler, remove_comments_from_code as remove_comments, 
    get_comments_from_code as get_comments, enable_comment_processing as enable_comments,
    disable_comment_processing as disable_comments,
    
    # 增强编译器
    EnhancedCompiler
)

__version__ = "0.2.0"
__author__ = "王子毅"

__all__ = [
    # 编译器核心
    'Compiler', 'Compiler_Code',
    
    # 配置函数
    'set_func', 'set_block_handler',
    
    # 主函数和命令行
    'main',
    
    # 表达式计算
    'safe_eval', 'Cexal',
    
    # 对象系统
    'String', 'Int', 'Bool', 'Any', 'string', 'IntObj', 'BoolObj', 'AnyObj',
    
    # 表达式解析
    'expr_format', 'optional', 'r_input', 'endl',
    
    # 类系统
    'ClassObject', 'InstanceObject', 'parse_class',
    
    # 条件处理
    'h_if',
    
    # 注释处理
    'add_comment_handler', 'remove_comments', 'get_comments', 'enable_comments', 'disable_comments',
    
    # 增强编译器
    'EnhancedCompiler'
]
