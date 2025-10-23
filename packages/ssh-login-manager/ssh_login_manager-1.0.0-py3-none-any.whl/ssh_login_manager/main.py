"""
SSH Login Manager - Main entry point
"""

import sys
import argparse
from .ssh_cli_interface import main as cli_main


def main():
    """Main entry point for SSH Login Manager"""
    parser = argparse.ArgumentParser(
        description="SSH Login Manager - 专注于SSH登录限制和IP访问控制",
        add_help=False
    )
    parser.add_argument(
        "--version", 
        action="store_true", 
        help="显示版本信息"
    )
    parser.add_argument(
        "-h", "--help", 
        action="store_true", 
        help="显示帮助信息"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print("SSH Login Manager v1.0.0")
        print("专注于SSH登录限制和IP访问控制")
        sys.exit(0)
    elif args.help:
        parser.print_help()
        sys.exit(0)
    
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\n程序已退出")
        sys.exit(0)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()