# AutoElectsys

上海交通大学 1999-2018 版本科教学信息服务网自动选课工具（对 2019 新版网站不可用）

## 支持环境

- 操作系统：Windows/Linux/macOS
- Python 3.4 或更高版本
- Chrome 浏览器

## 安装

克隆本仓库，或下载本项目的 ZIP 包，然后执行以下操作：

### Python 依赖库

- 执行 `pip3 install -r requirements.txt` 以安装本程序的 Python 依赖库
- 您还需要确保 Python 的 `tkinter` 库可用，可能需要安装软件包，如 Debian/Ubuntu：`sudo apt-get install python3-tk`

### ChromeDriver

本程序使用 ChromeDriver 以自动控制 Chrome 浏览器。由于其官方网站可能需要科学上网，本程序已经自带一份 ChromeDriver（在 `dependency` 目录中），并会不定期更新。**您需要确认本程序附带的 ChromeDriver 与您的 Chrome 版本相匹配**（参见 `dependency/chromedriver_version.txt` 并查看您的 Chrome 版本）。若不匹配，请自行前往 [ChromeDriver 官网](https://sites.google.com/a/chromium.org/chromedriver/) 下载匹配的版本，并替换本程序 `dependency` 目录下的（对应于您的操作系统的）相应文件。Linux/macOS 用户请为 ChromeDriver 程序设置可执行权限。

## 运行

### 配置设置

运行图形界面配置器 `AutoElectsysConfig.pyw` ，按提示进行参数设置。

### 自动选课主程序

运行自动选课主程序 `AutoElectsys.py`，该程序将启动一个 Chrome 浏览器，并对其进行自动控制以进行选课。使用时请注意控制台窗口的提示。

ChromeDriver 工作时需要在本地监听端口。Windows/macOS 用户如遇到防火墙提示，请点击允许，或临时关闭防火墙。

## 许可证与免责声明

- 本程序源代码遵循 MIT 许可证
- 本程序附带的 ChromeDriver 的二进制分发遵循其原本的许可证
- 本程序使用的验证码识别插件 `dependency/SJTU-jAccount-Login-Helper_v0.3.1.crx` 遵循其原本的许可证，该插件项目地址为：https://github.com/stooloveu/jHelper
- 使用本程序对您选课造成的一切影响，本程序开发者概不负责，一切后果由您自行承担。一旦使用本程序即视为您已经接受了本免责声明！
