def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "explore":
        from src.exploration import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "roles":
        from src.roles import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "conversations":
        from src.conversation import run
        threshold = None
        if len(sys.argv) > 2:
            try:
                threshold = float(sys.argv[2])
            except ValueError:
                print(f"[ERROR] Threshold harus angka, diterima: {sys.argv[2]}")
                return
        run(threshold_hours=threshold)
    elif len(sys.argv) > 1 and sys.argv[1] == "responses":
        from src.client_response import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "remote":
        from src.remote import run
        run()
    else:
        from src.parser import run
        run()


if __name__ == "__main__":
    main()
