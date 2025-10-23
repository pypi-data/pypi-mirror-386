"""
IP访问控制管理器
负责管理基于IP的访问控制（使用pam_access.so和/etc/security/access.conf）
"""

import os
import re
from typing import List, Dict, Optional


class IPAccessManager:
    """IP访问控制管理器"""
    
    def __init__(self, access_conf_path: str = "/etc/security/access.conf"):
        self.access_conf_path = access_conf_path
        self.backup_dir = "/var/backup/ssh"
    
    def read_access_rules(self) -> List[Dict[str, str]]:
        """读取访问控制规则"""
        if not os.path.exists(self.access_conf_path):
            raise FileNotFoundError(f"访问控制配置文件不存在: {self.access_conf_path}")
        
        rules = []
        with open(self.access_conf_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析访问控制规则：权限:用户:来源
                parts = line.split(':')
                if len(parts) >= 3:
                    rules.append({
                        'line_number': line_num,
                        'permission': parts[0].strip(),
                        'users': parts[1].strip(),
                        'origins': parts[2].strip(),
                        'original_line': line
                    })
        
        return rules
    
    def add_ip_restriction(self, username: str, ip_address: str, 
                          permission: str = "-") -> bool:
        """添加IP限制规则"""
        if not self._validate_ip(ip_address):
            raise ValueError(f"无效的IP地址格式: {ip_address}")
        
        if permission not in ["+", "-"]:
            raise ValueError("权限必须是 '+' (允许) 或 '-' (拒绝)")
        
        self._backup_access_conf()
        
        try:
            with open(self.access_conf_path, 'a', encoding='utf-8') as f:
                f.write(f"\n# SSH登录限制 - 用户 {username} 从 {ip_address}\n")
                f.write(f"{permission}:{username}:{ip_address}\n")
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def add_ip_range_restriction(self, username: str, ip_range: str, 
                                permission: str = "-") -> bool:
        """添加IP范围限制规则"""
        if not self._validate_ip_range(ip_range):
            raise ValueError(f"无效的IP范围格式: {ip_range}")
        
        self._backup_access_conf()
        
        try:
            with open(self.access_conf_path, 'a', encoding='utf-8') as f:
                f.write(f"\n# SSH登录限制 - 用户 {username} 从 {ip_range}\n")
                f.write(f"{permission}:{username}:{ip_range}\n")
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def remove_ip_restriction(self, username: str, ip_address: str = None) -> bool:
        """移除IP限制规则"""
        self._backup_access_conf()
        
        try:
            with open(self.access_conf_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            skip_next = False
            
            for i, line in enumerate(lines):
                if skip_next:
                    skip_next = False
                    continue
                
                stripped_line = line.strip()
                
                # 跳过注释行
                if stripped_line.startswith('#'):
                    # 检查注释是否包含用户信息
                    if username in stripped_line:
                        skip_next = True
                        continue
                    new_lines.append(line)
                    continue
                
                # 检查规则行
                if stripped_line and ':' in stripped_line:
                    parts = stripped_line.split(':')
                    if len(parts) >= 3:
                        rule_username = parts[1].strip()
                        rule_ip = parts[2].strip()
                        
                        # 如果指定了IP，精确匹配；否则匹配所有该用户的规则
                        if (rule_username == username and 
                            (ip_address is None or rule_ip == ip_address)):
                            # 跳过规则行
                            continue
                
                new_lines.append(line)
            
            with open(self.access_conf_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            self._restore_backup()
            raise e
    
    def _validate_ip(self, ip_address: str) -> bool:
        """验证IP地址格式"""
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$')
        return bool(ip_pattern.match(ip_address))
    
    def _validate_ip_range(self, ip_range: str) -> bool:
        """验证IP范围格式"""
        # 支持格式：192.168.1.0/24, 192.168.1.0/255.255.255.0, 192.168.1.0-192.168.1.255
        cidr_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$')
        subnet_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$')
        range_pattern = re.compile(r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}-(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$')
        
        return bool(cidr_pattern.match(ip_range) or 
                   subnet_pattern.match(ip_range) or 
                   range_pattern.match(ip_range))
    
    def _backup_access_conf(self):
        """备份访问控制配置文件"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"access.conf.backup.{timestamp}")
        
        shutil.copy2(self.access_conf_path, backup_path)
    
    def _restore_backup(self):
        """恢复备份配置"""
        if os.path.exists(self.backup_dir):
            backups = sorted([f for f in os.listdir(self.backup_dir) 
                             if f.startswith("access.conf.backup.")])
            if backups:
                latest_backup = os.path.join(self.backup_dir, backups[-1])
                shutil.copy2(latest_backup, self.access_conf_path)


import shutil