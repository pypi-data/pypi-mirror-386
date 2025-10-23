"""
SSH登录管理CLI接口
专注于SSH登录限制和IP访问控制
"""

import sys
from .ssh_config_manager import SSHConfigManager
from .ip_access_manager import IPAccessManager
from .login_monitor import LoginMonitor


class SSHCLIInterface:
    """SSH登录管理CLI接口"""
    
    def __init__(self):
        self.ssh_manager = SSHConfigManager()
        self.ip_manager = IPAccessManager()
        self.monitor = LoginMonitor()
        
        self.menu_options = {
            "1": "查看当前SSH配置",
            "2": "添加用户-IP限制",
            "3": "移除用户-IP限制",
            "4": "添加IP白名单",
            "5": "查看登录失败记录",
            "6": "封锁恶意IP",
            "7": "解除IP封锁",
            "8": "设置Fail2Ban保护",
            "9": "退出"
        }
    
    def display_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 50)
        print("      SSH登录管理器")
        print("=" * 50)
        
        for key, value in self.menu_options.items():
            print(f"{key}. {value}")
        
        print("=" * 50)
    
    def run(self):
        """运行CLI接口"""
        print("欢迎使用SSH登录管理器")
        print("专注于SSH登录限制和IP访问控制")
        
        while True:
            self.display_menu()
            choice = input("\n请选择操作 (1-9): ").strip()
            
            if choice == "1":
                self.view_ssh_config()
            elif choice == "2":
                self.add_user_ip_restriction()
            elif choice == "3":
                self.remove_user_ip_restriction()
            elif choice == "4":
                self.add_ip_whitelist()
            elif choice == "5":
                self.view_failed_logins()
            elif choice == "6":
                self.block_malicious_ip()
            elif choice == "7":
                self.unblock_ip()
            elif choice == "8":
                self.setup_fail2ban()
            elif choice == "9":
                print("感谢使用SSH登录管理器！")
                break
            else:
                print("无效选择，请重新输入")
    
    def view_ssh_config(self):
        """查看当前SSH配置"""
        try:
            print("\n正在读取SSH配置...")
            configs = self.ssh_manager.read_config()
            
            if not configs:
                print("✅ SSH配置文件存在，但未找到有效的配置指令")
                print("   配置文件路径: {}".format(self.ssh_manager.config_path))
                print("   可能原因:")
                print("   - 配置文件只包含注释或空行")
                print("   - 配置文件格式不正确")
                print("   - 使用默认SSH配置")
                print("\n💡 提示: 您可以添加用户-IP限制或IP白名单来增强SSH安全性")
                return
            
            print(f"\nSSH配置文件: {self.ssh_manager.config_path}")
            print("-" * 80)
            print(f"{'行号':<4} {'指令':<20} {'值'}")
            print("-" * 80)
            
            for config in configs:
                line_num = config.get('line_number', 'N/A')
                print(f"{line_num:<4} {config['directive']:<20} {config['value']}")
            
            print("-" * 80)
            print(f"✅ 共找到 {len(configs)} 条有效配置指令")
            
        except FileNotFoundError as e:
            print(f"❌ SSH配置文件不存在: {self.ssh_manager.config_path}")
            print("💡 提示: 请确保SSH服务已正确安装")
        except Exception as e:
            print(f"❌ 读取SSH配置失败: {e}")
    
    def add_user_ip_restriction(self):
        """添加用户-IP限制"""
        try:
            print("\n添加用户-IP限制")
            username = input("请输入用户名: ").strip()
            ip_address = input("请输入允许的IP地址 (支持CIDR格式): ").strip()
            
            if not username or not ip_address:
                print("用户名和IP地址不能为空")
                return
            
            # 确认操作
            print(f"\n即将添加限制: 用户 {username} 只能从 {ip_address} 登录SSH")
            confirm = input("确认添加? (y/N): ").strip().lower()
            
            if confirm == 'y':
                # 使用SSH配置管理器添加限制
                success = self.ssh_manager.add_user_ip_restriction(username, ip_address)
                if success:
                    print("✅ 用户-IP限制添加成功")
                    print("请重启SSH服务使配置生效: systemctl restart sshd")
                else:
                    print("❌ 添加失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"添加用户-IP限制失败: {e}")
    
    def remove_user_ip_restriction(self):
        """移除用户-IP限制"""
        try:
            print("\n移除用户-IP限制")
            username = input("请输入用户名: ").strip()
            
            if not username:
                print("用户名不能为空")
                return
            
            # 确认操作
            print(f"\n即将移除用户 {username} 的所有IP限制")
            confirm = input("确认移除? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.ssh_manager.remove_user_ip_restriction(username)
                if success:
                    print("✅ 用户-IP限制移除成功")
                    print("请重启SSH服务使配置生效: systemctl restart sshd")
                else:
                    print("❌ 移除失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"移除用户-IP限制失败: {e}")
    
    def add_ip_whitelist(self):
        """添加IP白名单"""
        try:
            print("\n添加IP白名单")
            ip_address = input("请输入允许的IP地址: ").strip()
            
            if not ip_address:
                print("IP地址不能为空")
                return
            
            # 确认操作
            print(f"\n即将添加IP白名单: {ip_address}")
            confirm = input("确认添加? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.ssh_manager.add_ip_whitelist(ip_address)
                if success:
                    print("✅ IP白名单添加成功")
                    print("请重启SSH服务使配置生效: systemctl restart sshd")
                else:
                    print("❌ 添加失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"添加IP白名单失败: {e}")
    
    def view_failed_logins(self):
        """查看登录失败记录"""
        try:
            print("\n查看登录失败记录")
            hours = input("查看最近多少小时的记录? (默认24): ").strip()
            hours = int(hours) if hours.isdigit() else 24
            
            print(f"\n正在获取最近{hours}小时的登录失败记录...")
            failed_logins = self.monitor.get_failed_login_attempts(hours)
            
            if not failed_logins:
                print("✅ 未发现登录失败记录")
                print("💡 提示信息:")
                print("   - 系统当前没有检测到SSH登录失败尝试")
                print("   - 这可能表示系统安全性良好，或者日志文件位置不正确")
                print("   - 默认监控路径: /var/log/auth.log")
                print("   - 如果使用不同系统，可能需要调整日志文件路径")
                return
            
            print(f"\n发现 {len(failed_logins)} 条登录失败记录:")
            print("-" * 100)
            print(f"{'时间':<20} {'用户名':<15} {'IP地址':<15} {'日志摘要'}")
            print("-" * 100)
            
            for login in failed_logins:
                log_line = login['log_line'][:50] + "..." if len(login['log_line']) > 50 else login['log_line']
                print(f"{login['timestamp']:<20} {login['username']:<15} {login['ip_address']:<15} {log_line}")
            
            print("-" * 100)
            
            # 显示统计信息
            ip_counts = self.monitor.get_failed_attempts_by_ip(hours)
            if ip_counts:
                print("\nIP失败次数统计:")
                for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {ip}: {count} 次失败")
            else:
                print("\n💡 未发现重复失败的IP地址")
                    
        except FileNotFoundError as e:
            print(f"❌ 日志文件不存在: {e}")
            print("💡 提示: 请检查系统日志文件路径，可能需要调整监控配置")
        except Exception as e:
            print(f"❌ 查看登录失败记录失败: {e}")
    
    def block_malicious_ip(self):
        """封锁恶意IP"""
        try:
            print("\n封锁恶意IP")
            ip_address = input("请输入要封锁的IP地址: ").strip()
            
            if not ip_address:
                print("IP地址不能为空")
                return
            
            duration = input("封锁时长(小时，0表示永久，默认24): ").strip()
            duration = int(duration) if duration.isdigit() else 24
            
            # 确认操作
            duration_text = "永久" if duration == 0 else f"{duration}小时"
            print(f"\n即将封锁IP: {ip_address} (时长: {duration_text})")
            confirm = input("确认封锁? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.monitor.block_ip_with_iptables(ip_address, duration)
                if success:
                    print("✅ IP封锁成功")
                else:
                    print("❌ 封锁失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"封锁恶意IP失败: {e}")
    
    def unblock_ip(self):
        """解除IP封锁"""
        try:
            print("\n解除IP封锁")
            ip_address = input("请输入要解除封锁的IP地址: ").strip()
            
            if not ip_address:
                print("IP地址不能为空")
                return
            
            # 确认操作
            print(f"\n即将解除IP封锁: {ip_address}")
            confirm = input("确认解除? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.monitor.unblock_ip(ip_address)
                if success:
                    print("✅ IP解除封锁成功")
                else:
                    print("❌ 解除封锁失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"解除IP封锁失败: {e}")
    
    def setup_fail2ban(self):
        """设置Fail2Ban保护"""
        try:
            print("\n设置Fail2Ban保护")
            max_retry = input("最大失败尝试次数 (默认3): ").strip()
            max_retry = int(max_retry) if max_retry.isdigit() else 3
            
            ban_time = input("封锁时长(秒，默认3600): ").strip()
            ban_time = int(ban_time) if ban_time.isdigit() else 3600
            
            # 确认操作
            print(f"\n即将设置Fail2Ban保护:")
            print(f"  最大失败尝试次数: {max_retry}")
            print(f"  封锁时长: {ban_time} 秒")
            confirm = input("确认设置? (y/N): ").strip().lower()
            
            if confirm == 'y':
                success = self.monitor.setup_fail2ban_protection(max_retry, ban_time)
                if success:
                    print("✅ Fail2Ban保护设置成功")
                else:
                    print("❌ 设置失败")
            else:
                print("操作已取消")
                
        except Exception as e:
            print(f"设置Fail2Ban保护失败: {e}")


def main():
    """主函数"""
    try:
        cli = SSHCLIInterface()
        cli.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()