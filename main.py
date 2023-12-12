#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   main.py
@Time    :   2023/12/12 17:06:02
@Author  :   lvguanjun
@Desc    :   main.py
"""

import asyncio
import os

import dotenv

from utils import GithubInfo, plot_year_distribution

dotenv.load_dotenv()

if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")
    github = GithubInfo(token=github_token)
    results = asyncio.run(github.start("lvguanjun", "copilot_share"))

    plot_year_distribution(results)
