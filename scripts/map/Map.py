import json
import numpy as np
# ==================================================================== #
# class Room:
    def __init__(self, arucoID, name=None):
        self.name = name
        self.arucoID = arucoID # a int obj for ARUCO marker ID
        pass


# ==================================================================== #
# class Aisle:
    def __init__(self, arucoIDs, name=None):
        '''
        Args:
            arucoIDs: a tuple(HeadArucoID, EndArucoID)
        '''        
        self.name = name
        self.arucoIDs = arucoIDs
        self.roomList = [] # a list of dict{'RoomObj', 'DistanceToHead'}
        pass
    
    def findRoom(self, roomName):
        for room in self.roomList:
            if room["RoomObj"].name == roomName:
                return i["RoomObj"]
        return None


# ==================================================================== #
# class ConNode:
    def __init__(self, name):
        self.name = name
        pass


# ==================================================================== #
class Map:
    def __init__(self, mapFilename):
        self.map = None
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

    '''
    def loadMap(self, mapFilename): # Load map from .json file
        with open(self, mapFilename,"r") as f:
            self.map = json.load(f)
            print("Loading map from "+mapFilename+" complete!")   
        pass
    '''

    def saveMap(self, mapFilename): # Save map to .json file
        if self.map is not None:
            with open(mapFilename, "w") as f:
                json.dump(self.map, f)
                print("Save map to "+mapFilename+" complete!")
        pass

def findPos(map,name):
    for aisle in map.map["AisleList"]:
        for room in aisle["Left"]:
            if room["Name"] == name:
                return (aisle,room,0)                
        for room in aisle["Right"]:
            if room["Name"] == name:
                return (aisle,room,1)
    print("Cannot find room: "+name)
    return None

def planPath(map, staName, desName):
    '''
    Args:
        sta: string
        des: string
    '''
    INF = float('inf') 
    staPos = findPos(map,staName)
    desPos = findPos(map,desName)
    # print("staPos",staPos)
    # print("desPos",desPos)
    staConNode = [staPos[0]["HeadNodeID"],staPos[0]["EndNodeID"]]
    desConNode = [desPos[0]["HeadNodeID"],desPos[0]["EndNodeID"]]
    print("staConNode",staConNode)
    print("desConNode",desConNode)
    if (staPos is not None) and (desPos is not None): 
        # 从原始邻接矩阵初始化本次路径规划用邻接矩阵
        adjMat = map.adjMat.copy()
        idxStaVex = map.map["ConnectionNodeNum"]
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
            pathList[idxDesVex][0] = "STA"
            pathList[idxDesVex][-1] = "DES"
            return (minDistList[idxDesVex],pathList[idxDesVex])
    pass

if __name__ == "__main__":
    map = Map("map.json")
    # map.printMap()
    # print(type(map.map))
    # target = map.findRoom("Room1")
    # print("Aisle: ", target[0])
    # print("Distance to Head: ",target[1]["Distance"])
    print("========Path Calc=========")
    # print(map.findPath("Room2","Room3"))
    print(planPath(map,"Room1","Room5"))
    pass