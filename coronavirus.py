import pandas as pd, matplotlib.pyplot as plt, tqdm, os, osascript, matplotlib.style as mplstyle, time

class CV():

	def makeNew(self):
		# Calculate new cases in recent days and growth
		self.df['new'] = self.df['total'].copy()
		for i in range(gap, self.df['total'].shape[1]):
			self.df['new'].iloc[:, i] = self.df['total'].iloc[:, i] - self.df['total'].iloc[:, i-gap]
		self.df['new'] = self.df['new'].iloc[:, gap:]
		self.df['growth'] = (self.df['new'] / (self.df['active'].iloc[:, gap:] + 1))

	def makeStack(self):
		self.stack = []
		for k, v in self.df.items():
			v = v.iloc[:, -days2:]
			v.columns = pd.to_datetime(v.columns)
			self.stack.append(v.stack().to_frame(k))
		self.stack = pd.concat(self.stack, axis = 1)

	def makeLast(self):
		# Make Table of Last Columns
		self.df['last'] = pd.DataFrame({k: v[self.lastColumn] for k, v in self.df.items()})
		rank = lambda col: self.df['last'][col].rank(ascending = False)
		self.df['last']['rank'] = rank('new')# + rank('growth')

	def getPlot(self, names, write = False, width = 13):
		f = plt.figure(figsize = (width, 6))
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 1)
		self.df['growth'].T[names].plot(ax=f.gca(), rot = 90)
		# Put legend on top
		plt.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol = 5)
		plt.ylim([0, 1])
		plt.grid(True, 'both')
		# If width < 13, print left graph only
		if width >= 13:
			plt.subplot(1, 2, 2)
			self.df['active'].T[gap:][names].plot(ax=f.gca(), rot = 90, logy = True)
			plt.legend().remove()
			plt.ylim([1, self.df['active'].max().max() * 1.5])
			plt.grid(True, 'both')
		# Save or Show?
		plt.savefig(f'{self.filename}/{"-".join(names)}.png') if write else plt.show()
		plt.close(f)

	def plotOne(self, names):
		fig, ax1 = plt.subplots()
		self.df['growth'].T[-days:][names].plot(ax=ax1, color = 'C3')
		plt.ylim([0, 1])
		# ax1.tick_params(axis = 'y', labelcolor='r')
		ax2 = ax1.twinx()
		for table in 'total','active', 'new':
			self.df[table].T[-days:][names].plot(ax=ax2, logy=True)
		plt.ylim([1, self.df['total'].max().max() * 1.5])
		# ax2.tick_params(axis = 'y', labelcolor='b')
		plt.savefig(f'{self.filename}/{names}.png')
		plt.close()

	def compareDate(self):
		old = pd.read_excel(f'{self.filename}.xlsx', sheet_name = 'total').columns[-1]
		new = self.lastColumn
		print('old', old, 'new', new)
		return new != old

	def writeExcel(self):
		timey = time.time()
		writer = pd.ExcelWriter(self.filename+'.xlsx')
		fix = lambda name: self.df[name].replace(0, float('nan'))[self.condition]
		fix('last').sort_values('rank', ascending = True).to_excel(writer, 'last')
		[fix(k).to_excel(writer, k) for k in self.df.keys()]
		# self.stack.to_excel(writer, 'stack')
		writer.save()

	def plotTop(self):
		for country in tqdm.tqdm(self.df['total'][self.condition].index):
			self.plotOne(country)

	def __init__(self, filename, total, active = None):
		self.filename = filename
		# Use active as denominator if present, else total
		self.df = {}
		self.df['total'] = total.fillna(0)
		self.df['active'] = self.df['total'].copy() if active is None else active.fillna(0)
		# Condition
		self.lastColumn = self.df['total'].columns[-1]
		self.condition = self.df['total'][self.lastColumn] > top
		self.makeNew()
		self.makeStack()
		self.makeLast()

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
	return CV('time_series_world', total, active, )

def getUS():
	total = pd.read_csv(f'{domain}_confirmed_US.csv').drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'], axis=1).groupby('Province_State').sum()
	return CV('time_series_us', total, )

domain = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19'

mplstyle.use('seaborn-pastel')
gap = 7
days = 365
top = 1000
days2 = 50

if __name__=='__main__':
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	notify = False
	for cv in getWorld(['Hong Kong', 'Macau', 'Hubei', 'Guangdong']), getUS():
		if cv.compareDate():
			cv.writeExcel()
			cv.plotTop()
			notify = True
	if notify:
		osascript.run('display notification "Coronavirus Updated"')
