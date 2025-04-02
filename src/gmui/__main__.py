import argparse
import logging

from gmui.app import App
from gmui.window import Window


def main():
    """GUI 主函数。"""
    parser = argparse.ArgumentParser(description="Open source genealogy manager.")
    parser.add_argument("--debug", action="store_true")
    args, qt_args = parser.parse_known_args()
    debug: bool = args.debug

    # 应用和主窗口创建
    app = App(qt_args)
    main_window = Window(debug=debug)
    main_window.show()

    # 配置日志记录
    if debug:
        logging.basicConfig(level=logging.DEBUG)

    # 开始运行
    app.exec()


if __name__ == "__main__":
    main()
