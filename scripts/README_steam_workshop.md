# Steam Workshop 更新脚本

这个目录下的 `update_steam_workshop.py` 用于把主 Mod 和子 Mod 的发布文案同步到 Steam Workshop 编辑页。

当前同步内容：

- `<包目录>/workshop_en.txt` -> `language=0` 的英文描述
- `<包目录>/workshop_cn.txt` -> `language=6` 的中文描述
- `<包目录>/descriptor.mod` 里的 `remote_file_id` -> 目标 Workshop 条目 ID

包目录规则：

- `main` -> 仓库根目录
- 其他包 -> `submods/<包名>/`

当前流程：

1. 从所选包的 `descriptor.mod` 读取 Workshop ID；默认依次处理 `main` 和所有子 Mod
2. 访问对应条目的英文编辑页
3. 覆写英文描述并保存
4. 访问对应条目的中文编辑页
5. 覆写中文描述并保存

## 运行前提

- 本机已安装 Microsoft Edge
- 项目 Conda 环境已安装 Python `playwright` 包
- 不需要安装 Playwright 自带浏览器；脚本会使用系统 Edge：
  `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`

安装 Python 包：

```powershell
conda run -n better_colony_automation python -m pip install playwright
```

不要运行 `playwright install`，否则会额外下载 Playwright 管理的浏览器。

## 推荐流程

1. 先预览将要发布的内容。默认会预览 `main` 和所有子 Mod：

```powershell
conda run -n better_colony_automation python scripts\update_steam_workshop.py --preview
```

只预览岗位调控子 Mod：

```powershell
conda run -n better_colony_automation python scripts\update_steam_workshop.py --package job_regulation --preview
```

2. 首次使用时，保存一次 Steam 登录态：

```powershell
conda run -n better_colony_automation python scripts\update_steam_workshop.py --login
```

登录态由所有包共用。也可以通过 `--package job_regulation --login` 直接打开子 Mod 的编辑页。

执行后会打开一个新的 Edge 自动化窗口。请在这个窗口里完成 Steam 登录，并回到 Workshop 编辑页；确认无误后，回到终端按回车，脚本才会保存登录态并关闭窗口。

如果按回车时仍在 Steam 登录页，脚本会继续等待，不会保存无效登录态。
如果登录流程中断，重新执行 `--login` 即可。

3. 打开编辑页并自动填充，但先不提交：

```powershell
conda run -n better_colony_automation python scripts\update_steam_workshop.py --dry-run
```

4. 默认直接提交：

```powershell
conda run -n better_colony_automation python scripts\update_steam_workshop.py
```

以上两个命令默认会依次操作 `main` 和所有子 Mod；如果只想操作单个条目，可追加 `--package main` 或 `--package job_regulation`。

## 缩略图

缩略图由各包目录中的 `thumbnail_0.png` 生成：

```powershell
conda run -n better_colony_automation python scripts\build_workshop_thumbnails.py
```

输出为 512x512 的 `thumbnail.png`。该文件会随 Mod 发布脚本复制到游戏 Mod 目录，但 Steam Workshop 网页预览图目前仍需手动上传。

## 登录态文件

脚本会把可复用状态保存到：

- `.codex/steam_workshop/storage_state.json`

如果 Steam 登录失效，重新执行 `--login` 即可。

## 注意事项

- 首次建议先用 `--dry-run`，观察 Steam 页面实际字段是否匹配。
- 当前默认不带参数就是自动提交 `main` 和所有子 Mod；如果只想打开页面并填充内容，请使用 `--dry-run`。
- 如果 Steam 更改了编辑页结构，脚本里的选择器可能需要更新。
- 当前脚本只同步中英文描述，还没有自动处理标题、预览图、可见性、标签等字段。
