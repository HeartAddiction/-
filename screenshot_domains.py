import os
import re
import asyncio
from playwright.async_api import async_playwright

# 当前所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 读列表
def load_domains(file_path="domains.txt"):
    path = os.path.join(script_dir, file_path)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# 合法文件名处理
def sanitize_filename(url: str):
    name = url.replace("://", "_").replace("/", "_")
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name

# 访问并截图
async def screenshot_domain(playwright, domain):
    for scheme in ["https://", "http://"]:
        if domain.startswith("http://") or domain.startswith("https://"):
            url = domain
        else:
            url = scheme + domain

        try:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            print(f"[+] 正在访问：{url}")
            response = await page.goto(url, timeout=15000, wait_until="load")

            # 跳过google红页
            if "proceed-link" in await page.content():
                print(f"[!] 检测到危险警告页面，尝试跳过：{url}")
                try:
                    await page.click("#details-button")
                    await page.click("#proceed-link")
                    await page.wait_for_load_state("load")
                except:
                    pass


            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as e:
                print(f"[!] 页面长时间未进入空闲状态，降级处理 {type(e).__name__}:{e}")
                await page.wait_for_load_state("load")
                aia = await page.wait_for_timeout(2000)
            # 构造文件名并截图
            safe_name = sanitize_filename(page.url)
            file_path = os.path.join(script_dir, f"{safe_name}.png")
            await page.screenshot(path=file_path, full_page=True)
            print(f"[✓] 截图成功：{file_path}")

            await browser.close()
            return
        except Exception as e:
            print(f"[✘] 访问失败：{url} - {type(e).__name__}: {e}")
            continue

# 主执行函数
async def main():
    domains = load_domains()
    async with async_playwright() as playwright:
        tasks = [screenshot_domain(playwright, domain) for domain in domains]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
