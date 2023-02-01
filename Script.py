import sys
import os.path
import pymel.core as pm
import maya.cmds as cm
from pymel.all import *
import maya.api.OpenMaya as om
import PySide2
from PySide2.QtWidgets import QMainWindow, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem

# Return the Maya node which matches the name of the specified rows' "char name"
def GetMayaNodeFromRow(rigList, row):
    charNameItem = rigList.item(row, 0)
    selectionList = om.MSelectionList()
    selectionList.add(charNameItem.text())
    mNode = selectionList.getDependNode(0)
    return mNode

# Scan the scene for root nodes containing the suffix "_Rig" and add them to the table
def ScanScene(rigList, displayText):

    # Filter rigs in the Maya scene
    mScanList = om.MSelectionList()
    try:
        mScanList.add("*_Rig", False)
    except:
        displayText.setText("Info: No root node with the suffix '_Rig'")
        return
    
    # Add rigs to the table
    rowCount = 0
    for i in range(mScanList.length()):
        try:
            rowCount += 1
            rigList.setRowCount(rowCount)
        
            # Setup "Char Name" widget item
            itemOne = QTableWidgetItem()
            itemOne.setText( om.MFnDagNode(mScanList.getDependNode(i)).partialPathName())
            rigList.setItem(rigList.rowCount()-1, 0, itemOne)
        
            # Setup "Display Rep (Rig / Cache)" widget item
            itemTwo = QTableWidgetItem()
            itemTwo.setText("Maya")
            rigList.setItem(rigList.rowCount()-1, 1, itemTwo)
        
            # Setup "Latest Cache" widget item
            itemThree = QTableWidgetItem()
            itemThree.setText("N/A")
            rigList.setItem(rigList.rowCount()-1, 2, itemThree)
        except:
            displayText.setText("Info: Something went wrong when scanning the scene")
    

