import pytest
import os
from llama_index.core.schema import BaseNode
from wujing.rag.markdown import MarkdownProcessor, create_processor


class TestMarkdownProcessor:
    """测试 MarkdownProcessor 类的所有方法"""
    
    @pytest.fixture
    def test_data_path(self):
        """测试数据文件路径"""
        return "/Users/sqjian/Documents/Code/py-kit/testdata/docx2md.md"
    
    @pytest.fixture
    def sample_markdown_text(self):
        """样例 Markdown 文本"""
        return """# 主标题

这是第一段内容。

## 二级标题

这是第二段内容，包含一些详细信息。

### 三级标题

这是第三段内容，用于测试多层级标题的解析。

#### 四级标题

这是四级标题下的内容。

## 另一个二级标题

最后一段内容。"""

    def test_init_default_parameters(self):
        """测试使用默认参数初始化 MarkdownProcessor"""
        processor = MarkdownProcessor()
        
        assert processor.include_metadata is True
        assert processor.include_prev_next_rel is True
        assert processor.chunk_size is None
        assert processor.chunk_overlap == 200
        assert processor.secondary_parser is None
        
    def test_init_with_chunk_size(self):
        """测试使用 chunk_size 初始化 MarkdownProcessor"""
        processor = MarkdownProcessor(
            chunk_size=500,
            chunk_overlap=50,
            include_metadata=False,
            include_prev_next_rel=False
        )
        
        assert processor.include_metadata is False
        assert processor.include_prev_next_rel is False
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        assert processor.secondary_parser is not None
        
    def test_extract_section_title_valid_titles(self):
        """测试提取有效的标题"""
        processor = MarkdownProcessor()
        
        # 测试不同级别的标题
        test_cases = [
            ("# 一级标题", "一级标题"),
            ("## 二级标题", "二级标题"),
            ("### 三级标题", "三级标题"),
            ("#### 四级标题", "四级标题"),
            ("##### 五级标题", "五级标题"),
            ("###### 六级标题", "六级标题"),
            ("# 带空格的标题 ", "带空格的标题"),
            ("##   多个空格的标题   ", "多个空格的标题"),
        ]
        
        for content, expected in test_cases:
            result = processor._extract_section_title(content)
            assert result == expected, f"输入: {content}, 期望: {expected}, 实际: {result}"
            
    def test_extract_section_title_invalid_titles(self):
        """测试无效标题的情况"""
        processor = MarkdownProcessor()
        
        # 测试无效情况
        invalid_cases = [
            "普通文本",
            "文本内容\n# 标题在第二行",
            "",
            "#无空格的标题",  # 缺少空格
            "## ",  # 只有标记没有内容
            "###\n",  # 只有标记换行但没有内容
        ]
        
        for content in invalid_cases:
            result = processor._extract_section_title(content)
            assert result is None, f"输入: {content}, 应该返回 None，实际: {result}"
            
    def test_parse_markdown_text_basic(self, sample_markdown_text):
        """测试基本的 Markdown 文本解析"""
        processor = MarkdownProcessor()
        nodes = processor.parse_markdown_text(sample_markdown_text)
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        assert all(isinstance(node, BaseNode) for node in nodes)
        
        # 验证节点内容不为空
        for node in nodes:
            assert node.get_content().strip()
            
    def test_parse_markdown_text_with_chunk_size(self, sample_markdown_text):
        """测试带有 chunk_size 限制的 Markdown 文本解析"""
        processor = MarkdownProcessor(chunk_size=100, chunk_overlap=20)
        nodes = processor.parse_markdown_text(sample_markdown_text)
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        
        # 检查是否存在子块
        sub_chunks = [node for node in nodes if hasattr(node, 'metadata') 
                     and node.metadata and node.metadata.get('is_sub_chunk')]
        
        # 如果有超过 chunk_size 的内容，应该会产生子块
        for sub_chunk in sub_chunks:
            assert 'sub_chunk_index' in sub_chunk.metadata
            assert 'total_sub_chunks' in sub_chunk.metadata
            assert 'is_sub_chunk' in sub_chunk.metadata
            
    def test_parse_markdown_text_section_titles(self, sample_markdown_text):
        """测试 section_title 的提取和设置"""
        processor = MarkdownProcessor(chunk_size=50, chunk_overlap=10)
        nodes = processor.parse_markdown_text(sample_markdown_text)
        
        # 查找包含标题的节点
        nodes_with_titles = [node for node in nodes if hasattr(node, 'metadata') 
                           and node.metadata and 'section_title' in node.metadata]
        
        assert len(nodes_with_titles) > 0
        
        # 验证标题内容
        expected_titles = ["主标题", "二级标题", "三级标题", "四级标题", "另一个二级标题"]
        found_titles = [node.metadata['section_title'] for node in nodes_with_titles]
        
        # 至少应该找到一些预期的标题
        assert any(title in found_titles for title in expected_titles)
        
    def test_parse_markdown_file(self, test_data_path):
        """测试解析 Markdown 文件"""
        if not os.path.exists(test_data_path):
            pytest.skip(f"测试数据文件不存在: {test_data_path}")
            
        processor = MarkdownProcessor()
        nodes = processor.parse_markdown_file(test_data_path)
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        assert all(isinstance(node, BaseNode) for node in nodes)
        
        # 验证至少有一些节点包含中文内容（基于测试数据特征）
        chinese_nodes = [node for node in nodes if any('\u4e00' <= char <= '\u9fff' 
                        for char in node.get_content())]
        assert len(chinese_nodes) > 0
        
    def test_parse_markdown_file_with_chunk_size(self, test_data_path):
        """测试带有 chunk_size 的文件解析"""
        if not os.path.exists(test_data_path):
            pytest.skip(f"测试数据文件不存在: {test_data_path}")
            
        processor = MarkdownProcessor(chunk_size=1000, chunk_overlap=200)
        nodes = processor.parse_markdown_file(test_data_path)
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        
        # 验证元数据
        nodes_with_metadata = [node for node in nodes if hasattr(node, 'metadata') 
                              and node.metadata]
        assert len(nodes_with_metadata) > 0
        
    def test_parse_markdown_file_encoding(self):
        """测试不同编码的文件解析"""
        # 创建临时测试文件
        test_content = """# 测试标题

这是一个测试内容，包含中文字符。

## 子标题

更多内容。"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.md') as f:
            f.write(test_content)
            temp_file = f.name
            
        try:
            processor = MarkdownProcessor()
            nodes = processor.parse_markdown_file(temp_file)
            
            assert len(nodes) > 0
            # 验证中文内容正确解析
            content = ''.join(node.get_content() for node in nodes)
            assert '测试标题' in content
            assert '中文字符' in content
        finally:
            os.unlink(temp_file)
            
    def test_metadata_inheritance_in_sub_chunks(self):
        """测试子块中元数据的继承"""
        # 创建一个长文本，确保会被分割
        long_text = """# 长标题

