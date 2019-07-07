import json
import numpy as np
import zmq
import multiprocessing
import threading
import pathlib

# ==================================================================== #
class Map:
    def __init__(self, mapFilename):
        self.pathPlanServiceSocketPath = "/run/toponavi/Map/CentralControl.ipc"
        self.pathPlanServiceEndpoint = "ipc://"+self.pathPlanServiceSocketPath
        self.aisleSearchServiceSocketPath = "/run/toponavi/Map/Location.ipc"
        self.aisleSearchServiceEndpoint = "ipc://"+self.aisleSearchServiceSocketPath
        self.map = None

        socketDir = pathlib.Path(self.pathPlanServiceSocketPath).parent
        socketDir.mkdir(parents=True, exist_ok=True)

        with open(mapFilename, "r") as f:
            self.map = json.load(f)
            print("Loading map from "+mapFilename+" complete!")
            # 构建走廊连接节点的邻接矩阵
            self.adjMat = np.full((self.map["ConnectionNodeNum"],self.map["ConnectionNodeNum"]),
                                    float('inf'),
                                    dtype=np.float)# 拓展的两个位置用于存放之后进行路径规划时的起点和终点
            for aisle in self.map["AisleList"]:
                if (aisle["HeadNodeID"] is not None) and (aisle["EndNodeID"] is not None):
                    if self.adjMat[aisle["HeadNodeID"],aisle["EndNodeID"]] == float('inf'):
                        self.adjMat[aisle["HeadNodeID"],aisle["EndNodeID"]] = aisle["Length"]
                        self.adjMat[aisle["EndNodeID"],aisle["HeadNodeID"]] = aisle["Length"]
                    else: # 用于应对两条走廊同头同尾（平行）的情况
                        dist = min(aisle["Length"],self.adjMat[aisle["HeadNodeID"],aisle["EndNodeID"]])
                        self.adjMat[aisle["HeadNodeID"],aisle["EndNodeID"]] = dist
                        self.adjMat[aisle["EndNodeID"],aisle["HeadNodeID"]] = dist
            for i in range(self.adjMat.shape[0]): # 对角线归零
                self.adjMat[i,i] = 0.0
            # print(self.adjMat)
        pass

    def printMap(self):
        print(self.map)

    def saveMap(self, mapFilename): # Save map to .json file
        if self.map is not None:
            with open(mapFilename, "w") as f:
                json.dump(self.map, f)
                print("Save map to "+mapFilename+" complete!")
        pass

    def findPos(self,name):
        for aisle in self.map["AisleList"]:
            for room in aisle["Left"]:
                if room["Name"] == name:
                    return (aisle,room,"L")
            for room in aisle["Right"]:
                if room["Name"] == name:
                    return (aisle,room,"R")
        print("Cannot find room: "+name)
        return None

    def findMarker(self, id):
        targetAisle = None
        for aisle in self.map["AisleList"]:
            if (aisle["HeadMarker"] == id or aisle["EndMarker"] == id):
                targetAisle = aisle
            else:
                for room in aisle["Left"]:
                    if room["ArucoID"] == id:
                        targetAisle = aisle
                if targetAisle is not None:
                    break
                for room in aisle["Right"]:
                    if room["ArucoID"] == id:
                        targetAisle = aisle
        return targetAisle

                

    def planPath(self, staName, desName):
        INF = float('inf')
        staPos = self.findPos(staName)
        desPos = self.findPos(desName)

        staConNode = [staPos[0]["HeadNodeID"],staPos[0]["EndNodeID"]]
        desConNode = [desPos[0]["HeadNodeID"],desPos[0]["EndNodeID"]]
        # print("staConNode",staConNode)
        # print("desConNode",desConNode)
        if (staPos is not None) and (desPos is not None):
            # 从原始邻接矩阵初始化本次路径规划用邻接矩阵
            adjMat = self.adjMat.copy()
            idxStaVex = self.map["ConnectionNodeNum"]
            idxDesVex = idxStaVex+1
            ins = np.full((2,adjMat.shape[0]),INF)
            adjMat = np.insert(adjMat, idxStaVex, values=ins, axis=0) # 在原adjMat增加两行
            ins = np.full((2,adjMat.shape[0]),INF)
            adjMat = np.insert(adjMat, idxStaVex, values=ins, axis=1) # 增加两列
            adjMat[idxStaVex,idxStaVex] = adjMat[idxDesVex,idxDesVex] = 0
            nVex = adjMat.shape[0]
            if staConNode[0] is not None:
                adjMat[idxStaVex,staConNode[0]] = staPos[1]["Distance"]
                adjMat[staConNode[0],idxStaVex] = staPos[1]["Distance"]
            if staConNode[1] is not None:
                adjMat[idxStaVex,staConNode[1]] = staPos[0]["Length"] - staPos[1]["Distance"]
                adjMat[staConNode[1],idxStaVex] = staPos[0]["Length"] - staPos[1]["Distance"]
            if desConNode[0] is not None:
                adjMat[idxDesVex,desConNode[0]] = desPos[1]["Distance"]
                adjMat[desConNode[0],idxDesVex] = desPos[1]["Distance"]
            if desConNode[1] is not None:
                adjMat[idxStaVex,desConNode[1]] = desPos[0]["Length"] - desPos[1]["Distance"]
                adjMat[desConNode[1],idxStaVex] = desPos[0]["Length"] - desPos[1]["Distance"]
            # print("adjMat\n",adjMat)

            minDistList = adjMat[idxStaVex].copy()
            dVexList = [] # deactivate vextexs，已确认最短路径的Vex列表
            dVexList.append(idxStaVex)
            pathList = [ [idxStaVex] for n in range(nVex)]
            path = []
            while len(dVexList)<nVex:
                minDist = INF
                aVex = -1 # Activative Vextex，当前离源点最近的结点
                temp = None
                for idxVex in range(nVex):
                    if idxVex in dVexList: continue
                    if minDist > minDistList[idxVex]:
                        minDist = minDistList[idxVex]
                        aVex = idxVex
                pathList[aVex].append(aVex)
                # print("aVex",aVex)
                dVexList.append(aVex)
                # print("dVexList",dVexList)
                # 松弛操作
                temp = adjMat[aVex].copy()+minDistList[aVex]
                # print("temp",temp)
                temp[aVex] = INF # 把节点自身到自身的距离设为INF，方便接下来更新minDistList
                for i in range(minDistList.shape[0]):
                    if temp[i] < minDistList[i]:
                        minDistList[i] = temp[i]
                        pathList[i] = pathList[aVex].copy()
                # print("minDistList",minDistList)
                # print("pathList",pathList)
            if minDistList[idxDesVex] != INF:
                # pathList[idxDesVex][0] = staPos[1]["ArucoID"]
                # pathList[idxDesVex][-1] = desPos[1]["ArucoID"]
                nodeSeq = pathList[idxDesVex] # 确定最后的路径点（路口）序列
                # return (minDistList[idxDesVex],pathList[idxDesVex])

            inAngle = 0
            outAngle = 0
            direction = 0
            turn = 0
            # path = [{"flag":"mk","value":staPos[1]["ArucoID"]}]
            path = []
            i = 1
            nextMk = 0
            nextAisle = staPos[0]
            while i < len(nodeSeq)-1:
                # get +/-
                if nodeSeq[i] == nextAisle["EndNodeID"]:
                    direction = 1
                    nextMk = nextAisle["EndMarker"]
                else:
                    direction = -1
                    nextMk = nextAisle["HeadMarker"]

                # path.append({"flag":"dirc", "value":direction})
                path.append(direction)
                # path.append({"flag":"dist", "value":adjMat[nodeSeq[i-1], nodeSeq[i]]})
                # path.append({"flag":"mk", "value":nextMk})
                path.append(nextMk)

                # get turning angle in Connection Node
                if nextAisle["HeadNodeID"] == nodeSeq[i]: inAngle = nextAisle["HeadDirection"]
                else: inAngle = nextAisle["EndDirection"]
                # get next aisle
                # print(nodeSeq[i])
                # print(nodeSeq[i+1])
                if i < len(nodeSeq)-2:
                    for aisle in self.map["AisleList"]:
                        if aisle["HeadNodeID"] == nodeSeq[i]:
                            if aisle["EndNodeID"] == nodeSeq[i+1]:
                                nextAisle = aisle
                                outAngle = aisle["HeadDirection"]
                                nextMk = aisle["HeadMarker"]
                        elif aisle["EndNodeID"] == nodeSeq[i]:
                            if aisle["HeadNodeID"] == nodeSeq[i+1]:
                                nextAisle = aisle
                                outAngle = aisle["EndDirection"]
                                nextMk = aisle["EndMarker"]
                else:
                    nextAisle = desPos[0]
                    if nextAisle["HeadNodeID"] == nodeSeq[i]:
                        outAngle = nextAisle["HeadDirection"]
                        nextMk = nextAisle["HeadMarker"]
                    else:
                        outAngle = nextAisle["EndDirection"]
                        nextMk = nextAisle["EndMarker"]
                # print("NextAisle", nextAisle["AisleName"])
                turn = outAngle - inAngle
                if turn > 180: turn -= 360
                elif turn < -180: turn += 360
                # path.append({"flag":"turn", "value":turn})
                path.append(turn)
                # path.append({"flag":"mk", "value":nextMk})
                path.append(nextMk)
                i+=1

            # Now the robot has been the room, next job is how to get in
            if nextAisle["HeadMarker"] == nextMk: direction = 1
            else: direction = -1
            # path.append({"flag":"dirc", "value":direction})
            path.append(direction)
            # path.append({"flag":"dist", "value":adjMat[nodeSeq[i-1], nodeSeq[i]]})
            # path.append({"flag":"mk", "value":desPos[1]["ArucoID"]})
            nextMk = desPos[1]["ArucoID"]
            path.append(nextMk)
            if desPos[2] == "L":
                if direction == 1: turn = -90
                else: turn = 90
            if desPos[2] == "R":
                if direction == 1: turn = 90
                else: turn = -90
            # path.append({"flag":"turn", "value":turn})
            path.append(turn)
            result = {"path":[]}
            result["path"] = path
            return result
        pass

    def aisleSearchService(self):
        ctx = zmq.Context()
        repSocket = ctx.socket(zmq.REP)
        repSocket.bind(self.aisleSearchServiceEndpoint)
        while True:
            reqInfo = repSocket.recv_json()
            aisle = self.findMarker(reqInfo["id"])
            unit = {"id":aisle["HeadMarker"], "dist":0.0}
            repDict = {"list":[unit]}
            for room in aisle["Left"]:
                unit["id"] = room["ArucoID"]
                unit["dist"] = room["Distance"]
                repDict["list"].append(unit)
            for room in aisle["Right"]:
                unit["id"] = room["ArucoID"]
                unit["dist"] = room["Distance"]
                repDict["list"].append(unit)
            unit["id"] = aisle["EndMarker"]
            unit["dist"] = aisle["Length"]
            repSocket.send_json(repDict)

    def pathPlanService(self):
        ctx = zmq.Context()
        repSocket = ctx.socket(zmq.REP)
        repSocket.bind(self.pathPlanServiceEndpoint)
        while True:
            topic, staName, desName = repSocket.recv_multipart()
            # topic.decode()
            staName = staName.decode()
            desName = desName.decode()
            print("REQ receive: "+staName+" to "+desName)
            path = self.planPath(staName, desName)

            repSocket.send_json(path)

    def main(self):
        aisleSearchThread = threading.Thread(target=self.aisleSearchService)
        pathPlanThread = threading.Thread(target=self.pathPlanService)
        aisleSearchThread.start()
        pathPlanThread.start()

    def run(self):
        mainProcess = multiprocessing.Process(target=self.main)
        mainProcess.start()

if __name__ == "__main__":
    map = Map("map.json")
    # print("========Path Calc=========")
    # print(map.findPath("Room2","Room3"))
    # path=map.planPath("Room1","Room5")
    # f = open("path.json","w")
    # json.dump(path,f)
    # print(type(path))
    # print(path)
    map.main()
    pass
