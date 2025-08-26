import os
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import urllib3
from urllib.parse import urlparse, urlunparse
from charset_normalizer import from_bytes
import pyfiglet

# 关闭 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def print_banner():
    banner = pyfiglet.figlet_format("xinY")
    print(banner)

# [.]改.加http
def normalize_to_http(url):
    url = url.replace("[.]", ".").strip()
    parsed = urlparse(url if "://" in url else f"http://{url}")
    return urlunparse(("http", parsed.netloc, parsed.path or "", "", "", ""))

# 爬tittle
def extract_title(resp):
    try:
        result = from_bytes(resp.content).best()
        html = result.output()
        soup = BeautifulSoup(html, "html.parser")
        return soup.title.string.strip() if soup.title and soup.title.string else "无标题"
    except:
        return "解析失败"

def fetch(url, proxy=None):
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=5,  # 超时
            verify=False,
            allow_redirects=True,
            proxies={"http": proxy, "https": proxy} if proxy else None
        )
        if resp.status_code != 200:
            return {"url": url, "status": f"状态码 {resp.status_code}", "title": ""}
        return {"url": url, "status": "存活", "title": extract_title(resp)}
    except requests.exceptions.Timeout:
        return {"url": url, "status": "失败: Timeout", "title": ""}
    except requests.exceptions.ProxyError:
        return {"url": url, "status": "失败: ProxyError", "title": ""}
    except Exception as e:
        return {"url": url, "status": f"失败: {type(e).__name__}", "title": ""}

# 测试代理
def test_proxy(proxy):
    try:
        resp = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        return resp.status_code == 200
    except:
        return False

def load_urls_with_duplicates(filepath):
    urls = []
    seen = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            raw = line.strip()
            if not raw:
                continue
            url = normalize_to_http(raw)
            if url not in seen:
                seen[url] = idx
                urls.append((url, None))
            else:
                urls.append((url, seen[url]))
    return urls

# txt与excel自定义
def save_results(results_map, urls_with_flags, fmt, filename):
    if fmt == "txt":
        if not filename.endswith(".txt"):
            filename += ".txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("URL\t状态\t标题\n")
            for url, dup_line in urls_with_flags:
                if dup_line:
                    f.write(f"{url}\t与第 {dup_line} 行重复\t\n")
                else:
                    r = results_map.get(url, {"status": "未知", "title": ""})
                    f.write(f"{url}\t{r['status']}\t{r['title']}\n")
    else:
        import openpyxl
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "URL检测结果"
        ws.append(["URL", "状态", "标题"])
        for url, dup_line in urls_with_flags:
            if dup_line:
                ws.append([url, f"与第 {dup_line} 行重复", ""])
            else:
                r = results_map.get(url, {"status": "未知", "title": ""})
                ws.append([url, r['status'], r['title']])
        wb.save(filename)

    print(f"\n 结果已保存至：{filename}")

def main():
    print_banner()

    # 输入txt
    input_file = input("请输入包含 URL 的 txt 文件名：").strip()
    if not input_file or not os.path.exists(input_file):
        print(f"\n 未找到文件：{input_file}")
        return

    # 代理
    while True:
        proxy_input = input("请输入 SOCKS5 代理 IP 和端口（如 127.0.0.1 7890，回车跳过）：").strip()
        if not proxy_input:
            proxy = None
            break
        parts = proxy_input.split()
        if len(parts) != 2:
            print(" 输入格式错误，应为：IP 端口，如 127.0.0.1 7890")
            continue
        ip, port = parts
        proxy = f"socks5h://{ip}:{port}"
        print(f" 正在测试代理：{proxy}")
        if test_proxy(proxy):
            print(" 代理可用")
            break
        else:
            print(" 代理不可用，请重新输入")

    urls_with_flags = load_urls_with_duplicates(input_file)
    unique_urls = [url for url, dup in urls_with_flags if dup is None]
    print(f"\n共 {len(urls_with_flags)} 条URL，其中唯一需检测：{len(unique_urls)}\n")

    results_map = {}
# 50线程
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(fetch, url, proxy): url for url in unique_urls}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results_map[res["url"]] = res
            print(f"{res['url']} → {res['status']}")

# 输出
    fmt = input("\n请输入输出文件格式（txt 或 excel，默认 excel）：").strip().lower()
    if fmt not in ("txt", "excel", ""):
        print(" 输出格式错误，仅支持 txt 或 excel")
        return
    fmt = "excel" if fmt == "" else fmt

    output_name = input("请输入输出文件名（默认 tittle_domains）：").strip() or "tittle_domains"

    save_results(results_map, urls_with_flags, fmt, output_name)

if __name__ == "__main__":
    main()
