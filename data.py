try:
    import matplotlib.pyplot as plt
except Exception:
    print('Could not import matplotlib. Plotting functions will not be available')

try:
    from scipy.stats import f_oneway
    import scipy
except:
    print("Could not import scipy. Data analysis will not be available")    

try:
    import numpy as np
except:
    print("Could not import numpy. Data analysis will not be available")

try:
    import scikit_posthocs as sp
except Exception:
    print('Could not import scikit_posthocs. Data analysis will not be available')

import os, math, stat, subprocess


class DataPoint:
    def __init__(self):
        pass


class FileReader:

    def __init__(self, filename, isTCP = True):
        self.filename = filename
        self.fd = open(filename)
        self.queries_sent = []
        self.queries_completed = []
        self.queries_lost = []
        self.queries_per_sec = []
        self.avg_latency = []
        self.std_latency = []
        self.reconnections = []
        self.connection_avg_latency = []
        self.connection_std_latency = []

        self.isTCP = isTCP

        # Actually load the data
        self.read(filename)



    def read_data_point(self):

        line = self.fd.readline()   # Read a blank line
        if not line: return False   # if the file is empty return false

        self.queries_sent += [ int(self.fd.readline().split(':')[1]) ]
        self.queries_completed += [ int(self.fd.readline().split()[2]) ]
        self.queries_lost += [ int(self.fd.readline().split()[2]) ]

        self.fd.readline() # read blank line
        self.fd.readline() # read response codes line
        self.fd.readline() # read avg packet size
        self.fd.readline() # read run time

        self.queries_per_sec += [ float(self.fd.readline().split()[3]) ]

        self.fd.readline() # read blank line

        self.avg_latency += [ float(self.fd.readline().split()[3]) ]
        self.std_latency += [ float(self.fd.readline().split()[3]) ]

        if self.isTCP:

            self.fd.readline() # read blank line

            self.fd.readline() # read Conection Statitics header
            self.fd.readline() # read blank line

            self.reconnections += [ int(self.fd.readline().split()[1]) ]

            self.fd.readline() # read blank line
        
            self.connection_avg_latency += [ float(self.fd.readline().split()[3]) ]
            self.connection_std_latency += [ float(self.fd.readline().split()[3]) ]

        self.fd.readline() # read blank line
        # self.fd.readline() # read blank line

        return True



    def read(self, filename = None):
        if filename is None: filename = self.filename
        
        while self.read_data_point():
            continue



    def avg(self, metric):
        if metric == 'sent':
            if len(self.queries_sent) is 0: return 0
            return sum(self.queries_sent) / len(self.queries_sent)

        elif metric == 'completed':
            if len(self.queries_completed) is 0: return 0
            return sum(self.queries_completed) / len(self.queries_completed)
        
        elif metric == 'lost':
            if len(self.queries_lost) is 0: return 0
            return sum(self.queries_lost) / len(self.queries_lost)
        
        elif metric == 'qps':
            if len(self.queries_per_sec) is 0: return 0
            return sum(self.queries_per_sec) / len(self.queries_per_sec)
        
        elif metric == 'latency':
            if len(self.avg_latency) is 0: return 0
            return sum(self.avg_latency) / len(self.avg_latency)
        
        elif metric == 'std':
            if len(self.std_latency) is 0: return 0
            return sum(self.std_latency) / len(self.std_latency)
        
        elif metric == 'conn latency':
            if len(self.connection_avg_latency) is 0: return 0
            return sum(self.connection_avg_latency) / len(self.connection_avg_latency)
        
        elif metric == 'conn std':
            if len(self.connection_std_latency) is 0: return 0
            return sum(self.connection_std_latency) / len(self.connection_std_latency)
        
        else:
            return 0



    def data(self, metric):
        if metric == 'sent':
            return self.queries_sent
        elif metric == 'completed':
            return self.queries_completed
        elif metric == 'lost':
            return self.queries_lost
        elif metric == 'qps':
            return self.queries_per_sec
        elif metric == 'latency':
            return self.avg_latency
        elif metric == 'std':
            return self.std_latency
        elif metric == 'conn latency':
            return self.connection_avg_latency
        elif metric == 'conn std':
            return self.connection_std_latency
        else:
            return []





