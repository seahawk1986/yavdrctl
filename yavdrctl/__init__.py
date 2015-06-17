#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__all__ = ['arguments', 'vdrctl']


def main():
    from . import vdrctl
    vdrctl.VDRCTL()

if __name__ == '__main__':
    main()
