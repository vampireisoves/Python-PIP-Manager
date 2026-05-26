#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======================== 管理员权限提示（Windows）========================
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import time
import json
import urllib.request
import configparser
import re
import shutil
from urllib.error import URLError, HTTPError

# ================== 定义版本号 ==================
VERSION = 'v20260526.1501'

# ================== 系统深色模式检测 ==================
def is_system_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value[0] == 0
    except:
        return False

# ================== 深浅色主题定义 ==================
def set_theme(is_dark: bool):
    global FONT_NORMAL, FONT_BOLD, FONT_SMALL
    global WINDOW_BG, CARD_BG, BORDER_COLOR
    global PRIMARY_COLOR, PRIMARY_HOVER, PRIMARY_TEXT
    global SECONDARY_BG, SECONDARY_HOVER, SECONDARY_TEXT
    global DANGER_COLOR, DANGER_BG, DANGER_HOVER
    global STRIPE_COLOR, OUTDATED_BG, OUTDATED_FG

    FONT_NORMAL = ("Microsoft YaHei UI", 9)
    FONT_BOLD = ("Microsoft YaHei UI", 9, "bold")
    FONT_SMALL = ("Microsoft YaHei UI", 8)

    if is_dark:
        # 深色模式
        WINDOW_BG = "#1E1E1E"
        CARD_BG = "#2D2D2D"
        BORDER_COLOR = "#3E3E3E"
        PRIMARY_COLOR = "#3498db"
        PRIMARY_HOVER = "#5dade2"
        PRIMARY_TEXT = "#FFFFFF"
        SECONDARY_BG = "#373737"
        SECONDARY_HOVER = "#4A4A4A"
        SECONDARY_TEXT = "#E0E0E0"
        DANGER_COLOR = "#E74C3C"
        DANGER_BG = "#4A2B2A"
        DANGER_HOVER = "#5C3736"
        STRIPE_COLOR = "#2A2A2A"
        OUTDATED_BG = "#4A3F2E"
        OUTDATED_FG = "#F5D061"
    else:
        # 浅色模式
        WINDOW_BG = "#F8FAFC"
        CARD_BG = "#FFFFFF"
        BORDER_COLOR = "#E2E8F0"
        PRIMARY_COLOR = "#2563EB"
        PRIMARY_HOVER = "#1D4ED8"
        PRIMARY_TEXT = "#FFFFFF"
        SECONDARY_BG = "#F1F5F9"
        SECONDARY_HOVER = "#E2E8F0"
        SECONDARY_TEXT = "#334155"
        DANGER_COLOR = "#EF4444"
        DANGER_BG = "#FEF2F2"
        DANGER_HOVER = "#FEE2E2"
        STRIPE_COLOR = "#F8FAFC"
        OUTDATED_BG = "#FFFBEB"
        OUTDATED_FG = "#92400E"

# 初始化主题
is_dark = is_system_dark_mode()
set_theme(is_dark)

# 检查是否以管理员身份运行
def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ================== 版本获取（精准获取官方正式Release版本） ==================
def get_local_python_version():
    try:
        out = subprocess.check_output([sys.executable, "--version"], text=True, errors="ignore")
        return out.strip().replace("Python ", "")
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        return "0.0.0"

def get_latest_python_version():
    try:
        url = "https://www.python.org/api/v2/downloads/release/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=8) as f:
            data = json.load(f)

        release_vers = []
        for item in data:
            name = item.get("name", "")
            if any(tag in name.lower() for tag in ["rc", "beta", "alpha", "dev", "pre"]):
                continue
            match = re.search(r"Python\s+(\d+\.\d+\.\d+)", name)
            if not match:
                continue
            ver_str = match.group(1)
            try:
                major, minor, patch = map(int, ver_str.split("."))
                if major == 3 and minor >= 15:
                    continue
                release_vers.append(ver_str)
            except ValueError:
                continue

        if not release_vers:
            return "获取失败"

        release_vers.sort(key=lambda v: tuple(map(int, v.split("."))), reverse=True)
        return release_vers[0]

    except (URLError, HTTPError, json.JSONDecodeError, TimeoutError):
        return "获取失败"
    except Exception:
        return "获取失败"

