#!/usr/bin/env python3
"""Hook to format CoLRev repositories"""
import colrev.review_manager


def main() -> int:
    """Main entrypoint for the formating"""

    review_manager = colrev.review_manager.ReviewManager()
    ret = review_manager.dataset.format_records_file()

    print(ret["msg"])

    return ret["status"]


if __name__ == "__main__":
    raise SystemExit(main())
