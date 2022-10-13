def uploader():
    import logging
    import requests
    import time
    from .models import ScreenshotModel,ConfigurationModel
    from . import API_BASE_URL

    # Logger
    logger = logging.getLogger(__name__)

    while True:
        if not ConfigurationModel().is_configured:
            logger.info("Configuration is not complete")
            time.sleep(5)
            continue
        else:
            break

    

    # Upload screenshots
    while True:
        # Get screenshots that are not uploaded
        for row in ScreenshotModel().table:
            data = dict(row)
            
            # Remove the id
            data.pop('id')

            # Set created_at to a string
            data['created'] = data['created'].isoformat()
            
            # Set the device_id
            data['device_id'] = ConfigurationModel().device_id
            
            try:
                r = requests.post(f"{API_BASE_URL}screenshots/add_screenshot/",json=data)
                if r.status_code == 200:
                    ScreenshotModel().table.delete(id=row['id'])
                    logger.info(f"Uploaded screenshot {row['id']}")
                else:
                    print(r.status_code)
                    print(r.content)
                    logger.error(f"Failed to upload screenshot {row['id']}")
            
            # If its a network error, wait 5 seconds and try again
            except requests.exceptions.ConnectionError:
                logger.error(f"Failed to upload screenshot {row['id']}")
                time.sleep(5)
                continue
            except:
                raise
        time.sleep(10)