# ================== 版本比较 ==================
def version_str_to_tuple(version_str):
    try:
        clean_ver = re.sub(r'[^\d.]', '', version_str)
        return tuple(map(int, clean_ver.split(".")))
    except:
        return (0, 0, 0)

def is_need_upgrade(local, latest):
    if local == "0.0.0" or latest == "获取失败":
        return False
    try:
        lv = version_str_to_tuple(local)
        rv = version_str_to_tuple(latest)
        max_len = max(len(lv), len(rv))
        lv = lv + (0,) * (max_len - len(lv))
        rv = rv + (0,) * (max_len - len(rv))
        return rv > lv
    except:
        return False

# ================== 自动下载 + 安装 + 清理 ==================
def upgrade_python():
    global local_ver, latest_ver, need_upg, btn_upgrade
    
    if not is_need_upgrade(local_ver, latest_ver):
        show_info("提示", "当前已是最新版本！")
        return

    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PPMUpdata")
    os.makedirs(base_dir, exist_ok=True)

    ver = latest_ver
    url_64 = f"https://www.python.org/ftp/python/{ver}/python-{ver}-amd64.exe"
    path = os.path.join(base_dir, f"python-{ver}-setup.exe")

    try:
        show_info("开始升级", f"即将下载 Python {ver}\n保存到：{base_dir}")

        def download_task():
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                req = urllib.request.Request(url_64, headers=headers)
                
                with urllib.request.urlopen(req, timeout=15) as r:
                    total = int(r.headers.get("Content-Length", 0))
                    downloaded = 0
                    
                    with open(path, "wb") as f:
                        while True:
                            chunk = r.read(1024 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total > 0:
                                progress = int((downloaded / total) * 100)
                                root.after(0, lambda p=progress: set_progress(p))

                if os.path.getsize(path) == 0:
                    raise Exception("下载的文件为空")

                install_process = subprocess.Popen(
                    [path, "/passive", "/norestart", "InstallAllUsers=1", "PrependPath=1"],
                    shell=True,
                    creationflags=0x08000000
                )
                
                time.sleep(5)

                try:
                    os.remove(path)
                except PermissionError:
                    pass

                root.after(0, lambda: show_info("完成", f"Python {ver} 安装程序已启动\n安装包已自动删除\n请等待安装完成后重启程序"))
                root.after(0, lambda: set_progress(100))

            except URLError as e:
                root.after(0, lambda: show_error("失败", f"下载失败：网络错误 - {str(e)}"))
            except TimeoutError:
                root.after(0, lambda: show_error("失败", "下载失败：连接超时"))
            except Exception as e:
                root.after(0, lambda: show_error("失败", f"下载失败：{str(e)}"))
            finally:
                root.after(0, lambda: set_progress(100))

        threading.Thread(target=download_task, daemon=True).start()

    except Exception as e:
        show_error("错误", str(e))

# ================== 路径 ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(SCRIPT_DIR, "requirements.txt")
PYTHON_PATH = sys.executable
PIP_CONFIG_DIR = os.path.join(os.path.expanduser("~"), "pip")
PIP_CONFIG_PATH = os.path.join(PIP_CONFIG_DIR, "pip.ini")

# ================== 全局状态变量 ==================
is_checking = False
is_cleaning = False
installed_cache = {}
outdated_cache = {}
local_ver = ""
latest_ver = ""
need_upg = False
btn_upgrade = None

# ================== 镜像源 ==================
PIP_MIRRORS = {
    "官方默认源": "https://pypi.org/simple/",
    "清华源": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "阿里源": "https://mirrors.aliyun.com/pypi/simple/",
    "中科大源": "https://pypi.mirrors.ustc.edu.cn/simple/",
    "163源": "https://mirrors.163.com/pypi/simple/",
    "豆瓣源": "https://pypi.doubanio.com/simple/"
}

# ================== 主界面 ==================
root = tk.Tk()
local_ver = get_local_python_version()
latest_ver = get_latest_python_version()
need_upg = is_need_upgrade(local_ver, latest_ver)

# 修改标题，添加版本号
root.title(f"Python PIP Manager ({VERSION}) | 本地:{local_ver} | 最新:{latest_ver}")
root.configure(bg=WINDOW_BG)
root.minsize(720, 520)

style = ttk.Style(root)
style.theme_use("clam")

# ===================== 动态主题样式应用 =====================
def apply_theme_styles():
    # 基础
    style.configure(".", font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT)
    
    # 按钮
    style.configure("TButton", padding=4, relief="flat", background=SECONDARY_BG, foreground=SECONDARY_TEXT, borderwidth=0, focusthickness=0)
    style.map("TButton", background=[("active", SECONDARY_HOVER), ("pressed", BORDER_COLOR)])
    
    style.configure("Primary.TButton", background=PRIMARY_COLOR, foreground=PRIMARY_TEXT, padding=4)
    style.map("Primary.TButton", background=[("active", PRIMARY_HOVER), ("pressed", "#1E40AF")])
    
    style.configure("Danger.TButton", foreground=DANGER_COLOR, background=DANGER_BG, padding=4)
    style.map("Danger.TButton", background=[("active", DANGER_HOVER)])
    
    # 列表
    style.configure("Treeview", rowheight=26, font=FONT_NORMAL, borderwidth=0, relief="flat", background=CARD_BG, fieldbackground=CARD_BG, foreground=SECONDARY_TEXT)
    style.configure("Treeview.Heading", font=FONT_BOLD, background=SECONDARY_BG, foreground=SECONDARY_TEXT, relief="flat", padding=5)
    style.map("Treeview", background=[("selected", PRIMARY_COLOR)], foreground=[("selected", PRIMARY_TEXT)])
    
    # 框架
    style.configure("TFrame", background=WINDOW_BG)
    style.configure("TLabelframe", background=WINDOW_BG, borderwidth=0)
    style.configure("TLabel", background=WINDOW_BG, font=FONT_NORMAL, foreground=SECONDARY_TEXT)
    
    # 输入
    style.configure("TEntry", fieldbackground=CARD_BG, borderwidth=1, relief="flat", padding=4, foreground=SECONDARY_TEXT)
    style.configure("Horizontal.TProgressbar", background=PRIMARY_COLOR, troughcolor=BORDER_COLOR, borderwidth=0)
    
    # 滚动条
    style.configure("Vertical.TScrollbar", background=BORDER_COLOR, borderwidth=0, arrowcolor=SECONDARY_TEXT, troughcolor=WINDOW_BG)
    style.map("Vertical.TScrollbar", background=[("active", "#CBD5E1")])
    
    # 单选/下拉
    style.configure("TRadiobutton", background=WINDOW_BG, foreground=SECONDARY_TEXT, font=FONT_NORMAL)
    style.configure("TCombobox", fieldbackground=CARD_BG, background=SECONDARY_BG, foreground=SECONDARY_TEXT, padding=3, borderwidth=1)

apply_theme_styles()

# ================== 进度条 ==================
progress_frame = ttk.Frame(root)
progress_frame.pack(fill=tk.X, padx=12, pady=6)
progress_label = ttk.Label(progress_frame, text="就绪", font=FONT_SMALL)
progress_label.pack(side=tk.LEFT, padx=(0, 8))
progress_bar = ttk.Progressbar(progress_frame, mode="determinate", style="Horizontal.TProgressbar")
progress_bar.pack(fill=tk.X, expand=True)

# ================== 主布局 ==================
main_pane = ttk.Frame(root)
main_pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

# 左侧按钮面板
btn_frame = ttk.Frame(main_pane)
btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

ttk.Label(btn_frame, text="🔍 搜索筛选", font=FONT_BOLD).pack(pady=(2,4))
search_var = tk.StringVar()
search_entry = ttk.Entry(btn_frame, textvariable=search_var, font=FONT_NORMAL)
search_entry.pack(fill=tk.X, pady=(0,6), ipady=3)
search_entry.focus()

# 功能按钮列表
btn_list = [
    ("📥 安装新包", False),
    ("🔄 刷新列表", False),
    ("🔍 检查更新", False),
    ("🧹 清理缓存", False),
    ("🌍 PIP 换源", False),
    ("↑ 升级选中包", False),
    ("↓ 降级选中包", False),
    ("🗑 卸载选中", False),
    ("❌ 全部卸载", True),
    ("📤 导出 requirements", False),
    ("📥 导入 requirements", False),
]

buttons = {}
for txt, danger in btn_list:
    btn = ttk.Button(btn_frame, text=txt, style="Danger.TButton" if danger else "TButton")
    btn.pack(fill=tk.X, pady=2, ipady=2)
    buttons[txt] = btn

# Python 升级按钮
ttk.Separator(btn_frame).pack(fill=tk.X, pady=6)
btn_upgrade = ttk.Button(btn_frame)
if need_upg:
    btn_upgrade.config(text=f"升级到 {latest_ver}", command=upgrade_python, style="Primary.TButton")
else:
    btn_upgrade.config(text="当前为最新", state=tk.DISABLED)
btn_upgrade.pack(fill=tk.X, pady=2, ipady=2)

# 右侧包列表
tree_container = ttk.Frame(main_pane)
tree_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(tree_container, columns=("icon", "name", "ver", "latest"), show="headings", style="Treeview")
tree.heading("icon", text="", anchor=tk.CENTER)
tree.heading("name", text="包名称", anchor=tk.W)
tree.heading("ver", text="当前版本", anchor=tk.CENTER)
tree.heading("latest", text="最新版本", anchor=tk.CENTER)

tree.column("icon", width=24, anchor=tk.CENTER)
tree.column("name", width=280, stretch=tk.YES, anchor=tk.W)
tree.column("ver", width=90, anchor=tk.CENTER)
tree.column("latest", width=90, anchor=tk.CENTER)

tree.tag_configure("even", background=CARD_BG)
tree.tag_configure("odd", background=STRIPE_COLOR)
tree.tag_configure("outdated_even", background=OUTDATED_BG, foreground=OUTDATED_FG)
tree.tag_configure("outdated_odd", background=OUTDATED_BG, foreground=OUTDATED_FG)

vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
tree.configure(yscrollcommand=vsb.set)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
tree.pack(fill=tk.BOTH, expand=True, pady=2)

# ================== 弹窗（自动深浅色） ==================
def center_win(win, w, h):
    try:
        root.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() - w) // 2
        y = root.winfo_y() + (root.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")
    except:
        win.geometry(f"{w}x{h}")

def show_warning(title, msg):
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 320, 120)
    ttk.Label(top, text=msg, wraplength=280, font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=12)
    ttk.Button(top, text="确定", command=top.destroy, width=8).pack()
    root.wait_window(top)

