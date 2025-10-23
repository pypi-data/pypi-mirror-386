"""
SSH配置管理模块
负责检测和修改SSH配置文件中的root登录设置
"""

import os
import re


class SSHConfigManager:
    """SSH配置管理器"""
    
    def __init__(self, ssh_config_path="/etc/ssh/sshd_config"):
        """
        初始化SSH配置管理器
        
        Args:
            ssh_config_path: SSH配置文件路径
        """
        self.ssh_config_path = ssh_config_path
        self.backup_config_path = f"{ssh_config_path}.backup"
    
    def config_file_exists(self):
        """检查配置文件是否存在"""
        return os.path.exists(self.ssh_config_path)
    
    def get_current_root_login_setting(self):
        """
        获取当前root登录设置
        
        Returns:
            dict: {
                'exists': bool,  # 配置文件是否存在
                'permit_root_login': str or None,  # 当前设置值
                'commented': bool  # 是否被注释
            }
        """
        if not self.config_file_exists():
            return {
                'exists': False,
                'permit_root_login': None,
                'commented': True
            }
        
        try:
            with open(self.ssh_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找PermitRootLogin设置
            pattern = r'^\s*(#?)\s*PermitRootLogin\s+(\S+)'
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            
            if matches:
                # 取最后一个匹配项（配置文件中的最后一个设置生效）
                commented, value = matches[-1]
                return {
                    'exists': True,
                    'permit_root_login': value.strip(),
                    'commented': bool(commented)
                }
            else:
                # 没有找到PermitRootLogin设置
                return {
                    'exists': True,
                    'permit_root_login': None,
                    'commented': True
                }
                
        except Exception as e:
            return {
                'exists': False,
                'permit_root_login': None,
                'commented': True,
                'error': str(e)
            }
    
    def is_root_login_enabled(self):
        """
        检查root登录是否启用
        
        Returns:
            bool: True表示启用，False表示禁用
        """
        setting = self.get_current_root_login_setting()
        
        if not setting['exists']:
            # 配置文件不存在，默认启用
            return True
        
        if setting['permit_root_login'] is None:
            # 没有设置PermitRootLogin，默认启用
            return True
        
        if setting['commented']:
            # 设置被注释，默认启用
            return True
        
        # 检查设置值
        value = setting['permit_root_login'].lower()
        if value in ['yes', 'true', '1', 'without-password', 'prohibit-password']:
            return True
        elif value in ['no', 'false', '0']:
            return False
        else:
            # 未知值，默认启用
            return True
    
    def backup_config(self):
        """备份配置文件"""
        if not self.config_file_exists():
            return False, "配置文件不存在，无需备份"
        
        try:
            import shutil
            shutil.copy2(self.ssh_config_path, self.backup_config_path)
            return True, f"配置文件已备份到 {self.backup_config_path}"
        except Exception as e:
            return False, f"备份配置文件失败: {str(e)}"
    
    def set_root_login(self, enable=True, force=False):
        """
        设置root登录权限
        
        Args:
            enable: True启用，False禁用
            force: 是否强制设置（即使配置文件不存在也创建）
            
        Returns:
            tuple: (success, message)
        """
        # 备份配置文件
        backup_success, backup_message = self.backup_config()
        
        if not self.config_file_exists() and not force:
            return False, "配置文件不存在，使用force参数强制创建"
        
        try:
            # 读取现有内容或创建新文件
            if self.config_file_exists():
                with open(self.ssh_config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # 构建新的设置行
            setting_value = "yes" if enable else "no"
            new_setting_line = f"PermitRootLogin {setting_value}\n"
            
            # 查找并替换现有的PermitRootLogin设置
            pattern = r'^\s*(#?)\s*PermitRootLogin\s+\S+'
            found = False
            new_lines = []
            
            for line in lines:
                if re.match(pattern, line, re.IGNORECASE):
                    if not found:
                        # 替换第一个匹配的设置
                        new_lines.append(new_setting_line)
                        found = True
                    # 跳过其他匹配的设置
                else:
                    new_lines.append(line)
            
            # 如果没有找到现有设置，在文件末尾添加
            if not found:
                # 确保文件以换行符结束
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] = new_lines[-1] + '\n'
                new_lines.append(new_setting_line)
            
            # 写入新内容
            with open(self.ssh_config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # 设置正确的文件权限
            os.chmod(self.ssh_config_path, 0o644)
            
            action = "启用" if enable else "禁用"
            return True, f"root登录已{action}"
            
        except Exception as e:
            # 恢复备份
            if backup_success and os.path.exists(self.backup_config_path):
                try:
                    shutil.copy2(self.backup_config_path, self.ssh_config_path)
                except:
                    pass
            return False, f"设置root登录失败: {str(e)}"
    
    def restart_ssh_service(self):
        """重启SSH服务使配置生效"""
        try:
            import subprocess
            
            # 检查systemd是否可用
            result = subprocess.run(["systemctl", "is-active", "ssh"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # 使用systemd重启服务
                subprocess.run(["systemctl", "restart", "ssh"], check=True)
                return True, "SSH服务重启成功"
            else:
                # 尝试使用service命令
                subprocess.run(["service", "ssh", "restart"], check=True)
                return True, "SSH服务重启成功"
                
        except subprocess.CalledProcessError as e:
            return False, f"重启SSH服务失败: {str(e)}"
        except Exception as e:
            return False, f"重启SSH服务失败: {str(e)}"


def check_root_login_status():
    """
    检查root登录状态的便捷函数
    
    Returns:
        dict: {
            'enabled': bool,  # 是否启用
            'config_exists': bool,  # 配置文件是否存在
            'current_setting': str,  # 当前设置
            'message': str  # 状态信息
        }
    """
    manager = SSHConfigManager()
    setting = manager.get_current_root_login_setting()
    enabled = manager.is_root_login_enabled()
    
    if not setting['exists']:
        return {
            'enabled': True,
            'config_exists': False,
            'current_setting': '默认启用（配置文件不存在）',
            'message': 'SSH配置文件不存在，root登录默认启用'
        }
    
    if setting['permit_root_login'] is None:
        return {
            'enabled': True,
            'config_exists': True,
            'current_setting': '默认启用（未设置PermitRootLogin）',
            'message': 'SSH配置文件中未设置PermitRootLogin，root登录默认启用'
        }
    
    if setting['commented']:
        return {
            'enabled': True,
            'config_exists': True,
            'current_setting': f'默认启用（{setting["permit_root_login"]}被注释）',
            'message': f'PermitRootLogin设置被注释，root登录默认启用'
        }
    
    return {
        'enabled': enabled,
        'config_exists': True,
        'current_setting': setting['permit_root_login'],
        'message': f'root登录{"启用" if enabled else "禁用"} (PermitRootLogin {setting["permit_root_login"]})'
    }