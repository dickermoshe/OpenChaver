from .logger import handle_error

@handle_error
def uploader():
    import logging
    import time
    from .db import get_screenshot_db, get_configuration_db
    from .api import api

    # Logger
    logger = logging.getLogger(__name__)

    # Connect to the database
    screenshotdb = get_screenshot_db()
    configdb = get_configuration_db()

    while True:
        if not configdb.is_configured:
            logger.info("Configuration is not complete. Waiting 5 seconds")
            time.sleep(5)
            continue
        else:
            break

    # Upload screenshots
    while True:
        # Get screenshots that are not uploaded
        for row in screenshotdb.table:
            data = dict(row)
            logger.info(f"Uploading screenshot {data['id']}")

            # Remove the id
            id = data.pop('id')

            # Set created_at to a string
            data['created'] = data['created'].isoformat()

            status, json = api(f'/devices/{configdb.device_id}/add_screenshot/',data=data)
            if status:
                logger.info(f"Screenshot {id} uploaded successfully")
                screenshotdb.table.delete(id=id)
            else:
                logger.error(f"Failed to upload screenshot {id}")
                continue
        time.sleep(10)
