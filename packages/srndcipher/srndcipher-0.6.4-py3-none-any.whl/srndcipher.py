#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import (
    absolute_import,
    division,
    generators,
    nested_scopes,
    print_function,
    unicode_literals,
    with_statement,
)

"""
字符串随机编码方案。编码后保持字符串的相对排序不变，允许局部搜索。
"""
import time
import string
from zenutils import cipherutils


class SrndCipher(cipherutils.MappingCipher):
    """字符串随机编码方案。编码后保持字符串的相对排序不变，允许局部搜索。

    注意：
    根据密码进行初始化时效率较低，
    可以在根据密码初始化后将内部数据dump出来，
    后续根据内部数据进行初始化则效率很高。
    初始化效率不影响编码和解码的效率。
    """

    default_result_encoder = cipherutils.Utf8Encoder()

    def __init__(
        self,
        password,
        seed_min_length=2,
        seed_max_length=11,
        chars=string.ascii_letters + string.digits + string.punctuation,
        **kwargs
    ):
        self.seed_min_length = seed_min_length
        self.seed_max_length = seed_max_length
        self.chars = chars
        self.get_seeds_loop_counter = 0
        stime = time.time()
        super(SrndCipher, self).__init__(password, **kwargs)
        self.get_seeds_time_used = time.time() - stime

    def get_seeds(self):
        seeds = set()
        bad_seeds = set()
        while True:
            self.get_seeds_loop_counter += 1
            length = self.randomGenerator.randint(
                self.seed_min_length, self.seed_max_length
            )
            seed = "".join(self.randomGenerator.choices(self.chars, k=length))
            if self.test_seed(seeds, bad_seeds, seed):
                self.put_bad_seeds(bad_seeds, seeds, seed)
                seeds.add(seed)
            if len(seeds) >= 256:
                break
        seeds = list([x.encode() for x in seeds])
        seeds.sort()
        return seeds

    def test_seed(self, seeds, bad_seeds, seed):
        if seed in bad_seeds:
            return False
        for x in bad_seeds:
            if x in seed:
                return False
            if seed in x:
                return False
        new_bad_seeds = set()
        for x in seeds:
            new_bad_seeds.add(x[-1] + seed[0])
            new_bad_seeds.add(seed[-1] + x[0])
        for x in new_bad_seeds:
            for y in seeds:
                if x in y:
                    return False
        return True

    def put_bad_seeds(self, bad_seeds, seeds, seed):
        bad_seeds.add(seed)
        bad_seeds.add(seed[-1] + seed[0])
        for x in seeds:
            bad_seeds.add(seed[-1] + x[0])
            bad_seeds.add(x[-1] + seed[0])
