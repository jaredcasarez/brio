import argparse
from .logging import LogLevel, configure_logging
from .sandbox import SandboxApp
def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description="trax - A Panda3D-based track layout designer")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--logfile", type=str, help="Specify a log file")
    parser.add_argument("--mode", type=str, choices=['brio', 'citystreets'], default='brio', help="Choose application mode (default: citystreets)")
    parser.add_argument("--show-collisions", action="store_true", help="Show collision planes/spheres for debugging")
    args = parser.parse_args()

    if args.debug:
        configure_logging(level=LogLevel.DEBUG, console=True)
    elif args.logfile:
        configure_logging(level=LogLevel.INFO, console=False, log_file=args.logfile)
    
    app = SandboxApp(mode=args.mode, show_collisions=args.show_collisions)
    app.run()
    
if __name__ == "__main__":
    main()