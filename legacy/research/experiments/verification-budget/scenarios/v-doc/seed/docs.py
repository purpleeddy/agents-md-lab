import argparse


def build(cache_dir):
    return "built examples in " + cache_dir


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--cache-dir", default=".cache")
    args = parser.parse_args(argv)
    print(build(args.cache_dir))


if __name__ == "__main__":
    main()
