import os, platform, subprocess, sys

def main():
    system = platform.system().lower()
    arch   = platform.machine().lower()
    key    = f"{system}-{arch}"
    fn     = f"jsonschema-{key}.exe" if system=="windows" else f"jsonschema-{key}"
    path   = os.path.join(os.path.dirname(__file__), fn)
    if not os.path.exists(path):
        print(f"Unsupported platform: {key}", file=sys.stderr)
        sys.exit(1)
    subprocess.run([path]+sys.argv[1:], check=True)

if __name__=="__main__":
    main()
