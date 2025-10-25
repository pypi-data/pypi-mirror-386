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
from zenutils import randomutils
from zenutils import cipherutils


def s1ncipher_test_seed(seeds, seed):
    if seed in seeds:
        return False
    for x in seeds:
        if seed in x:
            return False
        if x in seed:
            return False
    return True


class S1nCipher(cipherutils.MappingCipher):
    def get_seeds(self):
        seeds = []
        gen = randomutils.Random(self.password)
        loop = 0
        rand_bytes = b""
        while len(seeds) < 256:
            if len(rand_bytes) < 256:
                rand_bytes += gen.get_bytes(1024)
            loop += 1
            seed_length = loop % (loop // 10000 + 3) + 1
            seed = rand_bytes[:seed_length]
            rand_bytes = rand_bytes[seed_length:]
            if s1ncipher_test_seed(seeds, seed):
                seeds.append(seed)
        seeds.sort()
        return seeds


def s1ncipher_encrypt(data, password):
    cipher = S1nCipher(password=password)
    return cipher.encrypt(data)


def s1ncipher_decrypt(data, password):
    cipher = S1nCipher(password=password)
    return cipher.decrypt(data)
