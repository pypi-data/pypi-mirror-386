"""
systemd服务管理模块
提供通用的服务管理功能
"""

import os
import subprocess
from pathlib import Path


class ServiceManager:
    """通用的systemd服务管理器"""
    
    def __init__(self, service_name, executable_path, user="root", group="root", 
                 description=None, working_directory=None, environment_vars=None):
        """
        初始化通用的服务管理器
        
        Args:
            service_name: 服务名称
            executable_path: 可执行文件的完整路径
            user: 运行用户，默认为root
            group: 运行组，默认为root
            description: 服务描述，默认为服务名称
            working_directory: 工作目录，默认为None
            environment_vars: 环境变量字典，默认为None
        """
        self.service_name = service_name
        self.executable_path = executable_path
        self.user = user
        self.group = group
        self.description = description or f"{service_name} Service"
        self.working_directory = working_directory
        self.environment_vars = environment_vars or {}
        self.service_file_path = f"/etc/systemd/system/{service_name}.service"
    
    def check_systemd_available(self):
        """检查systemd是否可用"""
        try:
            result = subprocess.run(["systemctl", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def create_service_file(self, command_args="", description=None):
        """
        创建systemd服务文件
        
        Args:
            command_args: 完整的命令行参数字符串，默认为空
            description: 服务描述，默认为初始化时设置的描述
            
        Returns:
            tuple: (success, message) - 创建是否成功和相关信息
        """
        description = description or self.description
        
        # 构建环境变量部分
        env_vars = ""
        if self.environment_vars:
            for key, value in self.environment_vars.items():
                env_vars += f"Environment={key}={value}\n"
        
        # 构建工作目录部分
        working_dir = ""
        if self.working_directory:
            working_dir = f"WorkingDirectory={self.working_directory}\n"
        
        service_content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={self.user}
Group={self.group}
{working_dir}
{env_vars}
ExecStart={self.executable_path} {command_args}
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # 确保目录存在
            Path("/etc/systemd/system").mkdir(parents=True, exist_ok=True)
            
            # 写入服务文件
            with open(self.service_file_path, 'w') as f:
                f.write(service_content)
            
            # 设置正确的权限
            os.chmod(self.service_file_path, 0o644)
            
            return True, "服务文件创建成功"
            
        except Exception as e:
            return False, f"创建服务文件失败: {str(e)}"
    
    def check_executable(self):
        """
        检查可执行文件是否存在且可执行
        
        Returns:
            tuple: (success, message) - 检查是否成功和相关信息
        """
        try:
            # 检查可执行文件是否存在
            if os.path.exists(self.executable_path):
                # 检查文件是否可执行
                if os.access(self.executable_path, os.X_OK):
                    return True, "可执行文件已存在且可执行"
                else:
                    # 如果文件存在但不可执行，设置可执行权限
                    os.chmod(self.executable_path, 0o755)
                    return True, "可执行文件权限已修复"
            else:
                return False, f"可执行文件不存在: {self.executable_path}"
            
        except Exception as e:
            return False, f"检查可执行文件失败: {str(e)}"
    
    def enable_service(self):
        """启用服务"""
        try:
            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            # 启用服务
            subprocess.run(["systemctl", "enable", self.service_name], check=True)
            
            return True, "服务启用成功"
            
        except subprocess.CalledProcessError as e:
            return False, f"启用服务失败: {str(e)}"
    
    def start_service(self):
        """启动服务"""
        try:
            result = subprocess.run(["systemctl", "start", self.service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "服务启动成功"
            else:
                return False, f"服务启动失败: {result.stderr}"
                
        except subprocess.CalledProcessError as e:
            return False, f"启动服务失败: {str(e)}"
    
    def stop_service(self):
        """停止服务"""
        try:
            result = subprocess.run(["systemctl", "stop", self.service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "服务停止成功"
            else:
                return False, f"服务停止失败: {result.stderr}"
                
        except subprocess.CalledProcessError as e:
            return False, f"停止服务失败: {str(e)}"
    
    def disable_service(self):
        """禁用服务"""
        try:
            result = subprocess.run(["systemctl", "disable", self.service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "服务禁用成功"
            else:
                return False, f"服务禁用失败: {result.stderr}"
                
        except subprocess.CalledProcessError as e:
            return False, f"禁用服务失败: {str(e)}"
    
    def remove_service(self):
        """移除服务"""
        try:
            # 停止服务
            self.stop_service()
            
            # 禁用服务
            self.disable_service()
            
            # 删除服务文件
            if os.path.exists(self.service_file_path):
                os.remove(self.service_file_path)
            
            # 删除可执行文件
            if os.path.exists(self.executable_path):
                os.remove(self.executable_path)
            
            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            return True, "服务移除成功"
            
        except Exception as e:
            return False, f"移除服务失败: {str(e)}"
    
    def get_service_status(self):
        """
        获取服务状态，全面检测服务是否存在
        
        Returns:
            tuple: (exists, status_info) - 服务是否存在和状态信息
        """
        try:
            # 方法1：检查服务文件是否存在
            service_file_exists = os.path.exists(self.service_file_path)
            
            # 方法2：检查systemd是否知道该服务
            result_list = subprocess.run(["systemctl", "list-unit-files", self.service_name], 
                                       capture_output=True, text=True)
            
            # 如果systemctl list-unit-files返回0且输出包含服务名，说明服务存在
            service_listed = result_list.returncode == 0 and self.service_name in result_list.stdout
            
            # 方法3：检查服务状态
            result_status = subprocess.run(["systemctl", "status", self.service_name], 
                                         capture_output=True, text=True)
            
            # 分析状态输出判断服务是否存在
            status_exists = False
            if result_status.returncode == 0:
                # 服务正在运行或已停止但存在
                status_exists = True
            elif result_status.returncode == 3:
                # 服务不存在或未加载
                status_exists = False
            else:
                # 其他情况，检查输出中是否包含"loaded"或服务名
                status_exists = "loaded" in result_status.stdout.lower() or \
                              self.service_name in result_status.stdout
            
            # 综合判断：只要有一种方法认为服务存在，就认为服务存在
            service_exists = service_file_exists or service_listed or status_exists
            
            # 构建详细的状态信息
            status_info = f"服务检测结果:\n"
            status_info += f"- 服务文件存在: {service_file_exists}\n"
            status_info += f"- systemd列表中存在: {service_listed}\n"
            status_info += f"- 服务状态检测: {status_exists}\n"
            status_info += f"- 综合判断服务存在: {service_exists}\n"
            
            if service_exists:
                # 如果服务存在，获取详细状态信息
                if result_status.returncode == 0:
                    # 提取关键状态信息
                    lines = result_status.stdout.split('\n')
                    for line in lines:
                        if 'Active:' in line:
                            status_info += f"- 服务状态: {line.strip()}\n"
                        elif 'Loaded:' in line:
                            status_info += f"- 加载状态: {line.strip()}\n"
            else:
                status_info += "- 服务不存在或未在systemd中注册\n"
            
            return service_exists, status_info
            
        except Exception as e:
            # 如果出现异常，保守地认为服务不存在
            return False, f"检测服务状态时出错: {str(e)}"

    def register_service(self, command_args=""):
        """
        注册systemd服务
        
        Args:
            command_args: 完整的命令行参数字符串，默认为空
            
        Returns:
            tuple: (success, message) - 注册是否成功和相关信息
        """
        # 检查systemd是否可用
        if not self.check_systemd_available():
            return False, "systemd不可用，无法注册服务"
        
        # 检查权限
        if os.geteuid() != 0:
            return False, "需要root权限来注册systemd服务"
        
        try:
            # 检查可执行文件
            success, message = self.check_executable()
            if not success:
                return False, message
            
            # 创建服务文件
            success, message = self.create_service_file(command_args)
            if not success:
                return False, message
            
            # 启用服务
            success, message = self.enable_service()
            if not success:
                return False, message
            
            # 启动服务
            success, message = self.start_service()
            if not success:
                return False, message
            
            return True, "systemd服务注册成功，服务已启动并设置为开机自启"
            
        except Exception as e:
            return False, f"注册服务失败: {str(e)}"


def main():
    """测试函数"""
    # 使用通用的服务管理器
    manager = ServiceManager(
        service_name="test-service",
        executable_path="/usr/bin/echo",
        description="Test Service for Generic Service Manager"
    )
    
    # 检查systemd
    if manager.check_systemd_available():
        print("systemd可用")
    else:
        print("systemd不可用")
    
    # 测试服务状态
    success, status = manager.get_service_status()
    print(f"服务状态: {success}")
    print(f"状态信息: {status}")


if __name__ == "__main__":
    main()