import os
import sys
import time
import zipfile
import subprocess
import shutil
import requests
import psutil
import socket
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Callable
from dataclasses import dataclass


# 单例端口管理器（服务类插件端口记录）
class PortManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.port_map = {}  # {插件名: 端口号}
        return cls._instance

    def get_port(self, plugin_name: str) -> Optional[int]:
        return self.port_map.get(plugin_name)

    def set_port(self, plugin_name: str, port: int) -> None:
        self.port_map[plugin_name] = port

    def clear_port(self, plugin_name: str) -> None:
        if plugin_name in self.port_map:
            del self.port_map[plugin_name]

    def clear_all(self) -> None:
        self.port_map.clear()


# 插件配置数据类
@dataclass
class PluginConfig:
    name: str
    url: str
    extract_folder: str
    app_relative_path: str
    is_service: bool = False  # 是否为服务类型插件


class PluginManager:
    def __init__(self, config: Dict[str, Any] = None, config_path: str = "plugins.yaml"):
        """通过 YAML 配置文件初始化插件管理器"""
        self.config_path = Path(config_path)
        self.config = config if config is not None else self._load_yaml_config()  # 加载 YAML 配置
        self.plugin_install_dir = Path(self.config.get('plugin_install_dir', 'plugins'))
        self.plugins = self._parse_plugins(self.config.get('plugins', []))
        self.port_manager = PortManager()
        self._ensure_dir(self.plugin_install_dir)

    def _load_yaml_config(self) -> Dict:
        """加载并解析 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 配置解析错误: {str(e)}")

    def _parse_plugins(self, plugin_list: List[Dict]) -> List[PluginConfig]:
        """将 YAML 中的插件列表解析为数据类"""
        return [
            PluginConfig(
                name=p['name'],
                url=p['url'],
                extract_folder=p['extract_folder'],
                app_relative_path=p['app_relative_path'],
                is_service=p.get('is_service', False)
            ) for p in plugin_list
        ]

    def _ensure_dir(self, dir_path: Path) -> None:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {dir_path}")

    def _get_free_port(self) -> int:
        """获取随机可用端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def download_with_progress(
            url: str,
            save_path: str,
            progress_callback: Optional[Callable[[int, int, float], None]] = None,
            chunk_size: int = 8192,
            timeout: int = 30
    ) -> bool:
        """
        带进度回调的文件下载函数

        :param url: 下载链接
        :param save_path: 保存路径（含文件名）
        :param progress_callback: 进度回调函数，接收参数：已下载字节数、总字节数、下载速度(KB/s)
        :param chunk_size: 每次读取的块大小
        :param timeout: 超时时间（秒）
        :return: 下载成功返回 True，失败返回 False
        """
        try:
            # 发送 HEAD 请求获取文件总大小（可选，部分服务器不支持）
            head_response = requests.head(url, timeout=timeout)
            total_size = int(head_response.headers.get('Content-Length', 0))

            # 发送 GET 请求开始下载（流式传输）
            with requests.get(url, stream=True, timeout=timeout) as response:
                response.raise_for_status()  # 检查 HTTP 错误状态

                # 如果 HEAD 请求未获取到总大小，从响应头再试一次
                if total_size == 0:
                    total_size = int(response.headers.get('Content-Length', 0))

                downloaded_size = 0
                start_time = time.time()
                last_time = start_time
                last_downloaded = 0

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # 过滤空块
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 计算下载速度（最近一次的块下载速度，避免频繁计算）
                            current_time = time.time()
                            time_diff = current_time - last_time
                            if time_diff > 0.1:  # 每 0.1 秒计算一次速度，避免性能损耗
                                speed = (downloaded_size - last_downloaded) / (time_diff * 1024)  # KB/s
                                last_time = current_time
                                last_downloaded = downloaded_size

                                # 调用进度回调函数
                                if progress_callback:
                                    progress_callback(downloaded_size, total_size, speed)

                # 下载完成后强制触发一次回调（确保100%显示）
                if progress_callback:
                    total_time = time.time() - start_time
                    avg_speed = (downloaded_size / (total_time * 1024)) if total_time > 0 else 0
                    progress_callback(downloaded_size, total_size, avg_speed)

            print(f"\n下载完成：{save_path}")
            return True

        except Exception as e:
            print(f"\n下载失败：{str(e)}")
            return False

    def _extract_archive(self, archive_path: Path, extract_dir: Path) -> bool:
        try:
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"ZIP解压完成: {extract_dir}")
                return True
            else:
                print(f"不支持的压缩格式: {archive_path.suffix}")
                return False
        except Exception as e:
            print(f"解压失败: {str(e)}")
            return False

    def install_plugin(self, plugin_name: str) -> bool:
        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin:
            print(f"插件不存在: {plugin_name}")
            return False

        plugin_dir = self.plugin_install_dir / plugin.extract_folder
        temp_archive = self.plugin_install_dir / f"{plugin.name}_temp.zip"

        if plugin_dir.exists():
            print(f"插件已安装: {plugin_name}")
            return True

        if not self._download_file(plugin.url, temp_archive):
            return False

        self._ensure_dir(plugin_dir)
        if not self._extract_archive(temp_archive, plugin_dir):
            shutil.rmtree(plugin_dir, ignore_errors=True)
            temp_archive.unlink(missing_ok=True)
            return False

        temp_archive.unlink(missing_ok=True)
        print(f"插件安装完成: {plugin_name}")
        return True

    def install_all_plugins(self) -> None:
        print("开始安装所有插件...")
        for plugin in self.plugins:
            self.install_plugin(plugin.name)
        print("所有插件安装操作完成")

    def start_plugin(self, plugin_name: str) -> bool:
        if self.is_plugin_running(plugin_name):
            print(f"插件已在运行: {plugin_name}")
            return True

        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin:
            print(f"插件不存在: {plugin_name}")
            return False

        plugin_dir = self.plugin_install_dir / plugin.extract_folder
        app_path = plugin_dir / plugin.app_relative_path

        if not plugin_dir.exists():
            print(f"插件未安装: {plugin_name}，正在尝试安装...")
            if not self.install_plugin(plugin_name):
                return False

        if not app_path.exists():
            print(f"插件程序不存在: {app_path}")
            return False

        try:
            cmd = [str(app_path)]
            if plugin.is_service:
                port = self._get_free_port()
                cmd.extend([f"--port={port}"])  # 传递端口参数
                print(f"为服务插件 [{plugin_name}] 分配端口: {port}")

            print(f"启动插件: {plugin_name} ({app_path})")
            if os.name == 'nt':
                subprocess.Popen(cmd, shell=True)
            elif os.name == 'posix':
                subprocess.Popen(cmd)

            if plugin.is_service:
                self.port_manager.set_port(plugin_name, port)
            return True
        except Exception as e:
            print(f"启动插件失败: {str(e)}")
            if plugin.is_service:
                self.port_manager.clear_port(plugin_name)
            return False

    def _get_running_processes(self) -> Set[str]:
        processes = set()
        for proc in psutil.process_iter(['exe', 'cmdline']):
            try:
                if proc.info['exe']:
                    processes.add(str(Path(proc.info['exe']).resolve()))
                elif proc.info['cmdline']:
                    cmd_path = Path(proc.info['cmdline'][0]).resolve()
                    if cmd_path.exists():
                        processes.add(str(cmd_path))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes

    def is_plugin_running(self, plugin_name: str) -> bool:
        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin:
            print(f"插件不存在: {plugin_name}")
            return False

        plugin_dir = self.plugin_install_dir / plugin.extract_folder
        app_path = plugin_dir / plugin.app_relative_path
        if not app_path.exists():
            return False

        app_abs_path = str(app_path.resolve())
        return app_abs_path in self._get_running_processes()

    def get_service_port(self, plugin_name: str) -> Optional[int]:
        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin or not plugin.is_service:
            print(f"不是服务类型插件: {plugin_name}")
            return None
        return self.port_manager.get_port(plugin_name)

    def stop_plugin(self, plugin_name: str) -> bool:
        if not self.is_plugin_running(plugin_name):
            print(f"插件未在运行: {plugin_name}")
            self.port_manager.clear_port(plugin_name)
            return True

        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin:
            return False

        app_abs_path = str((self.plugin_install_dir / plugin.extract_folder / plugin.app_relative_path).resolve())

        try:
            for proc in psutil.process_iter(['exe']):
                try:
                    if str(Path(proc.info['exe']).resolve()) == app_abs_path:
                        proc.terminate()
                        proc.wait(timeout=5)
                        print(f"已终止插件进程: {plugin_name} (PID: {proc.pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue

            if plugin.is_service:
                self.port_manager.clear_port(plugin_name)
            return True
        except Exception as e:
            print(f"停止插件失败: {str(e)}")
            return False

    def uninstall_plugin(self, plugin_name: str) -> bool:
        if self.is_plugin_running(plugin_name):
            print(f"插件正在运行，先停止插件: {plugin_name}")
            if not self.stop_plugin(plugin_name):
                print("停止插件失败，无法卸载")
                return False

        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if not plugin:
            print(f"插件不存在: {plugin_name}")
            return False

        plugin_dir = self.plugin_install_dir / plugin.extract_folder
        if not plugin_dir.exists():
            print(f"插件未安装: {plugin_name}")
            return True

        try:
            shutil.rmtree(plugin_dir)
            print(f"插件卸载完成: {plugin_name}")
            return True
        except Exception as e:
            print(f"卸载插件失败: {str(e)}")
            return False

    def list_plugins(self) -> None:
        print("\n插件列表:")
        print("-" * 100)
        print(f"{'名称':<15} {'类型':<8} {'安装状态':<10} {'运行状态':<10} {'端口':<6} {'安装路径':<40}")
        print("-" * 100)
        for plugin in self.plugins:
            plugin_dir = self.plugin_install_dir / plugin.extract_folder
            install_status = "已安装" if plugin_dir.exists() else "未安装"
            run_status = "运行中" if self.is_plugin_running(plugin.name) else "未运行"
            port = self.port_manager.get_port(plugin.name) or "-"
            plugin_type = "服务" if plugin.is_service else "应用"

            print(
                f"{plugin.name:<15} {plugin_type:<8} {install_status:<10} "
                f"{run_status:<10} {str(port):<6} {str(plugin_dir):<40}"
            )
        print("-" * 100 + "\n")


def main():
    if len(sys.argv) < 2:
        print("插件管理器使用方法:")
        print("  python manager.py install <插件名>      - 安装指定插件")
        print("  python manager.py install-all           - 安装所有插件")
        print("  python manager.py start <插件名>        - 启动指定插件")
        print("  python manager.py stop <插件名>         - 停止指定插件")
        print("  python manager.py uninstall <插件名>    - 卸载指定插件")
        print("  python manager.py list                  - 列出所有插件状态")
        print("  python manager.py status <插件名>       - 查看单个插件状态")
        print("  python manager.py get-port <插件名>     - 获取服务插件端口")
        return

    try:
        # 初始化管理器（默认加载当前目录的 plugins.yaml）
        manager = PluginManager()

        command = sys.argv[1].lower()
        plugin_name = sys.argv[2] if len(sys.argv) > 2 else None

        if command == "install" and plugin_name:
            manager.install_plugin(plugin_name)
        elif command == "install-all":
            manager.install_all_plugins()
        elif command == "start" and plugin_name:
            manager.start_plugin(plugin_name)
        elif command == "stop" and plugin_name:
            manager.stop_plugin(plugin_name)
        elif command == "uninstall" and plugin_name:
            manager.uninstall_plugin(plugin_name)
        elif command == "list":
            manager.list_plugins()
        elif command == "status" and plugin_name:
            status = "运行中" if manager.is_plugin_running(plugin_name) else "未运行"
            port = manager.get_service_port(plugin_name)
            port_info = f", 端口: {port}" if port else ""
            print(f"{plugin_name} 状态: {status}{port_info}")
        elif command == "get-port" and plugin_name:
            port = manager.get_service_port(plugin_name)
            if port:
                print(f"{plugin_name} 端口: {port}")
        else:
            print("未知命令")
    except Exception as e:
        print(f"执行失败: {str(e)}")


if __name__ == "__main__":
    # 需安装依赖：pip install psutil pyyaml
    main()
