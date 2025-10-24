#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind核心引擎
提供XMind文件处理的核心业务逻辑
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# 导入现有的转换器组件
from universal_xmind_converter import ParserFactory, create_xmind_file
from validate_xmind_structure import XMindValidator

# 配置日志
logger = logging.getLogger(__name__)


class XMindCoreEngine:
    """XMind核心引擎 - 处理XMind文件的核心业务逻辑"""
    
    def __init__(self):
        self.validator = None  # 将在需要时创建
        self.active_files = {}  # 缓存活跃的XMind文件
    
    def get_tools(self):
        """获取可用工具列表 - 兼容MCP服务器"""
        return [
            {
                "name": "read_xmind_file",
                "description": "读取XMind文件内容（返回结构与统计信息）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "XMind文件路径"}
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "create_mind_map",
                "description": "创建新的思维导图（支持 children/topics/subtopics 等别名，服务器自动归一化）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "思维导图标题（将作为根节点标题）"
                        },
                        "topics_json": {
                            "type": "string",
                            "description": "主题结构的JSON字符串。每个节点至少包含`title`；子节点推荐使用`children`，也兼容`topics`/`subtopics`/`nodes`/`items`（服务器会自动归一化）。必须是合法JSON字符串，不要使用Markdown或纯文本。",
                            "examples": [
                                "[{\"title\":\"根\",\"children\":[{\"title\":\"子1\"},{\"title\":\"子2\",\"children\":[{\"title\":\"孙\"}]}]}]",
                                "[{\"title\":\"根\",\"topics\":[{\"title\":\"子1\"}]}]"
                            ]
                        },
                        "output_path": {
                            "type": "string",
                            "description": "可选。输出文件的绝对路径；未指定时使用配置 `default_output_dir`。",
                            "examples": ["D:/project/XmindMcp/output/demo.xmind"]
                        }
                    },
                    "required": ["title", "topics_json"]
                }
            },
            {
                "name": "analyze_mind_map",
                "description": "分析思维导图结构（统计节点数、最大层级等）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "XMind文件路径"}
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "convert_to_xmind",
                "description": "将纯文本、Markdown、HTML、Word、Excel等文件转换为XMind。不要传入JSON结构；JSON结构请使用 `create_mind_map`。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source_filepath": {"type": "string", "description": "源文件路径（支持 .txt/.md/.html/.docx/.xlsx 等）", "examples": ["D:/project/XmindMcp/examples/test_outline.md", "D:/project/XmindMcp/examples/test_outline.txt"]},
                        "output_filepath": {"type": "string", "description": "可选。输出XMind文件绝对路径；未指定时自动输出到 `output/<源文件名>.xmind`", "examples": ["D:/project/XmindMcp/output/my_outline.xmind"]}
                    },
                    "required": ["source_filepath"]
                }
            },
            {
                "name": "list_xmind_files",
                "description": "列出目录中的XMind文件",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "要遍历的目录，默认当前目录"},
                        "recursive": {"type": "boolean", "description": "是否递归遍历，默认 true"}
                    },
                    "required": []
                }
            }
        ]
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全的字符"""
        import re
        # 移除或替换不安全的字符
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除前导和尾随的空白字符
        safe_filename = safe_filename.strip()
        # 限制长度
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        # 如果文件名为空，使用默认值
        if not safe_filename:
            safe_filename = "untitled"
        # 替换空格为下划线
        safe_filename = safe_filename.replace(' ', '_')
        return safe_filename
        
    def read_xmind_file(self, file_path: str):
        try:
            validator = XMindValidator(file_path)
            if not validator.extract_xmind_content():
                return {
                    "status": "error",
                    "message": "无法提取XMind内容"
                }
            # JSON优先，失败再尝试XML
            if validator.parse_json_structure():
                structure = validator.structure
            elif validator.parse_xml_structure():
                structure = validator.structure
            else:
                return {
                    "status": "error",
                    "message": "无法解析XMind结构（JSON与XML均失败）"
                }
            # 统计
            total_nodes = validator.count_nodes()
            max_depth = validator.get_max_depth()
            titles = validator.get_all_titles()
            return {
                "status": "success",
                "format": "xmind",
                "source_format": validator.parsed_source or "unknown",
                "data": structure,
                "stats": {
                    "total_nodes": total_nodes,
                    "max_depth": max_depth,
                    "titles_count": len(titles)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"读取失败: {e}"
            }

    # 新增：翻译XMind标题并输出新文件
    def translate_xmind_titles(self, source_filepath: str, output_filepath: str = None, target_lang: str = "en", overwrite: bool = False):
        import re
        import io
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            src_path = Path(source_filepath)
            if not src_path.exists():
                return {"status": "error", "message": f"源文件不存在: {source_filepath}"}
            # 默认输出路径
            if not output_filepath:
                base = src_path.stem + f"_{target_lang}"
                output_filepath = str(src_path.with_name(base + src_path.suffix))
            out_path = Path(output_filepath)
            if out_path.exists() and not overwrite:
                return {"status": "error", "message": f"输出文件已存在: {output_filepath}. 需设置 overwrite=True"}
            # 读取content.xml
            with zipfile.ZipFile(str(src_path), 'r') as zf:
                if 'content.xml' not in zf.namelist():
                    return {"status": "error", "message": "XMind中未找到content.xml，无法进行标题翻译"}
                xml_bytes = zf.read('content.xml')
                xml_text = xml_bytes.decode('utf-8')
            # 解析XML
            ns = '{urn:xmind:xmap:xmlns:content:2.0}'
            root = ET.fromstring(xml_text)
            title_els = root.findall(f'.//{ns}title')
            # 翻译器
            try:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source='auto', target=target_lang)
            except Exception as te:
                return {"status": "error", "message": f"加载翻译器失败: {te}"}
            # 文本检测：含非ASCII字符则翻译
            def needs_translate(text: str) -> bool:
                if not text:
                    return False
                return any(ord(c) > 127 for c in text)
            cache = {}
            translated_count = 0
            for t in title_els:
                if t.text:
                    raw = t.text.strip()
                    if needs_translate(raw):
                        if raw in cache:
                            new_text = cache[raw]
                        else:
                            try:
                                new_text = translator.translate(raw)
                            except Exception:
                                new_text = raw
                            cache[raw] = new_text
                        if new_text and new_text != raw:
                            t.text = new_text
                            translated_count += 1
            # 重新打包zip，替换content.xml
            buf = io.BytesIO()
            new_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            with zipfile.ZipFile(str(src_path), 'r') as zf_in, zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                for name in zf_in.namelist():
                    if name == 'content.xml':
                        zf_out.writestr('content.xml', new_xml)
                    else:
                        zf_out.writestr(name, zf_in.read(name))
            # 写入输出文件
            with open(str(out_path), 'wb') as f:
                f.write(buf.getvalue())
            return {
                "status": "success",
                "message": "翻译完成",
                "translated_titles": translated_count,
                "output_file": str(out_path)
            }
        except Exception as e:
            return {"status": "error", "message": f"翻译失败: {e}"}

    def _build_topic_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """构建主题结构"""
        if not structure:
            return {"title": "空主题", "children": []}
        
        # 验证器返回的结构已经是根主题结构，直接转换即可
        return self._convert_topic_to_dict(structure)
    
    def _convert_topic_to_dict(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """转换主题为字典格式"""
        result = {
            "title": topic.get('title', '未命名主题'),
            "children": []
        }
        
        # 添加子主题 - 验证器返回的children已经是列表格式
        children = topic.get('children', [])
        if children and isinstance(children, list):
            for child in children:
                result["children"].append(self._convert_topic_to_dict(child))
        
        return result
    
    def create_mind_map(self, title: str, topics_json: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """创建新的思维导图"""
        try:
            # 解析JSON格式的主题
            try:
                topics = json.loads(topics_json)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"主题JSON格式无效: {str(e)}",
                    "title": title
                }
            
            # 构建文本大纲结构
            outline_content = self._build_outline_structure(title, topics)
            
            # 创建临时文件 - 使用安全的文件名
            safe_title = self._sanitize_filename(title)
            
            # 确定临时文件路径 - 使用当前工作目录
            current_dir = os.getcwd()
            temp_file = os.path.join(current_dir, f"temp_{safe_title}.txt")
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(outline_content)
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"无法创建临时文件: {str(e)}",
                    "title": title
                }
            
            # 确定输出文件路径
            if output_path:
                # 如果指定了输出路径，使用指定的路径
                output_file = output_path
                output_dir = os.path.dirname(output_file)
                if output_dir and not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                    except Exception as e:
                        return {
                            "status": "error",
                            "error": f"无法创建输出目录: {str(e)}",
                            "title": title
                        }
            else:
                # 默认保存到当前工作目录的output子目录
                output_dir = os.path.join(current_dir, "output")
                if not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                    except Exception as e:
                        return {
                            "status": "error",
                            "error": f"无法创建默认输出目录: {str(e)}",
                            "title": title
                        }
                output_file = os.path.join(output_dir, f"{safe_title}.xmind")
            
            # 转换为XMind
            try:
                parser = ParserFactory.get_parser(temp_file)
                json_structure = parser.parse()
                create_xmind_file(json_structure, output_file)
                success = True
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"XMind转换失败: {error_msg}")
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"清理临时文件失败: {str(e)}")
            
            if success:
                # 验证文件是否真的被创建
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    abs_path = os.path.abspath(output_file)
                    return {
                        "status": "success",
                        "filename": os.path.basename(output_file),
                        "title": title,
                        "topics_count": len(topics),
                        "message": f"思维导图已创建: {abs_path} (大小: {file_size} 字节)",
                        "absolute_path": abs_path,
                        "output_path": output_file,
                        "file_size": file_size
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"XMind文件创建失败，文件不存在: {output_file}",
                        "title": title,
                        "output_path": output_file
                    }
            else:
                return {
                    "status": "error",
                    "error": f"XMind转换失败: {error_msg}",
                    "title": title,
                    "output_path": output_file
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "title": title
            }
    
    def _build_outline_structure(self, title: str, topics: List[Dict[str, Any]]) -> str:
        """构建文本大纲结构"""
        lines = [title]
        
        def _get_children(topic: Dict[str, Any]):
            return (
                topic.get('children')
                or topic.get('topics')
                or topic.get('subtopics')
                or None
            )

        def add_topics(parent_line: str, topics_list: List[Dict[str, Any]], level: int = 1):
            for topic in topics_list:
                indent = "    " * level  # 使用4个空格作为一级缩进
                line = f"{indent}- {topic.get('title', '未命名主题')}"
                lines.append(line)
                
                # 递归添加子主题（兼容别名）
                children = _get_children(topic)
                if children:
                    add_topics(line, children, level + 1)
        
        add_topics(title, topics)
        return "\n".join(lines)
    
    def analyze_mind_map(self, filepath: str) -> Dict[str, Any]:
        """分析思维导图"""
        try:
            # 首先读取文件
            read_result = self.read_xmind_file(filepath)
            if read_result["status"] != "success":
                return read_result
            
            # 获取根主题结构
            root_structure = read_result["data"]["structure"]
            
            # 构建统计信息
            stats = {
                'total_nodes': read_result["data"]["total_nodes"],
                'max_depth': read_result["data"]["max_depth"],
                'leaf_nodes': self._count_leaf_nodes(root_structure),
                'branch_count': len(root_structure.get('children', []))
            }
            
            # 分析结构
            analysis = {
                "complexity": self._calculate_complexity(stats),
                "balance": self._calculate_balance(root_structure),
                "completeness": self._calculate_completeness(root_structure),
                "suggestions": self._generate_suggestions(stats, root_structure)
            }
            
            return {
                "status": "success",
                "filename": os.path.basename(filepath),
                "total_nodes": stats.get('total_nodes', 0),
                "max_depth": stats.get('max_depth', 0),
                "leaf_nodes": stats.get('leaf_nodes', 0),
                "branch_count": stats.get('branch_count', 0),
                "structure_analysis": analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "filename": os.path.basename(filepath)
            }
    
    def _count_leaf_nodes(self, structure: Dict[str, Any]) -> int:
        """计算叶子节点数量"""
        if not structure.get('children'):
            return 1
        
        count = 0
        for child in structure.get('children', []):
            if not child.get('children'):
                count += 1
            else:
                count += self._count_leaf_nodes(child)
        return count
    
    def _calculate_complexity(self, stats: Dict[str, Any]) -> str:
        """计算复杂度"""
        total_nodes = stats.get('total_nodes', 0)
        max_depth = stats.get('max_depth', 0)
        
        if total_nodes < 10:
            return "简单"
        elif total_nodes < 30:
            return "中等"
        elif total_nodes < 60:
            return "复杂"
        else:
            return "非常复杂"
    
    def _calculate_balance(self, root_topic: Dict[str, Any]) -> str:
        """计算平衡性"""
        children = root_topic.get('children', [])
        if len(children) <= 3:
            return "优秀"
        elif len(children) <= 5:
            return "良好"
        else:
            return "一般"
    
    def _calculate_completeness(self, root_topic: Dict[str, Any]) -> str:
        """计算完整性"""
        # 简化的完整性计算
        return "完整"
    
    def _generate_suggestions(self, stats: Dict[str, Any], root_topic: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        if stats.get('max_depth', 0) > 4:
            suggestions.append("建议减少层级深度，保持3-4层最佳")
        
        if stats.get('total_nodes', 0) > 50:
            suggestions.append("节点较多，考虑拆分为多个思维导图")
        
        if not suggestions:
            suggestions.append("结构良好，无需优化")
        
        return suggestions
    
    def convert_to_xmind(self, source_filepath: str, output_filepath: Optional[str] = None) -> Dict[str, Any]:
        """转换文件为XMind"""
        try:
            if not os.path.exists(source_filepath):
                raise Exception(f"源文件不存在: {source_filepath}")
            
            # 确定输出文件名 - 按照原来逻辑，默认输出到output目录
            if not output_filepath:
                base_name = os.path.splitext(os.path.basename(source_filepath))[0]
                output_dir = "output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_filepath = os.path.join(output_dir, f"{base_name}.xmind")
            
            # 使用转换器转换
            parser = ParserFactory.get_parser(source_filepath)
            json_structure = parser.parse()
            create_xmind_file(json_structure, output_filepath)
            success = True
            
            if success:
                return {
                    "status": "success",
                    "source_file": source_filepath,
                    "output_file": output_filepath,
                    "message": f"文件转换成功: {output_filepath}"
                }
            else:
                return {
                    "status": "error",
                    "error": "转换失败",
                    "source_file": source_filepath
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "source_file": source_filepath
            }
    
    def list_xmind_files(self, directory: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """列出XMind文件"""
        try:
            # 验证目录路径
            if not directory:
                directory = "."
            
            directory = os.path.abspath(directory)
            
            logger.info(f"开始列出XMind文件，目录: {directory}, 递归: {recursive}")
            
            if not os.path.exists(directory):
                return {
                    "status": "error",
                    "error": f"目录不存在: {directory}",
                    "directory": directory
                }
            
            if not os.path.isdir(directory):
                return {
                    "status": "error",
                    "error": f"路径不是目录: {directory}",
                    "directory": directory
                }
            
            xmind_files = []
            
            if recursive:
                # 递归搜索
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.xmind'):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, directory)
                            xmind_files.append({
                                "name": file,
                                "path": full_path,
                                "relative_path": rel_path,
                                "size": os.path.getsize(full_path),
                                "modified": os.path.getmtime(full_path)
                            })
            else:
                # 仅搜索当前目录
                for file in os.listdir(directory):
                    if file.endswith('.xmind'):
                        full_path = os.path.join(directory, file)
                        xmind_files.append({
                            "name": file,
                            "path": full_path,
                            "relative_path": file,
                            "size": os.path.getsize(full_path),
                            "modified": os.path.getmtime(full_path)
                        })
            
            return {
                "status": "success",
                "directory": directory,
                "recursive": recursive,
                "file_count": len(xmind_files),
                "files": xmind_files
            }
            
        except Exception as e:
            logger.error(f"列出XMind文件失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "directory": directory
            }


# 全局引擎实例
_engine = None

def get_engine() -> XMindCoreEngine:
    """获取全局引擎实例"""
    global _engine
    if _engine is None:
        _engine = XMindCoreEngine()
    return _engine


# 工具函数
def read_xmind_file(filepath: str) -> Dict[str, Any]:
    """读取XMind文件"""
    return get_engine().read_xmind_file(filepath)

def create_mind_map(title: str, topics_json: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """创建思维导图"""
    return get_engine().create_mind_map(title, topics_json, output_path)

def analyze_mind_map(filepath: str) -> Dict[str, Any]:
    """分析思维导图"""
    return get_engine().analyze_mind_map(filepath)

def convert_to_xmind(source_filepath: str, output_filepath: Optional[str] = None) -> Dict[str, Any]:
    """转换文件为XMind"""
    return get_engine().convert_to_xmind(source_filepath, output_filepath)

def list_xmind_files(directory: str = ".", recursive: bool = True) -> Dict[str, Any]:
    """列出XMind文件"""
    return get_engine().list_xmind_files(directory, recursive)

def get_available_tools() -> List[Dict[str, Any]]:
    """获取可用工具列表"""
    return [
        {
            "name": "read_xmind_file",
            "description": "读取XMind文件内容",
            "parameters": {
                "filepath": {"type": "string", "description": "XMind文件路径"}
            }
        },
        {
            "name": "create_mind_map",
            "description": "创建新的思维导图",
            "parameters": {
                "title": {"type": "string", "description": "思维导图标题"},
                "topics_json": {"type": "string", "description": "主题JSON结构"}
            }
        },
        {
            "name": "analyze_mind_map",
            "description": "分析思维导图结构",
            "parameters": {
                "filepath": {"type": "string", "description": "XMind文件路径"}
            }
        },
        {
            "name": "convert_to_xmind",
            "description": "转换文件为XMind格式",
            "parameters": {
                "source_filepath": {"type": "string", "description": "源文件路径"},
                "output_filepath": {"type": "string", "description": "输出文件路径（可选）"}
            }
        },
        {
            "name": "list_xmind_files",
            "description": "列出XMind文件",
            "parameters": {
                "directory": {"type": "string", "description": "搜索目录"},
                "recursive": {"type": "boolean", "description": "是否递归搜索"}
            }
        }
    ]


if __name__ == "__main__":
    # 测试引擎
    engine = get_engine()
    
    # 测试读取文件
    print("测试读取XMind文件...")
    result = engine.read_xmind_file("test_outline.xmind")
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    print("\n测试完成！")