def show_error(title, msg):
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 320, 120)
    ttk.Label(top, text=msg, wraplength=280, font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=12)
    ttk.Button(top, text="确定", command=top.destroy, width=8).pack()
    root.wait_window(top)

def show_info(title, msg):
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 320, 120)
    ttk.Label(top, text=msg, wraplength=280, font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=12)
    ttk.Button(top, text="确定", command=top.destroy, width=8).pack()
    root.wait_window(top)

def ask_yesno(title, msg):
    res = False
    def yes(): nonlocal res; res=True; top.destroy()
    def no(): nonlocal res; res=False; top.destroy()
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 320, 140)
    ttk.Label(top, text=msg, wraplength=280, font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=12)
    f = ttk.Frame(top, style="TFrame")
    f.pack()
    ttk.Button(f, text="是", command=yes, width=8, style="Primary.TButton").pack(side=tk.LEFT, padx=6)
    ttk.Button(f, text="否", command=no, width=8).pack(side=tk.LEFT, padx=6)
    root.wait_window(top)
    return res

def get_input(title, prompt):
    res = ""
    def ok(): nonlocal res; res=e.get().strip(); top.destroy()
    def on_enter(event): ok()
    top = tk.Toplevel(root)
    top.title(title)
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 320, 140)
    ttk.Label(top, text=prompt, font=FONT_NORMAL, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=8)
    e = ttk.Entry(top, font=FONT_NORMAL, width=28)
    e.pack(pady=3, ipady=2)
    e.focus()
    e.bind("<Return>", on_enter)
    ttk.Button(top, text="确定", command=ok, width=8, style="Primary.TButton").pack(pady=8)
    root.wait_window(top)
    return res

