import operator
import NurTestingPycharm.UtilNur as Util
import logging
import time
import os.path

class FVA:
    def __init__(self):
        self.m = 5
        self.theta = 2
        self.k = 10  # top k items should be returned
        self.alpha = 0.5

        self.baseFolder = "I:\\ExpDataUDI\\ExperimentFolder"
        self.datasetName = "Gowalla" #Change the dataset name here
        self.operatingFolder = os.path.join(self.baseFolder, self.datasetName)
        self.outputFolder = os.path.join(self.operatingFolder, "ExpResult2")

        self.userLocationDict = Util.convert_String_Into_Dict2(self, self.operatingFolder, "user_allChkIn_location_dictRound.txt")
        self.socialNetwork = Util.convert_String_Into_Dict2(self, self.operatingFolder, "Gowalla_edges_Dict.txt") #Load edge info

        self.userLocationDictUserList = ["4"] #Testing, otherwise load all users

        for user in self.userLocationDictUserList:
            self.bestScore = 0
            L = self.userLocationDict[user]
            noOfLoc = len(L)
            if user in self.socialNetwork.keys() and len(self.socialNetwork[user]) > 10 and len(set(L)) > self.k:
                ngbrsList = self.socialNetwork[user]
                ngbrLocs = []
                for ngbrs in ngbrsList:
                    if ngbrs in self.userLocationDict.keys():
                        ngbrLocs = ngbrLocs + self.userLocationDict[ngbrs]
                self.ngbrLocCombinedUnique = list(set(ngbrLocs))

                locIdLocMap = {}
                strLoc = ""
                lId = 0
                self.locNameAndLocId = {}
                for l in L:
                    self.locNameAndLocId[l] = lId
                    l = str(l).replace("(", "").replace(")", "").strip()
                    #strLoc = strLoc + str(lId) + "\t" + str(l) + "\n"
                    locIdLocMap[lId] = l
                    lId += 1

                self.L = list(set(L))  # converting into set rather than list. set will contain unique elements
                self.socialScoreDict = self.calcSocialScore(self.L, ngbrsList)
                self.d_m_dict = self.calcMaxDist(self.L, self.ngbrLocCombinedUnique)
                #print("d_m: ", self.d_m)
                self.maxD = self.calcMaxD(self.L)
                self.spatialScoreDict = self.calcSpatialScore(self.L, ngbrsList)
                self.S_gs_Dict = self.calcRelevanceScore(self.socialScoreDict, self.spatialScoreDict, user)

                self.socialSpatialDiversity(self.L, ngbrsList, user)

                # Now the original code starts
                start = time.time()

                self.S_I = []
                self.S_Rel = self.sortDesc(self.S_gs_Dict)
                self.S_R = list(self.S_Rel)  # Put as backup S_Rel arranged by relevance score
                self.Q = []  # initialize
                self.l = tuple
                self.S = set
                self.Q.append((list(self.S_I), list(self.S_R), 0))
                iterNo = 0
                while len(self.Q) > 0:
                    print("iteration done: ", iterNo)
                    iterNo += 1

                    firstElement = self.Q.pop(0)
                    S_I = firstElement[0]
                    S_R = firstElement[1]
                    if len(S_I) == self.k:
                        continue
                    while len(S_I) < self.k and len(S_I) + len(S_R) >= self.k:
                        if len(S_R) > 0:
                            if len(S_I) == 0:
                                self.l = S_R.pop(0)
                                S_I.append(self.l)

                            else:
                                if self.bestScore > 0:  # checking the S_I length is equal to k-1,
                                    totalScoreTerminateBound = self.calcAdvTermOnTotalScore(S_I, S_R)
                                    if totalScoreTerminateBound <= self.bestScore:
                                        break
                                self.l = S_R.pop(0)
                                S_I.append(self.l)
                            if len(S_I) == self.k:
                                score = self.calcTotalScoreofSet(S_I)
                                if score > self.bestScore:
                                    self.bestScore = score
                                    self.S = list(S_I)

                            if len(S_I) > 1:
                                tempSI = list(S_I)
                                tempSI.remove(self.l)
                                scoreS_I = self.calcTotalScoreofSet(set(S_I))
                                score_tempSI = self.calcTotalScoreofSet(set(tempSI))

                                indx = 0
                                for tupl in self.Q:
                                    scr = tupl[2]
                                    if scoreS_I > scr:
                                        self.Q.insert(indx, (list(S_I), list(S_R), scoreS_I))
                                        break
                                    indx += 1

                                indx2 = 0
                                for tupl2 in self.Q:
                                    scr2 = tupl2[2]
                                    if score_tempSI > scr2:
                                        self.Q.insert(indx2, (tempSI, list(S_R), score_tempSI))
                                        break
                                    indx2 += 1
                                break  # out of first while

                            else:
                                tempSI = list(S_I)
                                tempSI.remove(self.l)
                                if len(S_I) == 1:
                                    scoreS_I = self.S_gs_Dict[S_I[0]]
                                else:
                                    scoreS_I = 0

                                self.Q.append((list(S_I), list(S_R), scoreS_I))
                                self.Q.append((tempSI, list(S_R), 0))
                                break
                        else:
                            break

                locText = ""
                for loc in self.S:
                    loc = str(loc).replace("(", "").replace(")", "").strip()
                    locText = locText + loc + "\n"
                self.createFile("E:\\NurProjectPython\\PycharmProjects\\All\\NurLocationSelection\\finalSetTS.txt", locText)

                elapsed_time_fl = (time.time() - start)
                print("Elapsed Time: ", elapsed_time_fl)

    def calcAdvTermOnTotalScore(self, S_I_copy, S_R_copy):
        del_s_max = max([self.S_gs_Dict[loc] for loc in S_R_copy])
        listBestDivScoreTemp = []
        for loc in S_R_copy:
            divOfOneLocToSetSI = min([self.dictOfDgsFromFileAndFlyNewLatest(loc, l) for l in S_I_copy])
            listBestDivScoreTemp.append(divOfOneLocToSetSI)
        delDash_d_max = max(listBestDivScoreTemp)
        scoreSI = self.calcTotalScoreofSet(S_I_copy)
        totalScoreTerminateBoundLower = round((self.k - len(S_I_copy))*(self.theta*del_s_max + (1 - self.theta)*delDash_d_max) + scoreSI, 2)
        return totalScoreTerminateBoundLower

    def calcAdvTermLowerBound(self, S_I_copy, S_R_copy):
        S_gs_SI = sum([self.S_gs_Dict[loc] for loc in S_I_copy])
        del_s_max = max([self.S_gs_Dict[loc] for loc in S_R_copy])
        listBestDivScoreTemp = []
        for loc in S_R_copy:
            divOfOneLocToSetSI = min([self.dictOfDgsFromFileAndFlyNewLatest(loc, l) for l in S_I_copy])
            listBestDivScoreTemp.append(divOfOneLocToSetSI)
        delDash_d_max = max(listBestDivScoreTemp)
        del_dblDsh_dTermLower1 = round((self.bestScore - self.theta*(S_gs_SI + del_s_max))/(1-self.theta), 2) - delDash_d_max
        return round(del_dblDsh_dTermLower1, 2)


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

    def calcMaxDist(self, L, ngbrLocCombinedUnique):
        maxDist = 0
        maxDistEachLocAllNgbrs = {}
        for loc in L:
            dtempMax = max([Util.haversineDist(loc, lc) for lc in ngbrLocCombinedUnique])
            maxDistEachLocAllNgbrs[loc] = round(dtempMax, 2)
            #if dtempMax > maxDist:
            #    maxDist = dtempMax
        del ngbrLocCombinedUnique
        return maxDistEachLocAllNgbrs

    def calcMaxD(self, L):
        maxD = 0
        for loc1 in L:
            maxTemp = max([Util.haversineDist(loc1, lc) for lc in L])
            if maxTemp > maxD:
                maxD = maxTemp
        return round(maxD, 2)

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

    def calcRelevanceScore(self, S_sc, S_sp, userId):
        S_gs = {}
        S_gs_Text = ""
        for loc in S_sc.keys():
            if loc in S_sp.keys():
                lId = self.locNameAndLocId[loc]
                score = round((self.alpha*S_sc[loc] + (1-self.alpha)*S_sp[loc]), 2)
                S_gs[loc] = score
                S_gs_Text = S_gs_Text + str(lId) + "\t" + str(loc) + "\t" + str(S_sc[loc]) + "\t" + str(S_sp[loc]) + "\t" + str(score) + "\n"
        self.createFile(os.path.join(self.outputFolder, "RelScore", str(userId) + "_Rel.txt"), S_gs_Text)
        del S_gs_Text
        return S_gs


    def sortDesc(self, dictInput):
        logging.info("Arrange dict w.r.t. descending.")
        sorted_d = Util.sortDictByValueWithKey(dictInput)
        arrangedKeysOnly = [x[0] for x in sorted_d]
        return arrangedKeysOnly #Return list of locations  only


    def calcTotalScoreofSet(self, S):
        if len(S) == 1:
            return self.S_gs_Dict[list(S)[0]]
        if len(S) == 0:
            return 0


        totalSgs = 0
        minDgsTemp = []
        for loc in S:
            totalSgs += self.S_gs_Dict[loc]
            S_setminus = set(S)
            S_setminus.remove(loc)
            for loc2 in S_setminus:
                minDgsTemp.append(self.dictOfDgsFromFileAndFlyNewLatest(loc, loc2))  # *********************************************
        minDgsSet = min(minDgsTemp)
        totalscore = self.theta * totalSgs + (1 - self.theta) * minDgsSet
        return round(totalscore, 2)


    def dictOfDgsFromFileAndFlyNewLatest(self, loc1_Q, loc2_Q):
        if loc1_Q in self.locAndIndex and loc2_Q in self.locAndIndex:
            loc1_Index = self.locAndIndex.index(loc1_Q)
            loc2_Index = self.locAndIndex.index(loc2_Q)
            if len(self.twoDArray) >= loc1_Index:
                tempValDgs = self.twoDArray[loc1_Index][loc2_Index]
                return float(tempValDgs)
        else:
            print("locations are not available in self.locAndIndex list")
            return 0

    def createFile(self, fileNameFullPath, contents):
        try:
            fw_fileName = open(fileNameFullPath, "w", encoding="utf8")
            fw_fileName.write(contents.__str__())
            fw_fileName.close()
        except KeyError:
            print("Error while creating file.. ", KeyError)
            pass
obj = FVA()