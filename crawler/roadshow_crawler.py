#!/usr/bin/env python3
"""
全景路演爬虫
使用 Playwright 爬取全景路演网站的路演信息
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class RoadshowCrawler:
    """全景路演爬虫类"""
    
    def __init__(self, user_data_dir: str = "./browser_session", headless: bool = False):
        """
        初始化爬虫
        
        Args:
            user_data_dir: 浏览器用户数据目录（用于保持会话状态）
            headless: 是否使用无头模式
        """
        self.user_data_dir = Path(user_data_dir)
        self.headless = headless
        self.base_url = "https://rs.p5w.net/roadshow"
        self.results: List[Dict[str, str]] = []
        
    def _setup_browser(self, playwright) -> BrowserContext:
        """设置浏览器上下文"""
        try:
            # 尝试使用系统安装的 Edge 浏览器
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                channel='msedge',  # 使用 Microsoft Edge
                args=['--no-sandbox'],
                viewport={'width': 1280, 'height': 720}
            )
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] 无法启动 Edge 浏览器，尝试使用 Chromium: {e}")
            # 如果 Edge 不可用，回退到 Chromium
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                args=['--no-sandbox'],
                viewport={'width': 1280, 'height': 720}
            )
        return context
    
    def _search_roadshow(self, page: Page, keyword: str) -> bool:
        """
        在搜索框中输入关键词并搜索
        
        Args:
            page: Playwright Page 对象
            keyword: 搜索关键词
            
        Returns:
            是否成功执行搜索
        """
        try:
            console.print(f"[cyan]正在搜索关键词: {keyword}[/cyan]")
            
            # 等待页面加载完成
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)  # 额外等待页面渲染
            
            # 查找搜索输入框（placeholder="请输入关键字"）
            search_input = page.locator('input.txt[placeholder="请输入关键字"]').first
            if search_input.count() == 0 or not search_input.is_visible(timeout=3000):
                # 备用方法：查找包含"请输入关键字"placeholder的输入框
                search_input = page.locator('input[placeholder="请输入关键字"]').first
                if search_input.count() == 0 or not search_input.is_visible(timeout=2000):
                    # 最后备用：查找"查找路演"标签附近的输入框
                    console.print("[yellow]⚠[/yellow] 使用备用方法查找搜索框...")
                    search_input = page.locator('input.txt').first
                    if search_input.count() == 0 or not search_input.is_visible(timeout=2000):
                        raise Exception("无法找到搜索输入框")
            
            # 清空输入框并输入关键词
            search_input.clear()
            search_input.fill(keyword)
            console.print(f"[dim]已输入搜索关键词: {keyword}[/dim]")
            
            # 等待一下让输入生效
            time.sleep(0.5)
            
            # 查找并点击搜索按钮
            # 搜索按钮: <a class="btn ml20"><i></i></a>
            search_button = page.locator('a.btn.ml20').first
            if search_button.is_visible(timeout=3000):
                search_button.click()
                console.print("[green]✓[/green] 已点击搜索按钮")
                
                # 等待搜索结果加载
                page.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(2)  # 等待列表渲染
                return True
            else:
                # 如果找不到按钮，尝试回车键
                console.print("[yellow]⚠[/yellow] 未找到搜索按钮，尝试使用回车键...")
                search_input.press("Enter")
                page.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(2)
                return True
                
        except Exception as e:
            console.print(f"[red]✗[/red] 搜索失败: {str(e)}")
            return False
    
    def _extract_roadshow_items(self, page: Page) -> List[Dict[str, str]]:
        """
        提取当前页面的路演信息
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            路演信息列表
        """
        items = []
        
        try:
            # 查找列表容器: <ul class="roadList cf">
            list_container = page.locator('ul.roadList.cf, .roadList.cf, ul.roadList')
            
            if list_container.count() == 0:
                console.print("[yellow]⚠[/yellow] 未找到路演列表容器")
                return items
            
            # 获取所有 li 元素
            li_elements = list_container.locator('li').all()
            
            console.print(f"[cyan]找到 {len(li_elements)} 个路演项目[/cyan]")
            
            for li in li_elements:
                try:
                    item = {}
                    import re
                    
                    # 获取整个 li 的文本内容
                    li_text = li.inner_text(timeout=1000)
                    
                    # 提取标题和链接
                    # 标题链接在 <a class="t"> 中，使用 onclick 属性
                    title_link = li.locator('a.t').first
                    if title_link.count() > 0:
                        # 获取标题文本
                        item['title'] = title_link.inner_text(timeout=1000).strip()
                        
                        # 从 onclick 属性中提取 URL
                        onclick = title_link.get_attribute('onclick', timeout=1000) or ""
                        if onclick:
                            # 匹配 window.open('URL') 格式
                            url_match = re.search(r"window\.open\('([^']+)'\)", onclick)
                            if url_match:
                                item['url'] = url_match.group(1)
                    else:
                        # 如果没有找到 class="t" 的链接，尝试从图片链接获取
                        pic_link = li.locator('p.pic a').first
                        if pic_link.count() > 0:
                            onclick = pic_link.get_attribute('onclick', timeout=1000) or ""
                            if onclick:
                                url_match = re.search(r"window\.open\('([^']+)'\)", onclick)
                                if url_match:
                                    item['url'] = url_match.group(1)
                    
                    # 如果没有找到 URL，尝试从所有链接中查找
                    if not item.get('url'):
                        all_links = li.locator('a').all()
                        for link in all_links:
                            onclick = link.get_attribute('onclick', timeout=500) or ""
                            if onclick and 'window.open' in onclick:
                                url_match = re.search(r"window\.open\('([^']+)'\)", onclick)
                                if url_match:
                                    item['url'] = url_match.group(1)
                                    break
                    
                    # 如果没有标题，尝试从文本中提取
                    if not item.get('title'):
                        # 尝试从链接文本中提取标题
                        links = li.locator('a').all()
                        for link in links:
                            link_text = link.inner_text(timeout=500).strip()
                            # 跳过股票代码链接和分享链接
                            if link_text and '分享' not in link_text and len(link_text) > 5:
                                item['title'] = link_text
                                break
                    
                    # 提取时间信息（在 <p class="date"> 中）
                    date_para = li.locator('p.date').first
                    if date_para.count() > 0:
                        item['time'] = date_para.inner_text(timeout=1000).strip()
                    else:
                        # 如果没有找到，使用正则表达式从文本中提取
                        time_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}[~-]\d{2}:\d{2})'
                        time_match = re.search(time_pattern, li_text)
                        if time_match:
                            item['time'] = time_match.group(1)
                        else:
                            item['time'] = ""
                    
                    # 提取股票代码和名称（在第一个链接中，如：毅昌科技(002420)）
                    first_link = li.locator('a').first
                    if first_link.count() > 0:
                        first_link_text = first_link.inner_text(timeout=1000).strip()
                        # 匹配股票代码格式：名称(6位数字)
                        code_pattern = r'^([^(]+)\((\d{6})\)$'
                        code_match = re.match(code_pattern, first_link_text)
                        if code_match:
                            item['stock_name'] = code_match.group(1).strip()
                            item['stock_code'] = code_match.group(2)
                        else:
                            # 如果没有股票代码，可能是公司名称
                            if first_link_text and len(first_link_text) < 50:
                                item['stock_name'] = first_link_text
                            item['stock_code'] = ""
                    else:
                        item['stock_code'] = ""
                        item['stock_name'] = ""
                    
                    # 如果成功提取到url或title，添加到列表
                    if item.get('url') or item.get('title'):
                        items.append(item)
                        
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] 提取项目时出错: {str(e)}")
                    continue
            
            return items
            
        except Exception as e:
            console.print(f"[red]✗[/red] 提取路演信息失败: {str(e)}")
            return items
    
    def _check_next_page(self, page: Page) -> bool:
        """
        检查是否有下一页
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            是否有下一页
        """
        try:
            # 查找包含"下一页"文本的链接（在 li > a 中）
            next_link = page.locator('a:has-text("下一页")').first
            if next_link.count() > 0 and next_link.is_visible(timeout=1000):
                # 检查父元素（li）是否有disabled或active类
                try:
                    parent = next_link.locator('..').first
                    classes = parent.get_attribute('class', timeout=500) or ""
                    if 'disabled' in classes or 'active' in classes:
                        return False
                except:
                    pass
                return True
            
            # 备用方法：查找其他分页选择器
            next_selectors = [
                'a:has-text(">")',
                '.pagination a:has-text(">")',
                '.page-next',
                'a.next',
            ]
            
            for selector in next_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible(timeout=1000):
                        classes = btn.get_attribute('class', timeout=500) or ""
                        if 'disabled' not in classes:
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _click_next_page(self, page: Page) -> bool:
        """
        点击下一页
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            是否成功点击
        """
        try:
            # 优先查找包含"下一页"文本的链接（在 li > a 中）
            next_link = page.locator('a:has-text("下一页")').first
            if next_link.count() > 0 and next_link.is_visible(timeout=1000):
                try:
                    # 检查父元素（li）是否有disabled类
                    parent = next_link.locator('..').first
                    classes = parent.get_attribute('class', timeout=500) or ""
                    if 'disabled' not in classes and 'active' not in classes:
                        next_link.click()
                        console.print("[cyan]已点击下一页[/cyan]")
                        page.wait_for_load_state("networkidle", timeout=30000)
                        time.sleep(2)  # 等待列表渲染
                        return True
                except:
                    # 如果获取父元素失败，直接点击链接
                    try:
                        next_link.click()
                        console.print("[cyan]已点击下一页[/cyan]")
                        page.wait_for_load_state("networkidle", timeout=30000)
                        time.sleep(2)
                        return True
                    except:
                        pass
            
            # 备用方法：查找其他分页选择器
            next_selectors = [
                'a:has-text(">")',
                '.pagination a:has-text(">")',
                '.page-next',
                'a.next',
            ]
            
            for selector in next_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible(timeout=1000):
                        classes = btn.get_attribute('class', timeout=500) or ""
                        if 'disabled' not in classes:
                            btn.click()
                            console.print("[cyan]已点击下一页[/cyan]")
                            page.wait_for_load_state("networkidle", timeout=30000)
                            time.sleep(2)
                            return True
                except:
                    continue
            
            return False
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] 点击下一页失败: {str(e)}")
            return False
    
    def crawl(self, keyword: str = "年度业绩说明会", max_pages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        爬取路演信息
        
        Args:
            keyword: 搜索关键词
            max_pages: 最大爬取页数，None表示爬取所有页
            
        Returns:
            路演信息列表
        """
        console.print(f"\n[bold cyan]🕷️  开始爬取全景路演信息[/bold cyan]")
        console.print(f"[dim]搜索关键词: {keyword}[/dim]")
        console.print(f"[dim]最大页数: {max_pages or '全部'}[/dim]")
        
        self.results = []
        
        with sync_playwright() as playwright:
            context = self._setup_browser(playwright)
            page = context.new_page()
            
            try:
                # 访问首页
                console.print(f"\n[cyan]正在访问: {self.base_url}[/cyan]")
                page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                
                # 执行搜索
                if not self._search_roadshow(page, keyword):
                    console.print("[red]✗[/red] 搜索失败，终止爬取")
                    return self.results
                
                # 爬取所有页面
                current_page = 1
                while True:
                    console.print(f"\n[bold]正在爬取第 {current_page} 页[/bold]")
                    
                    # 提取当前页的数据
                    page_items = self._extract_roadshow_items(page)
                    
                    if not page_items:
                        console.print("[yellow]⚠[/yellow] 当前页没有找到路演信息")
                        break
                    
                    self.results.extend(page_items)
                    console.print(f"[green]✓[/green] 第 {current_page} 页爬取完成，共 {len(page_items)} 条，累计 {len(self.results)} 条")
                    
                    # 检查是否达到最大页数
                    if max_pages and current_page >= max_pages:
                        console.print(f"[cyan]已达到最大页数限制 ({max_pages})[/cyan]")
                        break
                    
                    # 检查是否有下一页
                    if not self._check_next_page(page):
                        console.print("[cyan]没有更多页面了[/cyan]")
                        break
                    
                    # 点击下一页
                    if not self._click_next_page(page):
                        console.print("[yellow]⚠[/yellow] 无法点击下一页，终止爬取")
                        break
                    
                    current_page += 1
                    time.sleep(1)  # 页面切换间隔
                
            except Exception as e:
                console.print(f"[red]✗[/red] 爬取过程出错: {str(e)}")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            
            finally:
                context.close()
        
        console.print(f"\n[bold green]✓ 爬取完成！共获取 {len(self.results)} 条路演信息[/bold green]")
        return self.results
    
    def show_results(self):
        """显示爬取结果"""
        if not self.results:
            console.print("[yellow]⚠[/yellow] 没有爬取到任何数据")
            return
        
        table = Table(title="爬取的路演信息", show_header=True, header_style="bold magenta")
        table.add_column("序号", style="dim", width=6)
        table.add_column("股票名称", style="cyan", width=15)
        table.add_column("股票代码", style="yellow", width=10)
        table.add_column("标题", style="green")
        table.add_column("时间", style="blue", width=20)
        table.add_column("URL", style="dim", overflow="fold")
        
        for idx, item in enumerate(self.results, 1):
            table.add_row(
                str(idx),
                item.get('stock_name', ''),
                item.get('stock_code', ''),
                item.get('title', ''),
                item.get('time', ''),
                item.get('url', '')
            )
        
        console.print("\n")
        console.print(table)
    
    def save_results(self, filename: str = "roadshow_results.json"):
        """保存爬取结果到JSON文件"""
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓[/green] 结果已保存到: {filepath.absolute()}")
    
    def save_results_csv(self, filename: str = "roadshow_results.csv"):
        """保存爬取结果到CSV文件"""
        import csv
        filepath = Path(filename)
        
        if not self.results:
            console.print("[yellow]⚠[/yellow] 没有数据可保存")
            return
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['stock_name', 'stock_code', 'title', 'time', 'url'])
            writer.writeheader()
            for item in self.results:
                writer.writerow({
                    'stock_name': item.get('stock_name', ''),
                    'stock_code': item.get('stock_code', ''),
                    'title': item.get('title', ''),
                    'time': item.get('time', ''),
                    'url': item.get('url', '')
                })
        
        console.print(f"[green]✓[/green] 结果已保存到: {filepath.absolute()}")
