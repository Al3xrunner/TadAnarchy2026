class SimClock:


    def __init__(self, start_clock="06:00", speed=60.0):
        h, m = map(int, start_clock.split(":"))
        self.start_s = h * 3600 + m * 60  
        self.t = 0.0
        self.speed = speed                

    def hour(self, t=None):
        return ((self.start_s + (self.t if t is None else t)) / 3600) % 24

    def label(self, t=None):
        s = int(self.start_s + (self.t if t is None else t)) % 86400
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}"
