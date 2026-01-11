#!/usr/bin/env python3
"""
爬虫入口文件
可以通过 python -m crawler 运行
"""

from .roadshow_crawler import RoadshowCrawler
from rich.console import Console
from rich.prompt import Prompt, Confirm
import sys

console = Console()


def main():
    """主函数"""
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold magenta]  全景路演爬虫工具[/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")
    
    # 询问是否使用无头模式
    headless = not Confirm.ask("是否显示浏览器窗口？", default=True)
    
    # 创建爬虫实例
    crawler = RoadshowCrawler(headless=headless)
    
    # 询问搜索关键词
    keyword = Prompt.ask("请输入搜索关键词", default="年度业绩说明会")
    
    # 询问最大页数
    max_pages_input = Prompt.ask("最大爬取页数（直接回车表示爬取所有页）", default="")
    max_pages = None
    if max_pages_input.strip():
        try:
            max_pages = int(max_pages_input)
        except ValueError:
            console.print("[yellow]输入无效，将爬取所有页[/yellow]")
    
    # 开始爬取
    try:
        crawler.crawl(keyword=keyword, max_pages=max_pages)
        
        # 显示结果
        crawler.show_results()
        
        # 询问是否保存
        if Confirm.ask("\n是否保存结果到JSON文件？", default=True):
            crawler.save_results()
        
        if Confirm.ask("是否保存结果到CSV文件？", default=False):
            crawler.save_results_csv()
            
    except KeyboardInterrupt:
        console.print("\n\n[yellow]用户中断操作[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]发生错误:[/red] {str(e)}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
