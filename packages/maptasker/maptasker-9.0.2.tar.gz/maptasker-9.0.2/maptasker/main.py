"""Main entry point for maptasker"""
#! /usr/bin/env python3

#                                                                                      #
# Main: MapTasker entry point                                                          #
#                                                                                      #
# MIT License   Refer to https://opensource.org/license/mit                            #

# FOR DEVELOPMENT ONLY  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# print("Path:", os.getcwd())
# print(
#     f"__file__={__file__:<35} | __name__={__name__:<25} | __package__={__package__!s:<25}",
# )
# print(sys.argv)
# # Verify Python version.
# print("Python version ", sys.version)
import os
import sys

# print("\nsys.path BEFORE modification:")
# for p in sys.path:
#     print(f"  {p}")
# =========================================================================
# >> NEW CODE TO FIX ModuleNotFoundError: No module named 'maptasker' <<
# =========================================================================
# Calculate the absolute path to the directory *containing* main.py,
# which should be the root of your project where 'maptasker' resides.
project_root_dir = os.path.dirname(os.path.abspath(__file__))

# Insert the project root path at the beginning of sys.path
# This ensures Python can find the 'maptasker' package.
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)
# =========================================================================

# Get the absolute path to your local overrides directory
override_path = os.path.join(os.path.dirname(__file__), "custom_overrides")

# Add your override path to the beginning of sys.path
# This makes Python look here first
sys.path.insert(0, override_path)
# Get the absolute path to your local overrides directory
override_path = os.path.join(os.path.dirname(__file__), "custom_overrides")

# Add your override path to the beginning of sys.path
# This makes Python look here first
sys.path.insert(0, override_path)
# print("\nsys.path AFTER modification:")
# for p in sys.path:
#     print(f"  {p}")

# Add this crucial check:
# if override_path != sys.path[0]:
#     print(
#         f"\nERROR: '{override_path}' IS NOT at the beginning of sys.path. Not picking up local mods.",
#     )

from maptasker.src import mapit
from maptasker.src.maputils import exit_program


def main() -> None:
    """
    Kick off the main program: mapit.pypwd
    """
    # Call the core function passing an empty filename
    return_code = mapit.mapit_all("")
    # Call it quits.
    exit_program(return_code)


if __name__ == "__main__":
    # FOR DEVELOPMENT ONLY  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # The following outputs a file "maptasker_profile.txt" with a breakdown of
    # function calls

    # import cProfile
    # import pstats

    # cProfile.run("main()", "results")
    # with open("maptasker_profile.txt", "w") as file:
    #     profile = pstats.Stats("results", stream=file).sort_stats("ncalls")
    #     profile.print_stats()
    #     file.close()

    main()
