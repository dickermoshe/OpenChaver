def cleanup():
    """Delete ScreenshotModel older than a week"""
    from .models import ScreenshotModel
    from time import sleep
    from datetime import datetime, timedelta
    while True:
        for row in ScreenshotModel().table:
            if (datetime.now() - row['created']).days > 7:
                ScreenshotModel().table.delete(id=row['id'])
        sleep(3600)