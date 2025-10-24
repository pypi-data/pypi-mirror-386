#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
from enum import Enum
from typing import Dict, Optional
import pandas as pd


sanitize_re = re.compile(r'[|:<>?*"\\/]')


def format_naming(posts):
    for post in posts:
        if post.get("title"):
            post['title'] = sanitize_re.sub('-', post['title'])
    return posts


class FilterMgr:
    def __init__(self, conf_filter: Optional[Dict[str, str]] = None) -> None:
        conf_filter = conf_filter or {}
        for regex_str in ("file",):
            regex_val = conf_filter.get(regex_str)
            if regex_val:
                _ = re.compile(regex_val)
                setattr(self, regex_str, lambda arg: bool(_.search(arg)))
            else:
                setattr(self, regex_str, lambda _: False)
        self.re_f = ReFilter(conf_filter.get("TitleRe", {}))
        self.rule_f = RuleFilter(conf_filter.get("RuleFEnum"))


class ReFilter:
    def __init__(self, title_filters: Optional[Dict[str, str]] = None):
        self._sanitize_re = re.compile(r'[|:<>?*"\\/]')
        self.artists_patterns = {}
        self.has_normal = False
        
        if title_filters:
            if 'normal' in title_filters:
                self.has_normal = True
                self._normal_pattern = re.compile(title_filters['normal'])
            for name, pattern in title_filters.items():
                self.artists_patterns[name] = re.compile(pattern)

    def base_process(self, posts):
        if self.has_normal:
            posts = list(filter(lambda p: not bool(self._normal_pattern.search(
                p.get('title', p.get('content', '')))), posts))
        return posts

    def do_artist_pattern(self, name: str):
        pattern = self.artists_patterns[name]
        return lambda posts: [p for p in self.base_process(posts) if not bool(pattern.search(p['title']))]


class RuleFEnum(Enum):
    DaikiKase="273185"
    # mdasdaro="3316400"


class RuleFilter:
    def __init__(self, ae: Optional[Dict] = None):
        self.ae = Enum("RuleFEnumFromDict", ae) if ae else RuleFEnum

    @staticmethod
    def keihh(posts):
        """patreon/user/
        naming hobby: title, title(v2), title(v3)...
        """
        df = pd.DataFrame(posts)

        df['BaseName'] = df['title'].str.replace(r'\s*\([vV]\d+\)', '', regex=True)
        df['Version'] = df['title'].apply(lambda x: re.search(r'\([vV](\d+)\)', x))
        df['Version'] = df['Version'].apply(lambda x: f"v{x.group(1)}" if x else 'v0')

        df['title'] = df['title'].str.replace(r'([|:<>?*"\\/])', '', regex=True)
        
        latest_versions = df.loc[df.groupby('BaseName')['Version'].idxmax()]
        dic_posts = latest_versions.drop(['BaseName','Version'], axis=1).to_dict('records')
        return dic_posts
