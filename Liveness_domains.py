import os
import re
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio
from playwright.async_api import async_playwright, TimeoutError

# 配置
MAX_CONCURRENT_TASKS = 10
PROXY_SERVER = "http://127.0.0.1:7890"
OUTPUT_DIR = Path("png")
FAILURE_LOG = Path("failure.log")

# 计数
stats = {
    "success": 0,
    "fail": 0,
    "proxy_used": 0
}



def safe_filename(url: str) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", url)
    return f"{date}_{cleaned}.png"


def load_domains() -> list[str]:
    if Path("domains.txt").exists():
        with open("domains.txt", "r", encoding="utf-8") as f:
            return list({line.strip() for line in f if line.strip()})

    excel_files = list(Path(".").glob("*.xls*"))
    domains = set()
    for file in excel_files:
        df = pd.read_excel(file, engine="openpyxl" if file.suffix == ".xlsx" else None)
        for col in df.columns:
            domains.update(str(val).strip() for val in df[col] if pd.notna(val))
    return list(domains)


def normalize_url(domain: str) -> str:
    domain = domain.strip().replace("http://http://", "http://").replace("http://https://", "https://")
    if not domain.startswith("http"):
        domain = "http://" + domain
    return domain


def log_failure(url: str, error: Exception, proxy: bool):
    with FAILURE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {url} | 使用代理: {proxy} | 错误: {type(error).__name__} - {error}\n")


# 访问与截图
async def visit_and_screenshot(playwright, url: str, index: int, total: int, progress):
    async with asyncio.Semaphore(MAX_CONCURRENT_TASKS):
        normalized_url = normalize_url(url)
        file_name = safe_filename(normalized_url)
        OUTPUT_DIR.mkdir(exist_ok=True)
        save_path = OUTPUT_DIR / file_name

        browser = None

        async def try_access(use_proxy=False):
            nonlocal browser
            launch_args = {"headless": True}
            if use_proxy:
                launch_args["proxy"] = {"server": PROXY_SERVER}

            browser = await playwright.chromium.launch(**launch_args)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            await page.goto(normalized_url, timeout=15000, wait_until="load")
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.screenshot(path=str(save_path), full_page=True)
            await context.close()

        try:
            print(f"[{index:03}/{total}] 访问：{normalized_url}")
            await try_access()
            stats["success"] += 1
            print(f"[✔] 成功截图：{save_path}")
        except Exception as e1:
            print(f"[!] 初次访问失败，尝试代理访问：{normalized_url}")
            stats["proxy_used"] += 1
            try:
                if browser:
                    await browser.close()
                await try_access(use_proxy=True)
                stats["success"] += 1
                print(f"[✔] 代理访问成功截图：{save_path}")
            except Exception as e2:
                stats["fail"] += 1
                log_failure(normalized_url, e2, proxy=True)
                print(f"[✘] 代理访问失败：{normalized_url} | 错误: {e2}")
        finally:
            if browser:
                await browser.close()
            progress.update(1)


# 主程序
async def main():
    FAILURE_LOG.write_text("")  # 清空日志
    domains = load_domains()
    if not domains:
        print(" 未找到 domains.txt 或 Excel 表，请确认文件是否存在。")
        return

    print(f" 共读取到 {len(domains)} 个域名，开始处理...\n")

    async with async_playwright() as playwright:
        with tqdm_asyncio(total=len(domains), desc="进度", ncols=80) as progress:
            tasks = [
                visit_and_screenshot(playwright, domain, i + 1, len(domains), progress)
                for i, domain in enumerate(domains)
            ]
            await asyncio.gather(*tasks)

    # 统计
    print("\n 执行完毕！")
    print(f" 成功截图数：{stats['success']}")
    print(f" 访问失败数：{stats['fail']}")
    print(f" 使用代理数：{stats['proxy_used']}")
    print(f" 失败日志路径：{FAILURE_LOG.resolve()}")
    print(f" 截图保存路径：{OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())