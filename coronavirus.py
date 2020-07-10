import pandas as pd, matplotlib.pyplot as plt, tqdm

class CV():
	
	def getData(self, gap, total, active = None, top = None):
		# Global Variables
		self.gap = gap
		self.tables = ['total', 'active', 'new', 'growth']
		if active is None:
			self.tables.remove('active')
		# Use active as denominator if present, else total
		self.total = total.fillna(0)
		self.active = self.total.copy() if active is None else active.fillna(0)
		# Calculate new cases in recent days and growth
		self.new = self.total.copy()
		for i in range(self.gap, self.total.shape[1]):
			self.new.iloc[:, i] = self.total.iloc[:, i] - self.total.iloc[:, i-self.gap]
		self.new = self.new.iloc[:, self.gap:]
		self.growth = (self.new / (self.active.iloc[:, self.gap:] + 1))
		# Condition
		self.lastColumn = self.total.columns[-1]
		self.condition = self.total[self.lastColumn] > top		
		# Make Table of Last Columns
		self.last = pd.DataFrame({name: eval('self.'+name)[self.lastColumn] for name in self.tables})
		rank = lambda col: self.last[col].rank(ascending = False)
		self.last['rank'] = rank('new') + rank('growth')

	def getPlot(self, names, write = False, width = 13):
		f = plt.figure(figsize = (width, 6))
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 1)
		self.growth.T[names].plot(ax=f.gca(), rot = 90)
		# Put legend on top
		plt.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol = 5)
		plt.ylim([0, 1])
		plt.grid(True, 'both')
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 2)
			self.active.T[self.gap:][names].plot(ax=f.gca(), rot = 90, logy = True)
			plt.legend().remove()
			plt.ylim([1, 2e6])
			plt.grid(True, 'both')
		# Save or Show?
		plt.savefig(f'{self.filename}/{"-".join(names)}.png') if write else plt.show()
		plt.close(f)

	def compareDate(self):
		old = pd.read_excel(f'{self.filename}.xlsx', sheet_name = 'total').columns[-1]
		new = self.lastColumn
		print('old', old, 'new', new)
		return new != old

	def writeExcel(self):
		writer = pd.ExcelWriter(self.filename+'.xlsx')
		fix = lambda name: eval(f'self.{name}').replace(0, float('nan'))[self.condition]
		fix('last').sort_values('rank', ascending = True).to_excel(writer, 'last')
		[fix(name).to_excel(writer, name) for name in self.tables]	
		writer.save()

	def plotTop(self):
		for country in tqdm.tqdm(self.total[self.condition].index):
			self.getPlot([country], write = True)

	def __init__(self, gap, filename, total, active = None, top = 1000):
		self.filename = filename
		self.getData(gap, total, active, top)

def getWorld(used):
	def makeSource(url):
		source = pd.read_csv(url)
		# Get Countries
		world = source.drop(['Province/State', 'Lat', 'Long'], axis = 1).groupby('Country/Region').sum()
		# Get Territories
		other = source[source['Province/State'].isin(used)].drop(['Country/Region', 'Lat', 'Long'], axis=1).groupby('Province/State').sum()
		return pd.concat([world, other])
	# Get Data
	total = makeSource(f'{domain}_confirmed_global.csv')
	active = total - makeSource(f'{domain}_recovered_global.csv')
	# Call Class
	return CV(7, 'time_series_world', total, active, )

def getUS():
	total = pd.read_csv(f'{domain}_confirmed_US.csv').drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'], axis=1).groupby('Province_State').sum()
	return CV(7, 'time_series_us', total, )

domain = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19'

if __name__=='__main__':
	for cv in getWorld(['Hong Kong', 'Macau', 'Hubei', 'Guangdong', 'Victoria']), getUS():	
		if cv.compareDate() or False:
			cv.writeExcel()
			cv.plotTop()