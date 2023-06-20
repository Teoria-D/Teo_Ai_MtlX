#実装したいもの一覧
#参照したmtlxファイル名をもとにaistandardsurfaceに名前をつける
#textureフォルダがない場合にエラーを吐くのでフォルダが無くてもマテリアル生成できるように処理フローを変更

import xml.etree.ElementTree as ET
import pymel.core as pm
import os
import maya.cmds as mc
import maya.mel as mel
import math

def createMaterial():
  # createMaterialでファイルパス取得
    file_path = getFilePath()

    # ファイルパスから整形
    file_attributes = searchAtt(file_path)

    # テクスチャパスの取得
    tex_path = getTexPath(file_path)
    
    # テクスチャのパスリスト作成
    textures = makeNodes(tex_path)

    # テンプレート作成
    ai_name = makeTemplate(textures)

    # マテリアルに割り当てる
    setMatAtt(ai_name, file_attributes)       
 

def getFilePath():
    file_path = cmds.fileDialog2(fileFilter="Mtlx Files (*.mtlx)", dialogStyle=2, fileMode=1)
    return file_path      
    
def find_input_children(element, parent_name):
    inputs = []
    for parent in element.iter(parent_name):
        for child in parent.findall("./input[@value]"):
            inputs.append(child)
    return inputs

def searchAtt(file_path):
    file_name = file_path[0].split('/')[-1] 
    extension = ".mtlx"
    text = file_name
    mat_name = text.replace(extension, "")

    if not file_path:
        print("No materialx file selected.")
    else:
        tree = ET.parse(file_path[0])
        root = tree.getroot()
    
    file_attributes = find_input_children(root,'standard_surface')
    
    result = {
      "name":[],
      "value":[]
    }
    
    
    for element in file_attributes:
        result['name'].append(element.attrib['name'])
        result['value'].append(element.attrib['value'])

        
    return result
    
           
def getTexPath(file_path):
    try:
        tex_path = os.path.join(os.path.dirname(file_path[0]), 'textures')
    except Exception as exception:
        return ""
    
    return tex_path

            
def makeNodes(tex_path):
    if not tex_path:
        print("textures folder does not exist.")
    else:
        textures = []
        for filename in os.listdir(tex_path):
            textures.append(os.path.join(tex_path, filename))
    return textures
    

def makeTemplate(textures):
    
    ai_name = pm.shadingNode('aiStandardSurface', asShader=True)
    sgname = pm.sets(renderable=True, noSurfaceShader=True, empty=True)
    pm.connectAttr(ai_name + '.outColor', sgname + '.surfaceShader', f=True)
    
        
    for i in range(len(textures)):
        if('Base' in textures[i] or 'base' in textures[i]):
            basename = fileNode()
            p2dname1 = p2dNode()
            pm.setAttr(basename + '.fileTextureName',textures[i])
            pm.connectAttr(basename + '.outColor', ai_name + '.baseColor', f=True)
            pm.connectAttr(p2dname1 + '.outUV', basename + '.uvCoord', f=True)
        elif('Roughness' in textures[i] or 'roughness' in textures[i]):
            roughname = fileNode()
            p2dname2 = p2dNode()
            pm.setAttr(roughname + '.fileTextureName',textures[i])
            pm.setAttr(roughname + '.colorSpace',"Raw")
            pm.connectAttr(roughname + '.outAlpha', ai_name + '.specularRoughness', f=True)
            pm.connectAttr(p2dname2 + '.outUV', roughname + '.uvCoord', f=True)
        elif('Metallic' in textures[i] or 'Metalness' in textures[i] or 'metallic' in textures[i]):
            metalname = fileNode()
            p2dname3 = p2dNode()
            pm.setAttr(metalname + '.fileTextureName',textures[i])
            pm.setAttr(metalname + '.colorSpace',"Raw")
            pm.connectAttr(metalname + '.outAlpha', ai_name + '.metalness', f=True)
            pm.connectAttr(p2dname3 + '.outUV', metalname + '.uvCoord', f=True)
        elif('Normal' in textures[i] or 'Normal_OpenGL' in textures[i] or 'normal' in textures[i] or 'Norm' in textures[i]):
            normalname = fileNode()
            p2dname4 = p2dNode()
            bname = pm.shadingNode('bump2d', asUtility=True)
            aibname = pm.shadingNode('aiNormalMap', asUtility=True)
            pm.setAttr(bname + '.bumpInterp',1)
            pm.setAttr(normalname + '.fileTextureName',textures[i])
            pm.setAttr(normalname + '.colorSpace',"Raw")
            pm.connectAttr(normalname + '.outColor', aibname + '.input', f=True)
            pm.connectAttr(p2dname4 + '.outUV', normalname + '.uvCoord', f=True)
            pm.connectAttr(aibname + '.outValue', ai_name + '.normalCamera', f=True)
        elif('Emissive' in textures[i]):
            eminame = fileNode()
            p2dname5 = p2dNode()
            pm.setAttr(eminame + '.fileTextureName',textures[i])
            pm.connectAttr(eminame + '.outAlpha', ai_name + '.emission', f=True)
            pm.connectAttr(p2dname5 + '.outUV', eminame + '.uvCoord', f=True)
        elif('Height' in textures[i] or 'height' in textures[i]):
            disname = fileNode()
            disshader = pm.shadingNode('displacementShader', asShader=True)
            p2dname6 = p2dNode()
            pm.setAttr(disname + '.fileTextureName',textures[i])
            pm.setAttr(disshader + '.scale',0.1)
            pm.connectAttr(p2dname6 + '.outUV', disname + '.uvCoord', f=True)
            pm.connectAttr(disname + '.outAlpha', disshader + '.displacement', f=True)
            pm.connectAttr(disshader + '.displacement', sgname + '.displacementShader', f=True)
            
    return ai_name
        
