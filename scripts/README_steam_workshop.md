# Steam Workshop 更新脚本

这个目录下的 `update_steam_workshop.py` 用于把仓库里的发布文案同步到 Steam Workshop 编辑页。

当前同步内容：

- `workshop_en.txt` -> `language=0` 的英文描述
- `workshop_cn.txt` -> `language=6` 的中文描述
- `descriptor.mod` 里的 `remote_file_id` -> 目标 Workshop 条目 ID

当前流程：

1. 访问 `https://steamcommunity.com/sharedfiles/itemedittext/?id=3673829479&language=0`
2. 覆写英文描述并保存
3. 访问 `https://steamcommunity.com/sharedfiles/itemedittext/?id=3673829479&language=6`
4. 覆写中文描述并保存

## 运行前提

- 本机已安装 Microsoft Edge
- 本机 Python 环境已安装 `playwright`
- 当前脚本默认使用：
  `C:\Users\Estelle\AppData\Local\miniconda3\python.exe`

## 推荐流程

1. 先预览将要发布的内容：

```powershell
& 'C:\Users\Estelle\AppData\Local\miniconda3\python.exe' scripts\update_steam_workshop.py --preview
```

2. 首次使用时，保存一次 Steam 登录态：

```powershell
& 'C:\Users\Estelle\AppData\Local\miniconda3\python.exe' scripts\update_steam_workshop.py --login
```

执行后会打开一个新的 Edge 自动化窗口。请在这个窗口里完成 Steam 登录，并回到 Workshop 编辑页；确认无误后，回到终端按回车，脚本才会保存登录态并关闭窗口。

3. 打开编辑页并自动填充，但先不提交：

```powershell
& 'C:\Users\Estelle\AppData\Local\miniconda3\python.exe' scripts\update_steam_workshop.py --dry-run
```

4. 默认直接提交：

```powershell
& 'C:\Users\Estelle\AppData\Local\miniconda3\python.exe' scripts\update_steam_workshop.py
```

## 登录态文件

脚本会把可复用状态保存到：

- `.codex/steam_workshop/storage_state.json`

如果 Steam 登录失效，重新执行 `--login` 即可。

## 注意事项

- 首次建议先用 `--dry-run`，观察 Steam 页面实际字段是否匹配。
- 当前默认不带参数就是自动提交；如果只想打开页面并填充内容，请使用 `--dry-run`。
- 如果 Steam 更改了编辑页结构，脚本里的选择器可能需要更新。
- 当前脚本只同步中英文描述，还没有自动处理标题、预览图、可见性、标签等字段。
