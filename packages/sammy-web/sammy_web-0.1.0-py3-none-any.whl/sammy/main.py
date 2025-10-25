import requests
import sys
from tqdm.auto import tqdm
import concurrent.futures
from pathlib import Path


def getStatus(url):
    print("=" * 40)

    response = requests.get(url)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        print("OK")
    elif response.status_code == 404:
        print("Could not connect!")
    else:
        print("Unknown status code!")

    print("=" * 40)
    return response.status_code


def getHeader(url):
    response = requests.get(url)
    print("=" * 16 + "HEADERS" + "=" * 17)
    for k in response.headers:
        print(k, end=": ")
        print(response.headers[k])
    print("=" * 40)


def getText(url):
    response = requests.get(url)
    print("=" * 18 + "TEXT" + "=" * 18)
    print(response.text)
    print("=" * 40)


def check_path(path):
    """
    Worker function for threading. Checks a single path.
    It's designed to be used with executor.map()
    """
    global url

    s = url + "/" + path
    try:
        response = requests.get(s, timeout=5)
        if response.status_code == 200:
            print(f"Found: {s}")
            return s
    except requests.exceptions.RequestException:
        pass

    return None


def main():
    global url
    if len(sys.argv) == 1:
        print("Sammy V0.1")
        print("Usage: sammy [url] -h|-t|-f|-d")
        sys.exit(0)
    url = sys.argv[1]

    print("  /$$$$$$                                                 ")
    print(" /$$__  $$                                                ")
    print("| $$  \\__/  /$$$$$$  /$$$$$$/$$$$  /$$$$$$/$$$$  /$$   /$$")
    print("|  $$$$$$  |____  $$| $$_  $$_  $$| $$_  $$_  $$| $$  | $$")
    print(" \\____  $$  /$$$$$$$| $$ \\ $$ \\ $$| $$ \\ $$ \\ $$| $$  | $$")
    print(" /$$  \\ $$ /$$__  $$| $$ | $$ | $$| $$ | $$ | $$| $$  | $$")
    print("|  $$$$$$/|  $$$$$$$| $$ | $$ | $$| $$ | $$ | $$|  $$$$$$$")
    print(" \\______/  \\_______/|__/ |__/ |__/|__/ |__/ |__/ \\____  $$")
    print("                                                 /$$  | $$")
    print("                                                |  $$$$$$/")
    print("                                                 \\______/ ")
    print()
    print("By Sanyam Asthana, 2025")

    print("Sammy initiated on URL:", url)

    print("=" * 40)

    response = requests.get(url)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        print("OK")
    elif response.status_code == 404:
        print("Could not connect!")
    else:
        print("Unknown status code!")

    print("=" * 40)

    if "-h" in sys.argv:
        print("=" * 16 + "HEADERS" + "=" * 17)
        for k in response.headers:
            print(k, end=": ")
            print(response.headers[k])
        print("=" * 40)

    if "-t" in sys.argv:
        print("=" * 18 + "TEXT" + "=" * 18)
        print(response.text)
        print("=" * 40)

    if "-d" in sys.argv:
        print("=" * 14 + "DIRECTORIES" + "=" * 15)

        try:
            NUM_THREADS = int(
                input(
                    "Number of threads (Default is 20) (A higher number of threads may result in rate limiting): "
                )
            )  # Number of simultaneous workers
        except:
            NUM_THREADS = 20

        print(f"Searching with {NUM_THREADS} threads...")
        path_list = []

        package_dir = Path(__file__).parent
        wordlist_path = package_dir / "wordlist.txt"

        try:
            with open(wordlist_path, "r") as F:
                for line in F:
                    path = line.strip()
                    if path:
                        path_list.append(path)
        except FileNotFoundError:
            print("[!] Error: wordlist.txt not found.")
            sys.exit(1)

        if not path_list:
            print("[!] Wordlist is empty.")
            sys.exit(1)

        found_paths = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            results = list(
                tqdm(
                    executor.map(check_path, path_list),
                    total=len(path_list),
                    desc="Checking",
                    unit="path",
                )
            )

        print("\n" + "=" * 40)
        print("--- Scan Complete ---")
        if not any(results):
            print("No directories or files found.")

        print("=" * 40)

    if "-f" in sys.argv:
        x = 1
        path = url
        while x:
            s = path + ": "
            inp = input(s)

            if inp.startswith("cd "):
                new_path = url + "/" + inp.split()[1]
                if getStatus(new_path) == 200:
                    getHeader(new_path)
                    print("Moved to the new path!")
                    path = new_path
                else:
                    print("Could not move to the new path!")

            if inp == "cd/":
                path = url
                getStatus(path)
                getHeader(path)

            if inp == "text":
                getText(path)

            if inp == "exit":
                x = 0


if __name__ == "__main__":
    main()