def fileNode():
    return pm.shadingNode('file', asTexture=True, isColorManaged=True)
    
def p2dNode():
    return pm.shadingNode('place2dTexture', asUtility=True)
    
def setMatAtt(ai_name, file_attributes):
    attribute_names = file_attributes['name']
    convert_value = list(map(safe_float,file_attributes['value']))
    rgbPropertyList = {
        'base_color':'.baseColor',
        'specular_color':'.specularColor',
        'transmission_color':'.transmissionColor',
        'transmission_scatter':'.transmissionScatter',
        'subsurface_color':'.subsurfaceColor',
        'subsurface_radius':'.subsurfaceRadius',
        'sheen_color':'.sheenColor',
        'coat_color':'.coatColor',
        'emission_color':'.emissionColor',
        'opacity':'.opacity'
    }
    lightPropertyList = {
        'base':'.base',
        'metalness':'.metalness',
        'diffuse_roughness':'.diffuseRoughness',
        'specular':'.specular',
        'specular_IOR':'.specular_IOR',
        'specular_anisotropy':'.specularAnisotropy',
        'specular_rotation':'.specularRotation',
        'transmission':'.transmission',
        'transmission_depth':'.transmissionDepth',
        'transmission_scatter_anisotropy':'.transmissionScatterAnisotropy',
        'transmission_dispersion':'.transmissionDispersion',
        'transmission_extra_roughness':'.transmissionExtraRoughness',
        'subsurface':'.subsurface',
        'subsurface_scale':'.subsurfaceScale',
        'subsurface_anisotropy':'.transmissionScatterAnisotropy',
        'sheen':'.sheen',
        'sheen_roughness':'.sheenRoughness',
        'coat':'.coat',
        'coat_roughness':'.coatRoughness',
        'coat_anisotropy':'.coatAnisotropy',
        'coat_rotation':'.coatRotation',
        'coat_IOR':'.coatIOR',
        'coat_affect_color':'.coatAffectColor',
        'coat_affect_roughness':'.coatAffectRoughness',
        'thin_film_thickness':'.thinFilmThickness',
        'thin_film_IOR':'.thinFilmIOR',
        'emission':'.emission'
    }

    
    for i in range(len(convert_value)):
        attribute_name = attribute_names[i]
        if attribute_name in rgbPropertyList:
            setAttrRGB(ai_name, rgbPropertyList[attribute_name], convert_value[i])
        elif attribute_name in lightPropertyList:
            setAttrLight(ai_name, lightPropertyList[attribute_name], convert_value[i])
    
def safe_float(x):
    try:
        return float(x)
    except ValueError:
        return list(x.split(','))
        
def setAttrRGB(ai_name, property_name, attribute_value):
     cmds.setAttr(ai_name + property_name, float(attribute_value[0]), float(attribute_value[1]), float(attribute_value[2]),type='double3')

def setAttrLight(ai_name, property_name, attribute_value):
     cmds.setAttr(ai_name + property_name, float(attribute_value))
    
         
with pm.window(title='autofilenode',width=300,height=50):
    with pm.horizontalLayout():
        pm.frameLayout(label='選択したmtlxファイルのアトリビュートをprintし、テクスチャをaistandardsurfaceに割り当てます',labelAlign='top');
        pm.button(label='MaterialX選択',command='createMaterial()')
        
                    