class TrialEvaluator:

    def __init__(self, files, isTCP = True):
        if type(files) is not list: files = [ files ]
        self.filenames = files
        self.isTCP = isTCP
        self.readers = [ FileReader(name, self.isTCP) for name in self.filenames ]



    def axis_name(self, metric):
        if metric == 'sent':
            return 'Queries Sent (int)'
        elif metric == 'completed':
            return 'Queries Completed (int)'
        elif metric == 'lost':
            return 'Queries Lost (int)'
        elif metric == 'qps':
            return 'Queries Per Second (q/s)'
        elif metric == 'latency':
            return "Average Latency (s)"
        elif metric == 'std':
            return 'Standard Dev of Latency (s)'
        elif metric == 'conn latency':
            return 'Average Latency of Connection (s)'
        elif metric == 'conn std':
            return 'Standard Dev of Connection (s)'
        else:
            return None



    def build_data(self, metric, showAverages = True, sortByAvg = True, even = False):
        all_latencies = [ x.data(metric) for x in self.readers ]
        avgs = [ x.avg(metric) for x in self.readers ]
        file_names = [ x.split('/')[-1] for x in self.filenames]

        # This order is actually necessary. Plz don't be stupid
        if showAverages:
            for i, avg in enumerate(avgs):
                all_latencies[i] += [ avg ]

        if sortByAvg:
            all_latencies = [x for _, x in sorted(zip(avgs, all_latencies))]
            file_names = [x for _, x in sorted(zip(avgs, file_names))]

        if even:    # Make sure all the data has the same number of data points in them
            shortest = len(all_latencies[0])
            for latency in all_latencies:
                if shortest > len(latency): shortest = len(latency)
            for i in range(0, len(all_latencies)):
                all_latencies[i] = all_latencies[i][:shortest]


        return all_latencies, file_names
    


    def render_plot(self, plt, metric, xlabel = 'Trial file names', ylabel = None, bottom = 0.3, vertical = True):
        if ylabel is None:
            plt.ylabel(self.axis_name(metric), fontsize = 15)
        else:
            plt.ylabel(ylabel, fontsize = 15)

        plt.xlabel(xlabel, fontsize = 15)

        # plt.rcParams.update({'figure.autolayout': True})
        
        if vertical:
            plt.xticks(rotation='vertical')

        plt.subplots_adjust(bottom=bottom)

        plt.show()



    def boxplot(self, metric, showAverages = True, sortByAvg = True):
        
        all_latencies, file_names = self.build_data(metric, showAverages, sortByAvg)
        
        plt.boxplot(all_latencies)

        self.render_plot(plt, metric)



    def histogram(self, metric, sortByAvg = True, histtype=u'bar'):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg)

        for latency in all_latencies:
            plt.hist(latency, histtype=histtype)

        self.render_plot(plt, metric, xlabel = self.axis_name(metric), ylabel="Number of Occurances")       


    def log_histogram(self, metric, sortByAvg = True, histtype=u'bar'):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg)

        for latency in all_latencies:
            latency = [math.log(x) for x in latency]
            plt.hist(latency, histtype=histtype)

        self.render_plot(plt, metric, xlabel = self.axis_name(metric), ylabel="Number of Occurances") 



    def scatter(self, metric, showAverages = True, sortByAvg = True, even = False, baseline_name='baseline.res', vertical = True):
        all_latencies, file_names = self.build_data(metric, showAverages, sortByAvg, even)

        # Need to unpack the data to have 1 array of names and 1 array of latencies with the same length
        x = []
        y = []
        baseline_data = []
        for i, latency_array in enumerate(all_latencies):
            for latency in latency_array:
                if file_names[i] == baseline_name:
                    baseline_data += [ latency ]
                x += [ file_names[i] ]
                y += [ latency ]  

        plt.scatter(x, y)

        if len(baseline_data):  # Needs to happen after so they cover
            plt.scatter([baseline_name for _ in range(0, len(baseline_data))], baseline_data, color='orange')

        if showAverages:
            for i, name in enumerate(file_names):
                plt.scatter(name, all_latencies[i][-1], color='red')   # if show averages, the last entry is the avg

        self.render_plot(plt, metric, vertical = vertical)


    def wilcoxon(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)

        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]

        for i, latency in enumerate(all_latencies):
            if i is not baseline_index:
                res = scipy.stats.wilcoxon(baseline_latency, latency)
                print(file_names[i], res)



    def ranksum(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)

        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]
        for i, latency in enumerate(all_latencies):
            if i is not baseline_index:
                res = scipy.stats.ranksums(baseline_latency, latency)
                print(file_names[i], res)



    def anova(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)
        
        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]
        for i, latency in enumerate(all_latencies):
            if i is not baseline_index:
                res = f_oneway(baseline_latency, latency)
                print(file_names[i], res)



    def kruskal(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)
        
        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]
        res = scipy.stats.kruskal(*all_latencies)

        print('Kruskal results: ', res)



    def tukey_hsd(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)

        res = scipy.stats.tukey_hsd(*all_latencies)
        conf = res.confidence_interval(confidence_level=.99)

        for ((i, j), l) in np.ndenumerate(conf.low):
            # filter out self comparisons

            if i != j:
                h = conf.high[i,j]
                print(f"({i} - {j}) {l:>6.3f} {h:>6.3f}")



    def dunns(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)

        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]

        data = [x for x in all_latencies]
        res = sp.posthoc_dunn(data, p_adjust = 'fdr_tsbky')
        larger = np.array(res <= 0.15)
        found_any_true = False

        for i in range(0,len(larger)):
            for j in range(0,len(larger[0])):
                if larger[i][j]:
                    print('good metric found between: ', '\n\t', file_names[i], '\n\t', file_names[j])
                    found_any_true = True
        
        if not found_any_true:
            print('No statistical significance found')
    

    def tukey(self, metric, sortByAvg = False):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg, even = True)

        baseline_index = file_names.index('baseline.res')
        baseline_latency = all_latencies[ baseline_index ]

        data = [x for x in all_latencies]

        res = sp.posthoc_tukey(data, val_col='values', group_col='groups')
        larger = np.array(res <= 0.15)
        found_any_true = False

        for i in range(0,len(larger)):
            for j in range(0,len(larger[0])):
                if larger[i][j]:
                    print('good metric found between: ', '\n\t', file_names[i], '\n\t', file_names[j])
                    found_any_true = True

        if not found_any_true:
            print('No statistical significance found')


    def avg(self, metric, sortByAvg = True):
        all_latencies, file_names = self.build_data(metric, showAverages = False, sortByAvg = sortByAvg)

        for i in range(0, len(all_latencies)):
            print(file_names[i] + ': ', sum(all_latencies[i]) / len(all_latencies[i]))
        print()


