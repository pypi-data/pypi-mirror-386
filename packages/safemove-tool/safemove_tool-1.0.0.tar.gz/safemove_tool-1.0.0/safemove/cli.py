#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全移动/复制文件工具
功能：将文件从源文件夹安全移动或复制到目标文件夹
处理文件名冲突：
- 文件完全相同时覆盖（严格模式）
- 文件大小相同时覆盖（默认模式）
- 文件不同时添加_1后缀
"""

import os
import shutil
import sys
import argparse
import filecmp
from pathlib import Path


def get_file_size(file_path):
    """获取文件大小"""
    return os.path.getsize(file_path)


def files_are_identical(file1, file2):
    """比较两个文件是否完全相同（逐字节比较）"""
    return filecmp.cmp(file1, file2, shallow=False)


def safe_copy_file(src_file, dst_folder, strict_mode=False):
    """
    安全复制单个文件
    
    Args:
        src_file (str): 源文件路径
        dst_folder (str): 目标文件夹路径
        strict_mode (bool): 是否启用严格模式（逐字节比较）
    """
    src_path = Path(src_file)
    dst_path = Path(dst_folder) / src_path.name
    
    # 如果目标文件不存在，直接复制
    if not dst_path.exists():
        shutil.copy2(str(src_path), str(dst_path))
        print(f"已复制: {src_path.name}")
        return
    
    # 如果目标文件存在，根据模式比较文件
    if strict_mode:
        # 严格模式：逐字节比较文件
        if files_are_identical(src_path, dst_path):
            # 文件完全相同，覆盖
            os.remove(dst_path)
            shutil.copy2(str(src_path), str(dst_path))
            print(f"已覆盖(文件相同): {src_path.name}")
        else:
            # 文件不同，添加_1后缀
            new_name = src_path.stem + "_1" + src_path.suffix
            new_dst_path = Path(dst_folder) / new_name
            shutil.copy2(str(src_path), str(new_dst_path))
            print(f"已复制(添加_1后缀): {new_name}")
    else:
        # 默认模式：比较文件大小
        src_size = get_file_size(src_path)
        dst_size = get_file_size(dst_path)
        
        if src_size == dst_size:
            # 文件大小相同，覆盖
            os.remove(dst_path)
            shutil.copy2(str(src_path), str(dst_path))
            print(f"已覆盖(大小相同): {src_path.name}")
        else:
            # 文件大小不同，添加_1后缀
            new_name = src_path.stem + "_1" + src_path.suffix
            new_dst_path = Path(dst_folder) / new_name
            shutil.copy2(str(src_path), str(new_dst_path))
            print(f"已复制(添加_1后缀): {new_name}")


def safe_move_file(src_file, dst_folder, strict_mode=False):
    """
    安全移动单个文件
    
    Args:
        src_file (str): 源文件路径
        dst_folder (str): 目标文件夹路径
        strict_mode (bool): 是否启用严格模式（逐字节比较）
    """
    src_path = Path(src_file)
    dst_path = Path(dst_folder) / src_path.name
    
    # 如果目标文件不存在，直接移动
    if not dst_path.exists():
        shutil.move(str(src_path), str(dst_path))
        print(f"已移动: {src_path.name}")
        return
    
    # 如果目标文件存在，根据模式比较文件
    if strict_mode:
        # 严格模式：逐字节比较文件
        if files_are_identical(src_path, dst_path):
            # 文件完全相同，覆盖
            os.remove(dst_path)
            shutil.move(str(src_path), str(dst_path))
            print(f"已覆盖(文件相同): {src_path.name}")
        else:
            # 文件不同，添加_1后缀
            new_name = src_path.stem + "_1" + src_path.suffix
            new_dst_path = Path(dst_folder) / new_name
            shutil.move(str(src_path), str(new_dst_path))
            print(f"已移动(添加_1后缀): {new_name}")
    else:
        # 默认模式：比较文件大小
        src_size = get_file_size(src_path)
        dst_size = get_file_size(dst_path)
        
        if src_size == dst_size:
            # 文件大小相同，覆盖
            os.remove(dst_path)
            shutil.move(str(src_path), str(dst_path))
            print(f"已覆盖(大小相同): {src_path.name}")
        else:
            # 文件大小不同，添加_1后缀
            new_name = src_path.stem + "_1" + src_path.suffix
            new_dst_path = Path(dst_folder) / new_name
            shutil.move(str(src_path), str(new_dst_path))
            print(f"已移动(添加_1后缀): {new_name}")


def safe_copy_files(src_folder, dst_folder, strict_mode=False):
    """
    安全复制文件夹中的所有文件
    
    Args:
        src_folder (str): 源文件夹路径
        dst_folder (str): 目标文件夹路径
        strict_mode (bool): 是否启用严格模式（逐字节比较）
    """
    src_path = Path(src_folder)
    dst_path = Path(dst_folder)
    
    # 检查源文件夹是否存在
    if not src_path.exists():
        print(f"错误: 源文件夹 '{src_folder}' 不存在")
        return False
    
    # 检查源路径是否为文件夹
    if not src_path.is_dir():
        print(f"错误: '{src_folder}' 不是一个文件夹")
        return False
    
    # 创建目标文件夹（如果不存在）
    dst_path.mkdir(parents=True, exist_ok=True)
    
    # 遍历源文件夹中的所有文件
    copied_count = 0
    for item in src_path.iterdir():
        if item.is_file():
            try:
                safe_copy_file(str(item), str(dst_path), strict_mode)
                copied_count += 1
            except Exception as e:
                print(f"复制文件 '{item.name}' 时出错: {e}")
    
    print(f"总共复制了 {copied_count} 个文件")
    return True


def safe_move_files(src_folder, dst_folder, strict_mode=False):
    """
    安全移动文件夹中的所有文件
    
    Args:
        src_folder (str): 源文件夹路径
        dst_folder (str): 目标文件夹路径
        strict_mode (bool): 是否启用严格模式（逐字节比较）
    """
    src_path = Path(src_folder)
    dst_path = Path(dst_folder)
    
    # 检查源文件夹是否存在
    if not src_path.exists():
        print(f"错误: 源文件夹 '{src_folder}' 不存在")
        return False
    
    # 检查源路径是否为文件夹
    if not src_path.is_dir():
        print(f"错误: '{src_folder}' 不是一个文件夹")
        return False
    
    # 创建目标文件夹（如果不存在）
    dst_path.mkdir(parents=True, exist_ok=True)
    
    # 遍历源文件夹中的所有文件
    moved_count = 0
    for item in src_path.iterdir():
        if item.is_file():
            try:
                safe_move_file(str(item), str(dst_path), strict_mode)
                moved_count += 1
            except Exception as e:
                print(f"移动文件 '{item.name}' 时出错: {e}")
    
    print(f"总共移动了 {moved_count} 个文件")
    return True


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="安全移动或复制文件，智能处理文件名冲突",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  safe-move -x /path/to/source /path/to/dest      # 移动文件
  safe-move -c /path/to/source /path/to/dest      # 复制文件
  safe-move -x -s /path/to/source /path/to/dest   # 移动文件(严格模式)
  safe-move -c -s /path/to/source /path/to/dest   # 复制文件(严格模式)

冲突处理规则:
  - 默认模式: 文件大小相同时覆盖，不同时添加 _1 后缀
  - 严格模式: 文件内容完全相同时覆盖，不同时添加 _1 后缀
        """
    )
    
    parser.add_argument("source", help="源文件夹路径")
    parser.add_argument("destination", help="目标文件夹路径")
    parser.add_argument("-x", "--move", action="store_true", 
                       help="移动模式")
    parser.add_argument("-c", "--copy", action="store_true", 
                       help="复制模式")
    parser.add_argument("-s", "--strict", action="store_true", 
                       help="严格模式（逐字节比较文件内容）")
    parser.add_argument("-v", "--version", action="version", 
                       version="%(prog)s 1.0.0")
    
    args = parser.parse_args()
    
    # 检查操作模式
    if args.move and args.copy:
        print("错误: 不能同时指定移动和复制模式")
        sys.exit(1)
    
    if not args.move and not args.copy:
        print("错误: 必须指定操作模式 (-x 移动 或 -c 复制)")
        sys.exit(1)
    
    source_folder = args.source
    destination_folder = args.destination
    strict_mode = args.strict
    
    # 执行相应操作
    if args.move:
        print(f"移动模式{' (严格模式)' if strict_mode else ''}: {source_folder} -> {destination_folder}")
        success = safe_move_files(source_folder, destination_folder, strict_mode)
        if success:
            print("✅ 文件移动完成")
        else:
            print("❌ 文件移动失败")
            sys.exit(1)
    elif args.copy:
        print(f"复制模式{' (严格模式)' if strict_mode else ''}: {source_folder} -> {destination_folder}")
        success = safe_copy_files(source_folder, destination_folder, strict_mode)
        if success:
            print("✅ 文件复制完成")
        else:
            print("❌ 文件复制失败")
            sys.exit(1)


if __name__ == "__main__":
    main()