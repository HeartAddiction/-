🔍 URL 批量检测工具（含标题提取）

本工具支持批量检测 URL 是否存活，并提取网页标题。支持 SOCKS5 代理、重复 URL 检测、支持导出为 .txt 或 .xlsx 格式，适合进行域名探测、资产收集、内容排查等任务。

🧩 功能简介

✅ 支持从 .txt 文件中批量读取 URL（自动补全 http）
✅ 自动识别并标记重复的 URL
✅ 检测目标网站是否可访问，并返回状态码/错误类型
✅ 提取网页 <title> 标签内容
✅ 支持通过 SOCKS5 代理访问（例如：127.0.0.1 7890）
✅ 多线程加速（默认 50 线程）
✅ 支持导出为 Excel 或 TXT 文件格式
🖥️ 环境依赖
请先安装依赖库（推荐使用 Python 3.8+）：
pip install -r requirements.txt

requirements.txt 内容示例：
requests[socks]>=2.25.1
beautifulsoup4>=4.9.3
charset-normalizer>=3.1.0
pyfiglet>=0.8.post1
openpyxl>=3.0.9
urllib3>=1.26.5

📂 使用说明
准备一个包含 URL 的文本文件，每行一个网址，例如：
example.com
⚠️ 支持自动将 example[.]com 转换为 http://example.com 格式。
运行程序：

python main.py

根据提示操作：

输入 URL 文件名（如：urls.txt）

输入代理（可跳过）

选择导出格式：txt 或 excel
指定输出文件名

📤 输出示例
TXT 格式输出：
URL              状态              标题
http://abc.com   存活              示例标题
http://test.com  失败: Timeout     无

Excel 格式输出：
三列：URL | 状态 | 标题，含重复标记信息。
🛠️ 注意事项


URL 文件中支持带路径、带端口的格式。

如果同一个 URL 多次出现，程序将标记其为“与第 X 行重复”。

网页编码通过 charset-normalizer 自动识别，兼容多语言网页。