class Collector:

    def __init__(self, server_ip, num_tests = 20, time=300, in_flight=100, clients = 12, threads = 12, loop=99, mode = 'tcp', local_addr = '127.0.0.1'):
        self.server_ip = str(server_ip)
        self.num_tests = str(num_tests)
        self.time = str(time)
        self.in_flight = str(in_flight)
        self.clients = str(clients)
        self.threads = str(threads)
        self.loop = str(loop)
        self.mode = str(mode)
        self.stats = str(5)
        self.local_addr = str(local_addr)

    def run(self, datafile, savefile = 'trial.res'):
        lines_length = 20 if self.mode == 'tcp' else 13
        
        cmd = '#!/bin/bash\n' + \
            'cmd="dnsperf -S ' + self.stats + ' ' + \
                    '-s ' + self.server_ip + ' ' + \
                    '-m ' + self.mode + ' ' + \
                    '-d ' + str(datafile) + ' ' + \
                    '-q ' + self.in_flight + ' ' + \
                    '-n ' + self.loop + ' ' + \
                    '-l ' + self.time + ' ' + \
                    '-a ' + self.local_addr + ' ' + \
                    '-c ' + self.clients + ' ' + \
                    '-T ' + self.threads + ' ' + \
                    '"; \n' + \
                    'eval $cmd | tail -' + str(lines_length) + ' >> "' + str(savefile) + '";'
        
        # Write to file and make it exe cause life is annoying
        f = open('tmp.sh', 'a')
        f.write(cmd)
        f.close()
        st = os.stat('./tmp.sh')
        os.chmod('./tmp.sh', st.st_mode | stat.S_IEXEC)
        for i in range(0, int(self.num_tests)):
            process = subprocess.Popen('./tmp.sh', stdout=subprocess.PIPE)
            output, error = process.communicate()
        
            print('finished trial: ', i)
            if output:
                print('output: ', output.decode())
            if error:
                print('error: ', error.decode())
        os.remove('./tmp.sh')
