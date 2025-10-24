import os


def fix_envs_shi_ban(path: str) -> bool:
    """修复conda环境中的shebang路径
    Fix shebang path in conda environment

    Args:
        path (str): 要修复的文件路径 / File path to fix

    Returns:
        bool: 是否成功修复 / Whether the fix was successful
    """
    path = os.path.abspath(path)

    if not os.path.exists(path):
        return False

    if "/envs/" not in path:
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            line = f.readline()
            shi_ban = line
    except Exception:
        return False

    if not shi_ban.startswith("#!"):
        return False

    shi_ban_path = shi_ban[2:]

    env_directory_path = os.path.dirname(path)

    while os.path.basename(os.path.dirname(env_directory_path)) != "envs":
        env_directory_path = os.path.dirname(env_directory_path)

    python_bin = os.path.join(env_directory_path, "bin", "python")

    if not os.path.exists(python_bin):
        return False

    if shi_ban_path == python_bin:
        return False

    shi_ban = f"!#{python_bin}"

    # 读取文件 / Read File
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 替换第一行 / Replace First Line
    lines[0] = shi_ban

    # 写回文件 / Write Back to File
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True
