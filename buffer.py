import arcpy
from arcpy.sa import *
import os
import logging
import sys 
#这里只是一个对sys的引用，只能reload才能进行重新加载
stdi,stdo,stde=sys.stdin,sys.stdout,sys.stderr 
reload(sys) 
#通过import引用进来时,setdefaultencoding函数在被系统调用后被删除了，所以必须reload一次
sys.stdin,sys.stdout,sys.stderr=stdi,stdo,stde 
sys.setdefaultencoding('utf-8')

# 根目录
base_dir = "//192.168.1.6/liuyunshu/buffer"
# 点位目录
dir_point = base_dir+"/points"
# 设计观测距离，单位：米
designDistance = 2000
# 缓冲区图层透明度
bufferTransparency = 50

# 项目文件地址
path_project = base_dir + "/buffer_10_3.mxd"
# temp目录
dir_temp = base_dir + "/temp"
# results目录
dir_results = base_dir + "/results"
# temp目录:mxd
# dir_temp_mxd = base_dir + "/temp/buffer_10_3.mxd"
dir_temp_mxd = base_dir + "/buffer_10_3.mxd"
# temp目录:buffer
dir_temp_buffer = base_dir + "/temp/buffer.shp"
# temp目录:buffer2
dir_temp_buffer2 = base_dir + "/temp/buffer2.shp"


# Step0: 预处理
# 查找必要数据
# 输入要素类
# mxd = arcpy.mapping.MapDocument(path_project)
# mxd.saveACopy(dir_temp_mxd)

arcpy.env.workspace = dir_point
try:
    point = arcpy.ListFeatureClasses("","Point")[0]
    print("已找到观测点:" + str(point))
except Exception as result: 
    raise Exception("未找到观测点: %s" % result)

# 清空temp/result目录，避免异常
print("清空temp目录:开始")
arcpy.env.workspace = dir_temp
for tempRaster in arcpy.ListRasters("*", "TIF"):
    try:
        arcpy.Delete_management(tempRaster)
        print("删除"+str(tempRaster))
    except Exception as result: 
        raise Exception("删除%s失败: %s" % (str(tempRaster),result))
for tempFeature in arcpy.ListFeatureClasses():
    try:
        arcpy.Delete_management(tempFeature)
        print("删除"+str(tempFeature))
    except Exception as result: 
        raise Exception("删除%s失败: %s" % (str(tempFeature),result))
print("清空temp目录:完成")

print("清空result目录:开始")
arcpy.env.workspace = dir_results
for tempRaster in arcpy.ListRasters("*", "All"):
    arcpy.management.Delete(tempRaster)
    print("删除"+str(tempRaster))
for tempFeature in arcpy.ListFeatureClasses():
    arcpy.management.Delete(tempFeature)
    print("删除"+str(tempFeature))
print("清空result目录:完成")

# Step1: 生成缓冲区
# 与要缓冲的输入要素之间的距离
distanceField = "distance"
# 指定将在输入要素的哪一侧进行缓冲
sideType = "FULL"
# 指定线输入要素末端的缓冲区形状
endType = "ROUND"
# 指定移除缓冲区重叠要执行的融合类型
dissolveType = "NONE"
# 融合输出缓冲区所依据的输入要素的字段列表
dissolveField = ""
# 指定是使用平面方法还是测地线方法来创建缓冲区
method = "PLANAR"

print("创建设计缓冲区:开始")
buffer = arcpy.Buffer_analysis(os.path.join(dir_point, point), dir_temp_buffer, "%s meters"%(str(designDistance)), sideType, endType,dissolveType, dissolveField,method)
print("创建设计缓冲区:完成")

print("创建方案缓冲区:开始")
buffer2 = arcpy.Buffer_analysis(os.path.join(dir_point, point), dir_temp_buffer2, distanceField, sideType, endType,dissolveType, dissolveField,method)
print("创建方案缓冲区:完成")


