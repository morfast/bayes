#!/usr/bin/python

from sklearn.naive_bayes import GaussianNB

class Frigate_Data():
    def __init__(self):
        # original frigate log infomation
        # destination IP
        self._dips_ = ""
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
        self._transport_protos_ = []
        # application layer protocols
        self._app_protos_ = []
        # http URLs
        self._urls_ = []
        # errno codes
        self._errnos_ = []
        

def read_frigate_log(logfilenames):
    res = {}
    total_lines = 0
    for logfilename in logfilenames:
        for line in open(logfilename):
            spline = line.strip().split("\t")
            print spline
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

            # update the features
            fdata._transport_protos_.append(trans_proto)
            fdata._dips_.append(dip)
            fdata._dports_.append(int(dport))
            fdata._ups_.append(int(up_traffic))
            fdata._downs_.append(int(down_traffic))
            fdata._durations_.append(float(duration))
            fdata._rtts_.append(int(handshake_rtt))
            fdata._app_protos_.append(app_proto)
            fdata._urls_.append(http_url)
            fdata._errnos_append(int(errro_code))

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


