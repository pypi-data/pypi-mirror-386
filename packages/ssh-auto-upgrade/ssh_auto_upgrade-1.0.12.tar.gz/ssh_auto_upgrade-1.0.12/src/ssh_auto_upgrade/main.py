"""
SSH自动升级工具主程序
"""

import argparse
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ssh_auto_upgrade.version_detector import VersionDetector
from ssh_auto_upgrade.installer import Installer
from ssh_auto_upgrade.service_manager import ServiceManager
from ssh_auto_upgrade.ssh_config_manager import SSHConfigManager
from ssh_auto_upgrade.logger import setup_logger
from ssh_auto_upgrade.systemd_checker import ensure_systemd_only
from ssh_auto_upgrade.legacy_cleaner import ensure_systemd_only_startup
from ssh_auto_upgrade.mirror_checker import MirrorChecker
from ssh_auto_upgrade.time_checker import TimeChecker





def main():
    """主函数 - 专为守护进程模式设计"""
    parser = argparse.ArgumentParser(description='OpenSSH自动升级守护进程工具')
    parser.add_argument('--mirror', '-m', 
                        default='https://mirrors.aliyun.com/openssh/portable/',
                        help='OpenSSH镜像源URL')
    parser.add_argument('--install-dir', '-i',
                        default='/usr/local/openssh',
                        help='OpenSSH安装目录')
    parser.add_argument('--download-dir', '-d',
                        default='/tmp/ssh-upgrade',
                        help='下载目录')
    parser.add_argument('--log-dir', '-l',
                        default='/var/log/ssh-auto-upgrade',
                        help='日志目录')
    parser.add_argument('--force', '-f',
                        action='store_true',
                        help='强制升级，即使版本相同也执行安装')
    parser.add_argument('--service',
                        action='store_true',
                        help='注册为systemd服务')
    parser.add_argument('--upgrade-time', '-t',
                        default='00:00:00-08:00:00',
                        help='升级时间段，格式为 HH:MM:SS-HH:MM:SS，默认00:00:00-08:00:00')
    parser.add_argument('--enable-root-login',
                        action='store_true',
                        help='升级后启用root登录')
    parser.add_argument('--disable-root-login',
                        action='store_true',
                        help='升级后禁用root登录')
    
    args = parser.parse_args()
    
    # 第一步：强制systemd检查
    ensure_systemd_only()
    
    # 设置日志
    logger = setup_logger(args.log_dir)
    
    # 第二步：镜像地址检测（在依赖检测之前）
    print("检查镜像地址可用性...")
    logger.info("检查镜像地址可用性")
    
    mirror_checker = MirrorChecker()
    mirror_available = mirror_checker.check_mirror_availability(args.mirror)
    
    if not mirror_available:
        error_msg = f"镜像地址不可用: {args.mirror}"
        print(f"错误: {error_msg}")
        logger.error(error_msg)
        return 1
    
    print("✓ 镜像地址检测通过")
    logger.info("镜像地址检测通过")
    
    # 第三步：依赖检测（无论是否服务注册都需要）
    print("检查编译依赖...")
    logger.info("检查编译依赖")
    
    from ssh_auto_upgrade.dependencies import DependencyManager
    dependency_manager = DependencyManager()
    
    # 确保所有依赖已安装（安装失败时会直接终止程序）
    deps_success, deps_message = dependency_manager.ensure_dependencies(auto_install=True)
    
    # 检查依赖检测结果，如果失败则终止程序
    if not deps_success:
        print(f"错误: {deps_message}")
        logger.error(f"依赖检查失败: {deps_message}")
        return 1
    
    # 如果依赖检查通过，继续执行
    print("✓ 编译依赖检查通过")
    logger.info("编译依赖检查通过")
    
    # 第二步：服务注册判断
    if args.service:
        try:
            print("正在注册systemd服务...")
            service_manager = ServiceManager(
                mirror_url=args.mirror,
                install_dir=args.install_dir,
                download_dir=args.download_dir,
                log_dir=args.log_dir,
                upgrade_time=args.upgrade_time,
                enable_root_login=args.enable_root_login,
                disable_root_login=args.disable_root_login
            )
            
            # 检查systemd是否可用
            if not service_manager.check_systemd_available():
                print("错误: systemd不可用，无法注册服务")
                return 1
            
            # 检查权限
            if os.geteuid() != 0:
                print("错误: 需要root权限来注册systemd服务")
                return 1
            
            # 注册服务
            success, message = service_manager.register_service()
            
            if success:
                print(f"成功: {message}")
                print("\n服务已注册，可以使用以下命令管理:")
                print("  systemctl start ssh-auto-upgrade    # 启动服务")
                print("  systemctl stop ssh-auto-upgrade     # 停止服务")
                print("  systemctl status ssh-auto-upgrade   # 查看服务状态")
                print("  systemctl enable ssh-auto-upgrade   # 启用开机自启")
                print("  systemctl disable ssh-auto-upgrade  # 禁用开机自启")
                return 0
            else:
                print(f"错误: {message}")
                return 1
                
        except Exception as e:
            print(f"服务注册失败: {str(e)}")
            return 1
    
    # 第三步：循环程序（如果没有传入服务注册参数）
    print("启动OpenSSH自动升级守护进程...")
    logger.info("启动OpenSSH自动升级守护进程")
    
    import time
    import signal
    import sys
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        print(f"收到信号 {signum}，正在退出...")
        logger.info(f"收到信号 {signum}，守护进程正在退出")
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 解析升级时间段
    try:
        time_checker = TimeChecker()
        start_time_str, end_time_str = time_checker.parse_time_range(args.upgrade_time)
        
        print(f"升级时间段设置为: {start_time_str} - {end_time_str}")
        logger.info(f"升级时间段设置为: {start_time_str} - {end_time_str}")
        
    except ValueError as e:
        print(f"错误: 升级时间段格式无效 - {e}")
        print("请使用格式: HH:MM:SS-HH:MM:SS")
        return 1
    
    # 守护进程主循环
    while True:
        try:
            from datetime import datetime
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # 检查当前时间是否在升级时间段内
            if time_checker.is_time_in_range(start_time_str, end_time_str):
                print(f"当前时间 {current_time} 在升级时间段内，执行版本检查...")
                logger.info(f"当前时间 {current_time} 在升级时间段内，执行版本检查")
                
                # 执行一次升级检查
                print("执行OpenSSH版本检查...")
                logger.info("执行OpenSSH版本检查")
                
                # 检查当前版本
                detector = VersionDetector(args.mirror)
                current_version = detector.check_current_version()
                
                if not current_version:
                    print("无法检测当前OpenSSH版本")
                    logger.warning("无法检测当前OpenSSH版本")
                    time.sleep(3600)  # 等待1小时后重试
                    continue
                
                print(f"当前OpenSSH版本: {current_version}")
                logger.info(f"当前OpenSSH版本: {current_version}")
                
                # 获取最新版本
                latest_version_info = detector.get_latest_version()
                
                print(f"最新OpenSSH版本: {latest_version_info['version']}")
                
                # 检查是否需要升级
                if current_version != latest_version_info['version'] or args.force:
                    print(f"检测到新版本 {latest_version_info['version']}，开始升级...")
                    logger.info(f"检测到新版本 {latest_version_info['version']}，开始升级")
                    
                    # 执行安装
                    installer = Installer(latest_version_info['download_url'], args.install_dir)
                    
                    if installer.install_openssh():
                        # 验证安装
                        verification_result = installer.verify_installation()
                        
                        if verification_result['success']:
                            print(f"OpenSSH升级成功! 新版本: {verification_result['current_version']}")
                            logger.info(f"OpenSSH升级成功! 新版本: {verification_result['current_version']}")
                            
                            # 重启SSH服务
                            service_manager = ServiceManager()
                            if service_manager.restart_ssh_service():
                                print("SSH服务重启成功")
                                logger.info("SSH服务重启成功")
                                
                                # 升级完成后清理传统启动脚本，确保只有systemd管理开机启动
                                try:
                                    ensure_systemd_only_startup()
                                    print("传统启动脚本清理完成，确保只有systemd进行开机启动管理")
                                    logger.info("传统启动脚本清理完成，确保只有systemd进行开机启动管理")
                                except SystemExit as e:
                                    print(f"警告: 传统启动脚本清理失败，但升级已完成: {e}")
                                    logger.warning(f"传统启动脚本清理失败，但升级已完成: {e}")
                                except Exception as e:
                                    print(f"警告: 传统启动脚本清理过程中出错: {e}")
                                    logger.warning(f"传统启动脚本清理过程中出错: {e}")
                                
                                # 处理root登录配置
                                if args.enable_root_login or args.disable_root_login:
                                     config_manager = SSHConfigManager()
                                     if args.enable_root_login:
                                         success, message = config_manager.set_root_login(enable=True, force=True)
                                         if success:
                                             print(f"已启用root登录: {message}")
                                             logger.info(f"已启用root登录: {message}")
                                         else:
                                             print(f"警告: 启用root登录失败: {message}")
                                             logger.warning(f"启用root登录失败: {message}")
                                     elif args.disable_root_login:
                                         success, message = config_manager.set_root_login(enable=False, force=True)
                                         if success:
                                             print(f"已禁用root登录: {message}")
                                             logger.info(f"已禁用root登录: {message}")
                                         else:
                                             print(f"警告: 禁用root登录失败: {message}")
                                             logger.warning(f"禁用root登录失败: {message}")
                                     
                                     # 重启SSH服务以应用配置更改
                                     success, message = config_manager.restart_ssh_service()
                                     if success:
                                         print(f"SSH服务重启成功（应用root登录配置）: {message}")
                                         logger.info(f"SSH服务重启成功（应用root登录配置）: {message}")
                                     else:
                                         print(f"警告: SSH服务重启失败，root登录配置可能未生效: {message}")
                                         logger.warning(f"SSH服务重启失败，root登录配置可能未生效: {message}")
                            else:
                                print("警告: SSH服务重启失败，请手动重启")
                                logger.warning("SSH服务重启失败，请手动重启")
                        else:
                            print("OpenSSH升级失败")
                            logger.error("OpenSSH升级失败")
                    else:
                        print("OpenSSH安装过程失败")
                        logger.error("OpenSSH安装过程失败")
                else:
                    print("当前已是最新版本，无需升级")
                    logger.info("当前已是最新版本，无需升级")
            else:
                print(f"当前时间 {current_time} 不在升级时间段内，跳过检测...")
                logger.info(f"当前时间 {current_time} 不在升级时间段内，跳过检测")
            
            # 等待1小时后再检查
            print("等待1小时后再次检查...")
            logger.info("等待1小时后再次检查")
            time.sleep(3600)  # 1小时
            
        except KeyboardInterrupt:
            print("\n守护进程被用户中断")
            logger.info("守护进程被用户中断")
            break
        except Exception as e:
            print(f"守护进程执行出错: {str(e)}")
            logger.error(f"守护进程执行出错: {str(e)}")
            # 出错后等待5分钟再重试
            time.sleep(300)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())