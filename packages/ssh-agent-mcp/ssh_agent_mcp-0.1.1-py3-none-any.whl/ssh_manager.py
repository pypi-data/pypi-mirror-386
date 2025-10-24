import paramiko
import asyncio
import uuid
import time
from typing import Dict, Optional, Tuple, List
from enum import Enum
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class CommandStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

@dataclass
class AsyncCommand:
    command_id: str
    connection_id: str
    command: str
    status: CommandStatus
    start_time: float
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    stdout_buffer: List[str] = field(default_factory=list)
    stderr_buffer: List[str] = field(default_factory=list)
    process: Optional[paramiko.Channel] = None
    stdout_size: int = 0
    stderr_size: int = 0

class SSHConnection:
    def __init__(self, host: str, username: str, port: int = 22):
        self.host = host
        self.username = username
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.error_message: Optional[str] = None
        
    async def connect(self, password: Optional[str] = None, 
                     private_key: Optional[str] = None,
                     private_key_password: Optional[str] = None) -> bool:
        """建立SSH连接"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 准备认证信息
            auth_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': 10
            }
            
            if private_key:
                # 使用私钥认证
                key_obj = paramiko.RSAKey.from_private_key_file(
                    private_key, password=private_key_password
                ) if isinstance(private_key, str) else paramiko.RSAKey.from_private_key(
                    private_key, password=private_key_password
                )
                auth_kwargs['pkey'] = key_obj
            elif password:
                # 使用密码认证
                auth_kwargs['password'] = password
            else:
                # 尝试使用默认SSH agent
                auth_kwargs['look_for_keys'] = True
                auth_kwargs['allow_agent'] = True
            
            # 在线程池中执行连接（因为paramiko是同步的）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.client.connect(**auth_kwargs))
            
            # 启用keep-alive
            transport = self.client.get_transport()
            if transport:
                # 启用TCP keep-alive
                transport.set_keepalive(60)  # 60秒间隔
                # 设置压缩
                transport.use_compression(True)
                logger.debug(f"已启用SSH keep-alive: {self.username}@{self.host}:{self.port}")
            
            self.status = ConnectionStatus.CONNECTED
            self.error_message = None
            logger.info(f"SSH连接成功: {self.username}@{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.error_message = str(e)
            logger.error(f"SSH连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开SSH连接"""
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.client.close)
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
            finally:
                self.client = None
                self.status = ConnectionStatus.DISCONNECTED
                self.error_message = None
    
    async def is_healthy(self) -> bool:
        """检查连接是否健康"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            # 检查传输层状态
            loop = asyncio.get_event_loop()
            transport = await loop.run_in_executor(None, lambda: self.client.get_transport())
            if not transport or not transport.is_active():
                self.status = ConnectionStatus.ERROR
                self.error_message = "SSH传输层不活跃"
                return False
            
            # 执行轻量级命令进行健康检查（使用echo避免输出过多）
            try:
                stdin, stdout, stderr = await loop.run_in_executor(
                    None, lambda: self.client.exec_command('echo "health_check"', timeout=5)
                )
                # 读取输出以确认命令执行成功
                await loop.run_in_executor(None, stdout.read)
                return True
            except Exception as cmd_error:
                # 如果命令执行失败，可能是连接问题，但不立即标记为错误
                logger.debug(f"健康检查命令执行失败: {cmd_error}")
                # 再次检查传输状态
                if transport.is_active():
                    return True  # 传输仍然活跃，认为连接正常
                else:
                    self.status = ConnectionStatus.ERROR
                    self.error_message = f"连接意外断开: {str(cmd_error)}"
                    return False
                    
        except Exception as e:
            logger.warning(f"连接健康检查失败: {e}")
            self.status = ConnectionStatus.ERROR
            self.error_message = f"连接意外断开: {str(e)}"
            return False
    
    async def send_keepalive(self) -> bool:
        """发送keep-alive信号"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            transport = await loop.run_in_executor(None, lambda: self.client.get_transport())
            if transport and transport.is_active():
                # 发送keep-alive包
                await loop.run_in_executor(None, transport.send_ignore)
                return True
        except Exception as e:
            logger.debug(f"发送keep-alive失败: {e}")
            self.status = ConnectionStatus.ERROR
            self.error_message = f"连接断开: {str(e)}"
        
        return False
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行SSH命令并返回退出码、stdout、stderr"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return -1, "", "SSH连接未建立"
        
        try:
            # 在执行命令前检查连接健康状态
            if not await self.is_healthy():
                return -1, "", "SSH连接已断开"
            
            loop = asyncio.get_event_loop()
            stdin, stdout, stderr = await loop.run_in_executor(
                None, lambda: self.client.exec_command(command, timeout=timeout)
            )
            
            # 读取输出
            stdout_data = await loop.run_in_executor(None, stdout.read)
            stderr_data = await loop.run_in_executor(None, stderr.read)
            exit_code = stdout.channel.recv_exit_status()
            
            return (
                exit_code,
                stdout_data.decode('utf-8', errors='replace'),
                stderr_data.decode('utf-8', errors='replace')
            )
            
        except Exception as e:
            error_msg = f"命令执行失败: {str(e)}"
            logger.error(error_msg)
            # 检查是否是连接断开导致的错误
            if "Broken pipe" in str(e) or "Connection reset" in str(e) or "Socket is closed" in str(e):
                self.status = ConnectionStatus.ERROR
                self.error_message = f"连接意外断开: {str(e)}"
            return -1, "", error_msg

