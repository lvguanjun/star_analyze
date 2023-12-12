#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   utils.py
@Time    :   2023/12/12 16:43:07
@Author  :   lvguanjun
@Desc    :   utils.py
"""


import asyncio
import datetime

import aiohttp
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from matplotlib.ticker import MaxNLocator


class GithubInfo(object):
    def __init__(self, token=None, max_concurrent_tasks=50):
        self.token = token
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}" if self.token else None,
            "Accept": "application/vnd.github.v3.star+json",
        }
        self.MAX_REQUESTS = 4500
        self.star_queue = asyncio.Queue()
        self.results = []
        self.max_concurrent_tasks = max_concurrent_tasks

    async def fetch_stargazers(self, session, owner, repo, page):
        route = f"/repos/{owner}/{repo}/stargazers"
        url = self.api_url + route
        params = {"page": page, "per_page": 100}
        async with session.get(url, params=params) as response:
            if response.status != 200:
                print(f"Error: {response.status}, {await response.text()}")
                return None
            return await response.json()

    async def get_stars_info(self, session, owner, repo):
        page = 1
        perpage = 100
        while True:
            data = await self.fetch_stargazers(session, owner, repo, page)
            if not data:
                break
            for star in data:
                user = star["user"]
                await self.star_queue.put(user["login"])
            print(f"Processed {page} pages of stars")
            if page * perpage >= self.MAX_REQUESTS:
                break
            page += 1
        # Signal the consumers to exit
        for _ in range(self.max_concurrent_tasks):
            await self.star_queue.put(None)

    async def fetch_user_creation_date(self, session, account):
        route = f"/users/{account}"
        url = self.api_url + route
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Error: {response.status}, {await response.text()}")
                return None
            return await response.json()

    async def fetch_user_creat_years(self, session, account):
        try:
            data = await self.fetch_user_creation_date(session, account)
            if data:
                now = datetime.datetime.now(datetime.timezone.utc)
                create_time = datetime.datetime.strptime(
                    data["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                )
                create_time = create_time.replace(tzinfo=datetime.timezone.utc)
                years = relativedelta(now, create_time).years
                return years
            return None
        except Exception as e:
            print(f"Error processing account {account}: {e}")

    async def consumer(self, session):
        while True:
            account = await self.star_queue.get()
            if account is None:
                self.star_queue.task_done()
                break
            res = await self.fetch_user_creat_years(session, account)
            if res:
                self.results.append(res)
                if len(self.results) % 100 == 0:
                    print(f"Processed {len(self.results)} stars accounts year")
            self.star_queue.task_done()

    async def start(self, owner, repo):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Start the producer coroutine
            producer = asyncio.create_task(self.get_stars_info(session, owner, repo))

            # Start consumer coroutines
            consumers = [
                asyncio.create_task(self.consumer(session))
                for _ in range(self.max_concurrent_tasks)
            ]

            # Wait for the producer to finish
            await producer

            # Wait for the consumer to process all items
            await self.star_queue.join()

            # Cancel any remaining consumer tasks
            for c in consumers:
                c.cancel()

            return self.results


def plot_year_distribution(years: list[int]):
    if not years:
        print("No data to plot")
        return

    # 统计每个年份的出现次数
    year_counts = {}
    for year in years:
        if year in year_counts:
            year_counts[year] += 1
        else:
            year_counts[year] = 1

    # 对年份进行排序
    sorted_years = sorted(year_counts.keys())

    # 获取每个年份的计数
    counts = [year_counts[year] for year in sorted_years]

    # 创建柱状图
    bars = plt.bar(sorted_years, counts)

    # 在柱子上方添加数字标签
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 0.05,
            yval,
            ha="center",
            va="bottom",
        )

    # 添加标题和标签
    plt.title("User account star creation year distribution")
    plt.xlabel("Account creation year")
    plt.ylabel("Number of user stars")

    plt.xticks(range(min(years), max(years) + 1))
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    # 显示图表
    plt.show()


if __name__ == "__main__":
    # import dotenv

    # dotenv.load_dotenv()

    # github_token = os.getenv("GITHUB_TOKEN")
    # github = GithubInfo(token=github_token)
    # results = asyncio.run(github.start("pandora-next", "deploy"))

    # 假设这是从某处获取的年份数据
    years_data = [1, 3, 5, 3, 2, 1, 1, 5, 6, 7, 2, 3, 5, 4, 2, 1, 0, 15, 10]

    # 调用函数
    plot_year_distribution(years_data)
