from pathlib import Path
import argparse, sys, concurrent.futures, platform, webbrowser

def find_tutorial_pdf():
    base = Path(__file__).resolve().parent
    possible_paths = [
        base / "tutorial_dearning.pdf",
        base / "dearning" / "tutorial_dearning.pdf",
        Path.home() / "Documents/dearning/tutorial_dearning.pdf",
        Path("/storage/emulated/0/my_libraries/dearning/dearning/tutorial_dearning.pdf"),
        Path("/sdcard/dearning/tutorial_dearning.pdf"),
        Path("tutorial_dearning.pdf"),
    ]
    for path in possible_paths + list(base.rglob("tutorial_dearning.pdf")):
        if path.exists():
            return path
    return None

def get_folder_size(folder: Path) -> float:
    with concurrent.futures.ThreadPoolExecutor() as ex:
        sizes = list(ex.map(lambda p: p.stat().st_size, folder.rglob("*") if folder.exists() else []))
    return sum(sizes) / 1024

def check_compatibility():
    py_version = sys.version_info
    device = platform.system()
    python_ok = py_version >= (3, 9)  # minimal Python 3.9
    return {
        "device": device,
        "python_version": f"{py_version.major}.{py_version.minor}.{py_version.micro}",
        "python_compatible": python_ok,
    }

def main():
    parser = argparse.ArgumentParser(description="🧠 Dearning CLI Interface")
    parser.add_argument("--task", choices=["classification", "regression"], default="classification")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--stats", action="store_true", help="Tampilkan status dearning (ukuran + kompatibilitas)")
    parser.add_argument("--tutorial", "-t", action="store_true", help="Buka tutorial resmi Dearning di GitHub")
    args = parser.parse_args()

    # === Mode: tampilkan statistik ===
    if args.stats:
        size = get_folder_size(Path(__file__).parent)
        comp = check_compatibility()
        print(f"Ukuran dearning: {size:.2f} KB")
        print(f"Device: {comp['device']}")
        print(f"Python: {comp['python_version']} (compatible={comp['python_compatible']})")
        sys.exit()

    # === Mode: buka tutorial resmi ===
    if args.tutorial:
        url = "https://github.com/maker-games/Dearning/tree/main/tutorial-dearning"
        print("[Dearning] Membuka tutorial resmi di GitHub...")
        webbrowser.open(url)
        sys.exit()

    # === Default CLI output ===
    print("[Dearning] CLI aktif. Gunakan --help untuk melihat semua perintah.")

if __name__ == "__main__":
    main()