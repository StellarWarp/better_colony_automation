Colony Automation: Parallel Construction Patch
================================================

This is a Windows native-code patch for Stellaris 4.4.6. It changes the
colony-automation scheduler so automation may enqueue construction while the
planet still has an unused parallel construction slot.

Installing
----------

1. Close Stellaris.
2. Double-click "Install Patch.bat".
3. Confirm the detected stellaris.exe path, or enter its full path.
4. Read the result shown in the console window.
5. Start Stellaris. The patch mod does not need to be enabled in the launcher.

Subscribing downloads the installer and makes its local folder easy to find.
Enabling the patch mod in the launcher is unnecessary: the applied executable
patch works independently of launcher load order. The installer must be run
manually.

Restoring
---------

1. Close Stellaris.
2. Double-click "Restore Original.bat".
3. Confirm the detected stellaris.exe path, or enter its full path.

The installer creates a hash-named backup next to stellaris.exe before making
any change. Restore only proceeds when that backup reconstructs the current
patched executable exactly.

Checking Installation After Updates
-----------------------------------

After a beta or Steam update, close Stellaris and double-click "Check Patch
Status.bat". It only reads the executable and its BCA backups. Its result is
one of:

- `installed_verified`: the current executable exactly matches a patch rebuilt
  from its automatic backup.
- `not_installed_supported`: no patch is installed, but this installer can
  safely scan the current executable. Run the installer again.
- `not_installed_unsupported`: no patch is installed and the new executable
  needs a patcher update before it can be applied.
- `modified_unverified`: a BCA marker or conflicting backups were found, but
  the current executable cannot be verified. Do not reinstall or restore until
  the state has been reviewed.

Compatibility And Safety
------------------------

- Windows x64 only.
- The current reviewed profile is Stellaris 4.4.6.
- The patcher locates native features and validates their semantics instead of relying only on fixed addresses or an executable hash.
- Unknown or structurally changed game versions fail closed.
- Steam verification and official updates may restore stellaris.exe.
- The executable is unsigned, so Windows or antivirus software may display a
  warning.

Source and investigation notes:
https://github.com/StellarWarp/better_colony_automation

Workshop item: 3774886744


殖民地自动化：并行建造补丁
============================

这是一个适用于 Stellaris 4.4.6 的 Windows 原生代码补丁。它修改殖民地
自动化调度器，使自动化能够在行星仍有空闲并行建造槽位时继续入队。

安装方法
--------

1. 关闭 Stellaris。
2. 双击 "Install Patch.bat"。
3. 确认自动发现的 stellaris.exe 路径，或输入完整路径。
4. 阅读控制台窗口显示的结果。
5. 启动 Stellaris。

补丁 Mod 无需在启动器中启用。订阅工坊项目仅用于下载并方便找到安装器；
补丁写入 stellaris.exe 后独立于启动器加载顺序工作。订阅或启用本项目本身
不会修改游戏 EXE，必须手动运行安装器。

恢复方法
--------

1. 关闭 Stellaris。
2. 双击 "Restore Original.bat"。
3. 确认自动发现的 stellaris.exe 路径，或输入完整路径。

安装器会在修改前于 stellaris.exe 旁创建带哈希名称的备份。恢复操作仅会在
该备份能精确重建当前已补丁 EXE 时执行。

更新后的安装状态检查
--------------------

在 Beta 或 Steam 更新后，关闭 Stellaris 并双击 "Check Patch Status.bat"。
该操作只读取 EXE 与同目录的 BCA 备份，结果有四种：

- `installed_verified`：当前 EXE 可由自动备份精确重建，补丁仍在生效。
- `not_installed_supported`：未安装补丁，但当前 EXE 通过兼容性扫描；可重新运行安装器。
- `not_installed_unsupported`：未安装补丁，且当前版本需要更新补丁器后才能安全安装。
- `modified_unverified`：发现 BCA 标记或冲突备份，但无法验证当前 EXE；在人工检查前请勿安装或恢复。

兼容性与安全性
--------------

- 仅支持 Windows x64。
- 当前经过验证的版本为 Stellaris 4.4.6。
- 安装器按原生特征与语义验证目标，不只依赖固定地址或 EXE 哈希。
- 未知版本或结构变化会拒绝修改。
- Steam 验证和官方更新可能恢复 stellaris.exe。
- EXE 未签名，Windows 或杀毒软件可能显示警告。