""" + "这是一个很长的段落内容。" * 50  # 创建超过默认 chunk_size 的内容
        
        processor = MarkdownProcessor(chunk_size=200, chunk_overlap=50)
        nodes = processor.parse_markdown_text(long_text)
        
        # 查找子块
        sub_chunks = [node for node in nodes if hasattr(node, 'metadata') 
                     and node.metadata and node.metadata.get('is_sub_chunk')]
        
        if sub_chunks:
            # 验证子块元数据
            for sub_chunk in sub_chunks:
                assert 'section_title' in sub_chunk.metadata
                assert sub_chunk.metadata['section_title'] == '长标题'
                assert isinstance(sub_chunk.metadata['sub_chunk_index'], int)
                assert isinstance(sub_chunk.metadata['total_sub_chunks'], int)
                assert sub_chunk.metadata['is_sub_chunk'] is True


class TestCreateProcessor:
    """测试 create_processor 工厂函数"""
    
    def test_create_processor_default_parameters(self):
        """测试使用默认参数创建处理器"""
        processor = create_processor()
        
        assert isinstance(processor, MarkdownProcessor)
        assert processor.chunk_size is None
        assert processor.chunk_overlap == 200
        assert processor.include_metadata is True
        assert processor.include_prev_next_rel is True
        
    def test_create_processor_custom_parameters(self):
        """测试使用自定义参数创建处理器"""
        processor = create_processor(
            chunk_size=500,
            chunk_overlap=100,
            include_metadata=False,
            include_prev_next_rel=False
        )
        
        assert isinstance(processor, MarkdownProcessor)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100
        assert processor.include_metadata is False
        assert processor.include_prev_next_rel is False
        assert processor.secondary_parser is not None


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def test_data_path(self):
        """测试数据文件路径"""
        return "/Users/sqjian/Documents/Code/py-kit/testdata/docx2md.md"
    
    def test_end_to_end_processing(self):
        """端到端测试：完整的处理流程"""
        markdown_content = """# 产品文档

