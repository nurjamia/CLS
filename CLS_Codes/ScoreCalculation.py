#This method is to calculate various scores related to location group selection task.
import collections
import os.path
import NurTestingPycharm.UtilNur as Util

class ScoreCalculation:
    def __init__(self):
        print("This method is to calculate various scores related to co-engaged location set selection task.")
        self.dataFlag = 3  # 1 = Gowalla, 2 = Brightkite, 3 = Yelp

        if self.dataFlag == 1:
            print("Going to process Gowalla")
            self.baseFolder = "I:\\ExpDataUDI\\ExperimentFolder\\LOC_Select\\Gowalla"
            self.allCheckinDict = Util.convert_String_Into_Dict2(self, self.baseFolder, "user_allChkIn_location_dict.txt")
            self.user_edge_dict = Util.convert_String_Into_Dict2(self, self.baseFolder, "Gowalla_edges_Dict_clean.txt")

        elif self.dataFlag == 2:
            print("Going to process Brightkite")
            self.baseFolder = "I:\\ExpDataUDI\\ExperimentFolder\\LOC_Select\\Brightkite"
            self.allCheckinDict = Util.convert_String_Into_Dict2(self, self.baseFolder, "user_allChkIn_location_dict.txt")
            self.user_edge_dict = Util.convert_String_Into_Dict2(self, self.baseFolder, "Brightkite_edges_Dict.txt")

        elif self.dataFlag == 3:
            print("Going to process Yelp")
            self.baseFolder = "I:\\ExpDataUDI\\ExperimentFolder\\LOC_Select\\Yelp"
            self.allCheckinDict = Util.convert_String_Into_Dict2(self, self.baseFolder, "user_allChkIn_location_dict.txt")
            self.user_edge_dict = Util.convert_String_Into_Dict2(self, self.baseFolder, "Yelp_edges_Dict.txt")


        scores = self.calcImpScoreOfLoc(self.allCheckinDict, self.user_edge_dict)
        self.createFile(os.path.join(self.baseFolder, "ImpScoreLocEachUserDict.txt"), scores[0])
        self.createFile(os.path.join(self.baseFolder, "LocalScrEchUsrInclNgbrDict.txt"), scores[1])

        self.globalScoreOfLoc(self.allCheckinDict)

    def calcImpScoreOfLoc(self, allCheckinFile, user_edge_dict):
        userLocImpScore = {}
        userNgrbLocImpScore = {}
        for user in allCheckinFile.keys():
            locList = allCheckinFile[user]
            counter = collections.Counter(locList)
            impScoreDictofEachUser = {key: counter[key]/sum(counter.values()) for key in counter.keys()}
            userLocImpScore[user] = impScoreDictofEachUser

            ngbrLocs = []
            if user in user_edge_dict.keys():
                ngbrList = user_edge_dict[user]
                for ngbr in ngbrList:
                    if ngbr in allCheckinFile.keys():
                        ngbrLocs = ngbrLocs + allCheckinFile[ngbr]
                tempList = locList + [x for x in ngbrLocs if (x in locList)] #the locations of user and the same locations checked-in by the neighbors
                counterNew = collections.Counter(tempList)
                impScoreDictofEachUserUsingNgbrs = {key: counterNew[key] / sum(counterNew.values()) for key in counterNew.keys()}
                userNgrbLocImpScore[user] = impScoreDictofEachUserUsingNgbrs
            else:
                print("No social network available. ")
                userNgrbLocImpScore[user] = impScoreDictofEachUser

        return [userLocImpScore, userNgrbLocImpScore]

    def globalScoreOfLoc(self, allCheckinDict):
        allCheckings = []
        for user in allCheckinDict.keys():
            allCheckings = allCheckings + allCheckinDict[user]
        counter = collections.Counter(allCheckings)
        globalScoreLocation = {key: counter[key] / sum(counter.values()) for key in counter.keys()}
        self.createFile(os.path.join(self.baseFolder, "globalScoreLoc.txt"), globalScoreLocation)

    def createFile(self, fileNameFullPath, contents):
        try:
            fw_fileName = open(fileNameFullPath, "w", encoding="utf8")
            fw_fileName.write(contents.__str__())
            fw_fileName.close()
        except KeyError:
            print("Error while creating file.. ", KeyError)
            pass

obj = ScoreCalculation()