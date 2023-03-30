# DNScalc

**Overview**

This package is built specifically to collect and analyze data on DNS servers using DNS perf. The collection method is effectively just a helpful wrapper around DNSperf and all the following functions are just fancy interpretation of its output. A quick start guide is given below and a full guide on the package follows that.

**Dependencies**

    matplotlib
    scipy
    numpy
    os
    math
    stat
    subprocess
    scikit_posthocs

# Quick Start

To collect data for a single TCP DNSperf test on the server located at 127.0.0.1 the following code can be run: 

    import data
    tmp = data.Collector('127.0.0.1', num_tests=1)
    tmp.run('some DNS data file usually specified with -d in traditional DNS perf', savefile='results.res')

This will APPEND the file results.res with a single datapoint (a datapoint is the last 20 lines of the dns perf output, which gives the overall averages).

A UDP test can be generated by specifying:

    tmp = data.Collector('127.0.0.1', num_tests=1, mode='udp')

Output files from data collection will be call RES files from now on.

Once a RES file has been created, it can be analyzed with the FileReader object. A simple example is printing all the data and averages. The following code demonstrates how to find all of the values:

    import data
    filename = 'results.res'
    data_recorded = ['sent', 'completed', 'lost', 'qps', 'latency', 'std', 'conn latency', 'conn std']
    
    tmp = data.FileReader(filename) 

    for type in data_recorded:
        data = tmp.data(type)
        print(type, 'data:\n', data)

        avg = tmp.avg(type)
        print(type, 'avg:', avg)

A collection of RES files will be refered to as a TRIAL and are usually analyzed as a group (like comparing possible improvements to some baseline).

Trails can be analyzed using the TrailEvaluator object using all the same metrics as a FileReader. The following code is a similar to the example above, instead creating scatter plots of the metrics and then printing the corresponding average:

    import data
    filenames = ['ex1.res', 'ex2.res', 'ex3.res']
    data_recorded = ['sent', 'completed', 'lost', 'qps', 'latency', 'std', 'conn latency', 'conn std']

    tmp = data.TrialEvaluator(filenames)

    for type in data_recorded:
        # Create the scatter plot
        tmp.scatter(type, showAverages=True, sortByAvg=True)
        # Print the averages
        tmp.avg(type, sortByAvg=True)

Finding statistically significant data can also be done with the following code:

    import data
    filenames = ['ex1.res', 'ex2.res', 'ex3.res']
    data_recorded = ['sent', 'completed', 'lost', 'qps', 'latency', 'std', 'conn latency', 'conn std']

    tmp = data.TrialEvaluator(filenames)

    for type in data_recorded:
        # Check for presence of significance using Anova
        tmp.anova(type, sortByAvg=True)
        # Check which parameters are significant using Tukey
        tmp.tukey(type, showAverages=True, sortByAvg=True)
        

It is worth noting that these outputs can be quite large if you have a lot of statistically significant data.


<br/>
<br/>

# Full Guide

**A list of all the metrics and their meanings is:**

    - sent         :   # of queries sent
    - completed    :   # queries completed
    - lost         :   # queries lost
    - qps          :   avg queries per second
    - latency      :   avg latency
    - std          :   standard deviation of the latency
    - conn latency :   avg connection latency (TCP only)
    - conn std     :   standard deviation of conn latency (TCP only)

<br/>
<br/>

**Collector** 

This object isn't strictly necessary but is helpful to abstract away from DNSperf and make sure the data is collected properly. (If you'd like to collect the data files yourself, just pipe the last 20 lines of DNSperf into a file)

<br/>

<u>Constructor:</u>

    tmp = Collector(server_ip, num_tests = 20, time=300, in_flight=100, clients = 12, threads = 12, loop=99, mode = 'tcp', local_addr = '127.0.0.1')

- server_ip is the IP address of the server you'd like to test
    - Corresponds to the -s flag

- num_tests is the number of test you'd like to run (ie how many datapoints to collect)

- time is the time limit, in seconds, you'd like to run the test for
    - corresponds to the -l flag

- in_flight specifies the number of allowable in-flight packets
    - corresponds to the -q flag

- clients specifies the number of clients DNSperf is allowed to use in parallel
    - corresponds to the -c flag

- threads specificies the number of threads DNSperf is allow to create
    - corresponds to the -T flag

- loop is the number of times the request from the datafile (see Collector.run) are run before stopping (if time limit hasn't been reached) 
    - corresponds to the -n flag

- mode can take values 'tcp' or 'udp' and changes which kind of requests are made
    - corresponds to the -m flag

- local_addr specifies the local address to send the requests from
    - corresponds to the -a flag


<br/>

<u>Taking Data</u>

    Collector.run(datafile, savefile='trial.res')

- This function takes a file name to the datafile you'd like to use for the queries and collections the number of tests specified in Collector.num_tests and saves the results to savefile (default trial.res)


<br/>
<br/>


**FileReader**

A FileReader should be associated with each individual file you wish to analyze, it's much simpler that way.

There isn't any extra functional documentation for the FileReader, all its abilities are actually listed in the examples above.

<br/>

<u>Constructor</u>

    FileReader(filename, isTCP = True)

- The filename is the path to the RES file you'd like to open and isTCP is specified because the outputs to DNSperf is different for UDP and TCP.

<br/>
<br/>

**TrialEvaluator**

<br/>

<u>Constructor:</u>

    TrialEvaluator(files, isTCP = True)

- files is an array of filenames you'd like to analyze. And because TCP and UDP have different file formats, this analysis is only done for one of them. If you'd like me to make it work for both, please let me know!

<br/>

One can easily <u>print the averages</u> of a trial using:

    TrialEvaluator.avg(metric, sortByAvg = True)

<br/>

A TrialEvaluator can <u>generate the plots</u>:

    TrialEvaluator.boxplot(metric, showAverages=True, sortByAvg=True)
        
- Generates a boxplot and displays a red line to indicate the avg is showAverage is true

<br/>

    TrialEvaluator.histogram(metric, sortByAvg=True, histtype=u'bar')

- Generates a histogram, with the display type of the histogram being controlled by histtype. See matplotlib.pyplot.histogram for other possible values
    
<br/>

    TrialEvaluator.log_histogram(metric, sortByAvg = True, histtype=u'bar')

- Generates a histogram of the logrithm of the data. histtype is specified in the same way as regular histogram

<br/>

    TrialEvaluator.scatter(metric, showAverages = True, sortByAvg = True, even = False, baseline_name='baseline.res', vertical = True)

- Generates a scatter plot of all the trials specified. Each trial is contained to its own vertical axis and labeled with its filename, the orientation of the filename can be changed with the vertical argument. The argument even displays the same number of datapoints for each trial

<br/>
<br/>

The TrialEvaluator can perform the following <u>statitical analysis</u> and automatically prints the results:

    TrialEvaluator.wilcoxon(metric, sortByAvg=False)

    TrialEvaluator.ranksum(metric, sortByAvg=False)

    TrialEvaluator.anova(metric, sortByAvg=False)

    TrialEvaluator.kruskal(metric, sortByAvg=False)

    TrialEvaluator.tukey_hsd(metric, sortByAvg=False)

    TrialEvaluator.dunns(metric, sortByAvg=False)

    TrialEvaluator.tukey(metric, sortByAvg=False)

While the TrailEvaluator can perform any of these tests, in my experience and based on the data I collected, the ANOVA test should be used to check if any statistical significance is present. Then, to determine where the significance is present, either Tukey or Dunn's should be used. But your mileage may vary. Let me know if you have any improvements!
