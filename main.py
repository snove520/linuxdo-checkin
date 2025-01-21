import os
import random
import time
import functools
import sys
import requests

from loguru import logger
from playwright.sync_api import sync_playwright
from tabulate import tabulate
from datetime import datetime
import pytz


def retry_decorator(retries=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        logger.error(f"函数 {func.__name__} 最终执行失败: {str(e)}")
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1}/{retries} 次尝试失败: {str(e)}")
                    time.sleep(1)
            return None

        return wrapper

    return decorator


os.environ.pop("DISPLAY", None)
os.environ.pop("DYLD_LIBRARY_PATH", None)

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

HOME_URL = "https://linux.do/"


class LinuxDoBrowser:
    def __init__(self) -> None:
        self.browse_count = 0  # 浏览帖子计数
        self.like_count = 0    # 点赞计数
        self.start_time = time.time()  # 记录开始时间

        self.pw = sync_playwright().start()
        self.browser = self.pw.firefox.launch(headless=True, timeout=30000)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(HOME_URL)

    def login(self):
        logger.info("开始登录")
        self.page.click(".login-button .d-button-label")
        time.sleep(2)
        self.page.fill("#login-account-name", USERNAME)
        time.sleep(2)
        self.page.fill("#login-account-password", PASSWORD)
        time.sleep(2)
        self.page.click("#login-button")
        time.sleep(10)
        user_ele = self.page.query_selector("#current-user")
        if not user_ele:
            logger.error("登录失败")
            return False
        else:
            logger.info("登录成功")
            return True

    # def click_topic(self):
    #     topic_list = self.page.query_selector_all("#list-area .title")
    #     logger.info(f"发现 {len(topic_list)} 个主题帖")
    #     for topic in topic_list:
    #         self.click_one_topic(topic.get_attribute("href"))

    def click_topic(self):
        topic_list = self.page.query_selector_all("#list-area .title")
        total_topics = len(topic_list)
        logger.info("=" * 50)
        logger.info(f"共发现 {total_topics} 个主题帖")
        logger.info("=" * 50)
        
        for index, topic in enumerate(topic_list, 1):
            logger.info("\n" + "-" * 30)
            logger.success(f"进度：{index}/{total_topics} ({(index/total_topics*100):.1f}%)")
            topic_url = topic.get_attribute("href")
            self.click_one_topic(topic_url, index, total_topics)
            
            if random.random() < 0.1:  # 10% 概率提前退出
                logger.info("随机退出浏览")
                break

    @retry_decorator()
    # def click_one_topic(self, topic_url):
    #     page = self.context.new_page()
    #     page.goto(HOME_URL + topic_url)
    #     if random.random() < 0.3:  # 0.3 * 30 = 9
    #         self.click_like(page)
    #     self.browse_post(page)
    #     self.browse_count += 1  # 增加浏览计数
    #     page.close()
    def click_one_topic(self, topic_url, current_index, total_topics):
        page = self.context.new_page()
        page.goto(HOME_URL + topic_url)
        
        try:
            # 获取帖子标题
            title = None
            title_selectors = [
                "#main-outlet .topic-title h1",
                "h1 .fancy-title span[dir='auto']",
                "#main-outlet h1",
                ".topic-title",
                ".title-wrapper h1 a[data-topic-id]",  # 使用更精确的选择器
                ".title-wrapper h1 a .fancy-title span"
            ]
            
            # 依次尝试不同的选择器
            for selector in title_selectors:
                try:
                    title_elements = page.locator(selector)
                    count = title_elements.count()
                    if count > 0:
                        # 如果有多个元素，遍历它们找到实际的标题
                        for i in range(count):
                            element_text = title_elements.nth(i).inner_text().strip()
                            if element_text and not element_text.startswith("此话题"):  # 排除提示文本
                                title = element_text
                                break
                        if title:  # 如果找到有效标题就退出循环
                            break
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 尝试失败: {str(e)}")
                    continue
            
            # 如果上述方法都失败，尝试直接获取带有 data-topic-id 的链接文本
            if not title:
                try:
                    topic_link = page.locator("a[data-topic-id]").first
                    if topic_link:
                        title = topic_link.inner_text().strip()
                except Exception as e:
                    logger.debug(f"备用方法获取标题失败: {str(e)}")
            
            if not title:
                title = "未知标题"
            
            logger.info(f"[{current_index}/{total_topics}] 正在浏览: {title}")
            
            # 根据已点赞数量动态调整点赞概率
            if self.like_count < 5:  # 如果点赞数少于5个，提高点赞概率
                like_probability = 0.5  # 50% 概率
            elif self.like_count < 10:  # 如果点赞数在5-10之间
                like_probability = 0.3  # 30% 概率
            else:  # 如果已经点赞超过10个
                like_probability = 0.1  # 降低到10%概率
            
            if random.random() < like_probability:
                self.click_like(page)
            
            self.browse_post(page)
            self.browse_count += 1
        except Exception as e:
            logger.error(f"浏览帖子时出错: {str(e)}")
        finally:
            page.close()

    def browse_post(self, page):
        # 获取帖子标题和信息
        try:
            # 尝试多种可能的标题选择器
            title = None
            title_selectors = [
                "#main-outlet .topic-title h1",           # 第一种形式
                "h1 .fancy-title span[dir='auto']",       # 第二种形式
                "#main-outlet h1",                        # 第三种形式
                ".topic-title",                           # 第四种形式
                ".title-wrapper h1 a[data-topic-id]",     # 第五种形式（分页帖子，使用更精确的选择器）
                ".title-wrapper h1 a .fancy-title span",  # 第六种形式
                "h1.topic-title",                         # 第七种形式
                ".topic-title h1 span"                    # 第八种形式
            ]
            
            # 依次尝试不同的选择器
            for selector in title_selectors:
                try:
                    title_elements = page.locator(selector)
                    count = title_elements.count()
                    if count > 0:
                        # 如果有多个元素，尝试找到包含实际标题的那个
                        for i in range(count):
                            element_text = title_elements.nth(i).inner_text().strip()
                            if element_text and not element_text.startswith("此话题"):  # 排除提示文本
                                title = element_text
                                break
                        if title:  # 如果找到有效标题就退出循环
                            break
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 尝试失败: {str(e)}")
                    continue
            
            # 如果上述方法都失败，尝试直接获取带有 data-topic-id 的链接文本
            if not title:
                try:
                    topic_link = page.locator("a[data-topic-id]").first
                    if topic_link:
                        title = topic_link.inner_text().strip()
                except Exception as e:
                    logger.debug(f"备用方法获取标题失败: {str(e)}")
            
            if not title:
                title = "未知标题"
                logger.warning("无法获取标题")
            
            # 获取分类（使用 first 避免多个元素的问题）
            category = page.locator(".title-wrapper .badge-category__name").first.inner_text()
            # 获取所有标签
            tags = page.locator(".discourse-tags .discourse-tag").all_inner_texts()
            
            logger.info(f"已加载页面: {page.url} | 标题: {title}")
            logger.info(f"分类：{category}")
            if tags:
                logger.info(f"标签：{', '.join(tags)}")
        except Exception as e:
            logger.warning(f"获取帖子信息失败: {str(e)}")
            title = "未知标题"

        prev_url = None
        # 开始自动滚动，最多滚动10次
        for _ in range(10):
            # 随机滚动一段距离
            scroll_distance = random.randint(550, 650)  # 随机滚动 550-650 像素
            logger.info(f"向下滚动 {scroll_distance} 像素...")
            page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            # logger.info(f"已加载页面: {page.url}")
            # logger.info(f"已加载页面: {page.url} | 标题: {title}")
            logger.info("已加载页面: {} | 标题: {}", page.url, title)

            if random.random() < 0.03:  # 33 * 4 = 132
                logger.success("随机退出浏览")
                break

            # 检查是否到达页面底部
            at_bottom = page.evaluate("window.scrollY + window.innerHeight >= document.body.scrollHeight")
            current_url = page.url
            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("已到达页面底部，退出浏览")
                break

            # 动态随机等待
            wait_time = random.uniform(2, 4)  # 随机等待 2-4 秒
            logger.info(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    def run(self):
        if not self.login():
            logger.error("登录失败，程序终止")
            sys.exit(1)  # 使用非零退出码终止整个程序
        self.click_topic()
        self.print_connect_info()

    def click_like(self, page):
        try:
            # 1. 首先检查是否有未点赞的按钮
            like_button = page.locator('.discourse-reactions-reaction-button[title="点赞此帖子"]').first
            if not like_button:
                logger.info("帖子可能已经点过赞了")
                return

            # 2. 获取帖子的点赞数
            likes_count = 0
            try:
                likes_element = page.locator('.discourse-reactions-counter').first
                if likes_element:
                    likes_text = likes_element.inner_text().strip()
                    likes_count = int(''.join(filter(str.isdigit, likes_text)) or 0)
                    logger.info(f"发现帖子，当前点赞数：{likes_count}")
            except Exception as e:
                logger.debug(f"获取点赞数失败: {str(e)}")
                return

            # 3. 根据点赞数决定点赞概率
            if likes_count >= 50:  # 高赞帖子
                probability = 0.9   # 90% 概率点赞
            elif likes_count >= 30:
                probability = 0.7   # 70% 概率点赞
            elif likes_count >= 10:
                probability = 0.5   # 50% 概率点赞
            else:
                probability = 0.3   # 30% 基础概率

            # 4. 执行点赞
            if random.random() < probability:
                logger.info(f"准备点赞(当前点赞数：{likes_count}，点赞概率：{probability:.0%})")
                like_button.click()
                self.like_count += 1
                logger.success(f"点赞成功 ✨ 总点赞数: {self.like_count}")
                time.sleep(random.uniform(1, 2))
            else:
                logger.info(f"跳过点赞(当前点赞数：{likes_count}，点赞概率：{probability:.0%})")

        except Exception as e:
            logger.error(f"点赞失败: {str(e)}")

    

    def get_yiyan(self):
        """获取一言"""
        try:
            headers = {
                'User-Agent': 'xiaoxiaoapi/1.0.0 (https://xxapi.cn)'
            }
            response = requests.get("https://v2.xxapi.cn/api/yiyan?type=hitokoto", headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:  # 修改这里：使用数字而不是字符串
                    return result.get("data")
            logger.warning("获取一言失败，API 返回：" + str(response.text))
        except Exception as e:
            logger.error(f"获取一言失败: {str(e)}")
        return "API 访问失败，未能获取一言"
    
    def print_connect_info(self):
        logger.info("获取连接信息")
        page = self.context.new_page()
        page.goto("https://connect.linux.do/")
        rows = page.query_selector_all("table tr")

        info = []
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        username = os.environ.get("USERNAME", "未知用户")
        
        # 使用更美观的 Markdown 格式输出
        print("# 🤖 自动浏览报告")
        print(f"### 👤 执行用户：{username}\n")
        
        # Connect 信息部分
        print("### 📊 Connect 数据")
        table_str = tabulate(info, headers=["项目", "当前", "要求"], tablefmt="github")
        print(table_str + "\n")

        # 运行统计部分
        print("### 📈 运行统计")
        print("```")  # 使用代码块使统计信息更醒目
        print(f"📖 浏览帖子：{self.browse_count} 篇")
        print(f"👍 点赞帖子：{self.like_count} 篇")
        
        # 计算运行时间
        elapsed_time = time.time() - self.start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        print(f"⏱️ 运行用时：{hours}小时{minutes}分{seconds}秒")
        print("```\n")
        
        # 底部信息
        print("---")  # 分隔线
        
        # 获取北京时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n⏰ 执行时间：`{beijing_time}`")
        
        # 添加一言
        yiyan = self.get_yiyan()
        print("\n### 📝 今日一言")
        print(f"> {yiyan}")

        page.close()


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD")
        exit(1)
    l = LinuxDoBrowser()
    l.run()
