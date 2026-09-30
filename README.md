# OmniCalc 通用运算器

> 万能计算器，可以进行各种数学运算，各种换算（实时汇率换算、单位换算、称呼换算等）能算的都能用。

OmniCalc 是一个 Windows 桌面通用运算器，采用 iOS 玻璃风格设计，支持多种运算模式自由切换。

## 功能特性

- **数学计算器** — 四则运算、百分比、退格清除，4×5 按键网格布局
- **汇率换算** — 5 行货币框，实时在线 API 汇率，100+ 种货币搜索选择
- **模式切换** — 可插拔模式架构，轻松扩展单位换算、称呼换算等新模式
- **iOS 玻璃风格** — 无边框圆角窗口、半透明毛玻璃面板、自绘圆角按钮
- **动态皮肤** — 支持静态图片（JPG/PNG/WebP）和动态视频（MP4/WebM/GIF）背景
- **自定义头像** — 选图后裁剪弹窗选择正方形区域，不压缩比例
- **单文件 EXE** — PyInstaller 打包，内嵌 ffmpeg，开箱即用

## 技术栈

| 组件 | 说明 |
|---|---|
| Python 3.10+ | 运行时 |
| tkinter | GUI 框架（内置，无需额外安装） |
| Pillow (PIL) | 图像处理（圆角遮罩、玻璃覆盖层、图标生成） |
| PyInstaller | 打包为单文件 EXE |
| ffmpeg | 视频背景解码（已内嵌于 EXE） |

## 项目结构

```
OmniCalc/
├── main.py              # 主程序入口
├── glass_ui.py          # iOS 玻璃 UI 框架（窗口、按钮、视频背景）
├── skin.py              # 皮肤与头像管理
├── currencies.py        # 货币数据（100+ 种货币）
├── crop_dialog.py       # 头像裁剪弹窗
├── make_icon.py         # 图标生成器（JPG → 多尺寸 ICO）
├── build.bat            # 一键打包脚本
├── .gitignore
├── assets/
│   ├── icon.jpg         # 图标源图
│   └── icon.ico         # 生成的多尺寸图标
├── bin/
│   └── ffmpeg.exe       # 视频解码器（不纳入版本控制，需自行下载）
├── modes/
│   ├── __init__.py      # 模式管理器（注册/切换/生命周期）
│   ├── exchange.py      # 汇率换算模式
│   └── calculator.py    # 数学计算器模式
└── docs/
    └── design.md        # 设计文档
```

## 快速开始

### 环境要求

```bash
pip install pyinstaller pillow
```

### 从源码构建

1. 克隆仓库：
   ```bash
   git clone https://github.com/LH1149/Omni_Calculator.git
   cd Omni_Calculator
   ```

2. （可选）将 `ffmpeg.exe` 放入 `bin/` 目录以支持视频背景：
   ```
   bin/ffmpeg.exe
   ```

3. 运行打包脚本：
   ```batch
   build.bat
   ```

4. 生成的 EXE 位于 `dist/OmniCalc.exe`。

### 从源码运行

```bash
python main.py
```

## 使用说明

- **更换头像** — 点击后选择图片，在裁剪弹窗中拖拽选择正方形区域
- **更换皮肤** — 点击后选择静态图片或视频作为背景
- **恢复默认** — 重置头像和皮肤为默认状态
- **模式选择** — 点击模式按钮切换计算器和汇率换算模式
- **汇率换算** — 点击菱形 ◆ 搜索选择货币；在第一行输入金额，实时显示其余四种货币的等值

## 汇率数据

汇率数据通过 [open.er-api.com](https://open.er-api.com) 免费在线 API 实时获取，无需 API Key。

默认货币：
1. CNY（人民币）
2. MYR（马来西亚林吉特）
3. IDR（印尼盾）
4. SGD（新加坡元）
5. VND（越南盾）

## 许可证

MIT License

## 致谢

- [tkinter-glass-ui](https://github.com/) — tkinter iOS 玻璃 UI 设计模式
- [open.er-api.com](https://open.er-api.com) — 免费汇率 API