class SSHManager:
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
        self.async_commands: Dict[str, AsyncCommand] = {}
        self._output_monitor_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._running = True
        
    def generate_connection_id(self, host: str, username: str, port: int) -> str:
        """生成连接ID"""
        return f"{username}@{host}:{port}"
    
    async def create_connection(self, host: str, username: str, port: int = 22,
                              password: Optional[str] = None,
                              private_key: Optional[str] = None,
                              private_key_password: Optional[str] = None) -> str:
        """创建新的SSH连接"""
        connection_id = self.generate_connection_id(host, username, port)
        
        # 如果连接已存在，先断开
        if connection_id in self.connections:
            await self.connections[connection_id].disconnect()
        
        # 创建新连接
        connection = SSHConnection(host, username, port)
        success = await connection.connect(password, private_key, private_key_password)
        
        # 无论连接成功与否，都将连接对象保存（用于查询错误状态）
        self.connections[connection_id] = connection
        
        if success:
            logger.info(f"SSH连接建立成功: {connection_id}")
            return connection_id
        else:
            logger.warning(f"SSH连接失败: {connection_id}, 错误: {connection.error_message}")
            # 不抛出异常，返回连接ID，让调用者检查状态
            return connection_id
    
    async def get_connection_status(self, connection_id: str) -> Dict:
        """获取连接状态"""
        if connection_id not in self.connections:
            return {
                "status": "not_found",
                "message": "连接不存在"
            }
        
        connection = self.connections[connection_id]
        return {
            "status": connection.status.value,
            "host": connection.host,
            "username": connection.username,
            "port": connection.port,
            "error_message": connection.error_message
        }
    
    async def list_connections(self) -> Dict[str, Dict]:
        """列出所有连接及其状态"""
        result = {}
        for conn_id, connection in self.connections.items():
            result[conn_id] = {
                "status": connection.status.value,
                "host": connection.host,
                "username": connection.username,
                "port": connection.port,
                "error_message": connection.error_message
            }
        return result
    
    async def disconnect(self, connection_id: str) -> bool:
        """断开指定连接"""
        if connection_id not in self.connections:
            return False
        
        await self.connections[connection_id].disconnect()
        del self.connections[connection_id]
        return True
    
    async def execute_command(self, connection_id: str, command: str, 
                            timeout: int = 30) -> Dict:
        """在指定连接上执行命令"""
        if connection_id not in self.connections:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "连接不存在"
            }
        
        connection = self.connections[connection_id]
        
        # 检查连接状态
        if connection.status != ConnectionStatus.CONNECTED:
            error_msg = connection.error_message or "连接未建立"
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"连接失败: {error_msg}"
            }
        
        try:
            exit_code, stdout, stderr = await connection.execute_command(command, timeout)
            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"命令执行失败: {str(e)}"
            }
    
    async def disconnect_all(self):
        """断开所有连接"""
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
    
    async def start_async_command(self, connection_id: str, command: str) -> str:
        """启动异步命令执行"""
        if connection_id not in self.connections:
            raise Exception("连接不存在")
        
        connection = self.connections[connection_id]
        if connection.status != ConnectionStatus.CONNECTED:
            raise Exception("连接未建立")
        
        # 生成命令ID
        command_id = str(uuid.uuid4())
        
        # 创建异步命令对象
        async_cmd = AsyncCommand(
            command_id=command_id,
            connection_id=connection_id,
            command=command,
            status=CommandStatus.RUNNING,
            start_time=time.time()
        )
        
        try:
            # 在线程池中执行命令
            loop = asyncio.get_event_loop()
            stdin, stdout, stderr = await loop.run_in_executor(
                None, lambda: connection.client.exec_command(command)
            )
            
            async_cmd.process = stdout.channel
            self.async_commands[command_id] = async_cmd
            
            # 启动输出监控任务
            if self._output_monitor_task is None:
                self._output_monitor_task = asyncio.create_task(self._monitor_command_outputs())
            
            logger.info(f"异步命令已启动: {command_id} ({command})")
            return command_id
            
        except Exception as e:
            async_cmd.status = CommandStatus.FAILED
            async_cmd.end_time = time.time()
            raise Exception(f"启动异步命令失败: {str(e)}")
    
    async def _monitor_command_outputs(self):
        """监控所有运行中命令的输出"""
        while self._running and self.async_commands:
            tasks = []
            for command_id, async_cmd in self.async_commands.items():
                if async_cmd.status == CommandStatus.RUNNING and async_cmd.process:
                    tasks.append(self._collect_command_output(command_id, async_cmd))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(0.1)  # 每100ms检查一次
    
    async def _collect_command_output(self, command_id: str, async_cmd: AsyncCommand):
        """收集单个命令的输出"""
        try:
            if async_cmd.process and async_cmd.process.recv_ready():
                # 读取stdout
                while async_cmd.process.recv_ready():
                    data = async_cmd.process.recv(4096)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        async_cmd.stdout_buffer.append(text)
                        async_cmd.stdout_size += len(text)
            
            if async_cmd.process and async_cmd.process.recv_stderr_ready():
                # 读取stderr
                while async_cmd.process.recv_stderr_ready():
                    data = async_cmd.process.recv_stderr(4096)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        async_cmd.stderr_buffer.append(text)
                        async_cmd.stderr_size += len(text)
            
            # 检查命令是否完成
            if async_cmd.process and async_cmd.process.exit_status_ready():
                exit_code = async_cmd.process.recv_exit_status()
                async_cmd.exit_code = exit_code
                async_cmd.end_time = time.time()
                
                if exit_code == 0:
                    async_cmd.status = CommandStatus.COMPLETED
                else:
                    async_cmd.status = CommandStatus.FAILED
                
                # 读取剩余输出（不再递归调用）
                try:
                    if async_cmd.process.recv_ready():
                        while async_cmd.process.recv_ready():
                            data = async_cmd.process.recv(4096)
                            if data:
                                text = data.decode('utf-8', errors='replace')
                                async_cmd.stdout_buffer.append(text)
                                async_cmd.stdout_size += len(text)
                    
                    if async_cmd.process.recv_stderr_ready():
                        while async_cmd.process.recv_stderr_ready():
                            data = async_cmd.process.recv_stderr(4096)
                            if data:
                                text = data.decode('utf-8', errors='replace')
                                async_cmd.stderr_buffer.append(text)
                                async_cmd.stderr_size += len(text)
                except:
                    pass  # 忽略读取剩余输出时的错误
                
                logger.info(f"异步命令完成: {command_id} (退出码: {exit_code})")
                
        except Exception as e:
            logger.error(f"收集命令输出时出错 {command_id}: {e}")
            async_cmd.status = CommandStatus.FAILED
            async_cmd.end_time = time.time()
    
    async def get_command_status(self, command_id: str) -> Dict:
        """获取异步命令状态和最新输出"""
        if command_id not in self.async_commands:
            return {
                "status": "not_found",
                "message": "命令不存在"
            }
        
        async_cmd = self.async_commands[command_id]
        
        # 手动收集一次最新输出
        if async_cmd.status == CommandStatus.RUNNING:
            await self._collect_command_output(command_id, async_cmd)
        
        return {
            "command_id": command_id,
            "connection_id": async_cmd.connection_id,
            "command": async_cmd.command,
            "status": async_cmd.status.value,
            "start_time": async_cmd.start_time,
            "end_time": async_cmd.end_time,
            "duration": (async_cmd.end_time or time.time()) - async_cmd.start_time,
            "exit_code": async_cmd.exit_code,
            "stdout_size": async_cmd.stdout_size,
            "stderr_size": async_cmd.stderr_size,
            "stdout": "".join(async_cmd.stdout_buffer),
            "stderr": "".join(async_cmd.stderr_buffer)
        }
    
    async def list_async_commands(self) -> Dict[str, Dict]:
        """列出所有异步命令状态"""
        result = {}
        for command_id, async_cmd in self.async_commands.items():
            # 手动收集一次最新输出
            if async_cmd.status == CommandStatus.RUNNING:
                await self._collect_command_output(command_id, async_cmd)
            
            result[command_id] = {
                "connection_id": async_cmd.connection_id,
                "command": async_cmd.command,
                "status": async_cmd.status.value,
                "start_time": async_cmd.start_time,
                "duration": (async_cmd.end_time or time.time()) - async_cmd.start_time,
                "exit_code": async_cmd.exit_code,
                "stdout_size": async_cmd.stdout_size,
                "stderr_size": async_cmd.stderr_size
            }
        return result
    
    async def terminate_command(self, command_id: str) -> bool:
        """终止异步命令"""
        if command_id not in self.async_commands:
            return False
        
        async_cmd = self.async_commands[command_id]
        
        try:
            if async_cmd.process:
                # 使用close()方法来终止SSH通道
                async_cmd.process.close()
                async_cmd.status = CommandStatus.TERMINATED
                async_cmd.end_time = time.time()
                logger.info(f"异步命令已终止: {command_id}")
                return True
        except Exception as e:
            logger.error(f"终止命令失败 {command_id}: {e}")
        
        return False
    
    async def cleanup_completed_commands(self, max_age: float = 3600):
        """清理已完成的命令（默认保留1小时）"""
        current_time = time.time()
        to_remove = []
        
        for command_id, async_cmd in self.async_commands.items():
            if (async_cmd.status in [CommandStatus.COMPLETED, CommandStatus.FAILED, CommandStatus.TERMINATED] 
                and async_cmd.end_time 
                and current_time - async_cmd.end_time > max_age):
                to_remove.append(command_id)
        
        for command_id in to_remove:
            del self.async_commands[command_id]
            logger.info(f"清理已完成的命令: {command_id}")
        
        return len(to_remove)
    
    async def start_health_check(self, interval: int = 30):
        """启动连接健康检查任务"""
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(self._health_check_loop(interval))
        logger.info("连接健康检查任务已启动")
    
    async def stop_health_check(self):
        """停止连接健康检查任务"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("连接健康检查任务已停止")
    
    async def start_keepalive(self, interval: int = 120):
        """启动keep-alive任务"""
        if self._keepalive_task:
            return
        
        self._keepalive_task = asyncio.create_task(self._keepalive_loop(interval))
        logger.info("SSH keep-alive任务已启动")
    
    async def stop_keepalive(self):
        """停止keep-alive任务"""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            self._keepalive_task = None
            logger.info("SSH keep-alive任务已停止")
    
    async def _keepalive_loop(self, interval: int):
        """keep-alive循环"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._send_keepalive_to_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"keep-alive循环出错: {e}")
    
    async def _send_keepalive_to_all_connections(self):
        """向所有活跃连接发送keep-alive信号"""
        for connection_id, connection in self.connections.items():
            if connection.status == ConnectionStatus.CONNECTED:
                if not await connection.send_keepalive():
                    logger.debug(f"keep-alive失败，连接可能已断开: {connection_id}")
    
    async def _health_check_loop(self, interval: int):
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._check_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")
    
    async def _check_all_connections(self):
        """检查所有连接的健康状态"""
        disconnected_connections = []
        
        for connection_id, connection in self.connections.items():
            if connection.status == ConnectionStatus.CONNECTED:
                if not await connection.is_healthy():
                    logger.warning(f"检测到连接断开: {connection_id}")
                    disconnected_connections.append(connection_id)
        
        # 清理断开的连接上的异步命令
        for connection_id in disconnected_connections:
            await self._cleanup_commands_on_disconnected_connection(connection_id)
    
    async def _cleanup_commands_on_disconnected_connection(self, connection_id: str):
        """清理断开连接上的异步命令"""
        commands_to_cleanup = []
        
        for command_id, async_cmd in self.async_commands.items():
            if async_cmd.connection_id == connection_id and async_cmd.status == CommandStatus.RUNNING:
                commands_to_cleanup.append(command_id)
        
        for command_id in commands_to_cleanup:
            try:
                # 终止命令
                await self.terminate_command(command_id)
                # 更新命令状态
                if command_id in self.async_commands:
                    self.async_commands[command_id].status = CommandStatus.FAILED
                    self.async_commands[command_id].end_time = time.time()
                    self.async_commands[command_id].exit_code = -1
                logger.info(f"已清理断开连接上的命令: {command_id}")
            except Exception as e:
                logger.error(f"清理命令失败 {command_id}: {e}")
    
    async def shutdown(self):
        """关闭管理器，清理所有资源"""
        self._running = False
        
        # 停止keep-alive
        await self.stop_keepalive()
        
        # 停止健康检查
        await self.stop_health_check()
        
        # 终止所有运行中的命令
        for command_id in list(self.async_commands.keys()):
            if self.async_commands[command_id].status == CommandStatus.RUNNING:
                await self.terminate_command(command_id)
        
        # 停止监控任务
        if self._output_monitor_task:
            self._output_monitor_task.cancel()
            try:
                await self._output_monitor_task
            except asyncio.CancelledError:
                pass
        
        # 断开所有连接
        await self.disconnect_all()