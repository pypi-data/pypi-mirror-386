# ypp

多分支 worktree 管理工具（支持 `krepo-ng` 与 `git`）。

## 安装

```bash
pip install ypp
```

## 使用

- 创建 worktree：

```bash
ypp add <path> <branch>
```

这会在 `~/<path>/wpsmain` 和 `~/<path>/wpsweb` 下分别创建或切换到 `<branch>`。

- 列出 worktree：

```bash
ypp list
```

- 移除 worktree：

```bash
ypp remove <path>
```

这会移除 `~/<path>/wpsmain` 和 `~/<path>/wpsweb` 的 worktree，并删除整个 `<path>` 目录。

- 配置管理：

```bash
ypp set work_dir=~/workspace  # 设置工作目录
ypp config                    # 显示当前配置
```

- 修改配置和生成构建脚本（仅限 Linux）：

```bash
ypp modify                    # 修改 wpsweb/server/Makefile 和生成 build_server.sh
ypp modify --force            # 强制在非 Linux 系统上运行（不推荐）
```

这会自动查找 wpsweb 目录，并执行以下操作：
1. **修改 `server/Makefile`**：
   - 去掉 `-Wl,-s` 参数
   - 将 `-O2` 修改为 `-g`
2. **生成 `build_server.sh`**：
   - 清空文件内容并写入构建脚本
   - 动态替换路径变量（基于当前执行路径）
   - 自动设置执行权限

> **注意**: `modify` 命令仅在 Linux 系统上支持，因为它需要修改 Makefile 和生成 shell 脚本。

- 初始化仓库：

```bash
ypp init wpsmain             # 初始化 wpsmain 仓库
ypp init wpsweb              # 初始化 wpsweb 仓库
ypp init                     # 依次初始化 wpsmain 和 wpsweb 仓库
```

这会执行以下操作：
1. **wpsmain 初始化**：在当前目录执行 `krepo-ng init -b master_kso_v12 --bundle all`
2. **wpsweb 初始化**：在当前目录执行 `git clone git@ksogit.kingsoft.net:wow/wpsweb.git`

- 自动编译 wpsmain：

```bash
ypp build                     # 自动编译 wpsmain
```

这会自动查找 wpsmain 目录，并在 Docker 中执行以下操作：
1. **配置 weboffice**：执行 `krepo-ng config --new -x weboffice`
2. **检查目录**：验证 `debug_weboffice` 目录是否创建成功
3. **编译项目**：在 `debug_weboffice` 目录中执行 `krepo-ng build`
4. **执行构建脚本**：查找并执行 `wpsweb/build_server.sh` 脚本

> **注意**: `build` 命令需要在 Docker 环境中执行，使用 `kdocker -r qt5` 命令。

- 读取和清除 PPTX 文件属性：

```bash
ypp pptattr <filepath>                    # 读取 PPTX 文件属性
ypp pptattr <filepath> --clean           # 清除指定属性并保存到原文件
```

这会执行以下操作：
1. **读取属性**：显示 PPTX 文件的核心属性、应用属性和自定义属性
2. **清除属性**（使用 `--clean` 参数时）：
   - 清除核心属性中的 `lastModifiedBy`
   - 清除自定义属性中的 `ICV`
   - 保持原有的 XML 结构，确保与 Office 应用程序兼容
   - 自动保存到原文件

> **注意**: `pptattr` 命令只支持 `.pptx` 格式的文件。使用 `--clean` 参数会直接修改原文件，建议先备份。

- WSL 端口转发管理：

```bash
ypp wsl port <本机端口> <WSL端口>        # 添加端口转发
ypp wsl port remove <本机端口>           # 移除端口转发
ypp wsl port list                       # 列出所有端口转发规则
```

这会执行以下操作：
1. **添加端口转发**：将本机的指定端口转发到 WSL 中的指定端口
2. **移除端口转发**：删除指定的端口转发规则
3. **列出规则**：显示当前所有的端口转发规则

> **注意**: `wsl port` 命令仅在 Windows 系统上支持。添加和移除端口转发需要管理员权限，系统会自动检测并请求权限。查看端口转发规则不需要管理员权限。

- 反馈导出管理：

```bash
ypp feedback export <Excel文件路径>      # 从Excel文件导出WPP或P组件的对话详情
ypp feedback export <Excel文件路径> --sheet <表名>  # 指定表名导出
ypp feedback format                      # 格式化客服原语，在特定关键词前添加换行符
```

这会执行以下操作：

**export 命令：**
1. **读取Excel文件**：
   - 默认读取最新的sheet表（倒数第二个表）
   - 可通过 `--sheet` 或 `-s` 参数指定表名
2. **查找满足条件的数据**：在表中查找同时满足以下条件的行：
   - 业务归属列为"AI"、"AI-会员"或"AI-365"
   - 一级分类列为"演示"
3. **提取对话详情**：获取"对话详情1"列的文本内容
4. **导出文件**：将每个对话详情导出为独立的txt文件，文件名使用Excel行号
5. **创建输出目录**：在当前路径下创建"客服"文件夹存放导出的文件

**format 命令：**
1. **遍历当前目录**：自动查找当前路径下的所有txt文件
2. **识别关键词**：查找"客服"、"用户"、"WPS客户"等关键词
3. **添加换行符**：在关键词前添加换行符，让日志更易读
4. **删除空行**：删除多余的空行，保持文档整洁
5. **清理空白**：清理行首行尾的空白字符
6. **保存文件**：将格式化后的内容保存回原文件

> **注意**: `feedback export` 命令支持 `.xlsx` 和 `.xls` 格式的Excel文件。系统会自动识别组件列和对话详情列，支持多种列名格式。`feedback format` 命令会直接修改原文件，建议先备份重要文件。

## 依赖

- 需要本机已安装并在 PATH 中可用：`krepo-ng`、`git`。
- 配置文件位置：`~/.ypp.json`

## 许可

MIT