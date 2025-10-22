"""
FileShareCLI – Simple CLI for the remote File‑Sharing service.

Checkout the application to generate token
https://filesharecli.vercel.app

This script allows a user to:
  1. Upload the content of a local text file to the server (create a new document)
  2. Retrieve a document from the server by its unique ID (read/download)

The server endpoints are:
  POST   https://filesharecli-r4ilw.ondigitalocean.app/api/createDoc   – create a new document
  GET    https://filesharecli-r4ilw.ondigitalocean.app/api/getDoc/<id>  – retrieve a document

A valid authentication token must be available in the environment variable
`FILESHARECLI_TOKEN`.  The token is added as the `X-User-ID` header and
as a bearer token in the `Authorization` header for the create request.

The CLI works both interactively and via command‑line arguments:
  $ python install filesharecli
  $ filesharecli
  $ filesharecli read <file_id>

Colorama is used for coloured terminal output.
"""

import sys
from colorama import init, Fore, Style
import requests
import os
import json
import threading
import itertools
import time

# Start colourama so that `Fore`, `Style`, etc. work cross‑platform.
init(autoreset=True)

def spinner(message="Processing..."):
    """
    Display a loading spinner with a dynamic message.
    Call stop_spinner() to stop it.
    """
    global loading
    loading = True

    def run_spinner():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if not loading:
                break
            sys.stdout.write(f'\r{message} {c}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write(f'\r✅ {message} Done!               \n')

    thread = threading.Thread(target=run_spinner)
    thread.start()
    return thread

def stop_spinner(thread):
    """Stop the spinner gracefully."""
    global loading
    loading = False
    thread.join()


def get_token():
    """
    Retrieve the authentication token from the environment.

    Returns:
        str: The token value stored in the `FILESHARECLI_TOKEN` environment variable.

    Raises:
        SystemExit: If the environment variable is not set.  The function
        prints an error message and exits the program with status 1.
    """
    token = os.getenv("FILESHARECLI_TOKEN")
    if not token:
        print()
        print("\033[91m❌ Error: Environment variable FILESHARECLI_TOKEN not set.\033[0m")
        print("👉 Please set it using:")
        print("   export FILESHARECLI_TOKEN=your_token_here  (Linux/macOS)")
        print("   set FILESHARECLI_TOKEN=your_token_here    (Windows)")
        sys.exit(1)

    thread = spinner("🔑 Verifying token...")
    data = requests.get(
        f"https://filesharecli-r4ilw.ondigitalocean.app/api/verifyToken/{token}",
    ).json()
    stop_spinner(thread)

    if(data['status']== False):
        print()
        print("\033[91m❌ Error: Environment variable FILESHARECLI_TOKEN is not valid.\033[0m")
        sys.exit(1)
    
    return token


def main():
    """
    Main entry point of the program.

    Handles user interaction, argument parsing, and orchestrates the
    communication with the remote file sharing service.  The workflow is:

    1. Load the authentication token with :func:`get_token`.
    2. Determine the desired action (`create` or `read`) from the
       command‑line arguments or interactive prompts.
    3. For a *create* action – read the specified local file and
       upload its content to the server.
    4. For a *read* action – fetch the document from the server
       using the provided ID and display or download the result.
    """
    token = get_token()
    print()

    action = ""
    arg = ""

    try:
        # ------------------------------------------------------------------
        # 1. Argument parsing / interactive mode
        # ------------------------------------------------------------------
        if len(sys.argv) < 2:
            # Interactive prompt: ask whether to create or read
            c_r = input("Do you want to create cmd or read the file (C/R): ").strip().lower()
            if c_r == "r":
                action = "read"
                choice = input("Do you know the file ID? (y/n): ").strip().lower()
                if choice == 'y':
                    arg = input("Enter the file ID to download: ").strip()
                elif choice == 'n':
                    print(f"{Fore.RED}ID is needed to get the data.{Style.RESET_ALL}")
                    return
            elif c_r == "c":
                action = "create"
                create = input("Pick the file name to read the content: ").strip().lower()
                if not os.path.exists(create):
                    print(f"\n{Fore.RED}❌ Error: File `{create}` not found{Style.RESET_ALL}")
                    return
                # Read file content for uploading
                with open(create, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Check the size of content
                    if len(content.encode('utf-8')) > 1 * 1024 * 1024:
                        print(f"\n{Fore.RED}❌ Error: File exceeds 1MB limit{Style.RESET_ALL}")
                        return
                print()
            else:
                print(f"{Fore.RED}Invalid choice. Exiting.{Style.RESET_ALL}")
                return
        else:
            # Command line arguments were supplied
            if sys.argv[1] == "create":
                create = input("Pick the file name to read the content: ").strip().lower()
                action = "create"
                if not os.path.exists(create):
                    print(f"Error: File '{create}' not found")
                    return
                with open(create, "r") as f:
                    content = f.read()
                print()
            elif sys.argv[1] == "read":
                if len(sys.argv) > 2:
                    action = "read"
                    arg = sys.argv[2]
                else:
                    action = "read"
                    choice = input("Do you know the file ID? (y/n): ").strip().lower()
                    if choice == 'y':
                        arg = input("Enter the file ID to download: ").strip()
                    elif choice == 'n':
                        print(f"{Fore.RED}ID is needed to get the data.{Style.RESET_ALL}")
                        return

        # ------------------------------------------------------------------
        # 2. Execute action
        # ------------------------------------------------------------------
        if action == "read":
            # Fetch the document from the server
            thread = spinner("📂 Reading file...")
            data = requests.get(
                f"https://filesharecli-r4ilw.ondigitalocean.app/api/getDoc/{arg}",
                headers={"X-User-ID": arg}
            ).json()
            stop_spinner(thread)

            if data['status'] == "error":
                print()
                print(f"\033[91m❌ Error: {data['detail']}\033[0m")
            else:
                # User chooses whether to view or save the content
                choose = input(
                    "Do you want to see the content or download the content as .txt "
                    "(see/download): "
                ).strip().lower()
                print()
                if choose == "download":
                    filename = f"{arg}_downloaded.txt"
                    with open(filename, "w") as f:
                        f.write(data['filesharecliRes'])
                    print(f"{Fore.GREEN}File saved as {filename}{Style.RESET_ALL}")
                else:
                    print(data['filesharecliRes'])
        else:
            # Create a new document on the server
            thread = spinner("📂 Creating file...")
            data = requests.post(
                "https://filesharecli-r4ilw.ondigitalocean.app/api/createDoc",
                headers={
                    "X-User-ID": token,
                    "Authorization": f"Bearer {token}"
                },
                json={"content": content}
            ).json()
            stop_spinner(thread)

            if data['valid']:
                print()
                print(f"{Fore.GREEN}Here is your command below to install content{Style.RESET_ALL}")
                print(f"> pip install filesharecli\n> filesharecli read {data['filesharecliRes']}")
            else:
                
                thread = spinner("📂 Creating file error...")
                print()
                print(f"\033[91m❌ Error: {data['filesharecliRes']}\033[0m")
                stop_spinner(thread)
            
    except KeyboardInterrupt:
        print()
        print(f"\n{Fore.RED}❌ Error: Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)  # Exit gracefully with non-zero code    

if __name__ == "__main__":
    main()