# 小说创作辅助工具安装说明

## 概述
恭喜！您已成功将小说创作辅助工具打包为独立的Windows可执行程序。本说明文档将指导您完成最终的安装包创建过程。

## 打包结果

### 已生成的文件：
- `dist/NovelCreationTool/` - 包含所有可执行文件的目录
- `dist/NovelCreationTool/NovelCreationTool.exe` - 主程序文件
- `setup_script.iss` - Inno Setup安装脚本

### 目录结构：
`dist/NovelCreationTool/` 目录包含了运行应用程序所需的所有文件，包括Python解释器和所有依赖库，因此可以独立运行，无需安装Python环境。

## 创建安装程序

### 方法一：使用Inno Setup（推荐）

1. 下载并安装 [Inno Setup](https://jrsoftware.org/isdl.php)
2. 运行以下命令：
   ```
   iscc setup_script.iss
   ```
3. 或者双击 `setup_script.iss` 文件并在Inno Setup中编译

### 方法二：手动使用Inno Setup

1. 安装Inno Setup后，启动Inno Setup Compiler
2. 打开 `setup_script.iss` 脚本文件
3. 点击"Build"按钮进行编译
4. 编译完成后，将在当前目录生成 `小说创作辅助工具安装程序.exe`

## 最终安装包

编译完成后，您将获得一个名为 `小说创作辅助工具安装程序.exe` 的单文件安装程序，用户可以双击运行进行安装。

## 验证安装

1. 在另一台没有Python环境的Windows计算机上运行安装程序
2. 按照安装向导完成安装
3. 启动应用程序验证其正常工作

## 分发

现在您可以将 `小说创作辅助工具安装程序.exe` 分发给任何需要使用此工具的用户，他们无需安装Python或其他依赖即可使用。

## 注意事项

- 生成的可执行文件仅适用于Windows操作系统
- 由于包含了Python解释器和所有依赖，文件体积较大，这属于正常现象
- 应用程序使用tkinter作为GUI框架，完全兼容Windows环境