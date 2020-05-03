import pandas as pd, matplotlib.pyplot as plt, tqdm

class CV():
	
	def getData(self, gap, total, active = None):
		# How many days to use as recent days
		self.gap = gap
		self.total = total.fillna(0)
		# Use active if present
		self.active = self.total.copy() if active is None else active.fillna(0)
		# Calculate new cases in recent days
		self.new = self.total.copy()
		for i in range(self.gap, self.total.shape[1]):
			self.new.iloc[:, i] = self.total.iloc[:, i] - self.total.iloc[:, i-self.gap]
		# Get growth rate
		self.ratio = (self.new / (self.active + 1)).iloc[:, self.gap:]
		self.new = self.new.iloc[:, self.gap:]

	def getPlot(self, names, write = None, width = 13):
		f = plt.figure(figsize = (width, 6))
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 1)
		self.ratio.T[names].plot(ax=f.gca(), rot = 90)
		# Put legend on top
		plt.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol = 5)
		plt.ylim([0, 1])
		plt.grid(True, 'both')
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 2)
			self.active.T[self.gap:][names].plot(ax=f.gca(), rot = 90, logy = True)
			plt.legend().remove()
			plt.ylim([1, 3e6])
			plt.grid(True, 'both')
		# Save or Show?
		plt.savefig('%s/%s.png' % (self.filename, '-'.join(names))) if write else plt.show()
		plt.close(f)

	def getUpdated(self):
		old = pd.read_excel(self.filename+'.xlsx').columns[-1]
		new = self.total.columns[-1]
		print('old', old, 'new', new)
		return new != old

	def writeOut(self):
		writer = pd.ExcelWriter(self.filename+'.xlsx')
		for name in 'total', 'active', 'new', 'ratio':
			eval('self.'+name).replace(0, float('nan')).to_excel(writer, name)
		writer.save()

	def plotTop(self, top = 1000):
		lastColumn = self.total.columns[-1]
		for country in tqdm.tqdm(self.total[self.total[lastColumn] > top].index):
			self.getPlot([country], write = True)

	def __init__(self, gap, filename, total, active = None):
		self.filename = filename
		self.getData(gap, total, active)

def getWorld(used):
	def makeSource(url):
		source = pd.read_csv(url)
		# Get Countries
		world = source.drop(['Province/State', 'Lat', 'Long'], axis = 1).groupby('Country/Region').sum()
		# Get Territories
		other = source[source['Province/State'].isin(used)].drop(['Country/Region', 'Lat', 'Long'], axis=1).groupby('Province/State').sum()
		return pd.concat([world, other])
	# Get Data
	total = makeSource('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
	active = total - makeSource('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')
	# Call Class
	return CV(7, 'time_series_world', total, active, )

def getUS():
	total = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv').drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'], axis=1).groupby('Province_State').sum()
	return CV(7, 'time_series_us', total, )

if __name__=='__main__':
	world = getWorld(['Hong Kong', 'Macau', 'Hubei', 'Guangdong'])
	us = getUS()
	override = False
	if world.getUpdated() or override:
		world.writeOut()
		world.plotTop()
	if us.getUpdated() or override:
		us.writeOut()
		us.plotTop()