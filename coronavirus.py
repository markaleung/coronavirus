import pandas as pd, matplotlib.pyplot as plt

class CV():
	
	def getData(self, gap, filename, total, active = None):
		self.gap = gap
		self.total = total.fillna(0)
		self.active = self.total.copy() if active is None else active.fillna(0)
		self.new = self.total.copy()
		for i in range(self.gap, self.total.shape[1]):
			self.new.iloc[:, i] = self.total.iloc[:, i] - self.total.iloc[:, i-self.gap]
		self.ratio = (self.new / (self.active + 1)).iloc[:, self.gap:]
		self.new = self.new.iloc[:, self.gap:]
		writer = pd.ExcelWriter(filename)
		for name in 'total', 'active', 'new', 'ratio':
			eval('self.'+name).replace(0, float('nan')).reset_index().to_excel(writer, name, index=False)
		writer.save()

	def plotHelper(self, names, width = 13):
		self.figure = plt.figure(figsize = (width, 6))
		if width == 13:
			plt.subplot(1, 2, 1)
		self.ratio.T[names].plot(ax=self.figure.gca(), rot = 90)
		plt.legend(loc='lower left', bbox_to_anchor=(0, 1), ncol = 5)
		plt.ylim([0, 1])
		plt.grid(True)
		
		if width == 13:
			plt.subplot(1, 2, 2)
			self.active.T[self.gap:][names].plot(ax=self.figure.gca(), rot = 90, logy = True)
			plt.legend().remove()
			plt.ylim([1, 1e6])
			plt.grid(True)

	def getPlot(self, names, width = 13):
		self.plotHelper(names, width)
		plt.show()
		plt.close(self.figure)

	def getPlot2(self, names, folder, width = 13):
		f = self.plotHelper(names, width)
		plt.savefig('%s/%s.png' % (folder, '-'.join(names)))
		plt.close(self.figure)