"""
基础转换器类 - 提供转换器的通用接口和功能
"""

import tempfile
import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseConverter(ABC):
    """基础转换器抽象类"""
    
    def __init__(self):
        self.temp_files = []  # 跟踪临时文件以便清理
    
    def get_desktop_path(self) -> Path:
        """
        获取桌面路径，支持跨平台
        
        Returns:
            桌面目录的Path对象
        """
        system = platform.system().lower()
        home = Path.home()
        
        if system == "windows":
            # Windows系统：优先使用注册表获取桌面路径，fallback到Desktop
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
                    return Path(desktop_path)
            except (ImportError, OSError, FileNotFoundError):
                # 如果无法获取注册表信息，使用默认路径
                desktop_candidates = [
                    home / "Desktop",
                    home / "桌面",  # 中文系统
                    home / "デスクトップ",  # 日文系统
                ]
                for candidate in desktop_candidates:
                    if candidate.exists():
                        return candidate
                # 如果都不存在，返回Desktop并创建
                desktop_path = home / "Desktop"
                desktop_path.mkdir(exist_ok=True)
                return desktop_path
                
        elif system == "darwin":  # macOS
            return home / "Desktop"
            
        else:  # Linux和其他系统
            # 尝试使用XDG用户目录
            try:
                xdg_desktop = os.environ.get('XDG_DESKTOP_DIR')
                if xdg_desktop:
                    return Path(xdg_desktop)
            except:
                pass
            
            # 尝试常见的桌面目录名
            desktop_candidates = [
                home / "Desktop",
                home / "桌面",
                home / "デスクトップ",
                home / "Bureau",  # 法语
                home / "Escritorio",  # 西班牙语
                home / "Schreibtisch",  # 德语
            ]
            
            for candidate in desktop_candidates:
                if candidate.exists():
                    return candidate
            
            # 如果都不存在，创建Desktop目录
            desktop_path = home / "Desktop"
            desktop_path.mkdir(exist_ok=True)
            return desktop_path
    
    @abstractmethod
    def convert(self, filepath: str, **kwargs) -> Dict[str, Any]:
        """
        转换文件的抽象方法
        
        Args:
            filepath: 输入文件路径
            **kwargs: 转换选项
            
        Returns:
            转换结果字典，包含状态和内容信息
        """
        pass
    
    def validate_file(self, filepath: str, valid_extensions: list) -> None:
        """
        验证文件是否存在且格式正确
        
        Args:
            filepath: 文件路径
            valid_extensions: 有效的文件扩展名列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        file_path = Path(filepath)
        
        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        # 检查文件扩展名
        if file_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"文件格式不支持: {file_path.suffix} (支持: {', '.join(valid_extensions)})")
    
    def create_output_file(self, content: str, input_filepath: str, suffix: str = '.md', encoding: str = 'utf-8', output_dir: Optional[str] = None) -> str:
        """
        创建输出文件并写入内容
        
        Args:
            content: 文件内容
            input_filepath: 输入文件路径（用于生成输出文件名）
            suffix: 文件后缀
            encoding: 文件编码
            output_dir: 输出目录（如果为None则使用桌面）
            
        Returns:
            输出文件路径
        """
        # 获取输入文件名（不含扩展名）
        input_path = Path(input_filepath)
        base_name = input_path.stem
        
        # 确定输出目录
        if output_dir is None:
            # 使用跨平台桌面目录
            desktop_path = self.get_desktop_path()
        else:
            desktop_path = Path(output_dir)
        
        # 确保输出目录存在
        desktop_path.mkdir(exist_ok=True)
        
        # 构建输出文件路径
        output_filename = f"{base_name}_converted{suffix}"
        output_path = desktop_path / output_filename
        
        # 如果文件已存在，添加序号
        counter = 1
        while output_path.exists():
            output_filename = f"{base_name}_converted_{counter}{suffix}"
            output_path = desktop_path / output_filename
            counter += 1
        
        # 写入文件
        with open(output_path, 'w', encoding=encoding) as output_file:
            output_file.write(content)
        
        return str(output_path)
    
    def create_temp_file(self, content: str, suffix: str = '.md', encoding: str = 'utf-8') -> str:
        """
        创建临时文件并写入内容（保留原有功能）
        
        Args:
            content: 文件内容
            suffix: 文件后缀
            encoding: 文件编码
            
        Returns:
            临时文件路径
        """
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding=encoding
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
            self.temp_files.append(temp_path)  # 记录临时文件
            return temp_path
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink()
            except (OSError, FileNotFoundError):
                pass  # 忽略清理失败
        self.temp_files.clear()
    
    def get_file_size(self, filepath: str) -> int:
        """获取文件大小（字节）"""
        return Path(filepath).stat().st_size
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"