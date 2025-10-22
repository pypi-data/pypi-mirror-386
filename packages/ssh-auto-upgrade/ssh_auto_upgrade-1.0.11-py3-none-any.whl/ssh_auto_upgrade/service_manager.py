"""
systemd服务管理模块
"""

import os
import subprocess
from pathlib import Path


class ServiceManager:
    """systemd服务管理器"""
    
    def __init__(self, service_name="ssh-auto-upgrade", install_dir="/usr/local/bin",
                 mirror_url="https://mirrors.aliyun.com/openssh/portable/",
                 download_dir="/tmp/ssh-upgrade", log_dir="/var/log/ssh-auto-upgrade",
                 upgrade_time="00:00:00-08:00:00", enable_root_login=False, 
                 disable_root_login=False, user="root", group="root"):
        """
        初始化服务管理器
        
        Args:
            service_name: 服务名称
            install_dir: 安装目录
            mirror_url: 镜像URL
            download_dir: 下载目录
            log_dir: 日志目录
            upgrade_time: 升级时间段
            enable_root_login: 启用root登录
            disable_root_login: 禁用root登录
            user: 运行用户
            group: 运行组
        """
        self.service_name = service_name
        self.install_dir = install_dir
        self.mirror_url = mirror_url
        self.download_dir = download_dir
        self.log_dir = log_dir
        self.upgrade_time = upgrade_time
        self.enable_root_login = enable_root_login
        self.disable_root_login = disable_root_login
        self.user = user
        self.group = group
        self.service_file_path = f"/etc/systemd/system/{service_name}.service"
        self.executable_path = f"{install_dir}/ssh-auto-upgrade"
    
    def check_systemd_available(self):
        """检查systemd是否可用"""
        try:
            result = subprocess.run(["systemctl", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def create_service_file(self, description="OpenSSH Auto Upgrade Service"):
        """
        创建systemd服务文件
        
        Args:
            description: 服务描述
        """
        # 构建命令行参数
        cmd_args = f" --mirror {self.mirror_url}"
        cmd_args += f" --download-dir {self.download_dir}"
        cmd_args += f" --log-dir {self.log_dir}"
        cmd_args += f" --upgrade-time {self.upgrade_time}"
        
        if self.enable_root_login:
            cmd_args += " --enable-root-login"
        elif self.disable_root_login:
            cmd_args += " --disable-root-login"
        
        service_content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=simple
User={self.user}
Group={self.group}
ExecStart={self.executable_path} {cmd_args}
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
    
    def install_executable(self):
        """安装可执行文件到系统目录"""
        try:
            # 获取当前脚本路径
            current_script = Path(__file__).parent.parent / "ssh_auto_upgrade" / "main.py"
            
            # 确保安装目录存在
            Path(self.install_dir).mkdir(parents=True, exist_ok=True)
            
            # 创建可执行文件
            executable_content = f"""#!/usr/bin/env python3
import sys
from ssh_auto_upgrade.main import main

if __name__ == "__main__":
    sys.exit(main())
"""
            
            with open(self.executable_path, 'w') as f:
                f.write(executable_content)
            
            # 设置可执行权限
            os.chmod(self.executable_path, 0o755)
            
            return True, "可执行文件安装成功"
            
        except Exception as e:
            return False, f"安装可执行文件失败: {str(e)}"
    
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
        """获取服务状态"""
        try:
            result = subprocess.run(["systemctl", "status", self.service_name], 
                                  capture_output=True, text=True)
            
            return result.returncode == 0, result.stdout
            
        except subprocess.CalledProcessError as e:
            return False, f"获取服务状态失败: {str(e)}"
    
    def check_service_exists(self, service_name):
        """
        检查服务是否存在
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 服务是否存在
        """
        try:
            result = subprocess.run(["systemctl", "list-unit-files", service_name], 
                                  capture_output=True, text=True)
            
            # 检查输出中是否包含服务名称
            return service_name in result.stdout
            
        except subprocess.CalledProcessError:
            return False
    
    def register_service(self):
        """
        注册systemd服务
        
        在注册服务前会检查是否存在SSH守护服务（cls和xc-ssh.service），
        如果是SSH守护服务则可以继续，因为在升级期间会停止这些服务，升级完成后再启动。
        如果不是SSH守护服务则建议重命名以避免冲突。
        """
        # 检查systemd是否可用
        if not self.check_systemd_available():
            return False, "systemd不可用，无法注册服务"
        
        # 检查权限
        if os.geteuid() != 0:
            return False, "需要root权限来注册systemd服务"
        
        # 检查是否存在SSH守护服务
        ssh_services = []
        non_ssh_services = []
        
        # 检查cls服务是否存在
        if self.check_service_exists('cls'):
            print("⚠️  检测到cls服务存在")
            print("请确认cls服务是否为SSH守护服务：")
            print("   - 如果是SSH守护服务，可以继续注册，升级期间会停止该服务，升级完成后启动")
            print("   - 如果不是SSH守护服务，建议重命名该服务以避免冲突")
            
            while True:
                response = input("cls服务是否为SSH守护服务？(y/n): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    ssh_services.append('cls')
                    print("确认cls为SSH守护服务，继续注册...")
                    break
                elif response in ['n', 'no', '否']:
                    non_ssh_services.append('cls')
                    print("cls不是SSH守护服务，建议重命名该服务")
                    break
                else:
                    print("请输入 'y' 或 'n' 来确认")
        
        # 检查xc-ssh.service是否存在
        if self.check_service_exists('xc-ssh'):
            print("⚠️  检测到xc-ssh.service存在")
            print("请确认xc-ssh.service是否为SSH守护服务：")
            print("   - 如果是SSH守护服务，可以继续注册，升级期间会停止该服务，升级完成后启动")
            print("   - 如果不是SSH守护服务，建议重命名该服务以避免冲突")
            
            while True:
                response = input("xc-ssh.service是否为SSH守护服务？(y/n): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    ssh_services.append('xc-ssh')
                    print("确认xc-ssh为SSH守护服务，继续注册...")
                    break
                elif response in ['n', 'no', '否']:
                    non_ssh_services.append('xc-ssh')
                    print("xc-ssh不是SSH守护服务，建议重命名该服务")
                    break
                else:
                    print("请输入 'y' 或 'n' 来确认")
        
        # 如果检测到非SSH守护服务，建议用户处理
        if non_ssh_services:
            print(f"⚠️  警告: 检测到以下非SSH守护服务: {', '.join(non_ssh_services)}")
            print("这些服务可能与SSH自动升级服务产生冲突。")
            print("建议重命名这些服务或使用不同的端口以避免冲突。")
            print("如果继续注册，可能会在升级期间影响这些服务的正常运行。")
            
            while True:
                response = input("是否继续注册服务？(y/n): ").strip().lower()
                if response in ['y', 'yes', '是']:
                    print("继续注册服务...")
                    break
                elif response in ['n', 'no', '否']:
                    return False, "用户取消注册流程"
                else:
                    print("请输入 'y' 或 'n' 来确认是否继续")
        
        # 如果检测到SSH守护服务，说明可以继续
        if ssh_services:
            print(f"✓ 确认以下服务为SSH守护服务: {', '.join(ssh_services)}")
            print("这些服务将在升级期间被停止，升级完成后重新启动。")
        
        try:
            # 安装可执行文件
            success, message = self.install_executable()
            if not success:
                return False, message
            
            # 创建服务文件
            success, message = self.create_service_file()
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
    manager = ServiceManager()
    
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