from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from parse.zone_outputs import main
else:
    from .zone_outputs import main


if __name__ == "__main__":
    main()
