import mouseinfo
import time

class Mouse:
    def __init__(self):
        self.position = None
    
    def is_idle(self, duration):
        time.sleep(duration)
        p = mouseinfo._winPosition()
        if self.position == p:
            return True
        else:
            self.position = p
            return False
