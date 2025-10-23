import os
import shutil
from tqdm import tqdm


def copyjindu(source, destination, return_size=False):
    """
    智能复制，自动识别文件或文件夹
    只需要提供源路径和目标路径即可
    
    Args:
        source (str): 源文件或文件夹路径
        destination (str): 目标路径
        return_size (bool): 是否返回源的大小（字节数）
    
    Returns:
        如果return_size为True，返回源的大小（字节数）
        否则不返回任何内容
    """
    # 检查源路径是否存在
    if not os.path.exists(source):
        raise ValueError(f"源路径不存在: {source}")

    # 计算源的大小
    source_size = _calculate_source_size(source)

    # 如果是文件
    if os.path.isfile(source):
        _copy_single_file(source, destination)

    # 如果是文件夹
    elif os.path.isdir(source):
        _copy_folder_recursive(source, destination)

    else:
        raise ValueError(f"源路径不是有效的文件或文件夹: {source}")

    # 如果要求返回大小，则返回源的大小
    if return_size:
        return source_size


def get_source_size(source):
    """
    获取源文件或文件夹的大小
    
    Args:
        source (str): 源文件或文件夹路径
    
    Returns:
        int: 源的大小（字节数）
    """
    if not os.path.exists(source):
        raise ValueError(f"源路径不存在: {source}")
    
    return _calculate_source_size(source)


def _calculate_source_size(source):
    """计算源文件或文件夹的大小"""
    if os.path.isfile(source):
        # 单个文件，直接获取大小
        return os.path.getsize(source)
    elif os.path.isdir(source):
        # 文件夹，递归计算所有文件的总大小
        total_size = 0
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size
    else:
        raise ValueError(f"源路径不是有效的文件或文件夹: {source}")


def _copy_single_file(source, destination, buffer_size=1024 * 1024):
    """复制单个文件"""
    # 如果目标是目录，则在目录中创建同名文件
    if os.path.isdir(destination):
        destination = os.path.join(destination, os.path.basename(source))

    # 确保目标目录存在
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    total_size = os.path.getsize(source)
    with open(source, 'rb') as src, open(destination, 'wb') as dst:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"复制文件: {os.path.basename(source)}") as pbar:
            while True:
                buffer = src.read(buffer_size)
                if not buffer:
                    break
                dst.write(buffer)
                pbar.update(len(buffer))


def _copy_folder_recursive(source, destination, buffer_size=1024 * 1024):
    """递归复制整个文件夹"""
    # 如果目标是目录，则在目录中创建同名文件夹
    if os.path.isdir(destination) and not destination.endswith(os.path.sep):
        destination = os.path.join(destination, os.path.basename(source))

    # 创建目标文件夹
    os.makedirs(destination, exist_ok=True)

    # 首先计算总大小
    total_size = 0
    file_list = []

    for root, dirs, files in os.walk(source):
        for file in files:
            src_file = os.path.join(root, file)
            # 计算相对路径
            rel_path = os.path.relpath(src_file, source)
            dst_file = os.path.join(destination, rel_path)
            file_list.append((src_file, dst_file))
            total_size += os.path.getsize(src_file)

    # 复制文件并显示进度
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="复制文件夹") as pbar:
        for src_file, dst_file in file_list:
            # 创建目标目录
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            # 复制文件
            with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
                while True:
                    buffer = src.read(buffer_size)
                    if not buffer:
                        break
                    dst.write(buffer)
                    pbar.update(len(buffer))