# Step3: 绘制专题图
# 查找必要图层并替换数据源
mxd = arcpy.mapping.MapDocument(dir_temp_mxd)
layers = arcpy.mapping.ListLayers(mxd)
for layer in layers:
    if(layer.isServiceLayer):
        print("ServiceLayer:"+layer.name)
    if(layer.isRasterLayer):
        print("RasterLayer:"+layer.name)
        layer.visible = False
    if(layer.isFeatureLayer):
        print("FeatureLayer:"+layer.name)
        if(layer.supports("DATASOURCE") and layer.supports("workspacePath")):
            print("图层dataSource:"+layer.dataSource)
            if(layer.dataSource.endswith(str("points.shp"))):
                lyr_point = layer
            elif(layer.dataSource.endswith(str("buffer.shp"))):
                lyr_buffer = layer
            elif(layer.dataSource.endswith(str("buffer2.shp"))):
                lyr_buffer2 = layer
            else:
                layer.visible = False
if(lyr_point):
    print("找到观测点图层:"+str(lyr_point.dataSource))
    lyr_point.replaceDataSource(lyr_point.workspacePath,"SHAPEFILE_WORKSPACE")
else:
    raise Exception("未找到观测点图层")
if(lyr_buffer):
    print("找到buffer图层:"+str(lyr_buffer.dataSource))
    lyr_buffer.replaceDataSource(lyr_buffer.workspacePath,"SHAPEFILE_WORKSPACE")
    print("设置buffer图层透明度:",bufferTransparency)
    lyr_buffer.transparency = bufferTransparency
else:
    raise Exception("未找到buffer图层")
if(lyr_buffer2):
    print("找到buffer2图层:"+str(lyr_buffer2.dataSource))
    lyr_buffer2.replaceDataSource(lyr_buffer2.workspacePath,"SHAPEFILE_WORKSPACE")
    print("设置buffer2图层透明度:",bufferTransparency)
    lyr_buffer2.transparency = bufferTransparency
else:
    raise Exception("未找到buffer2图层")

try:
    mxd.save()
except Exception as result: 
    raise Exception("项目打开期间无法保存，请新建空白项目运行此脚本: %s" % result)

# 开始导出
print("导出专题图:开始")
mxd = arcpy.mapping.MapDocument(dir_temp_mxd)
layers = arcpy.mapping.ListLayers(mxd)
for layer in layers:
    if(layer.supports("DATASOURCE") and layer.supports("workspacePath")):
        if(layer.dataSource.endswith(str("points.shp"))):
            lyr_point = layer
        if(layer.dataSource.endswith(str("buffer.shp"))):
            lyr_buffer = layer
        if(layer.dataSource.endswith(str("buffer2.shp"))):
            lyr_buffer2 = layer

for pageNum in range(1, mxd.dataDrivenPages.pageCount+1):
    mxd.dataDrivenPages.currentPageID = pageNum
    mapName = mxd.dataDrivenPages.pageRow.getValue(mxd.dataDrivenPages.pageNameField.name)
    if (mxd.dataDrivenPages.pageNameField.type =="Double"):
        sql = '"%s" = %s' %(mxd.dataDrivenPages.pageNameField.name,str(mapName))
    elif (mxd.dataDrivenPages.pageNameField.type =="Integer"):
        sql = '"%s" = %s' %(mxd.dataDrivenPages.pageNameField.name,str(mapName))
    elif (mxd.dataDrivenPages.pageNameField.type =="Single"):
        sql = '"%s" = %s' %(mxd.dataDrivenPages.pageNameField.name,str(mapName))
    elif (mxd.dataDrivenPages.pageNameField.type =="SmallInteger"):
        sql = '"%s" = %s' %(mxd.dataDrivenPages.pageNameField.name,str(mapName))
    else :
        sql = '"%s" = \'%s\'' %(mxd.dataDrivenPages.pageNameField.name,str(mapName))

    lyr_point.definitionQuery = lyr_buffer.definitionQuery = lyr_buffer2.definitionQuery = sql
    print("导出专题图:%s,查询条件为：%s"% (str(mapName),sql))
    arcpy.mapping.ExportToJPEG(mxd, dir_results +"/"+ str(mapName) +".jpg")

print("导出专题图:完成")

# 重置筛选条件
lyr_point.definitionQuery = ""
lyr_buffer.definitionQuery = ""
lyr_buffer2.definitionQuery = ""
mxd.save()
del point,buffer,buffer2,mxd