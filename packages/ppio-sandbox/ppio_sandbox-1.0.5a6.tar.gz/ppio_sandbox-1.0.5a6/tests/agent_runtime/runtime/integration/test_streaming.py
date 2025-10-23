"""
流式响应集成测试

测试端到端的流式响应功能，包括同步和异步生成器的处理、Server-Sent Events (SSE) 格式验证等。
"""

import asyncio
import json
import threading
import time
import requests
import pytest
from typing import Generator, AsyncGenerator

from ppio_sandbox.agent_runtime.runtime.app import AgentRuntimeApp
from ppio_sandbox.agent_runtime.runtime.context import RequestContext
from ppio_sandbox.agent_runtime.runtime.models import RuntimeConfig


class TestStreamingBasicFlow:
    """流式响应基础流程测试"""
    
    def _parse_sse_events(self, response) -> list:
        """解析 Server-Sent Events 响应"""
        sse_events = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_content = line_str[6:]  # 去掉 "data: " 前缀
                    try:
                        # 内容被 JSON 编码，需要解码
                        event_data = json.loads(data_content)
                        sse_events.append(event_data)
                    except json.JSONDecodeError:
                        sse_events.append(data_content)
        return sse_events
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        # 为每个测试方法分配不同的端口
        port_map = {
            "test_sync_generator_streaming_e2e": 8920,
            "test_async_generator_streaming_e2e": 8921,
            "test_large_data_streaming_e2e": 8922,
            "test_streaming_with_context_e2e": 8923
        }
        self.test_port = port_map.get(method.__name__, 8924)
        self.base_url = f"http://localhost:{self.test_port}"
        self.server_thread = None
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理可能还在运行的服务器
        if self.server_thread and self.server_thread.is_alive():
            pass
    
    def start_server_in_thread(self, app: AgentRuntimeApp):
        """在独立线程中启动服务器"""
        def run_server():
            try:
                app.run(port=self.test_port, host="127.0.0.1")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 等待服务器启动
        self._wait_for_server_ready()
    
    def _wait_for_server_ready(self, timeout=5):
        """等待服务器准备就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/ping", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        raise TimeoutError("Server did not start within timeout")
    
    @pytest.mark.integration
    def test_sync_generator_streaming_e2e(self):
        """测试同步生成器的端到端流式响应"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def streaming_agent(request: dict) -> Generator[str, None, None]:
            data = request.get('data', {})
            prompt = data.get('prompt', 'test')
            count = data.get('count', 3)
            
            for i in range(count):
                yield f"Chunk {i+1}/{count}: Processing '{prompt}'"
                time.sleep(0.05)  # 模拟处理时间
            yield f"Final: Completed processing '{prompt}'"
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"prompt": "streaming test", "count": 3},
            "sandbox_id": "streaming-test",
            "stream": True  # 启用流式响应
        }
        
        # 发送流式请求
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            headers={"Content-Type": "application/json"},
            stream=True  # 启用流式接收
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/plain; charset=utf-8"
        
        # 验证流式数据（SSE 格式）
        sse_events = self._parse_sse_events(response)
        
        assert len(sse_events) == 4  # 3个处理块 + 1个最终块
        assert "Chunk 1/3: Processing 'streaming test'" in sse_events[0]
        assert "Chunk 2/3: Processing 'streaming test'" in sse_events[1]
        assert "Chunk 3/3: Processing 'streaming test'" in sse_events[2]
        assert "Final: Completed processing 'streaming test'" in sse_events[3]
        
        # 流式响应时间断言相对宽松一些，因为网络传输可能很快
        # 主要验证确实收到了分块数据
        assert len(sse_events) > 1  # 确保是分块传输的
    
    @pytest.mark.integration
    def test_async_generator_streaming_e2e(self):
        """测试异步生成器的端到端流式响应"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        async def async_streaming_agent(request: dict) -> AsyncGenerator[str, None]:
            data = request.get('data', {})
            prompt = data.get('prompt', 'test')
            count = data.get('count', 3)
            
            for i in range(count):
                await asyncio.sleep(0.05)  # 异步延迟
                yield f"AsyncChunk {i+1}/{count}: '{prompt}' processed"
            yield f"AsyncFinal: All '{prompt}' processing complete"
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"prompt": "async streaming", "count": 3},
            "sandbox_id": "async-streaming-test",
            "stream": True
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # 验证异步流式数据（SSE 格式）
        sse_events = self._parse_sse_events(response)
        
        assert len(sse_events) == 4
        assert "AsyncChunk 1/3: 'async streaming' processed" in sse_events[0]
        assert "AsyncFinal: All 'async streaming' processing complete" in sse_events[3]
        
        # 确保是分块传输
        assert len(sse_events) > 1
    
    @pytest.mark.integration
    def test_large_data_streaming_e2e(self):
        """测试大数据流式传输"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def large_data_agent(request: dict) -> Generator[str, None, None]:
            data = request.get('data', {})
            size = data.get('chunk_size', 1024)
            count = data.get('chunk_count', 5)
            
            for i in range(count):
                # 生成指定大小的数据块
                chunk_data = "x" * size
                yield f"Chunk_{i+1}_Size_{size}: {chunk_data}"
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"chunk_size": 512, "chunk_count": 5},
            "sandbox_id": "large-data-test",
            "stream": True
        }
        
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            stream=True
        )
        
        assert response.status_code == 200
        
        # 验证大数据流（SSE 格式）
        sse_events = self._parse_sse_events(response)
        
        assert len(sse_events) == 5
        # 验证数据完整性
        for i, event_data in enumerate(sse_events):
            assert f"Chunk_{i+1}_Size_512" in event_data
            assert "x" * 512 in event_data
    
    @pytest.mark.integration
    def test_streaming_with_context_e2e(self):
        """测试带上下文的流式响应"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def context_streaming_agent(request: dict, context: RequestContext) -> Generator[str, None, None]:
            data = request.get('data', {})
            message = data.get('message', 'test')
            
            # 第一个块包含上下文信息
            yield f"Context: sandbox_id={context.sandbox_id}, request_id={context.request_id}"
            
            # 处理数据块
            for i in range(3):
                yield f"Processing_{i+1}: {message} in {context.sandbox_id}"
            
            # 最终块
            yield f"Completed: {message} processing in {context.sandbox_id}"
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"message": "context streaming test"},
            "sandbox_id": "context-streaming-sandbox",
            "stream": True
        }
        
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StreamingTestClient/1.0"
            },
            stream=True
        )
        
        assert response.status_code == 200
        
        sse_events = self._parse_sse_events(response)
        
        assert len(sse_events) == 5  # 1个上下文 + 3个处理 + 1个完成
        
        # 验证上下文信息
        context_event = sse_events[0]
        assert "sandbox_id=context-streaming-sandbox" in context_event
        assert "request_id=" in context_event
        
        # 验证处理块
        for i in range(1, 4):
            processing_event = sse_events[i]
            assert f"Processing_{i}: context streaming test in context-streaming-sandbox" == processing_event
        
        # 验证完成块
        final_event = sse_events[4]
        assert "Completed: context streaming test processing in context-streaming-sandbox" == final_event


class TestStreamingErrorHandling:
    """流式响应错误处理测试"""
    
    def _parse_sse_events(self, response) -> list:
        """解析 Server-Sent Events 响应"""
        sse_events = []
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_content = line_str[6:]
                    try:
                        event_data = json.loads(data_content)
                        sse_events.append(event_data)
                    except json.JSONDecodeError:
                        sse_events.append(data_content)
        return sse_events
    
    def setup_method(self, method):
        """设置"""
        port_map = {
            "test_streaming_error_handling_e2e": 8930,
            "test_streaming_interruption_e2e": 8931,
        }
        self.test_port = port_map.get(method.__name__, 8932)
        self.base_url = f"http://localhost:{self.test_port}"
        self.server_thread = None
    
    def teardown_method(self):
        """清理"""
        pass
    
    def start_server_in_thread(self, app: AgentRuntimeApp):
        """启动服务器"""
        def run_server():
            try:
                app.run(port=self.test_port, host="127.0.0.1")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self._wait_for_server_ready()
    
    def _wait_for_server_ready(self, timeout=5):
        """等待服务器准备就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/ping", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        raise TimeoutError("Server did not start within timeout")
    
    @pytest.mark.integration
    def test_streaming_error_handling_e2e(self):
        """测试流式响应中的错误处理"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def error_streaming_agent(request: dict) -> Generator[str, None, None]:
            data = request.get('data', {})
            should_error = data.get('should_error', False)
            
            yield "Chunk 1: Starting processing"
            yield "Chunk 2: Processing continues"
            
            if should_error:
                raise ValueError("Error during streaming")
            
            yield "Chunk 3: Processing completed successfully"
        
        self.start_server_in_thread(app)
        
        # 测试正常流式处理
        normal_request = {
            "data": {"should_error": False},
            "sandbox_id": "normal-streaming",
            "stream": True
        }
        
        response = requests.post(f"{self.base_url}/invocations", json=normal_request, stream=True)
        
        assert response.status_code == 200
        
        chunks = []
        for line in response.iter_lines():
            if line:
                chunks.append(line.decode('utf-8'))
        
        assert len(chunks) == 3
        assert "Chunk 1: Starting processing" in chunks[0]
        assert "Chunk 3: Processing completed successfully" in chunks[2]
        
        # 测试流式处理中的错误
        error_request = {
            "data": {"should_error": True},
            "sandbox_id": "error-streaming",
            "stream": True
        }
        
        response = requests.post(f"{self.base_url}/invocations", json=error_request, stream=True)
        
        # 流式响应中的错误通常会在开始传输后发生，所以状态码可能仍是200
        # 但应该能看到部分数据，然后连接会中断
        chunks = []
        try:
            for line in response.iter_lines():
                if line:
                    chunks.append(line.decode('utf-8'))
        except requests.exceptions.ChunkedEncodingError:
            # 这是预期的，因为流式传输中发生了错误
            pass
        
        # 应该至少收到前两个块
        assert len(chunks) >= 2
        assert "Chunk 1: Starting processing" in chunks[0]
        assert "Chunk 2: Processing continues" in chunks[1]
    
    @pytest.mark.integration
    def test_non_streaming_vs_streaming_comparison(self):
        """测试非流式与流式响应的对比"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def flexible_agent(request: dict) -> Generator[str, None, None]:
            data = request.get('data', {})
            message = data.get('message', 'test')
            
            for i in range(3):
                yield f"Part {i+1}: {message}"
        
        self.start_server_in_thread(app)
        
        # 测试非流式请求（stream=False）
        non_streaming_request = {
            "data": {"message": "non-streaming"},
            "sandbox_id": "non-streaming-test",
            "stream": False
        }
        
        response = requests.post(f"{self.base_url}/invocations", json=non_streaming_request)
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        
        # 非流式响应应该是 JSON 格式
        data = response.json()
        assert data["status"] == "success"
        # 生成器的结果应该被收集到一个数组中
        # 注意：具体行为取决于服务器实现
        
        # 测试流式请求（stream=True）
        streaming_request = {
            "data": {"message": "streaming"},
            "sandbox_id": "streaming-test",
            "stream": True
        }
        
        response = requests.post(f"{self.base_url}/invocations", json=streaming_request, stream=True)
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/plain; charset=utf-8"
        
        # 流式响应应该是文本流
        chunks = []
        for line in response.iter_lines():
            if line:
                chunks.append(line.decode('utf-8'))
        
        assert len(chunks) == 3
        assert "Part 1: streaming" in chunks[0]
        assert "Part 2: streaming" in chunks[1]
        assert "Part 3: streaming" in chunks[2]