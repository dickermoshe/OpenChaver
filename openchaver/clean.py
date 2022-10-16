def cleanup():
    """Delete Screenshots older than a week"""
    from .db import get_screenshot_db
    from time import sleep
    from datetime import datetime
    screenshot_db = get_screenshot_db()

    while True:
        for row in screenshot_db.table:
            if (datetime.now() - row['created']).days > 7:
                screenshot_db.table.delete(id=row['id'])
        sleep(3600)