## 概述

这是产品的基本介绍。

### 功能特性

- 特性1：描述1
- 特性2：描述2
- 特性3：描述3

### 技术规格

详细的技术规格说明。

## 使用指南

### 安装步骤

1. 步骤一
2. 步骤二
3. 步骤三

### 配置说明

配置相关的详细信息。

## 问题排查

常见问题和解决方案。"""
        
        # 测试不同配置的处理器
        configs = [
            {"chunk_size": None},  # 只按结构分割
            {"chunk_size": 200, "chunk_overlap": 50},  # 带大小限制
            {"chunk_size": 100, "chunk_overlap": 20},  # 更小的块
        ]
        
        for config in configs:
            processor = create_processor(**config)
            nodes = processor.parse_markdown_text(markdown_content)
            
            assert len(nodes) > 0
            
            # 验证所有节点都有内容
            for node in nodes:
                assert node.get_content().strip()
                
            # 验证节点覆盖了原始内容的主要部分
            all_content = ' '.join(node.get_content() for node in nodes)
            key_phrases = ['产品文档', '概述', '功能特性', '技术规格', '使用指南', '问题排查']
            for phrase in key_phrases:
                assert phrase in all_content, f"关键短语 '{phrase}' 未在节点内容中找到"
                
    def test_performance_with_large_document(self, test_data_path):
        """测试大文档的处理性能"""
        if not os.path.exists(test_data_path):
            pytest.skip(f"测试数据文件不存在: {test_data_path}")
            
        import time
        
        processor = create_processor(chunk_size=1000, chunk_overlap=200)
        
        start_time = time.time()
        nodes = processor.parse_markdown_file(test_data_path)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证处理结果
        assert len(nodes) > 0
        assert processing_time < 30  # 处理时间应该在合理范围内（30秒）
        
        print(f"处理了 {len(nodes)} 个节点，耗时 {processing_time:.2f} 秒")


if __name__ == "__main__":
    # 运行简单的验证测试
    from rich import print as rprint
    
    def demo_test():
        """演示测试"""
        processor = create_processor(chunk_size=1000, chunk_overlap=20)
        test_data_path = "/Users/sqjian/Documents/Code/py-kit/testdata/docx2md.md"
        
        if os.path.exists(test_data_path):
            nodes = processor.parse_markdown_file(test_data_path)
            
            print(f"解析得到 {len(nodes)} 个节点")
            
            if len(nodes) > 56:
                node = nodes[56]
                rprint("节点 56 的内容:")
                rprint(node.get_content()[:200] + "..." if len(node.get_content()) > 200 else node.get_content())
                rprint("节点 56 的元数据:")
                rprint(node.metadata)
                rprint("===")
                
            # 统计包含标题的节点
            nodes_with_titles = [n for n in nodes if hasattr(n, 'metadata') 
                               and n.metadata and 'section_title' in n.metadata]
            print(f"包含 section_title 的节点数量: {len(nodes_with_titles)}")
            
            # 显示前几个标题
            for i, node in enumerate(nodes_with_titles[:5]):
                print(f"  {i+1}. {node.metadata['section_title']}")
        else:
            print(f"测试数据文件不存在: {test_data_path}")
    
    demo_test()
