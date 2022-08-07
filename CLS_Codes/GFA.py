import os.path
import operator
from scipy.spatial.distance import cdist
import NurTestingPycharm.UtilNur as Util
import logging
import time
import random
import re
import ast

class GFA:
    def __init__(self):

        self.m = 5
        self.theta = 2
        self.k = 10  # top k items should be returned
        self.alpha = 0.5
        self.topSet_Score_m = []

        self.baseFolder = "I:\\ExpDataUDI\\ExperimentFolder"
        self.datasetName = "Gowalla" #Gowalla, Brightkite, Yelp
        self.operatingFolder = os.path.join(self.baseFolder, self.datasetName)
        self.outputFolder = os.path.join(self.operatingFolder, "ExpResult2")

        if self.datasetName == "Yelp":
            self.userLocationDict = self.convert_EachLines_Into_Dict(self.operatingFolder, "user_allChkIn_ListDict.txt")
            print("first dict loaded")
            self.socialNetwork = Util.convert_String_Into_Dict2(self, self.operatingFolder, "Yelp_edges_anonym_Dict_New.txt")
            print("Len: ", len(self.socialNetwork))
        else:
            self.userLocationDict = Util.convert_String_Into_Dict2(self, self.operatingFolder, "user_allChkIn_location_dictRound.txt")
            print("first dict loaded")
            self.socialNetwork = Util.convert_String_Into_Dict2(self, self.operatingFolder, self.datasetName+"_edges_Dict.txt")

        self.userLocationDictUserList = self.convert_String_Into_List(os.path.join(self.outputFolder, "CheckinBins"))
        print("size: ", len(self.userLocationDictUserList))

        self.newUserList = []

        self.startBegin = time.time()
        for user in self.userLocationDictUserList:
            self.bestScore = 0
            L = self.userLocationDict[user]
            noOfLoc = len(L)
            if user in self.socialNetwork.keys() and len(self.socialNetwork[user]) > 5 and len(set(L)) > self.k:
                self.newUserList.append(user)  # Will process only these users further as they have satisfied minimum requirements
                ngbrsList = self.socialNetwork[user]
                ngbrLocs = []
                for ngbrs in ngbrsList:
                    if ngbrs in self.userLocationDict.keys():
                        ngbrLocs = ngbrLocs + self.userLocationDict[ngbrs]
                self.ngbrLocCombinedUnique = list(set(ngbrLocs))
                if len(self.ngbrLocCombinedUnique) < 1:
                    continue
                self.L = list(set(L))  # converting into set rather than list. set will contain unique elements

                locIdLocMap = {}
                strLoc = ""
                lId = 0
                self.locNameAndLocId = {}
                for l in self.L:
                    self.locNameAndLocId[l] = lId
                    l = str(l).replace("(", "").replace(")", "").strip()
                    strLoc = strLoc + str(lId) + "\t" + str(l) + "\n"
                    locIdLocMap[lId] = l
                    lId += 1
                self.createFile(os.path.join(self.outputFolder, "Location", str(user) + ".txt"), strLoc)

                self.socialScoreDict = self.calcSocialScore(self.L, ngbrsList)
                self.d_m_dict = self.calcMaxDist(self.L, self.ngbrLocCombinedUnique)
                # print("d_m: ", self.d_m)
                self.maxD = self.calcMaxD(self.L)
                self.spatialScoreDict = self.calcSpatialScore(self.L, ngbrsList)
                self.S_gs_Dict = self.calcRelevanceScore(self.socialScoreDict, self.spatialScoreDict, user)

                self.socialSpatialDiversity(self.L, ngbrsList, user)
                contents = self.loadDgsContents(os.path.join(self.outputFolder, "Diversity", str(user) + ".txt"))  # loading self.content and creating self.locAndIndex

                # Now the original code starts
                self.start = time.time()
                S_I = []
                self.S_Rel = self.sortDesc(self.S_gs_Dict)
                if self.flagRandomSort:
                    random.shuffle(self.S_Rel)

                self.l = tuple
                self.S = []
                self.ResultListStr = ""
                self.ResultList = []

                outerloop = 0

                while True:
                    loopstartTime = time.time()
                    outerloop += 1
                    print("outerloop: ", outerloop)
                    S_R = list(self.S_Rel)  # making a different list S_R, everytime S_R will decrease when S_Rel decreases and make list at that time
                    if len(self.S_Rel) < self.k:
                        break
                    if len(S_I) == 0:
                        self.l = S_R[0]
                        S_R.remove(self.l)
                        self.S_Rel.remove(self.S_Rel[0])  # no user of S_Rel, just to iterate the list
                        print("self.l ", self.l)
                        S_I.append(self.l)

                    while len(S_I) < self.k:
                        if len(S_I) == 1 and self.bestScore > 0:
                            relScore = self.S_gs_Dict[S_I[0]]  # S_I contains single location
                            DgsM = max([self.dictOfDgsFromFileAndFlyNew(S_I[0], l) for l in S_R])  # *************************************************
                            flag = self.earlyTermination(self.bestScore, relScore, DgsM, self.k)
                            if flag:
                                S_I = []
                                break
                        topRelLoc = S_R[0]
                        topRelScore = self.S_gs_Dict[topRelLoc]
                        D_max = self.calcDgsMax(S_R, S_I)
                        lowerRelBoundSgs = self.calcRelLowerBound(topRelScore, D_max, topRelLoc, S_I)
                        minRelInS_R = min(self.S_gs_Dict[l] for l in S_R)
                        tempSR = list(S_R)
                        tempSR.remove(topRelLoc)
                        VP = self.potentialLocs(tempSR, lowerRelBoundSgs)
                        referenceTopSet = list(S_I)
                        referenceTopSet.append(topRelLoc)
                        self.scoreTop = self.calcTotalScoreofSet(referenceTopSet)
                        for loc in VP:
                            tempLocSet = list(S_I)
                            tempLocSet.append(loc)
                            score = self.calcTotalScoreofSet(tempLocSet)
                            if score > self.scoreTop:
                                self.scoreTop = score
                                topRelLoc = loc  # dont confuse the term topRelLoc!!!
                        S_I.append(topRelLoc)
                        S_R.remove(topRelLoc)
                        S_R = list(self.arrangeListBasedOnRelScore(S_R))
                        # print("S_I new: ", S_I, "S_R new: ", S_R)

                        if len(S_I) == self.k:
                            if len(self.topSet_Score_m) == self.m:
                                if self.topSet_Score_m[self.m - 1][1] < self.scoreTop:
                                    self.topSet_Score_m.pop()
                                    self.topSet_Score_m.append((S_I, self.scoreTop))
                            elif len(self.topSet_Score_m) < self.m:
                                self.topSet_Score_m.append((S_I, self.scoreTop))
                            self.topSet_Score_m = sorted(self.topSet_Score_m, key=lambda x: x[1], reverse=True)

                            if self.scoreTop > self.bestScore:
                                self.bestScore = self.scoreTop
                                self.S = list(S_I)
                                self.ResultListStr = self.ResultListStr + str(outerloop) + "\t" + str(self.bestScore) + "\t" + str(self.S) + "\t" + str(round(time.time() - loopstartTime, 2)) + "\n"
                                self.ResultList.append(self.S)

                            S_I = []
                            elapsed_time_loop = round(time.time() - loopstartTime, 2)
                            print("elapsed_time_loop: ", elapsed_time_loop, "seconds")
                            break

                print("Final Set: ", self.S, "score: ", self.calcTotalScoreofSet(set(self.S)))
                elapsed_time_fl = round(time.time() - self.start , 2)
                print("Total Elapsed Time: ", elapsed_time_fl, "seconds")

                locText = ""
                for loc in self.S:
                    lId = self.locNameAndLocId[loc]
                    loc = str(loc).replace("(", "").replace(")", "").strip()
                    locText = locText + str(lId) + "\t" + loc + "\n"
                self.createFile(os.path.join(self.outputFolder, "Results",  self.binId, str(self.k), str(user) + "_" + str(self.k) + ".txt"), locText)

                if len(self.ResultList) > 1:
                    optimal = self.ResultList[len(self.ResultList) -1] #last entry is optimal
                    for entryId in range(len(self.ResultList) -1):
                        feasible = self.ResultList[entryId]
                        common = set(optimal) & set(feasible)

                strTempTopMSets = ""
                for setKeys in self.topSet_Score_m:
                    strTempTopMSets = strTempTopMSets + str(setKeys[0]) + "\t" + str(setKeys[1]) + "\n"
                self.createFile(os.path.join(self.outputFolder, "Results", self.binId, "top_m_Exact", str(self.k), str(user) + "_" + str(self.k) + ".txt"), strTempTopMSets)

                #self.minDiversitySetOfEachLoc(self.S)
        strTimeStat = "Time:\t", str(round(time.time() - self.startBegin, 2)), "\t k:\t", str(self.k), "\tbin:\t", str(self.binId), "\tm:\t", str(self.m)
        self.createFile(os.path.join(self.outputFolder, "Results", self.binId, str(self.k), "TimeAndStats.txt"), strTimeStat)

    def convert_EachLines_Into_Dict(self, baseDirectory, fileInListForm):
        filePath = os.path.join(baseDirectory, fileInListForm)
        with open(filePath) as f:
            content = f.readlines()
        content = [x.strip() for x in content]

        tempDict = {}
        for i in range(len(content)):
            splitArray = content[i].split("\t")
            if len(splitArray) > 1:
                userid = str(splitArray[0])
                locsListStr = ast.literal_eval(splitArray[1])
                tempDict[userid] = locsListStr
        return tempDict

    def convert_String_Into_List(self, baseDirectory, fileName_to_convertDict):

        joinedPath = os.path.join(baseDirectory, fileName_to_convertDict)
        tt = []
        try:
            # f = open(joinedPath, "r", encoding="utf8")
            f = open(joinedPath, "r", encoding="ISO-8859-1")

            for line in f:
                line = re.sub(r'[^\x00-\x7f]', r' ', line)  # remove non ascii
                tt = ast.literal_eval(line)
            f.close()
        except:
            # f.close()
            # f = open(joinedPath, "r", encoding="ISO-8859-1")
            pass

        return tt

    def calcSocialScore(self, L, socialNetworkNgbrList):
        userDegree = len(socialNetworkNgbrList)
        socScore = {}

        for loc in L:
            totalNgbrChks = 0
            for ngbr in socialNetworkNgbrList:
                if ngbr in self.userLocationDict.keys() and loc in self.userLocationDict[ngbr]:
                    totalNgbrChks += 1
            socScore[loc] = round(totalNgbrChks / userDegree, 2)
        return socScore


    def calcSpatialScore(self, L, socialNetworkNgbrList):
        logging.info("Going to calculate spatial score of each location w.r.t. user u")
        userDegree = len(socialNetworkNgbrList)
        spatialScore = {}
        for loc in L:
            totalDist = 0
            for ngbr in socialNetworkNgbrList:
                if ngbr in self.userLocationDict.keys():
                    locListNgbr = self.userLocationDict[ngbr]
                    misDistTemp = min([Util.haversineDist(loc, l) for l in locListNgbr])
                    totalDist += misDistTemp
            if self.d_m_dict[loc] > 0:
                scoreSPTemp = 1 - (totalDist/(self.d_m_dict[loc] * userDegree))
            else:
                scoreSPTemp = 0
            spatialScore[loc] = round(scoreSPTemp, 2)
        return spatialScore


    def loadDgsContents(self, filePath):
        f = open(filePath, "r")
        self.content = f.readlines()
        self.content = [x.strip() for x in self.content]
        self.locAndIndex = []
        for i in range(len(self.content)):
            splitArray = self.content[i].split("\t")
            if len(splitArray) > 1:
                loc = eval(splitArray[0].strip())
                self.locAndIndex.append(loc)

        return self.content

    def dictOfDgsFromFileAndFly(self, content, locAndIndex, loc1_Q, loc2_Q):
        for i in range(len(content)):
            splitArray = content[i].split("\t")
            if len(splitArray) > 1:
                loc1Temp = eval(splitArray[0].strip())
                if loc1Temp == loc1_Q and loc2_Q in locAndIndex:
                    loc2Index = locAndIndex.index(loc2_Q)
                    tempValDgs = splitArray[loc2Index + 1]

                    return float(tempValDgs)

    def dictOfDgsFromFileAndFlyNew(self, loc1_Q, loc2_Q):
        if loc1_Q in self.locAndIndex and loc2_Q in self.locAndIndex:
            loc1_Index = self.locAndIndex.index(loc1_Q)
            loc2_Index = self.locAndIndex.index(loc2_Q)
            if len(self.content) >= loc1_Index:
                splitArray = self.content[loc1_Index].split("\t")
                if len(splitArray) > 1:
                    tempValDgs = splitArray[loc2_Index + 1]

                    return float(tempValDgs)
        else:
            print("locations are not available in self.locAndIndex list")
            return 0

    def sortDesc(self, dictInput):
        logging.info("Arrange dict w.r.t. descending.")
        sorted_d = Util.sortDictByValueWithKey(dictInput) #return (-37.73, 145.06): 0.99, (-37.19, 145.28): 0.98, (-37.56, 145.92): 0.97 in descending order
        arrangedKeysOnly = [x[0] for x in sorted_d]
        return arrangedKeysOnly # return [(-37.73, 145.06), (-37.19, 145.28), (-37.56, 145.92)] as list

    def earlyTermination(self, bestScore, relScore, DgsM, k):
        statFlag = False
        F_max = k*(self.omega*relScore + (1 - self.omega)*DgsM)
        if bestScore > F_max:
            statFlag = True
        return statFlag

    def calcDgsMax(self, S_R, S_I):
        tt = []
        for loc in S_R:
            tt.append(self.calcDgsOfLocToSet(loc, S_I))
        maxDiv = max(tt)
        return maxDiv

    def calcDgsOfLocToSet(self, loc, S):
        minDgs = min([self.dictOfDgsFromFileAndFlyNew(loc, l) for l in S])  # *********************************************
        return minDgs

    def calcRelLowerBound(self, topRelScore, D_max, topRelLoc, S_I):
        S_I_dash = list(S_I)
        S_I_dash.append(topRelLoc)
        Dgs_SI_dash = self.calcDgsOfSet(S_I_dash)
        Dgs_SI = self.calcDgsOfSet(S_I)
        Sgs_lower = topRelScore + ((1-self.omega)/self.omega)*(Dgs_SI_dash - Dgs_SI - D_max)
        return round(Sgs_lower,2)

    def calcDgsOfSet(self, S):
        totalDgs = 0
        if len(S) <= 1:
            return 0
        for loc in S:
            S_setminus = set(S)
            S_setminus.remove(loc)
            minDgs = min([self.dictOfDgsFromFileAndFlyNew(loc, l) for l in S_setminus])  # *********************************************
            totalDgs += minDgs
        return totalDgs

    def potentialLocs(self, S_R_copy, lowerRelBoundSgs_copy):
        potentialLocDict = {}
        for loc in S_R_copy:
            if self.S_gs_Dict[loc] > lowerRelBoundSgs_copy:
                potentialLocDict[loc] = self.S_gs_Dict[loc]
        arrangedPotLoc = self.sortDesc(potentialLocDict)
        return arrangedPotLoc

    def calcTotalScoreofSet(self, S):
        totalSgs = 0
        minDgsTemp = []
        for loc in S:
            totalSgs += self.S_gs_Dict[loc]
            S_setminus = set(S)
            S_setminus.remove(loc)
            for loc2 in S_setminus:
                minDgsTemp.append(self.dictOfDgsFromFileAndFlyNew(loc, loc2))  # *********************************************
        minDgsSet = min(minDgsTemp)
        totalscore = self.omega * totalSgs + (1 - self.omega) * minDgsSet
        return round(totalscore, 2)

    def arrangeListBasedOnRelScore(self, lst):
        tempDict = {}
        for l in lst:
            tempDict[l] = self.S_gs_Dict[l]
        arrabgeList = self.sortDesc(tempDict)
        return arrabgeList

    def createFile(self, fileNameFullPath, contents):
        try:
            fw_fileName = open(fileNameFullPath, "w", encoding="utf8")
            fw_fileName.write(contents.__str__())
            fw_fileName.close()
        except KeyError:
            print("Error while creating file.. ", KeyError)
            pass

objec = GFA()