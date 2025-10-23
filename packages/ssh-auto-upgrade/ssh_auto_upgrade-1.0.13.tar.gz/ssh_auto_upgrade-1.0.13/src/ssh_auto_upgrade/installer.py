"""
安装器模块
负责执行OpenSSH的安装过程
"""

import subprocess
import re

# 导入编译模块
from .compile import compile_openssh
# 导入服务管理和文件管理模块
from .service_manager import ServiceManager
from .installer_file_manager import InstallerFileManager
from .installer_service_manager import InstallerServiceManager

class Installer:
    """安装器类"""
    
    def __init__(self, download_url, install_dir="/usr/local/openssh", ssl_dir=None):
        """
        初始化安装器
        
        Args:
            download_url: OpenSSH源码下载URL
            install_dir: 安装目录，默认为/usr/local/openssh
            ssl_dir: OpenSSL安装目录，可选
        """
        self.download_url = download_url
        self.install_dir = install_dir
        self.ssl_dir = ssl_dir
        # 初始化服务管理和文件管理模块
        self.service_manager = ServiceManager()
        self.file_manager = InstallerFileManager()
        # 初始化安装器服务管理器
        self.installer_service_manager = InstallerServiceManager()
    
    def delete_old_openssh_dir(self):
        """
        删除旧版本的OpenSSH目录
        
        Returns:
            bool: 删除是否成功
        """
        old_dir = "/usr/local/.ssh/openssh"
        # 委托给文件管理模块
        return self.file_manager.delete_directory(old_dir)

    def install_openssh(self):
        """
        执行OpenSSH安装
        
        Returns:
            bool: 安装是否成功
        """
        try:
            print(f"开始安装OpenSSH...")
            print(f"下载URL: {self.download_url}")
            print(f"安装目录: {self.install_dir}")
            if self.ssl_dir:
                print(f"OpenSSL目录: {self.ssl_dir}")
            
            # 第一步：停止所有SSH守护服务，避免升级过程中被误检测执行重置
            print("停止SSH守护服务...")
            if not self.installer_service_manager.stop_ssh_guard_services():
                print("警告: SSH守护服务停止可能不完整，继续执行安装...")
            
            # 第二步：禁用原生SSH服务，避免端口冲突
            print("禁用原生SSH服务...")
            if not self.installer_service_manager.disable_native_ssh_service():
                print("警告: 原生SSH服务禁用可能不完整，继续执行安装...")
            
            # 第三步：直接调用编译模块进行安装
            success = compile_openssh(
                download_url=self.download_url,
                install_dir=self.install_dir,
                ssl_dir=self.ssl_dir
            )
            
            # 无论安装成功还是失败，都执行以下操作
            if success:
                # 安装成功后，先删除旧版本目录
                if not self.delete_old_openssh_dir():
                    print("警告: 删除旧版本目录失败，继续执行后续操作...")
                
                print("OpenSSH安装成功!")
            else:
                print("OpenSSH安装失败!")
            
            # 第四步：确保SSH守护服务被重新启动
            ssh_services_started = self.installer_service_manager.start_ssh_guard_services()
            if ssh_services_started:
                print("SSH守护服务已重新启动")
            else:
                print("警告: SSH守护服务启动失败")
                
            return success
                
        except Exception as e:
            # 异常情况下也确保SSH守护服务被重新启动
            print(f"安装过程中发生异常: {e}")
            ssh_services_started = self.installer_service_manager.start_ssh_guard_services()
            if ssh_services_started:
                print("SSH守护服务已重新启动")
            else:
                print("警告: SSH守护服务启动失败")
            raise Exception(f"安装失败: {e}")
    
    def verify_installation(self):
        """
        验证安装是否成功
        
        Returns:
            dict: 验证结果
        """
        try:
            # 检查SSH服务状态
            result = subprocess.run(
                ['systemctl', 'status', 'sshd'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            ssh_active = result.returncode == 0
            
            # 检查新版本
            version_result = subprocess.run(
                ['ssh', '-V'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            version_match = re.search(r'OpenSSH_(\d+\.\d+p\d+)', version_result.stderr)
            current_version = version_match.group(1) if version_match else "未知"
            
            return {
                'success': ssh_active,
                'ssh_service_active': ssh_active,
                'current_version': current_version,
                'service_status': result.stdout if ssh_active else result.stderr
            }
            
        except subprocess.SubprocessError as e:
            return {
                'success': False,
                'error': str(e),
                'ssh_service_active': False,
                'current_version': "未知"
            }
    
    def rollback_if_needed(self, original_version):
        """
        如果需要，回滚到原始版本
        
        Args:
            original_version: 原始版本号
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            print("检测到安装问题，尝试回滚...")
            
            # 这里可以实现回滚逻辑
            # 由于OpenSSH安装比较复杂，回滚可能需要系统包管理器
            # 暂时只记录警告
            print(f"警告: 安装可能有问题，原始版本为: {original_version}")
            print("建议手动检查系统状态")
            
            return False
            
        except Exception as e:
            print(f"回滚失败: {e}")
            return False