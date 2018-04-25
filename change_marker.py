import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datacube
import xarray as xr
from datacube.api import GridWorkflow
from datacube.storage.masking import mask_invalid_data

sref_products = ['ls5_arcsi_sref_ingested', 'ls7_arcsi_sref_ingested', 'ls8_arcsi_sref_ingested']

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

def transformToDf(dataset_to_transform):

	"""Transforms xarray Dataset object into a Pandas dataframe"""

	new_df = pd.DataFrame()

	new_df['datetime'] = dataset_to_transform.time.data
	new_df['datetime'] = new_df['datetime'].apply(lambda x: x.toordinal())

	for name, var in dataset_to_transform.data_vars.items():
		new_df[name] = np.reshape(var.data, -1)
        
    # Points at the edge of the image could return empty arrays (all 0's) - this will remove any columns to which this applies
	new_df = new_df.dropna(axis=1, how='all')

	return new_df   

if __name__ == '__main__':

	# Create datacube object
	dc = datacube.Datacube()

	# Create GridWorkflow object so we can work with tiles
	gw = GridWorkflow(dc.index, product=sref_products[-1])

	# List to store the three datasets (LS5, LS7, LS8)
	sref_ds = []
	
	# The key represents which tile we are using
	key = (5, -28)

	# Need to fetch the tiles for each product seperately
	for product in sref_products:
		
		gw = GridWorkflow(dc.index, product=product)

		# Get the list of tiles (one for each time point) for this product
		tile_list = gw.list_tiles(product=product, cell_index=key)

		# Load all tiles
		for tile_index, tile in tile_list.items():
			dataset = gw.load(tile[0:1, 0:1, 0:10], measurements=['red', 'nir']) # Only need red and NIR to calculate NDVI

			if(dataset.variables):
				sref_ds.append(dataset)

	# Close datacube connection to database
	dc.close()

	# Concatenate the three datasets 
	sref = xr.concat(sref_ds, dim='time')

	# Change nodata values (0's) to NaN
	sref = mask_invalid_data(sref)

	# We want to process each pixel seperately
	for i in range(len(sref.x)):
		for j in range(len(sref.y)):

			# Get the time series of observations for this pixel
			sref_ts = sref.isel(x=i, y=j)
	
			# Transform to pandas dataframe
			sref_data = transformToDf(sref_ts)

			# Check columns weren't dropped
			if(sref_data.shape[1] == 3):

				# Get projected coordinates of this pixel
				x_val = float(sref_ts.x)
				y_val = float(sref_ts.y)

				# Set up output file name
				change_file = str(x_val) + "_" + str(y_val) + ".csv"

				# Calculate NDVI: (NIR-red) / (NIR+red)
				sref_data["ndvi"] = (sref_data.nir - sref_data.red) / (sref_data.nir + sref_data.red)

				# Set up the plot
				fig, ax = plt.subplots(figsize=(25, 5))
				ax.plot(sref_data.datetime, sref_data.ndvi, 'o', markersize=2)

				# Format dates to month/year rather than rata die
				myFmt = mdates.DateFormatter('%m/%Y')
				ax.xaxis.set_major_formatter(myFmt)

				pointy = GetChangePoints(ax)

				plt.show()		

				xlist = pointy.get_xlist()

				print(xlist)

				with open(change_file, 'w') as output_file:
					file_writer = csv.writer(output_file, delimiter=' ')

					for change in xlist:
						file_writer.writerow([change[0], change[1]])

	

	
	

