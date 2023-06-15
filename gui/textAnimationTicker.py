import PyQt6.QtCore


class TextAnimationTicker(PyQt6.QtCore.QObject):
    text_animation_tick = PyQt6.QtCore.pyqtSignal(int)

    def __init__(self):
        super(TextAnimationTicker, self).__init__()
        self.running = False
        self.tickcounter = 0

    @PyQt6.QtCore.pyqtSlot()
    def run(self):
        self.running = True
        self.tickcounter = 0

        while self.running:
            self.text_animation_tick.emit(self.tickcounter)
            self.thread().msleep(100)
            self.tickcounter += 1

    @PyQt6.QtCore.pyqtSlot()
    def stop(self):
        self.running = False
