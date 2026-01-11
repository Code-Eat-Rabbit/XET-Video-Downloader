#!/usr/bin/env python3
"""
爬虫使用示例
演示如何使用 RoadshowCrawler 爬取路演信息
"""

from crawler import RoadshowCrawler
from rich.console import Console

console = Console()


def example_basic_crawl():
    """基本使用示例"""
    console.print("[bold cyan]示例：基本爬取[/bold cyan]")
    
    # 创建爬虫实例（headless=False 显示浏览器窗口）
    crawler = RoadshowCrawler(headless=False)
    
    # 爬取数据（默认搜索"年度业绩说明会"）
    results = crawler.crawl(keyword="年度业绩说明会", max_pages=2)
    
    # 显示结果
    crawler.show_results()
    
    # 保存结果
    crawler.save_results("roadshow_results.json")
    crawler.save_results_csv("roadshow_results.csv")


def example_custom_keyword():
    """自定义关键词示例"""
    console.print("[bold cyan]示例：自定义关键词[/bold cyan]")
    
    crawler = RoadshowCrawler(headless=True)  # 无头模式
    
    # 搜索其他关键词
    results = crawler.crawl(keyword="投资者说明会", max_pages=1)
    
    console.print(f"\n[green]共爬取 {len(results)} 条数据[/green]")
    
    # 只保存JSON
    crawler.save_results()


if __name__ == "__main__":
    # 运行基本示例
    example_basic_crawl()
