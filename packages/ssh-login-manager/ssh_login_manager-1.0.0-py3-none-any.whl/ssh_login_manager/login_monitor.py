"""
登录失败监控器
负责监控SSH登录失败尝试和IP封锁管理
"""

import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class LoginMonitor:
    """登录失败监控器"""
    
    def __init__(self, log_file: str = "/var/log/auth.log"):
        self.log_file = log_file
        self.fail2ban_config_dir = "/etc/fail2ban"
    
    def get_failed_login_attempts(self, hours: int = 24) -> List[Dict[str, str]]:
        """获取指定时间段内的失败登录尝试"""
        if not os.path.exists(self.log_file):
            raise FileNotFoundError(f"认证日志文件不存在: {self.log_file}")
        
        failed_logins = []
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 解析日志时间戳
                    log_time = self._parse_log_timestamp(line)
                    if log_time and log_time >= time_threshold:
                        # 检查失败登录
                        if self._is_failed_login(line):
                            ip_address = self._extract_ip(line)
                            username = self._extract_username(line)
                            
                            if ip_address and username:
                                failed_logins.append({
                                    'timestamp': log_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'username': username,
                                    'ip_address': ip_address,
                                    'log_line': line.strip()
                                })
        except Exception as e:
            raise RuntimeError(f"读取日志文件失败: {e}")
        
        return failed_logins
    
    def get_failed_attempts_by_ip(self, hours: int = 24) -> Dict[str, int]:
        """按IP统计失败登录次数"""
        failed_logins = self.get_failed_login_attempts(hours)
        ip_counts = {}
        
        for login in failed_logins:
            ip = login['ip_address']
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
        
        return ip_counts
    
    def block_ip_with_iptables(self, ip_address: str, duration_hours: int = 24) -> bool:
        """使用iptables封锁IP"""
        if not self._validate_ip(ip_address):
            raise ValueError(f"无效的IP地址格式: {ip_address}")
        
        try:
            # 检查是否已存在封锁规则
            check_cmd = f"iptables -L INPUT -n | grep {ip_address}"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if ip_address in result.stdout:
                return True  # 已存在封锁规则
            
            # 添加封锁规则
            block_cmd = f"iptables -A INPUT -s {ip_address} -p tcp --dport 22 -j DROP"
            subprocess.run(block_cmd, shell=True, check=True)
            
            # 保存iptables规则
            save_cmd = "iptables-save > /etc/iptables/rules.v4"
            subprocess.run(save_cmd, shell=True, check=True)
            
            # 设置定时解除封锁
            if duration_hours > 0:
                unblock_time = datetime.now() + timedelta(hours=duration_hours)
                cron_time = unblock_time.strftime("%M %H %d %m *")
                cron_cmd = f"(crontab -l 2>/dev/null; echo '{cron_time} iptables -D INPUT -s {ip_address} -p tcp --dport 22 -j DROP') | crontab -"
                subprocess.run(cron_cmd, shell=True, check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"封锁IP失败: {e}")
    
    def unblock_ip(self, ip_address: str) -> bool:
        """解除IP封锁"""
        try:
            # 移除iptables规则
            unblock_cmd = f"iptables -D INPUT -s {ip_address} -p tcp --dport 22 -j DROP"
            subprocess.run(unblock_cmd, shell=True, check=True)
            
            # 保存iptables规则
            save_cmd = "iptables-save > /etc/iptables/rules.v4"
            subprocess.run(save_cmd, shell=True, check=True)
            
            # 移除定时任务
            remove_cron_cmd = f"crontab -l | grep -v '{ip_address}' | crontab -"
            subprocess.run(remove_cron_cmd, shell=True, check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"解除IP封锁失败: {e}")
    
    def setup_fail2ban_protection(self, max_retry: int = 3, 
                                 ban_time: int = 3600) -> bool:
        """设置Fail2Ban保护"""
        try:
            # 检查Fail2Ban是否已安装
            check_cmd = "which fail2ban-client"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            
            if result.returncode != 0:
                raise RuntimeError("Fail2Ban未安装，请先安装Fail2Ban")
            
            # 创建SSH jail配置
            jail_config = f"""
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = {max_retry}
bantime = {ban_time}
findtime = 600
"""
            
            jail_file = os.path.join(self.fail2ban_config_dir, "jail.d", "ssh.conf")
            os.makedirs(os.path.dirname(jail_file), exist_ok=True)
            
            with open(jail_file, 'w') as f:
                f.write(jail_config)
            
            # 重启Fail2Ban服务
            restart_cmd = "systemctl restart fail2ban"
            subprocess.run(restart_cmd, shell=True, check=True)
            
            return True
        except Exception as e:
            raise RuntimeError(f"设置Fail2Ban失败: {e}")
    
    def _parse_log_timestamp(self, log_line: str) -> Optional[datetime]:
        """解析日志时间戳"""
        # 匹配格式: "Jan 01 12:00:00"
        timestamp_pattern = r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
        match = re.search(timestamp_pattern, log_line)
        
        if match:
            timestamp_str = match.group(1)
            current_year = datetime.now().year
            
            try:
                return datetime.strptime(f"{current_year} {timestamp_str}", 
                                       "%Y %b %d %H:%M:%S")
            except ValueError:
                return None
        
        return None
    
    def _is_failed_login(self, log_line: str) -> bool:
        """检查是否为失败登录记录"""
        failed_patterns = [
            r'Failed password for',
            r'authentication failure',
            r'Connection closed by.*\[preauth\]'
        ]
        
        return any(re.search(pattern, log_line) for pattern in failed_patterns)
    
    def _extract_ip(self, log_line: str) -> Optional[str]:
        """从日志行中提取IP地址"""
        ip_pattern = r'(?:[0-9]{1,3}\\.){3}[0-9]{1,3}'
        match = re.search(ip_pattern, log_line)
        return match.group() if match else None
    
    def _extract_username(self, log_line: str) -> Optional[str]:
        """从日志行中提取用户名"""
        # 匹配格式: "Failed password for username"
        pattern = r'Failed password for (\\S+)'
        match = re.search(pattern, log_line)
        return match.group(1) if match else None
    
    def _validate_ip(self, ip_address: str) -> bool:
        """验证IP地址格式"""
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$')
        return bool(ip_pattern.match(ip_address))