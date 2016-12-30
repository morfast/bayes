#!/usr/bin/python

from sklearn.naive_bayes import GaussianNB
import sys
import numpy
import math
import argparse
import scipy.signal

def basic_float_numerical_info(array):
    minval = min(array)
    maxval = max(array)
    midval = numpy.median(array)
    meanval = numpy.mean(array)
    stdval = numpy.std(array)

    return minval, maxval, midval, meanval, stdval

def modal_value(array, n):
    d = {}
    for v in array:
        if v in d.keys():
            d[v] += 1
        else:
            d[v] = 1
    sorted_pairs = sorted(d.iteritems(), key=lambda d:d[1], reverse = True)
    res = [x[0] for x in sorted_pairs[0:n]]
    times = [x[1] for x in sorted_pairs[0:n]]
    ratio = [x/float(len(array)) for x in times]
    length = len(res)
    if length < n:
        res += [-1] * (n - length)
        ratio += [-1] * (n - length)
    return res, ratio

def basic_int_info(array):
    pass


def add_feature_dict(d, key):
    if key in d:
        d[key] += 1

def get_dict_values(d):
    sorted_pairs = sorted(d.iteritems(), key=lambda d:d[0])
    return [x[1] for x in sorted_pairs]

def get_ratio(total_num, array):
    return [x/float(total_num) for x in array]

def get_timeinfo(atime_list):
    freq, power = scipy.signal.periodogram([float(x) for x in atime_list])
    max_freqs = sorted(zip(freq, power), key = lambda x:x[1], reverse=True)[:3]
    return [x[0] for x in max_freqs] + [x[1] for x in max_freqs]

def convert_time(timestr):
    # 2016-10-11 09:11:13 -> 9*60+11
    x = timestr.split()[1].split(':')
    h = x[0]
    m = x[1]
    return int(h) * 60 + int(m)

    

class Frigate_Data():
    def __init__(self):
        # original frigate log infomation
        # access time
        self._atime_ = [0] * 1440
        # destination IP
        self._dip_ = ""
        # source IP
        self._sip_ = set()
        # destination port
        self._dports_ = []
        # up traffic
        self._ups_ = []
        # down traffic
        self._downs_ = []
        # link duration
        self._durations_ = []
        # time of the handshake
        self._rtts_ = []
        # trasport layer protocols
        self._transport_protos_ = {'TCP':0, 'UDP':0, 'ICMP':0, }
        # application layer protocols
        self._app_protos_ = {'HTTP':0, }
        # http URLs
        self._n_url_ = 0
        # errno codes
        self._errnos_ = {0:0, 104:0, 62:0, 110:0, 111:0}

        # features
        self._features_ = []


    def print_original_logs(self):
        print " ====================== "
        print "destination IP: %s" % (self._dip_)
        print "destination port:", self._dports_
        print "up_traffic", self._ups_
        print "down_traffic", self._downs_
        print "duration", self._durations_
        print "rtt", self._rtts_
        print "trans_proto", self._transport_protos_
        print "application protocols", self._app_protos_
        print "url", self._n_url_
        print "errno", self._errnos_
        print " ====================== "

    def cal_features(self):
        n = len(self._ups_)
        # dport
        modval, ratio = modal_value(self._dports_, 3)
        self._features_ += modval
        self._features_ += ratio
        # ups
        self._features_ += basic_float_numerical_info(self._ups_)
        modval, ratio = modal_value(self._ups_, 2)
        self._features_ += modval
        self._features_ += ratio
        # downs
        self._features_ += basic_float_numerical_info(self._downs_)
        modval, ratio = modal_value(self._downs_, 2)
        self._features_ += modval
        self._features_ += ratio
        # duration
        self._features_ += basic_float_numerical_info(self._durations_)
        # rtt
        self._features_ += basic_float_numerical_info(self._rtts_)
        # protocols
        self._features_ += get_ratio(n, get_dict_values(self._transport_protos_))
        self._features_ += get_ratio(n, get_dict_values(self._app_protos_))
        # error code
        self._features_ += get_ratio(n, get_dict_values(self._errnos_))
        # pv uv
        self._features_.append(n)
        self._features_.append(len(self._sip_))
        # time info
        self._features_ += get_timeinfo(self._atime_)

    def print_features(self):
        print len(self._features_), self._features_

    def get_features(self):
        return self._features_

        

def read_frigate_log(logfilenames):
    res = {}
    total_lines = 0
    for logfilename in logfilenames:
        print logfilename
        for line in open(logfilename):
            spline = line.strip().split("\t")
            # grab features
            atime = spline[0]
            atime_minute = convert_time(atime)
            trans_proto = spline[2]
            dipport = spline[5]
            dip, dport = dipport.split(':')
            sipport = spline[3]
            sip, sport = sipport.split(':')
            up_traffic = spline[7]
            down_traffic = spline[8]
            duration = spline[10]
            handshake_rtt = spline[13]
            app_proto = spline[16]
            http_url = spline[17]
            errro_code = spline[20]

            if dip in res.keys():
                # get the Frigate_Data object
                fdata = res[dip]
            else:
                fdata = Frigate_Data()
                res[dip] = fdata
                fdata._dip_ = dip

            # update the features
            assert(dip == fdata._dip_)
            add_feature_dict(fdata._transport_protos_, trans_proto)
            fdata._atime_[atime_minute] += 1
            fdata._dports_.append(int(dport))
            fdata._sip_.add(sip)
            fdata._ups_.append(float(up_traffic))
            fdata._downs_.append(float(down_traffic))
            fdata._durations_.append(float(duration))
            fdata._rtts_.append(float(handshake_rtt))
            add_feature_dict(fdata._app_protos_, app_proto)
            if http_url != "NULL":
                fdata._n_url_ += 1
            add_feature_dict(fdata._errnos_, int(errro_code))

            total_lines += 1
            if total_lines % 10000 == 0:
                print "%d lines read" % total_lines

    return res

def test():
    X = [[1,1,[0]], [2,2,[1]], [1,2,[1]], [11,11,[1]], [12,12,[1]],]
    Y = [0,0,0,1,1]
    
    gnb = GaussianNB()
    f = gnb.fit(X,Y)
    print f.predict([2,3])
    print f.predict([12,13])

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--train", action='store', nargs='*')
    parser.add_argument("-d", "--data", action='store', nargs='*')
    a = parser.parse_args()
    return a.train, a.data

def main():
    train_filenames, data_filenames = parse_arguments()
    if not train_filenames or not data_filenames:
        sys.exit(0)

    # read the training sets
    X = []
    Y = []
    for filename in train_filenames:
        res = read_frigate_log([filename])
        for key in res:
            res[key].cal_features()
            X.append(res[key].get_features())
        # get Y value from the filename
        filename = filename.split('/')[-1]
        y_value = int(filename.split('_')[0])
        Y += ([y_value] * len(res))

    # training
    gnb = GaussianNB()
    f = gnb.fit(X,Y)

    # judge
    res = read_frigate_log(data_filenames)
    for key in res:
        res[key].cal_features()
        pres = f.predict([res[key].get_features()])[0]
        print "-%d- %s" %  (pres, key)

main()

