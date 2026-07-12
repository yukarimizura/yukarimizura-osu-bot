import os

from config import MAX_BEATMAP_CACHE, MAX_DELETE_BATCH


MAX_CACHE_FILES = MAX_BEATMAP_CACHE
CACHE_DELETE_BATCH = MAX_DELETE_BATCH


def cleanup_cache(
    cache_directory,
    extension=".osu"
):
    """
    Keeps the cache size below MAX_CACHE_FILES.

    This function is intended to be called
    BEFORE downloading a new file.

    Examples
    --------
    49 files -> delete 0
    50 files -> delete 1
    55 files -> delete 6
    80 files -> delete 31

    After downloading one new file,
    the cache will always contain
    MAX_CACHE_FILES files.
    """

    os.makedirs(
        cache_directory,
        exist_ok=True
    )

    files = [
        os.path.join(
            cache_directory,
            file
        )
        for file in os.listdir(
            cache_directory
        )
        if file.endswith(extension)
    ]

    # Nothing to clean.
    if len(files) < MAX_CACHE_FILES:
        return

    # Oldest -> Newest
    files.sort(
        key=os.path.getmtime
    )

    # Number of files that must be removed
    # to leave one free slot.
    files_to_delete = min(
        CACHE_DELETE_BATCH,
        len(files)
    )

    for file in files[:files_to_delete]:

        try:

            os.remove(file)

            print(
                "[CACHE] Deleted "
                f"{os.path.basename(file)}"
            )

        except OSError as error:

            print(
                "[CACHE] Failed to delete "
                f"{os.path.basename(file)}"
                f": {error}"
            )


def touch(path):
    """
    Refresh the modification time of
    a cached file.

    Frequently-used beatmaps remain
    newer than unused ones.
    """

    try:

        os.utime(
            path,
            None
        )

    except OSError:
        pass