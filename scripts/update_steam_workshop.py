from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]
DESCRIPTOR_PATH = ROOT_DIR / "descriptor.mod"
WORKSHOP_EN_PATH = ROOT_DIR / "workshop_en.txt"
WORKSHOP_CN_PATH = ROOT_DIR / "workshop_cn.txt"
STATE_DIR = ROOT_DIR / ".codex" / "steam_workshop"
STATE_FILE = STATE_DIR / "storage_state.json"
EDGE_PATH = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
EDIT_URL_TEMPLATE = (
    "https://steamcommunity.com/sharedfiles/itemedittext/"
    "?id={workshop_id}&language={language}"
)

LANGUAGE_ENGLISH = "0"
LANGUAGE_SIMPLIFIED_CHINESE = "6"


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


def load_publish_payload() -> dict[str, object]:
    descriptor = parse_descriptor(DESCRIPTOR_PATH)
    required_keys = ["remote_file_id"]
    missing = [key for key in required_keys if not descriptor.get(key)]
    if missing:
        raise ValueError(f"descriptor.mod 缺少必要字段: {', '.join(missing)}")

    return {
        "workshop_id": descriptor["remote_file_id"],
        "descriptions": [
            {
                "label": "English",
                "language": LANGUAGE_ENGLISH,
                "path": WORKSHOP_EN_PATH,
                "description": WORKSHOP_EN_PATH.read_text(encoding="utf-8"),
            },
            {
                "label": "Simplified Chinese",
                "language": LANGUAGE_SIMPLIFIED_CHINESE,
                "path": WORKSHOP_CN_PATH,
                "description": WORKSHOP_CN_PATH.read_text(encoding="utf-8"),
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


def print_preview(payload: dict[str, str]) -> None:
    print("=== Steam Workshop 更新预览 ===")
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
        input()
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


def require_login_if_needed(page) -> None:
    if page.locator("input#steamAccountName").count() > 0:
        raise RuntimeError(
            "当前处于 Steam 登录页，尚未保存可复用的登录态。\n"
            "请先运行: python scripts/update_steam_workshop.py --login"
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


def update_language_page(page, *, workshop_id: str, language_item: dict[str, str], do_submit: bool) -> None:
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
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            f"未能在预期时间内定位到 {language_item['label']} 页面上的描述编辑框。\n"
            "可能是 Steam 页面结构变化，或当前账号没有该创意工坊条目的编辑权限。"
        ) from exc

    update_form(page, language_item["description"])

    if do_submit:
        submit_form(page)
        page.wait_for_load_state("networkidle", timeout=30_000)
        page.wait_for_timeout(1500)
        print(f"已提交 {language_item['label']} 描述更新。")
    else:
        print(f"已填充 {language_item['label']} 描述，但未提交。")


def run_update(*, do_submit: bool, headless: bool) -> None:
    payload = load_publish_payload()

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="用 Edge + Playwright 依次更新 Steam Workshop 的英文和中文描述。"
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
        payload = load_publish_payload()

        if args.preview:
            print_preview(payload)
            return 0

        if args.login:
            save_storage_state_interactive(payload["workshop_id"])
            return 0

        run_update(do_submit=not args.dry_run, headless=args.headless)
        return 0
    except Exception as exc:  # pragma: no cover - CLI error path
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
