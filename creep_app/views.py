import multiprocessing as mp


def single_service(request):
    from .services import screenshot_process, detect_process
    """One Service that runs all the requsite services"""
    queue = mp.Queue()
    p1 = mp.Process(
        target=screenshot_process,
        args=(queue,),
    )
    p2 = mp.Process(
        target=detect_process,
        args=(queue,),
    )
    # p3 = multiprocessing.Process(
    #    target=alert_process,
    # )
    p1.daemon = True
    p1.name = "Screenshot Process"
    p2.daemon = True
    p2.name = "Detect Process"
    # p3.daemon = True
    p1.start()
    p2.start()
    # p3.start()
    p1.join()
    p2.join()
    # p3.join()
