# AutoElectsys

## 使用环境

- 操作系统：Windows/Linux/Mac
- Python版本：Python 2.7

## 安装依赖项

### Chrome 浏览器

可从[Chrome 官方网站](http://www.google.cn/chrome/browser/)下载。

### ChromeDriver

- ChromeDriver 用于驱动 Chrome 浏览器。本程序的 `dependency` 目录下面已经附有适用于各个操作系统的 ChromeDriver，无须自行下载。
- 然而需要注意的是，__ChromeDriver 的版本必须与 Chrome 相匹配__，若启动 Chrome 出错，请从 [ChromeDriver 官网](https://sites.google.com/a/chromium.org/chromedriver/)（可能需要科学上网）自行下载与您的 Chrome 版本相匹配的 ChromeDriver，并__替换本程序__ `dependency` __目录下的相应文件__。

### 在 Python 中安装 selenium 库

可使用 pip 安装：`pip install selenium`

- Windows 系统下 Python 通常自带 pip。若提示“'pip'不是内部或外部命令，也不是可运行的程序或批处理文件”，请将 __Python 的安装目录以及安装目录下的 Scripts 目录__ 都添加至 __环境变量的“系统变量”的 Path__ 中。
- Linux/Mac 用户若无 pip，请自行安装。

### 在 Python 中安装 Tkinter 库

- Windows 系统下 Python 通常自带 Tkinter 库，无需手动安装。
- Linux(Debian/Ubuntu): `sudo apt-get install python-tk`
- Mac: 参见 https://www.python.org/download/mac/tcltk/

## 配置
运行配置器 `AutoElectsysConfig.pyw` ，按提示进行参数设置。

- Windows 系统下直接双击运行即可。
- Linux/Mac 用户请从终端运行：`python AutoElectsysConfig.pyw`

## 使用

运行主程序 `AutoElectsys.py`。使用时请注意控制台窗口的提示。

- Windows 系统下直接双击运行即可。若使用过程中弹出“Windows防火墙”对话框，请点击“__允许访问__”，之后可能需要重新打开程序才能正常运行。
- Linux/Mac 用户请从终端运行：`python AutoElectsys.py`

## 免责声明

使用本程序对您选课造成的一切影响，本程序开发者概不负责，一切后果由您自行承担。一旦使用本程序即视为您已经接受了本免责声明！
