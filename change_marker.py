import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import keyboard

class GetChangePoints(object):

	def __init__(self, ax):

		self.fig = ax.figure
		self.ax = ax
		self.point_list = []
		self.start = None
		self.end = None

		self.fig.canvas.mpl_connect('button_press_event', self.on_click)

	def on_click(self, event):

		if event.inaxes == self.ax: # Check click is within plot limits
			x_point = event.xdata

			# Red lines mark the start of disturbances; green lines mark the end
			if(not self.start):
				line_col = 'r'
			else:
				line_col = 'g'

			self.ax.axvline(x=x_point, color=line_col, alpha=0.5)
			self.fig.canvas.draw()

			if(self.start):
				self.end = x_point
				disturbed = [self.start, self.end]
				self.point_list.append(disturbed)
				self.start = None
				self.end = None

			else:
				self.start = x_point

	def get_xlist(self):
		return self.point_list

if __name__ == '__main__':

	ph = [1]

	for pixel in ph:
	
		test_data = pd.read_csv('sample_5.csv')

		# Sort data by date
		test_data = test_data.sort_values(by=['datetime'])

		# Only select clear pixels (0 is clear land; 1 is clear water)
		test_data = test_data[test_data.qa < 2]

		# Calculate NDVI: (NIR-red) / (NIR+red)
		test_data["ndvi"] = (test_data.band_4 - test_data.band_3) / (test_data.band_4 + test_data.band_3)

		# Set up the plot
		fig, ax = plt.subplots(figsize=(25, 5))
		ax.plot(test_data.datetime, test_data.ndvi, 'o', markersize=2)

		# Format dates to month/year rather than rata die
		myFmt = mdates.DateFormatter('%m/%Y')
		ax.xaxis.set_major_formatter(myFmt)

		pointy = GetChangePoints(ax)

		plt.show()		

		xlist = pointy.get_xlist()

		print(xlist)

		with open('output_file.csv', 'w') as output_file:
			file_writer = csv.writer(output_file, delimiter=' ')

			for change in xlist:
				file_writer.writerow([change[0], change[1]])

	

	
	

