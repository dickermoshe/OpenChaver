from pathlib import Path
import logging

def is_frozen():
    """Check if the program is frozen by PyInstaller or Nuitka"""
    import sys
    pyinstaller = getattr(sys, 'frozen', False)
    nuitka = "__compiled__" in globals()
    logging.debug(f"Pyinstaller: {pyinstaller}, Nuitka: {nuitka}")
    return pyinstaller or nuitka

def delete_old_logs(log_location:Path,keep:list[Path] = []):
    for f in log_location.glob("*.log"):
        if f not in keep:
            f.unlink()

def thread_runner(threads, die_event=None):
    # Create threads and start them
    import threading as th
    import time

    for k in threads.keys():
        threads[k]["thread"] = th.Thread(
            target=threads[k]["target"],
            args=threads[k]["args"],
            kwargs=threads[k]["kwargs"],
            daemon=threads[k]["daemon"],
        )

    # Start threads
    for k in threads.keys():
        threads[k]["thread"].start()

    # Print threads ids
    for k in threads.keys():
        logging.info(f"{k}: {threads[k]['thread'].ident}")

    # Loop -> Restart threads if they die and sleep for 5 seconds
    while True:
        for k in threads.keys():
            if not threads[k]["thread"].is_alive():
                logging.error(f'Thread "{k}" is dead, restarting...')
                threads[k]["thread"] = th.Thread(
                    target=threads[k]["target"],
                    args=threads[k]["args"],
                    kwargs=threads[k]["kwargs"],
                    daemon=threads[k]["daemon"],
                )
                threads[k]["thread"].start()

        if die_event and die_event.is_set():
            break

        time.sleep(5)