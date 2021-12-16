import json
import time
from datetime import datetime
from itertools import zip_longest

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


def on_modified(event):
    with (
        open(f"{event.src_path}", "r", encoding="utf-8") as journal,
        open("out_dir/working.txt", "r+", encoding="utf-8") as cache_file,
    ):
        jf = journal.readlines()
        c = cache_file.readlines()
        if jf == c:
            pass  # a save event without any modification
        else:
            diff = pull_out_diff(jf, c)
            print(diff)
            with open("out_dir/chunked.json", "r+", encoding="utf-8") as chunk:
                j = json.load(chunk)
                now = datetime.now()
                data = [x[1][0] for x in diff]
                if data != []:
                    payload = {
                        "ts": now.isoformat(),
                        "journal_chunk": "\n".join(data),
                        "check": str(diff),
                    }
                    j["journal_data"].append(payload)
                    stringed_json = json.dumps(j, indent=2)
                    fully_overwrite_file(chunk, stringed_json)
                    fully_overwrite_file(cache_file, "".join(jf))


def pull_out_diff(jf, c):
    diff = [line for line in enumerate(zip_longest(jf, c)) if line[1][1] is None]
    return diff


def fully_overwrite_file(file, data):
    file.seek(0)
    file.write(data)
    file.truncate()


if __name__ == "__main__":
    # e.g. taken from here: https://thepythoncorner.com/posts/2019-01-13-how-to-create-a-watchdog-in-python-to-look-for-filesystem-changes/
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(
        patterns, ignore_patterns, ignore_directories, case_sensitive
    )
    my_event_handler.on_modified = on_modified
    path = "./path_to_watch"
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()
