# For Licensing refer LICENSE.md
import tweepy
import untangle
import MySQLdb

__author__ = 'Ashwani Agarwal'

consumer_key = "AB"
consumer_secret = "CD"

access_token = "EF"
access_token_secret = "GH"

HOST = 'IJ'
USER = 'KL'
PW = 'MN'
DB = 'dictionaryStudyTool' #http://sourceforge.net/projects/mysqlenglishdictionary/

dictapi = "OP"

USER_HANDLE = 'tellmeaningof'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def log(*s):
    """
    log the input
    :param *s: collection of strings
    :return: void
    """
    st = ""
    for i in s:
        st += str(i) + " "
    f = open("log.txt", "a+")
    st = st.encode('utf-8')
    f.write(st + "\n")
    # print st
    f.close()


def printaboutme(api):
    """
    print name and handler of authenticated user
    :param api: tweepy.API() (authenticated)
    :return: void
    """
    me = api.me()
    log(me.screen_name)
    log(me.name)


def tellmeaningof(word):
    """
    return the meaning of word from Merriam-Webster
    using it's api call
    :param word: String
    :return: Meaning of word
    """
    # First try to fetch from local-database
    db = MySQLdb.connect(host = HOST, user = USER, passwd = PW, db = DB)
    cur = db.cursor()
    cur.execute("select definition from entries where word='" + word + "';")
    if int(cur.rowcount) > 1:
        return cur.fetchone()
    else:
        # Not found in local-dictionary use dictionary api
        # http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=api
        url = "http://www.dictionaryapi.com/api/v1/references/collegiate/xml/" + word + "?key=" + dictapi
        obj = untangle.parse(url)
        entry = obj.entry_list.entry
        if isinstance(entry, list):
            entry = entry[0]
        defn = getattr(entry, 'def')
        if isinstance(defn, list):
            defn = defn[0]
        dataarr = defn.dt
        if isinstance(dataarr, list):
            i = 0
            while dataarr[i].get_elements(name = 'sx') != []:
                i += 1
            if i == len(dataarr):
                return "Can't find any good meaning"
            data = dataarr[i]
        else:
            data = dataarr
        mean = data.cdata.split(':')[1]
        if data.get_elements(name = 'fw') != []:
            mean += data.fw.cdata
        return mean


def findUserWord(tweet):
    """
    find user mention, and word in a tweet
    :param tweet: tweet text
    :return: list of users, word as string
    """
    li = tweet.split()
    users = []
    words = ""
    for x in li:
        if x[:1] == '@' and x[1:] != USER_HANDLE:
            users += [x]
        elif x[:1] != '#' and x[:1] != '@':  # Shouldn't be a hash-tag or tweet to self
            words += x + ' '
    return users, words.strip()  # strip method to remove any lead/trail space


class StatusListener(tweepy.StreamListener):
    def on_status(self, status):
        print status
        log(status.text)
        if status.text[:2] == 'RT':  # Status is a retweet
            pass
        else:
            # remove prefix
            tweet = status.text
            log("In " + tweet)
            user, word = findUserWord(tweet)
            log(user, word)
            # word = status.text[len('@tellmeaningof') + 1:]
            # log(word)
            try:
                meaning = tellmeaningof(word)
            except:
                meaning = "Can't find meaning"
            log("meaning = ", meaning)
            # tgt_user = '@' + status.user.screen_name
            mention = ''
            for x in user:
                mention += x + ' '
            tgt_status_id = status.id_str
            status_text = '@' + status.user.screen_name + ' ' + mention + word + '- ' + meaning
            log("Out:" + status_text)
            try:
                # print status
                api.update_status(status = status_text[:139], in_reply_to_status_id = tgt_status_id)
            except:
                log('error while updating status')

    def on_error(self, status_code):
        log(status_code)


def start_stream():
    l = StatusListener()
    stream = tweepy.Stream(auth, l)
    while True:
        stream.filter(track = ['@' + USER_HANDLE])
        # stream.filter(track = ['ucldraw'])


if __name__ == '__main__':
    start_stream()
    # print tellmeaningof('tweet')
    # print findUserWord("@tellmeaningof tit for tat #Twitter #Bot #Python #Testing")
