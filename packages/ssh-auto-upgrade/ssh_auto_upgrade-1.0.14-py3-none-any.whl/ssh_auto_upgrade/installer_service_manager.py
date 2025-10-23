"""
安装器服务管理模块
专门处理OpenSSH安装过程中的系统服务管理功能
提供安装器特定的服务管理功能，通用服务管理由service_manager.py处理
"""

from .installer_service_detector import InstallerServiceDetector, detect_services_for_installation
from .service_manager import ServiceManager


class InstallerServiceManager:
    """安装器服务管理器"""
    
    def __init__(self):
        """初始化服务管理器"""
        # 使用服务检测器
        self.service_detector = InstallerServiceDetector()
        # 使用通用的服务管理器
        self.service_manager = ServiceManager()
    
    def detect_ssh_guard_services(self):
        """
        检测系统中已安装的SSH防护服务
        
        Returns:
            list: 已安装的SSH防护服务列表
        """
        try:
            # 直接调用服务检测器的检测方法
            return self.service_detector.detect_ssh_guard_services()
        except Exception as e:
            print(f"检测SSH防护服务时出错: {e}")
            return []
    
    def perform_service_detection(self):
        """
        执行完整的服务检测流程
        
        Returns:
            tuple: (ssh_services, non_ssh_services, should_continue)
                   - SSH守护服务列表
                   - 非SSH守护服务列表  
                   - 是否继续注册流程
        """
        try:
            # 调用服务检测器的完整检测流程
            return self.service_detector.perform_service_detection()
        except Exception as e:
            print(f"执行服务检测流程时出错: {e}")
            return [], [], False
    
    def check_and_handle_ssh_guard_services(self):
        """
        检查并处理SSH防护服务
        
        Returns:
            tuple: (ssh_services, should_continue)
                   - SSH守护服务列表
                   - 是否继续安装流程
        """
        try:
            print("=== 开始SSH防护服务检测 ===")
            
            # 执行服务检测
            ssh_services, non_ssh_services, should_continue = self.perform_service_detection()
            
            # 如果有非SSH服务，需要用户确认
            if non_ssh_services:
                print(f"检测到以下非SSH服务: {non_ssh_services}")
                print("这些服务可能与SSH服务冲突，建议重命名或停止这些服务。")
            
            # 如果有SSH服务，显示确认信息
            if ssh_services:
                print(f"检测到以下SSH守护服务: {ssh_services}")
                print("这些服务将被用于SSH连接管理。")
            
            print("=== SSH防护服务检测完成 ===")
            
            return ssh_services, should_continue
            
        except Exception as e:
            print(f"检查和处理SSH防护服务时出错: {e}")
            return [], False
    
    def stop_ssh_guard_services(self):
        """
        停止所有SSH守护服务（包括CLS、xc-ssh等）
        
        Returns:
            bool: 停止是否成功
        """
        try:
            print("=== 开始停止SSH守护服务 ===")
            
            # 获取所有SSH守护服务
            ssh_services, _ = self.check_and_handle_ssh_guard_services()
            
            success = True
            
            # 停止每个SSH守护服务
            for service_name in ssh_services:
                exists, _ = self.service_manager.get_service_status(service_name)
                if exists:
                    stop_success, message = self.service_manager.stop_service(service_name)
                    if stop_success:
                        print(f"✓ {service_name} 服务已停止")
                    else:
                        print(f"✗ {service_name} 服务停止失败: {message}")
                        success = False
                else:
                    print(f"{service_name} 服务不存在，无需停止")
            
            print("=== SSH守护服务停止完成 ===")
            return success
            
        except Exception as e:
            print(f"停止SSH守护服务时出错: {e}")
            return False
    
    def start_ssh_guard_services(self):
        """
        启动所有SSH守护服务（包括CLS、xc-ssh等）
        
        Returns:
            bool: 启动是否成功
        """
        try:
            print("=== 开始启动SSH守护服务 ===")
            
            # 获取所有SSH守护服务
            ssh_services, _ = self.check_and_handle_ssh_guard_services()
            
            success = True
            
            # 启动每个SSH守护服务
            for service_name in ssh_services:
                exists, _ = self.service_manager.get_service_status(service_name)
                if exists:
                    start_success, message = self.service_manager.start_service(service_name)
                    if start_success:
                        print(f"✓ {service_name} 服务已启动")
                    else:
                        print(f"✗ {service_name} 服务启动失败: {message}")
                        success = False
                else:
                    print(f"{service_name} 服务不存在，无需启动")
            
            print("=== SSH守护服务启动完成 ===")
            return success
            
        except Exception as e:
            print(f"启动SSH守护服务时出错: {e}")
            return False
    
    def check_native_ssh_service(self):
        """
        检查系统原生SSH服务状态
        
        Returns:
            dict: 包含原生SSH服务信息的字典
        """
        # 直接检查原生SSH服务
        ssh_services = ['ssh', 'openssh-server']
        
        for service_name in ssh_services:
            exists, status_info = self.service_manager.get_service_status(service_name)
            if exists:
                # 使用ServiceManager的方法检查服务状态
                # 从状态信息中推断服务是否活跃和启用
                is_active = "Active: active" in status_info
                is_enabled = "enabled" in status_info.lower()
                
                return {
                    'exists': True,
                    'service_name': service_name,
                    'is_active': is_active,
                    'is_enabled': is_enabled,
                    'is_native': True
                }
        
        return {'exists': False, 'service_name': None, 'is_active': False, 'is_enabled': False, 'is_native': False}
    
    def disable_native_ssh_service(self):
        """
        禁用原生SSH服务，避免端口冲突
        
        Returns:
            bool: 禁用是否成功
        """
        ssh_info = self.check_native_ssh_service()
        
        if not ssh_info['exists']:
            print("系统未安装原生SSH服务，无需禁用")
            return True
        
        service_name = ssh_info['service_name']
        print(f"检测到原生SSH服务: {service_name}")
        
        success = True
        
        # 停止原生SSH服务
        if ssh_info['is_active']:
            stop_success, message = self.service_manager.stop_service(service_name)
            if not stop_success:
                print(f"警告: 原生SSH服务 {service_name} 停止失败: {message}")
                success = False
        
        # 禁用原生SSH服务开机自启
        if ssh_info['is_enabled']:
            disable_success, message = self.service_manager.disable_service(service_name)
            if not disable_success:
                print(f"警告: 原生SSH服务 {service_name} 禁用开机自启失败: {message}")
                success = False
        
        if success:
            print("原生SSH服务已成功禁用")
        else:
            print("警告: 原生SSH服务禁用可能不完整")
        
        return success


def main():
    """测试函数"""
    manager = InstallerServiceManager()
    
    # 测试SSH防护服务检测
    ssh_services, should_continue = manager.check_and_handle_ssh_guard_services()
    print(f"检测到的SSH防护服务: {ssh_services}")
    print(f"是否继续安装流程: {should_continue}")
    
    # 测试统一的SSH守护服务管理
    print("\n=== 测试SSH守护服务管理 ===")
    if ssh_services:
        stopped = manager.stop_ssh_guard_services()
        print(f"SSH守护服务停止结果: {stopped}")
        
        started = manager.start_ssh_guard_services()
        print(f"SSH守护服务启动结果: {started}")
    
    # 测试原生SSH服务管理
    print("\n=== 测试原生SSH服务管理 ===")
    ssh_info = manager.check_native_ssh_service()
    print(f"原生SSH服务信息: {ssh_info}")
    
    if ssh_info['exists']:
        disabled = manager.disable_native_ssh_service()
        print(f"原生SSH服务禁用结果: {disabled}")


if __name__ == "__main__":
    main()