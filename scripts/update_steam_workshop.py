from __future__ import annotations

import argparse
import random
import sys
import textwrap
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SUBMODS_DIR = ROOT_DIR / "submods"
STATE_DIR = ROOT_DIR / ".codex" / "steam_workshop"
STATE_FILE = STATE_DIR / "storage_state.json"
EDGE_PATH = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDIT_URL_TEMPLATE = (
    "https://steamcommunity.com/sharedfiles/itemedittext/"
    "?id={workshop_id}&language={language}"
)

LANGUAGE_ENGLISH = "0"
LANGUAGE_SIMPLIFIED_CHINESE = "6"
ALL_PACKAGES = "all"
POST_SUBMIT_WAIT_SECONDS_MIN = 20
POST_SUBMIT_WAIT_SECONDS_MAX = 60


def load_playwright():
    try:
        from playwright.sync_api import TimeoutError as playwright_timeout_error
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "当前 Python 环境未安装 Playwright。预览不需要 Playwright；"
            "浏览器更新请先运行: "
            "conda run -n better_colony_automation python -m pip install playwright。"
            "不要运行 playwright install，本脚本会使用系统 Edge。"
        ) from exc
    return sync_playwright, playwright_timeout_error


def parse_descriptor(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"')
        data[key] = value
    return data


def available_packages() -> list[str]:
    packages = ["main"]
    if SUBMODS_DIR.is_dir():
        packages.extend(
            path.name
            for path in sorted(SUBMODS_DIR.iterdir())
            if path.is_dir() and (path / "descriptor.mod").is_file()
        )
    return packages


def package_choices() -> list[str]:
    return [ALL_PACKAGES, *available_packages()]


def selected_packages(package: str) -> list[str]:
    if package == ALL_PACKAGES:
        return available_packages()
    if package not in available_packages():
        raise ValueError(f"未知 Workshop 包: {package}")
    return [package]


def package_directory(package: str) -> Path:
    if package == "main":
        return ROOT_DIR
    if package not in available_packages():
        raise ValueError(f"未知 Workshop 包: {package}")
    directory = (SUBMODS_DIR / package).resolve()
    if SUBMODS_DIR.resolve() not in directory.parents:
        raise ValueError(f"非法 Workshop 包目录: {directory}")
    return directory


def load_publish_payload(package: str = "main") -> dict[str, object]:
    directory = package_directory(package)
    descriptor_path = directory / "descriptor.mod"
    workshop_en_path = directory / "workshop_en.txt"
    workshop_cn_path = directory / "workshop_cn.txt"
    required_files = [descriptor_path, workshop_en_path, workshop_cn_path]
    missing_files = [path for path in required_files if not path.is_file()]
    if missing_files:
        raise FileNotFoundError(
            "Workshop 发布资料缺失: "
            + ", ".join(str(path) for path in missing_files)
        )

    descriptor = parse_descriptor(descriptor_path)
    required_keys = ["remote_file_id"]
    missing = [key for key in required_keys if not descriptor.get(key)]
    if missing:
        raise ValueError(f"{descriptor_path} 缺少必要字段: {', '.join(missing)}")

    return {
        "package": package,
        "directory": directory,
        "workshop_id": descriptor["remote_file_id"],
        "descriptions": [
            {
                "label": "English",
                "language": LANGUAGE_ENGLISH,
                "path": workshop_en_path,
                "description": workshop_en_path.read_text(encoding="utf-8"),
            },
            {
                "label": "Simplified Chinese",
                "language": LANGUAGE_SIMPLIFIED_CHINESE,
                "path": workshop_cn_path,
                "description": workshop_cn_path.read_text(encoding="utf-8"),
            },
        ],
    }


def ensure_storage_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_edge_exists() -> None:
    if not EDGE_PATH.exists():
        raise FileNotFoundError(
            f"未找到 Edge 可执行文件: {EDGE_PATH}\n"
            "如果你的 Edge 安装在别的位置，请修改脚本顶部的 EDGE_PATH。"
        )


def print_preview(payload: dict[str, object]) -> None:
    print("=== Steam Workshop 更新预览 ===")
    print(f"Package: {payload['package']}")
    print(f"资料目录: {payload['directory']}")
    print(f"Workshop ID: {payload['workshop_id']}")
    for item in payload["descriptions"]:
        description = item["description"]
        preview = description[:800]
        if len(description) > len(preview):
            preview += "\n...\n"
        print(f"--- {item['label']} / language={item['language']} ---")
        print(f"来源文件: {item['path'].name}")
        print(f"描述长度: {len(description)} 字符")
        print(preview)


def print_previews(payloads: list[dict[str, object]]) -> None:
    for index, payload in enumerate(payloads):
        if index:
            print()
        print_preview(payload)


def launch_browser(playwright, *, headless: bool):
    ensure_edge_exists()
    return playwright.chromium.launch(
        executable_path=str(EDGE_PATH),
        headless=headless,
    )


def new_context(browser):
    if STATE_FILE.exists():
        return browser.new_context(storage_state=str(STATE_FILE))
    return browser.new_context()


def save_storage_state_interactive(workshop_id: str) -> None:
    ensure_storage_dir()
    ensure_edge_exists()
    sync_playwright, _ = load_playwright()

    with sync_playwright() as playwright:
        browser = launch_browser(playwright, headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(
            EDIT_URL_TEMPLATE.format(
                workshop_id=workshop_id,
                language=LANGUAGE_ENGLISH,
            ),
            wait_until="domcontentloaded",
        )
        print(
            textwrap.dedent(
                """
                请在打开的 Edge 窗口中确认以下事项：
                1. 完成 Steam 登录（如果页面要求登录）
                2. 确认已进入 Workshop 编辑页面
                3. 不要手动提交表单，回到终端按回车继续
                """
            ).strip()
        )
        while True:
            input()
            if is_editor_page(page):
                break
            if is_login_page(page):
                print(
                    "当前仍处于 Steam 登录页。请在 Edge 中完成登录并进入 Workshop 编辑页面后，"
                    "再回到终端按回车。"
                )
                continue
            print(
                "当前页面还没有描述编辑框。请确认 Edge 中已经进入 Workshop 编辑页面后，"
                "再回到终端按回车。"
            )
        context.storage_state(path=str(STATE_FILE))
        context.close()
        browser.close()
    print(f"已保存登录态到 {STATE_FILE}")


def launch_context(playwright, *, headless: bool):
    ensure_storage_dir()
    browser = launch_browser(playwright, headless=headless)
    context = new_context(browser)
    return browser, context


def wait_for_editor(page) -> None:
    description_locator = page.locator("#description")
    description_locator.wait_for(timeout=30_000)


def is_editor_page(page) -> bool:
    return page.locator("#description").count() > 0


def is_login_page(page) -> bool:
    login_selectors = [
        "input#steamAccountName",
        "input[name='username']",
        "input[type='password']",
        "text=Sign in",
        "text=登录",
        "text=登入",
    ]
    if any(page.locator(selector).count() > 0 for selector in login_selectors):
        return True
    lowered_url = page.url.lower()
    return "/login" in lowered_url or "openid/login" in lowered_url


def require_editor_or_login_hint(page, label: str) -> None:
    if is_editor_page(page):
        return
    if is_login_page(page):
        raise RuntimeError(
            "当前处于 Steam 登录页，尚未保存可复用的登录态。\n"
            "请先运行: "
            "conda run -n better_colony_automation python "
            "scripts\\update_steam_workshop.py --login"
        )
    raise RuntimeError(
        f"未能在预期时间内定位到 {label} 页面上的描述编辑框。\n"
        "可能是 Steam 页面结构变化，或当前账号没有该创意工坊条目的编辑权限。"
    )


def require_login_if_needed(page) -> None:
    if is_login_page(page):
        raise RuntimeError(
            "当前处于 Steam 登录页，尚未保存可复用的登录态。\n"
            "请先运行: "
            "conda run -n better_colony_automation python "
            "scripts\\update_steam_workshop.py --login"
        )


def update_form(page, description: str) -> None:
    page.locator("#description").fill(description)


def submit_form(page) -> None:
    submit_button = page.locator("a.btn_green_white_innerfade[href='javascript:ValidateForm()']")
    if submit_button.count() == 0:
        submit_button = page.locator("a.btn_green_white_innerfade", has_text="保存")
    if submit_button.count() == 0:
        submit_button = page.locator("a.btn_green_white_innerfade", has_text="Save")
    if submit_button.count() == 0:
        submit_button = page.locator("input[type='submit'][value='保存']")
    if submit_button.count() == 0:
        submit_button = page.locator("input[type='submit'][value='Save and Continue']")
    if submit_button.count() == 0:
        submit_button = page.locator("input[type='submit']")
    submit_button.first.click()


def wait_after_submit(page) -> None:
    wait_seconds = random.uniform(
        POST_SUBMIT_WAIT_SECONDS_MIN,
        POST_SUBMIT_WAIT_SECONDS_MAX,
    )
    print(f"提交后等待 {wait_seconds:.1f} 秒，降低 Steam 限流风险。")
    page.wait_for_timeout(int(wait_seconds * 1000))


def update_language_page(page, *, workshop_id: str, language_item: dict[str, str], do_submit: bool) -> None:
    _, playwright_timeout_error = load_playwright()
    page.goto(
        EDIT_URL_TEMPLATE.format(
            workshop_id=workshop_id,
            language=language_item["language"],
        ),
        wait_until="domcontentloaded",
    )

    require_login_if_needed(page)

    try:
        wait_for_editor(page)
    except playwright_timeout_error as exc:
        try:
            require_editor_or_login_hint(page, language_item["label"])
        except RuntimeError as hint:
            raise hint from exc
        raise

    update_form(page, language_item["description"])

    if do_submit:
        submit_form(page)
        page.wait_for_load_state("networkidle", timeout=30_000)
        print(f"已提交 {language_item['label']} 描述更新。")
        wait_after_submit(page)
    else:
        print(f"已填充 {language_item['label']} 描述，但未提交。")


def run_update_payload(payload: dict[str, object], *, do_submit: bool, headless: bool) -> None:
    sync_playwright, _ = load_playwright()

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, headless=headless)
        page = context.new_page()

        try:
            for language_item in payload["descriptions"]:
                update_language_page(
                    page,
                    workshop_id=payload["workshop_id"],
                    language_item=language_item,
                    do_submit=do_submit,
                )
        except Exception:
            context.close()
            browser.close()
            raise

        context.storage_state(path=str(STATE_FILE))
        context.close()
        browser.close()


def run_update(*, package: str, do_submit: bool, headless: bool) -> None:
    for package_name in selected_packages(package):
        payload = load_publish_payload(package_name)
        print(f"=== 更新 Workshop 包: {package_name} ===")
        run_update_payload(payload, do_submit=do_submit, headless=headless)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="用 Edge + Playwright 依次更新 Steam Workshop 的英文和中文描述。"
    )
    parser.add_argument(
        "--package",
        choices=package_choices(),
        default=ALL_PACKAGES,
        help="选择要更新的 Workshop 包（默认: all，依次更新 main 和所有子 Mod）。",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="只在终端输出将要发布的标题和描述预览，不打开浏览器。",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="打开浏览器并保存 Steam 登录态，供后续复用。",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="显式请求提交。当前默认行为已经会自动提交，保留该参数仅为兼容。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="打开页面并填充内容，但不点击保存。",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头运行。首次调试时通常不建议开启。",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        packages = selected_packages(args.package)
        payloads = [load_publish_payload(package) for package in packages]

        if args.preview:
            print_previews(payloads)
            return 0

        if args.login:
            save_storage_state_interactive(payloads[0]["workshop_id"])
            return 0

        run_update(
            package=args.package,
            do_submit=not args.dry_run,
            headless=args.headless,
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI error path
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
