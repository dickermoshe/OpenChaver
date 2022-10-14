def cleanup():
    """Delete Screenshots older than a week"""
    from .db import ScreenshotDB
    from time import sleep
    from datetime import datetime
    while True:
        for row in ScreenshotDB().table:
            if (datetime.now() - row['created']).days > 7:
                ScreenshotDB().table.delete(id=row['id'])
        sleep(3600)