**Tip:** Tinfoleak is one of the proposed applications but not yet added officially to the list of livecd applications, information to help during testing

# Introduction #

Tinfoleak is a simple Python script that allow to obtain detailed information about a Twitter user activity


# Details #

Detailed information about a Twitter user activity:

  * basic information about a Twitter user (name, picture, location, followers, etc.)
  * devices and operating systems used by the Twitter user
  * applications and social networks used by the Twitter user
  * place and geolocation coordinates to generate a tracking map of locations visited
  * show user tweets in Google Earth!
  * download all pics from a Twitter user
  * hashtags used by the Twitter user and when are used (date and time)
  * user mentions by the the Twitter user and when are occurred (date and time)
  * topics used by the Twitter user

You can filter all the information by:

> start date / time
> end date / time
> keywords

### Usage ###

```
tinfoleak.py [-n|--name] username [-c|--count] count [-t|--time] [-b|--basic] [-s|--source] [-h|--hashtags] [-m|--mentions] [-g|--geo] geofile [--stime] stime [--etime] etime [--sdate] sdate [--edate] edate [-f|--find] word [-p|--pics] images [-o|--output] file

        (*) username: Twitter account
            count: number of tweets to analyze (default value: 100)
            time: show time in every result (default value: off)
        (+) basic: show basic information about the username (default value: off)
        (+) source: show applications used by username (default value: off)
        (+) hashtags: show hashtags used by username (default value: off)
        (+) mentions: show twitter accounts used by username (default value: off)
        (+) geofile: show geolocation information and save the results in KML format for Google Earth visualization (default value: off)
            stime: filter tweets from this start time. Format: HH:MM:SS (default value: 00:00:00)
            etime: filter tweets from this end time. Format: HH:MM:SS (default value: 23:59:59)
            sdate: filter tweets from this start date. Format: YYYY/MM/DD (default value: 1900/01/01)
            edate: filter tweets from this end date. Format: YYYY/MM/DD (default value: 2100/01/01)
        (+) word: filter tweets that include this word
        (x) images: [0] show images (parameter "geofile" is mandatory), [1] download images (to the "screen_name" directory)
            file: output file

        (*) Required parameter
        (+) One of these parameters must be informed
        (x) If you enabled this option, you need to be patient. The execution time is greatly increased.

        Examples:
                # tinfoleak.py -n vaguileradiaz -b
                # tinfoleak.py -n stevewoz -sc 1000
                # tinfoleak.py -n nicholasstoller -g nicholasstoller.kml -o output.log
                # tinfoleak.py -n vaguileradiaz -thm
                # tinfoleak.py -n billgates -g billgates.kml -p 1 -c 300
                # tinfoleak.py -n vaguileradiaz -tc 500 -f secret --sdate 2013/10/01 -o output.log
                # tinfoleak.py -n vaguileradiaz -shmtc 1000 --stime 08:00:00 --etime 18:00:00
```

More info (including tinfoleak script) and screenshots:
http://vicenteaguileradiaz.com/tools/