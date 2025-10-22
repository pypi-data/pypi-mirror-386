"""
PDF转Markdown转换器
"""

from typing import Any, Dict
from markitdown import MarkItDown
from .base_converter import BaseConverter


class PDFToMarkdownConverter(BaseConverter):
    """PDF文件转换为Markdown格式的转换器"""
    
    def __init__(self):
        super().__init__()
        self.markitdown = MarkItDown()
        self.valid_extensions = ['.pdf']
    
    def convert(self, filepath: str, output_dir: str = None, **kwargs) -> Dict[str, Any]:
        """
        转换PDF文件为Markdown格式
        
        Args:
            filepath: PDF文件路径
            output_dir: 输出目录路径（可选，默认为桌面）
            **kwargs: 其他转换参数
            
        Returns:
            转换结果字典
        """
        # 验证文件
        self.validate_file(filepath, self.valid_extensions)
        
        # 执行转换
        result = self.markitdown.convert(filepath)
        
        # 创建输出文件
        output_path = self.create_output_file(result.text_content, filepath, suffix='.md', output_dir=output_dir)
        
        # 准备结果
        file_size = self.get_file_size(filepath)
        output_size = len(result.text_content.encode('utf-8'))
        
        conversion_result = {
            'success': True,
            'input_file': filepath,
            'output_file': output_path,
            'content': result.text_content,
            'input_size': self.format_file_size(file_size),
            'output_size': self.format_file_size(output_size),
            'message': "PDF转换成功！"
        }
        
        return conversion_result