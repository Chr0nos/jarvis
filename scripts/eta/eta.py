from PyQt5.QtWidgets import (
	QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QLineEdit, QFileDialog,
	QProgressBar
)
import sys
from threading import Thread
from time import sleep
from datetime import datetime, timedelta


class Updater(Thread):
	def __init__(self, parent):
		super().__init__()
		self.parent = parent
		self.quit = False
		self.begin = datetime.strptime('11/02/2019 09:40', "%d/%m/%Y %H:%M")
		self.end = datetime.strptime("09/08/2019 18:00", "%d/%m/%Y %H:%M")
		self.total = (self.end - self.begin)
		self.parent.pbar.setMinimum(0)
		self.parent.pbar.setMaximum(self.total.days)
		self.parent.dailypbar.setMaximum(1000)

	def exit(self):
		self.quit = True

	def set_progress(self, now):
		today = now.replace(hour=0, minute=0, second=0)
		morning = today + timedelta(hours=10)
		evening = morning + timedelta(hours=8)
		total = int((evening - morning).total_seconds())
		seconds = total - int(evening.timestamp() - now.timestamp())
		coef = min(seconds / total, 1.0)
		percents = coef * 100
		self.parent.dailypbar.setValue(int(coef * 1000))
		# self.parent.win.setWindowTitle(f'Eta ({round(percents, 2)})')

	@property
	def remaining_time(self) -> int:
		now = datetime.now()
		eta = self.end - now
		return eta

	@property
	def elapsed_time(self):
		now = datetime.now()
		return now - self.begin

	def run(self):
		try:
			while not self.quit:
				now = datetime.now()
				remaining = self.remaining_time
				self.parent.label.setText(str(remaining).split('.')[0])
				self.parent.pbar.setValue(self.elapsed_time.days)
				self.set_progress(now)
				sleep(1)
		except KeyboardInterrupt:
			self.quit = True
			return


class Main:
	def __init__(self):
		self.app = QApplication(sys.argv)
		self.win = QWidget()
		self.win.setWindowTitle('Eta')
		self.label = QLabel('hello world')
		self.pbar = QProgressBar(self.win)
		self.dailypbar = QProgressBar(self.win)
		self.quit_button = QPushButton('Quit')
		self.quit_button.clicked.connect(self.quit_button_clicked)

		# add elements to layout
		self.layout = QVBoxLayout(self.win)
		self.layout.addWidget(self.label)
		self.layout.addWidget(self.pbar)
		self.layout.addWidget(self.dailypbar)
		self.layout.addWidget(self.quit_button)
		self.win.setLayout(self.layout)
		self.updater = Updater(self)

	def __del__(self):
		self.updater.exit()

	def quit_button_clicked(self):
		self.updater.exit()
		self.updater.join()
		self.win.close()
		self.app.quit()

	def show(self):
		self.win.show()
		self.updater.start()
		try:
			self.app.exec()
			self.updater.exit()
		except KeyboardInterrupt:
			self.quit_button_clicked()


if __name__ == '__main__':
	Main().show()
