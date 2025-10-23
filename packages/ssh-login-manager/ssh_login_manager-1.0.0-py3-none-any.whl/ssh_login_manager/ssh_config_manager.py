"""
SSH配置管理器
负责管理SSH配置文件（/etc/ssh/sshd_config）
"""

import os
import re
from typing import List, Dict, Optional


class SSHConfigManager:
    """SSH配置文件管理器"""
    
    def __init__(self, config_path: str = "/etc/ssh/sshd_config"):
        self.config_path = config_path
        self.backup_dir = "/var/backup/ssh"
    
    def read_config(self) -> List[Dict[str, str]]:
        """读取SSH配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"SSH配置文件不存在: {self.config_path}")
        
        configs = []
        with open(self.config_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析配置行：指令 值
                parts = line.split(None, 1)
                if len(parts) == 2:
                    configs.append({
                        'line_number': line_num,
                        'directive': parts[0],
                        'value': parts[1],
                        'original_line': line
                    })
        
        return configs
    
    def add_user_ip_restriction(self, username: str, ip_address: str) -> bool:
        """添加用户-IP限制规则"""
        # 验证IP地址格式
        if not self._validate_ip(ip_address):
            raise ValueError(f"无效的IP地址格式: {ip_address}")
        
        # 备份配置
        self._backup_config()
        
        try:
            with open(self.config_path, 'a', encoding='utf-8') as f:
                f.write(f"\n# 用户 {username} 只能从 {ip_address} 登录\n")
                f.write(f"Match User {username} Address {ip_address}\n")
                f.write(f"    AllowTCPForwarding no\n")
                f.write(f"    X11Forwarding no\n")
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def remove_user_ip_restriction(self, username: str) -> bool:
        """移除用户-IP限制规则"""
        self._backup_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找并移除相关配置块
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 检查是否匹配用户限制块
                if (line.startswith("Match User") and username in line and 
                    i + 2 < len(lines) and "Address" in line):
                    # 跳过整个配置块（当前行 + 下一行 + 配置行）
                    i += 3
                    # 检查是否有注释行需要跳过
                    while i < len(lines) and lines[i].strip().startswith('#'):
                        i += 1
                else:
                    new_lines.append(lines[i])
                    i += 1
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def add_ip_whitelist(self, ip_address: str) -> bool:
        """添加IP白名单"""
        if not self._validate_ip(ip_address):
            raise ValueError(f"无效的IP地址格式: {ip_address}")
        
        self._backup_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在AllowUsers配置
            if "AllowUsers" in content:
                # 在现有AllowUsers配置后添加IP
                content = re.sub(
                    r'(AllowUsers\\s+[^\\n]*)(\\n)',
                    f'\\1 {ip_address}\\n',
                    content
                )
            else:
                # 添加新的AllowUsers配置
                content += f"\n# IP白名单\nAllowUsers *@{ip_address}\n"
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def _validate_ip(self, ip_address: str) -> bool:
        """验证IP地址格式"""
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$')
        cidr_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$')
        
        return bool(ip_pattern.match(ip_address) or cidr_pattern.match(ip_address))
    
    def _backup_config(self):
        """备份配置文件"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"sshd_config.backup.{timestamp}")
        
        shutil.copy2(self.config_path, backup_path)
    
    def _restore_backup(self):
        """恢复备份配置"""
        # 查找最新的备份文件
        if os.path.exists(self.backup_dir):
            backups = sorted([f for f in os.listdir(self.backup_dir) 
                             if f.startswith("sshd_config.backup.")])
            if backups:
                latest_backup = os.path.join(self.backup_dir, backups[-1])
                shutil.copy2(latest_backup, self.config_path)


import shutil