# ================== 功能函数 ==================
def set_progress(v):
    try:
        progress_bar["value"] = v
        progress_label.config(text=f"进度: {v}%")
        root.update_idletasks()
    except:
        pass

def filter_packages(*a):
    try:
        k = search_var.get().lower()
        for i in tree.get_children():
            tree.delete(i)
        idx = 0
        for n, v in installed_cache.items():
            if k in n.lower():
                lv = outdated_cache.get(n, v)
                icon = "📦"
                if lv != v:
                    tag = "outdated_odd" if idx % 2 == 1 else "outdated_even"
                else:
                    tag = "odd" if idx % 2 == 1 else "even"
                tree.insert("", "end", values=(icon, n, v, lv), tags=(tag,))
                idx += 1
    except:
        pass

def run_cmd(args):
    try:
        return subprocess.check_output(
            args,
            creationflags=0x08000000,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return ""

def load_packages():
    def task():
        global installed_cache, outdated_cache
        try:
            installed_cache = {}
            outdated_cache = {}
            set_progress(20)
            pip_list_output = run_cmd([PYTHON_PATH, "-m", "pip", "list", "--format=freeze"])
            if pip_list_output:
                lines = pip_list_output.strip().splitlines()
                for line in lines:
                    if "==" in line:
                        pkg_name, pkg_ver = line.split("==", 1)
                        installed_cache[pkg_name] = pkg_ver
            else:
                lines = run_cmd([PYTHON_PATH, "-m", "pip", "list"]).strip().splitlines()[2:]
                for line in lines:
                    parts = line.split()
                    if len(parts)>=2:
                        installed_cache[parts[0]] = parts[1]
            set_progress(50)
            filter_packages()
            outdated_output = run_cmd([PYTHON_PATH, "-m", "pip", "list", "--outdated", "--format=freeze"])
            if outdated_output:
                lines = outdated_output.strip().splitlines()
                for line in lines:
                    if "==" in line:
                        pkg_name, pkg_ver = line.split("==", 1)
                        try:
                            latest_ver = run_cmd([PYTHON_PATH, "-m", "pip", "index", "versions", pkg_name])
                            if latest_ver:
                                match = re.search(r"Latest:\s+(\d+\.\d+\.\d+.*)", latest_ver)
                                if match:
                                    outdated_cache[pkg_name] = match.group(1)
                        except:
                            pass
            else:
                out = run_cmd([PYTHON_PATH, "-m", "pip", "list", "--outdated"]).strip().splitlines()[2:]
                for line in out:
                    p = line.split()
                    if len(p)>=3:
                        outdated_cache[p[0]] = p[2]
            filter_packages()
            set_progress(100)
        except:
            set_progress(100)
    threading.Thread(target=task, daemon=True).start()

def manual_check_updates():
    global is_checking
    if is_checking:
        return
    is_checking = True
    buttons["🔍 检查更新"].config(state=tk.DISABLED, text="检查中...")
    def task():
        global is_checking
        try:
            outdated_cache.clear()
            out = run_cmd([PYTHON_PATH, "-m", "pip", "list", "--outdated"]).strip().splitlines()[2:]
            for line in out:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    outdated_cache[parts[0]] = parts[2]
            filter_packages()
            show_info("完成", "✅ 检查更新完成")
        except Exception as e:
            show_error("错误", f"检查更新失败：{str(e)}")
        finally:
            set_progress(100)
            is_checking = False
            buttons["🔍 检查更新"].config(state=tk.NORMAL, text="🔍 检查更新")
    threading.Thread(target=task, daemon=True).start()

def clean_pip_cache():
    if not ask_yesno("清理缓存", "确定清理 PIP 缓存？\n此操作不会影响已安装的包。"):
        return
    buttons["🧹 清理缓存"].config(state=tk.DISABLED, text="清理中...")
    set_progress(0)
    def task():
        try:
            cache_dir = run_cmd([PYTHON_PATH, "-m", "pip", "cache", "dir"]).strip()
            size = 0
            if os.path.exists(cache_dir):
                for r, ds, fs in os.walk(cache_dir):
                    for f in fs:
                        try:
                            size += os.path.getsize(os.path.join(r,f))
                        except:
                            pass
            result = subprocess.run(
                [PYTHON_PATH, "-m", "pip", "cache", "purge"],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                show_info("成功", f"✅ 清理完成！\n释放空间：{round(size/1024/1024,2)} MB")
            else:
                raise Exception(result.stderr)
        except Exception as e:
            show_error("失败", f"清理失败：{str(e)}")
        finally:
            set_progress(100)
            buttons["🧹 清理缓存"].config(state=tk.NORMAL, text="🧹 清理缓存")
    threading.Thread(target=task, daemon=True).start()

def change_pip_mirror():
    top = tk.Toplevel(root)
    top.title("PIP 镜像源")
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 300, 280)
    ttk.Label(top, text="选择镜像源", font=FONT_BOLD, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=8)
    current_mirror = "官方默认源"
    try:
        if os.path.exists(PIP_CONFIG_PATH):
            cfg = configparser.RawConfigParser()
            cfg.read(PIP_CONFIG_PATH, encoding="utf-8")
            if cfg.has_section("global") and cfg.has_option("global", "index-url"):
                current_url = cfg.get("global", "index-url")
                for name, url in PIP_MIRRORS.items():
                    if current_url.startswith(url):
                        current_mirror = name
                        break
    except:
        pass
    v = tk.StringVar(value=current_mirror)
    for name in PIP_MIRRORS:
        ttk.Radiobutton(top, text=name, variable=v, value=name).pack(anchor="w", padx=20, pady=2)
    def save():
        name = v.get()
        url = PIP_MIRRORS[name]
        try:
            if not os.path.exists(PIP_CONFIG_DIR):
                os.makedirs(PIP_CONFIG_DIR)
            cfg = configparser.RawConfigParser()
            cfg.add_section("global")
            cfg.set("global", "index-url", url)
            cfg.set("global", "trusted-host", url.split("/")[2])
            cfg.set("global", "timeout", "10")
            with open(PIP_CONFIG_PATH, "w", encoding="utf-8") as f:
                cfg.write(f)
            show_info("成功", f"✅ 已切换至：{name}")
            top.destroy()
        except Exception as e:
            show_error("失败", f"切换失败：{str(e)}")
    ttk.Button(top, text="确认切换", command=save, style="Primary.TButton").pack(pady=8)
    root.wait_window(top)

def install_package():
    pkg = get_input("安装新包", "请输入要安装的包名：")
    if not pkg:
        return
    def task():
        set_progress(0)
        try:
            result = subprocess.run(
                [PYTHON_PATH, "-m", "pip", "install", pkg],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            set_progress(100)
            if result.returncode == 0:
                show_info("完成", f"✅ {pkg} 安装完成")
            else:
                show_error("失败", f"安装失败：{result.stderr[:200]}")
            load_packages()
        except Exception as e:
            set_progress(100)
            show_error("失败", f"安装失败：{str(e)}")
            load_packages()
    threading.Thread(target=task, daemon=True).start()

def upgrade_package():
    try:
        selection = tree.selection()
        if not selection:
            raise IndexError
        pkg = tree.item(selection[0])["values"][1]
    except IndexError:
        show_warning("提示", "请先选择一个包")
        return
    if not ask_yesno("升级", f"确定升级包：{pkg}？"):
        return
    def task():
        set_progress(0)
        try:
            result = subprocess.run(
                [PYTHON_PATH, "-m", "pip", "install", "--upgrade", pkg],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            set_progress(100)
            if result.returncode == 0:
                show_info("完成", f"✅ {pkg} 升级完成")
            else:
                show_error("失败", f"升级失败：{result.stderr[:200]}")
            load_packages()
        except Exception as e:
            set_progress(100)
            show_error("失败", f"升级失败：{str(e)}")
            load_packages()
    threading.Thread(target=task, daemon=True).start()

def downgrade_package():
    try:
        selection = tree.selection()
        if not selection:
            raise IndexError
        pkg = tree.item(selection[0])["values"][1]
    except IndexError:
        show_warning("提示", "请先选择一个包")
        return
    vers = []
    try:
        url = f"https://pypi.org/pypi/{pkg}/json"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as f:
            data = json.load(f)
        vers = sorted(data["releases"].keys(), key=version_str_to_tuple, reverse=True)
        vers = [v for v in vers if not any(tag in v.lower() for tag in ["rc", "beta", "alpha", "dev"])]
    except:
        try:
            out = run_cmd([PYTHON_PATH, "-m", "pip", "index", "versions", pkg])
            if out:
                matches = re.findall(r"(\d+\.\d+\.\d+)", out)
                if matches:
                    vers = sorted(list(set(matches)), key=version_str_to_tuple, reverse=True)
        except:
            pass
    if not vers:
        show_error("错误", "无法获取版本列表")
        return
    top = tk.Toplevel(root)
    top.title(f"{pkg} 降级")
    top.resizable(False, False)
    top.transient(root)
    top.grab_set()
    top.configure(bg=WINDOW_BG)
    center_win(top, 280, 140)
    ttk.Label(top, text="选择版本", font=FONT_BOLD, background=WINDOW_BG, foreground=SECONDARY_TEXT).pack(pady=6)
    v = tk.StringVar(value=vers[0])
    c = ttk.Combobox(top, textvariable=v, values=vers, state="readonly", width=24)
    c.pack(pady=3, ipady=2)
    def ok():
        ver = v.get()
        top.destroy()
        def task():
            set_progress(0)
            try:
                result = subprocess.run(
                    [PYTHON_PATH, "-m", "pip", "install", f"{pkg}=={ver}"],
                    creationflags=0x08000000,
                    capture_output=True,
                    text=True
                )
                set_progress(100)
                if result.returncode == 0:
                    show_info("完成", f"✅ {pkg} 已降级到 {ver}")
                else:
                    show_error("失败", f"降级失败：{result.stderr[:200]}")
                load_packages()
            except Exception as e:
                set_progress(100)
                show_error("失败", f"降级失败：{str(e)}")
                load_packages()
        threading.Thread(target=task, daemon=True).start()
    ttk.Button(top, text="确定降级", command=ok, style="Primary.TButton").pack(pady=8)
    root.wait_window(top)

def uninstall():
    try:
        selection = tree.selection()
        if not selection:
            raise IndexError
        pkg = tree.item(selection[0])["values"][1]
    except IndexError:
        show_warning("提示", "请先选择一个包")
        return
    if pkg.lower() in ["pip", "setuptools"]:
        if not ask_yesno("警告", f"{pkg} 是核心组件，卸载可能导致PIP无法使用！\n确定继续卸载？"):
            return
    if not ask_yesno("卸载", f"确定卸载包：{pkg}？"):
        return
    def task():
        set_progress(30)
        try:
            result = subprocess.run(
                [PYTHON_PATH, "-m", "pip", "uninstall", "-y", pkg],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            set_progress(100)
            if result.returncode == 0:
                show_info("完成", f"✅ {pkg} 已卸载")
            else:
                show_error("失败", f"卸载失败：{result.stderr[:200]}")
            load_packages()
        except Exception as e:
            set_progress(100)
            show_error("失败", f"卸载失败：{str(e)}")
            load_packages()
    threading.Thread(target=task, daemon=True).start()

def uninstall_all():
    if not ask_yesno("⚠️ 危险操作", "确定卸载所有第三方包？\n此操作不可恢复！\n核心组件将被保留。"):
        return
    def task():
        try:
            lines = run_cmd([PYTHON_PATH, "-m", "pip", "list"]).strip().splitlines()[2:]
            pkgs_to_uninstall = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    pkg = parts[0].lower()
                    if pkg not in ["pip", "setuptools", "python"]:
                        pkgs_to_uninstall.append(parts[0])
            total = len(pkgs_to_uninstall)
            if total == 0:
                root.after(0, lambda: show_info("提示", "没有可卸载的第三方包"))
                root.after(0, lambda: set_progress(100))
                return
            for i, pkg in enumerate(pkgs_to_uninstall):
                try:
                    subprocess.run(
                        [PYTHON_PATH, "-m", "pip", "uninstall", "-y", pkg],
                        creationflags=0x08000000,
                        capture_output=True
                    )
                    progress = 10 + int(80*(i/total))
                    root.after(0, lambda p=progress: set_progress(p))
                except:
                    continue
            root.after(0, lambda: set_progress(100))
            root.after(0, lambda: show_info("完成", f"✅ 已卸载 {len(pkgs_to_uninstall)} 个第三方包"))
            root.after(0, load_packages)
        except Exception as e:
            root.after(0, lambda: set_progress(100))
            root.after(0, lambda: show_error("失败", f"卸载过程中出错：{str(e)}"))
            root.after(0, load_packages)
    threading.Thread(target=task, daemon=True).start()

def export_requirements():
    try:
        file_path = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile="requirements.txt",
            title="导出requirements.txt"
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as f:
            subprocess.run(
                [PYTHON_PATH, "-m", "pip", "freeze"],
                stdout=f,
                creationflags=0x08000000
            )
        show_info("成功", f"✅ requirements.txt 已导出到：\n{file_path}")
    except Exception as e:
        show_error("失败", f"导出失败：{str(e)}")

def import_requirements():
    p = filedialog.askopenfilename(
        parent=root,
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        title="选择requirements.txt文件"
    )
    if not p:
        return
    def task():
        set_progress(0)
        try:
            result = subprocess.run(
                [PYTHON_PATH, "-m", "pip", "install", "-r", p],
                creationflags=0x08000000,
                capture_output=True,
                text=True
            )
            set_progress(100)
            if result.returncode == 0:
                show_info("完成", "✅ 依赖安装完成")
            else:
                show_error("失败", f"安装失败：{result.stderr[:200]}")
            load_packages()
        except Exception as e:
            set_progress(100)
            show_error("失败", f"安装失败：{str(e)}")
            load_packages()
    threading.Thread(target=task, daemon=True).start()

# ================== 绑定按钮 ==================
buttons["📥 安装新包"].config(command=install_package)
buttons["🔄 刷新列表"].config(command=load_packages)
buttons["🔍 检查更新"].config(command=manual_check_updates)
buttons["🧹 清理缓存"].config(command=clean_pip_cache)
buttons["🌍 PIP 换源"].config(command=change_pip_mirror)
buttons["↑ 升级选中包"].config(command=upgrade_package)
buttons["↓ 降级选中包"].config(command=downgrade_package)
buttons["🗑 卸载选中"].config(command=uninstall)
buttons["❌ 全部卸载"].config(command=uninstall_all)
buttons["📤 导出 requirements"].config(command=export_requirements)
buttons["📥 导入 requirements"].config(command=import_requirements)

search_var.trace_add("write", filter_packages)

# ================== 启动 ==================
if not is_admin():
    top = tk.Toplevel(root)
    top.title("权限提示")
    top.resizable(False,False)
    top.configure(bg=WINDOW_BG)
    center_win(top, 360, 120)
    ttk.Label(
        top,
        text="⚠️ 建议以管理员身份运行，部分功能会受限",
        wraplength=320,
        font=FONT_NORMAL,
        background=WINDOW_BG,
        foreground=SECONDARY_TEXT
    ).pack(pady=14)
    ttk.Button(top,text="确定",command=top.destroy, width=8).pack()
    root.wait_window(top)

root.after(100, lambda: root.geometry(f"{max(root.winfo_reqwidth(), 720)}x{max(root.winfo_height(), 520)}"))
root.after(200, load_packages)

root.mainloop()
