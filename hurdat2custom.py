from hurdat2parser import storm,stormStats,seasonStats,rankStats,guide

# HURDAT2 Record goes from 1851 to last year
# Set the 'minyear' and 'maxyear' to operate on a range of years
minyear = 1851
maxyear = 2018

# SAMPLE SCRIPT
"""
with open("test" + str(minyear) + "-" + str(maxyear) + "-maxwinds-minmslp.csv","w") as f:
    # CSV HEADER
    header = ["ATCF ID","NAME","MAX WIND","MIN MSLP"]
    for each in header:     # write column titles from header
        f.write("{},".format(each))
    f.write("\n")
    for x in storm:
        data = [x.atcfid,x.name,x.maxwind,x.minmslp]  # storm object attributes of interest
        if int(x.atcfid[4:8]) >= minyear and int(x.atcfid[4:8]) <= maxyear:
            for each in data:
                f.write("{},".format(each))
        f.write("\n")
"""
