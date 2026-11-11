#!/usr/bin/env python3
"""
hf_push.py — واجهة مختصرة لـ hf_deploy.py (للتوافق مع الأدلة القديمة).
    python hf_push.py --repo <user>/<space> [--slim]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hf_deploy import main  # noqa: E402

if __name__ == "__main__":
    main()
