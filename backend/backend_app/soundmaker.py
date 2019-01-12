import pandas as pd
import numpy as np
import json
from . import thinkdsp_stereo as tds
from jseg import Jieba
antusd = pd.read_csv('backend_app/dict/pantusd.csv')
jb = Jieba()
jb.add_guaranteed_wordlist(list(antusd.word))
stopwords = {}.fromkeys([ line.rstrip() for line in open('backend_app/dict/stop_words.txt') ])
linebreaks = ['\n', ' ', '\t']

def antusd_lookup(token):
    try:
        return antusd.loc[antusd['word'] == token, 'score'].iloc[0]
    except (KeyError, IndexError):
        return 0.0
    
def text_to_emo_arr(text):
    token_list = []
    # build a list of words
    for line in text.split('\n'):
        if line:
            try:
                for w in jb.seg(line, pos=False):
                    if w not in stopwords and w not in linebreaks:
                        token_list.append(w)
            except:
                pass
    score_arr = np.array([antusd_lookup(w) for w in token_list])
    if len(score_arr) == 0:
        score_arr = np.array([0.0])
    return score_arr

class ArticleMeloday():
    def __init__(self, data):
        """ Initialize the class
        data: dict. article item.
        
        """
        # read comments from db or file to pd
        #with open(srcpath, encoding='utf-8') as srcfile:
        #    data = json.loads(srcfile.read())
        #    self.cmdf = pd.DataFrame.from_dict(data[0]['comments'])
            #self.content = data['content']
        self.cmdf = pd.DataFrame.from_dict(data[0]['comments'])
        # define ADSR envelope generators that apply to different types of comment
        self.aaenv_push = tds.AdsrAmpEnvelope(adr=[0.3,0.3,0.1], suslv=0, inc_type='lin')
        self.aaenv_boo = tds.AdsrAmpEnvelope(adr=[0.3,0.3,0.1], suslv=0, inc_type='lin')
        self.aaenv_arrow = tds.AdsrAmpEnvelope(adr=[0.3,0.3,0.1], suslv=0, inc_type='lin')
        
        # datetime labels
        self.dt_labels = None

        # full wav
        self.full_stereowave = None
        
    def preprocess(self, gpfreq='10min', *args, **kwargs):
        """ Data preprocessing
        gpfreq: float. Time frequency of comments that should be groupped together and played in a second of the output wave
        For avaliable frequency aliases see: https://pandas.pydata.org/pandas-docs/stable/timeseries.html#timeseries-offset-aliases
        lkp_period: float. (optional), the period length of look up range, or hours the last looked up comment is be within.

        return: expected duration in seconds
        """
        # convert dt from string to datetime object
        self.cmdf['dt'] = pd.to_datetime(self.cmdf['dt'], format='%Y-%m-%d %H:%M:%S')
        
        # start and end of the lookup preiod
        dt_start = self.cmdf.iloc[0]['dt']
        # if lkp_period is not specified, use the last comment
        if not kwargs.get('lkp_period'):
            dt_end = self.cmdf.iloc[-1]['dt']
        else:
            dt_end = dt_start + pd.to_timedelta(kwargs.get('lkp_period')+'H')
        
        # dt_end must be larger then an inteval
        if dt_end < dt_start + pd.to_timedelta(gpfreq):
            dt_end = dt_start + pd.to_timedelta(gpfreq)

        # make a series of bins from comment's datetime
        dt_bins = pd.date_range(start=dt_start, end=dt_end, freq=gpfreq)
        dt_bins_str = dt_bins.astype(str).values

        self.dt_labels = ['({}, {}]'.format(dt_bins_str[i-1], dt_bins_str[i]) for i in range(1, len(dt_bins_str))]
        
        # assign dt_labels for each comment
        # Note: df.Date.astype(np.int64)//10**9 - converts datetime values into UNIX epoch
        self.cmdf['dt_bin'] = pd.cut(
            self.cmdf.dt.astype(np.int64)//10**9,
            bins=dt_bins.astype(np.int64)//10**9,
            labels=self.dt_labels,
            include_lowest=True)
        
        # drop rows that are out of lookup range ('dt_bin' is None)
        
        # calculate emotion arrays
        self.cmdf['emo_arr'] = self.cmdf.content.apply(text_to_emo_arr)
        
        # print the result of preprocessing
        print('Preprocess finished. We have %s comments groupped into %s dt bins.'%(len(self.cmdf), len(self.dt_labels)))
        print('Expected wave duration: %s secs.'%len(self.dt_labels))
        
        return len(self.dt_labels)
    # evaluate article wave
    def make_article_wave(self):
        """ Make wave from article content
        """
        pass

    # evaluate comment wave
    def make_comment_wave(self):
        """ Make wave from comments
        """
        full_lwave = None
        full_rwave = None
        for dt_bin in self.dt_labels:
            comments = self.cmdf[self.cmdf.dt_bin == dt_bin]
            # use white noise as base sound
            push_wv = tds.UncorrelatedGaussianNoise(amp=0.01).make_wave(duration=1.000)
            boo_wv = tds.UncorrelatedGaussianNoise(amp=0.01).make_wave(duration=1.000)
            for index, comment in comments.iterrows():
                # generate a sequence of beats from score array
                comment_bs = tds.BeatSeq(varocts=comment['emo_arr'])
                
                # determine signal's arguments, apply with different adsr
                if comment['score'] == 1:
                    comment_wv = comment_bs.make_wave(duration=1.000, aaenv=self.aaenv_push)
                    push_wv += comment_wv
                    
                elif comment['score'] == -1:
                    comment_wv = comment_bs.make_wave(duration=1.000, aaenv=self.aaenv_boo)
                    boo_wv += comment_wv
                else:
                    comment_wv = comment_bs.make_wave(duration=1.000, amp=0.5, aaenv=self.aaenv_arrow)
                    push_wv += comment_wv
                    boo_wv += comment_wv
                    
            # concatenate waves
            # if not none, concatenate waves
            if full_lwave:
                full_lwave = full_lwave | push_wv
            else:
                full_lwave = push_wv
            
            if full_rwave:
                full_rwave = full_rwave | boo_wv
            else:
                full_rwave = boo_wv
            
        self.full_stereowave = tds.StereoWave(full_lwave, full_rwave)
       
    def write(self, filepath):
        if self.full_stereowave:
            self.full_stereowave.write(filename=filepath)
        else:
            raise AttributeError('No wave data to write.')
# if __name__ == "__main__":
#     am = ArticleMeloday(srcpath='output.json')
#     am.preprocess()
#     full_wav = am.make_comment_wave()
#     full_stereowav = tds.StereoWave(full_wav[0], full_wav[1])
#     full_stereowav.write(filename='stereooutput.wav')