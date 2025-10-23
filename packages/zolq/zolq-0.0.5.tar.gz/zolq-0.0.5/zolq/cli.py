import argparse, json
from .binding import bell_demo

def main():
    ap = argparse.ArgumentParser(description="ZOL-Q CLI")
    ap.add_argument("--p_dephase", type=float, default=0.20)
    ap.add_argument("--p_depol", type=float, default=0.15)
    ap.add_argument("--mode", choices=["project", "twirl"], default="project",
                    help="project = post-selected stabilizer projection; twirl = CPTP averaging")
    args = ap.parse_args()
    res = bell_demo(args.p_dephase, args.p_depol, mode=args.mode)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
