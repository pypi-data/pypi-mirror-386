import sys
import os
from aggregator import aggregate_code
from constants import TEXT_VI, TEXT_EN


def main():
    print("🚀 PROJECTDUMP")
    print("=" * 40)

    # Select language
    lang = input("🌐 Select language (en/vi): ").strip().lower()
    text = TEXT_EN if lang == "en" else TEXT_VI

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = input(text["input_project_path"]).strip() or os.getcwd()

    project_path = os.path.abspath(project_path)
    success = aggregate_code(project_path, text)

    if success:
        print(text["done"])
    else:
        print(text["error"])
        sys.exit(1)


if __name__ == "__main__":
    main()
