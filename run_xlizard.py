# -*- coding: utf-8 -*-
"""Entry point for PyInstaller / frozen Windows builds (GUI)."""
import multiprocessing
import sys


def main():
    # Required for multiprocessing in frozen Windows apps
    multiprocessing.freeze_support()
    from xlizard.gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