class MainWindow(QMainWindow):
    #Member Variables
    m_displayText = 0
    m_cacheBtn = 0
    m_swapBtn = 0
    m_rigList = 0
    
    def __init__(self):
        # Setup Main Window
        super().__init__()
        self.setFixedSize(500, 500)
        self.setWindowTitle("SpinVFX Cache System")
                
        # Create Display Text
        self.m_displayText = QTextEdit(self)
        self.m_displayText.setReadOnly(True)
        self.m_displayText.move(10, 460)
        self.m_displayText.setFixedSize(280, 30)
        
        # Create Cache Button
        self.m_cacheBtn = QPushButton("Cache Selection", self)
        self.m_cacheBtn.clicked.connect(self.m_CacheBtnFunc)
        self.m_cacheBtn.move(350, 20)
        
        # Create Swap Button
        self.m_swapBtn = QPushButton("Swap Selection", self)
        self.m_swapBtn.clicked.connect(self.m_SwapBtnFunc)
        self.m_swapBtn.move(350, 60)
        
        # Create Rig List
        self.m_rigList = QTableWidget(0, 3, self)
        self.m_rigList.setFixedSize(320, 200)
        self.m_rigList.setHorizontalHeaderLabels(("Char Name", "Displayed Rep\n (Rig / Chache)", "Latest Cache"))
        self.m_rigList.setShowGrid(True)

        # Scan scene for nodes with the suffix "_Rig"
        ScanScene(self.m_rigList, self.m_displayText)

    # Method triggered on cacheBtn pressed
    def m_CacheBtnFunc(self):

        # Returns if no "Char Name" have been selected in the UI
        if self.m_rigList.currentColumn() != 0:
            return

        # Get selected "Char Name" string
        itemStr = self.m_rigList.currentItem().text()

        # Get row number of the selected "Char Name"
        currentRow = self.m_rigList.currentRow()

        # Disable cache selection button if it's in USD mode
        if self.m_rigList.item(currentRow, 1).text() == "USD":
            self.m_displayText.setText("Info: Cannot cache since " + itemStr + " is in USD mode")
            return
        
        # Get MObject for the root node
        selectedItem = om.MSelectionList()
        try:
            selectedItem.add(itemStr)
        except: # Return if the selecteion is less than 1, ie none found
            self.m_displayText.setText("Info: No node named " + itemStr)
            return

        # Prep version number value
        versionNumberItem = self.m_rigList.item(currentRow, 2)
        versionNumberStr = versionNumberItem.text()

        if versionNumberStr == "N/A":
            versionNumberStr = "000"
        else:
            versionNumberStr = versionNumberStr[1:]
            versionNumberStr = str(int(versionNumberStr) + 1).zfill(len(versionNumberStr))
        
        versionNumberItem.setText("v" + versionNumberStr)

        # Prepare for USD Export
        mDagNode = om.MFnDagNode(selectedItem.getDependNode(0))
        self.m_displayText.setText("Info: " + mDagNode.partialPathName() + " cached to " + "v" + versionNumberStr + " USD")
        
        # Export USD file
        sceneName = cm.file(q=True, sn=True, shn=True)
        if len(sceneName) == 0:
            self.m_displayText.setText("Info: Please save scene before caching")
            return
        scenePath = cm.file(q=True, sn=True)
        cutIndex = len(scenePath) - len(sceneName)
        scenePath = scenePath[0:cutIndex]
        
        path = scenePath + "/anim_caches/" + ""+ mDagNode.partialPathName() + "_anim_cache_v" + str(versionNumberStr) + ".usd"
        options = ";exportUVs=1;exportSkels=none;exportSkin=none;exportBlendShapes=0;exportColorSets=1;defaultMeshScheme=none;defaultUSDFormat=usda;animation=1;eulerFilter=0;staticSingleSample=0;startTime=1;endTime=200;frameStride=1;frameSample=0.0;parentScope=;exportDisplayColor=0;shadingMode=useRegistry;exportInstances=1;exportVisibility=1;mergeTransformAndShape=1;stripNamespaces=0"
        #options = ";exportUVs=1;exportSkels=none;exportSkin=none;exportBlendShapes=0;exportColorSets=1;defaultMeshScheme=none;defaultUSDFormat=usda;animation=1;"
        nodeToExport = pm.ls(mDagNode.partialPathName())
        pm.select(nodeToExport)
        try:
            pm.exportSelected(path, force=True, op=options, type="USD Export", pr=True, es=True)
        except:
            versionNumberItem.setText("N/A")
            self.m_displayText.setText("Info: Failed to cache " + mDagNode.partialPathName())
        
        pm.select(nodeToExport, deselect=True)
        
    # Method triggered on swapBtn pressed
    def m_SwapBtnFunc(self):

        # Returns if no "Char Name" have been selected in the UI
        if self.m_rigList.currentColumn() != 0:
            return

        # Get row number of the selected "Char Name"
        currentRow = self.m_rigList.currentRow()

        # Get all column items and strings for the selected row
        currCharNameStr = self.m_rigList.item(currentRow, 0).text()
        currDispRef = self.m_rigList.item(currentRow, 1)
        currVersionStr = self.m_rigList.item(currentRow, 2).text()

        # Returns if there isn't a USD file
        if currVersionStr == "N/A":
            self.m_displayText.setText("Info: Version is N/A, please cache the geometry first")
            return

        if currDispRef.text() == "Maya":    # If the selected object is in Maya mode
            # Import latest cached rig
            sceneName = cm.file(q=True, sn=True, shn=True)
            scenePath = cm.file(q=True, sn=True)
            cutIndex = len(scenePath) - len(sceneName)
            scenePath = scenePath[0:cutIndex]
            
            path = scenePath + "/anim_caches/" + currCharNameStr + "_anim_cache_" + currVersionStr + ".usd"
            if os.path.isfile(path):
                options = ";shadingMode=[[none,default]];preferredMaterial=none;primPath=/;readAnimData=1;useCustomFrameRange=0;startTime=0;endTime=200;importUSDZTextures=0"
                cm.file(path, r=True, type="USD Import", ignoreVersion=True, mergeNamespacesOnClash=False, op=options, pr=True )   # Creates the "anim_caches"-folder if it doesn't exist
            else:
                self.m_displayText.setText("Info: No cached USD file found")
                return  # Returns if the file doesn't exist

            # Hide maya rig
            pm.hide(pm.ls(om.MFnDagNode(GetMayaNodeFromRow(self.m_rigList, currentRow)).partialPathName()))

            # Set Display Ref to "USD"
            currDispRef.setText("USD")

            # Update info text
            self.m_displayText.setText("Info: " + currCharNameStr + " swapped to " + currVersionStr + " USD cache")

            return
            
        elif currDispRef.text() == "USD":   # If the selected object is in USD mode
            # Delete USD rig
            mDagNode = om.MFnDagNode(GetMayaNodeFromRow(self.m_rigList, currentRow))
            
            node = pm.ls(mDagNode.partialPathName() + "1")[0]
            pm.select(node)
            refPath = pm.referenceQuery(node, f=True)
            cm.file(refPath, removeReference=True)

            # Show Maya rig
            pm.showHidden(pm.ls(mDagNode.partialPathName()))

            # Set Display Ref to "Maya"
            currDispRef.setText("Maya")

            # Update info text
            self.m_displayText.setText("Info: " + currCharNameStr + " swapped to " + currVersionStr + " Maya")

            return

        return

mainWindow = MainWindow()
mainWindow.show()