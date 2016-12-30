#!/usr/bin/python

from sklearn.naive_bayes import GaussianNB
import sys
import numpy
import math
import argparse

def basic_float_numerical_info(array):
    minval = min(array)
    maxval = max(array)
    midval = numpy.median(array)
    meanval = numpy.mean(array)
    stdval = numpy.std(array)

    return minval, maxval, midval, meanval, stdval

def modal_value(array):
    d = {}
    for v in array:
        if v in d.keys():
            d[v] += 1
        else:
            d[v] = 1
    sorted_pairs = sorted(d.iteritems(), key=lambda d:d[1], reverse = True)
    res = [x[0] for x in sorted_pairs[0:3]]
    times = [x[1] for x in sorted_pairs[0:3]]
    ratio = [x/float(len(array)) for x in times]
    length = len(res)
    if length < 3:
        res += [-1] * (3 - length)
        ratio += [-1] * (3 - length)
    return res + ratio

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
    

class Frigate_Data():
    def __init__(self):
        # original frigate log infomation
        # destination IP
        self._dip_ = ""
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
        self._features_ += modal_value(self._dports_)
        self._features_ += basic_float_numerical_info(self._ups_)
        self._features_ += basic_float_numerical_info(self._downs_)
        self._features_ += basic_float_numerical_info(self._durations_)
        self._features_ += basic_float_numerical_info(self._rtts_)
        self._features_ += get_ratio(n, get_dict_values(self._transport_protos_))
        self._features_ += get_ratio(n, get_dict_values(self._app_protos_))
        self._features_ += get_ratio(n, get_dict_values(self._errnos_))
        self._features_.append(n)

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
            trans_proto = spline[2]
            dipport = spline[5]
            dip, dport = dipport.split(':')
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
            fdata._dports_.append(int(dport))
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
        if pres > 0:
            print key, pres

main()

