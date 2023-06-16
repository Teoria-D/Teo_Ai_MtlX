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
    tex_path = os.path.join(os.path.dirname(file_path[0]), 'textures')
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
        if('Base_color' in textures[i] or 'BaseColor' in textures[i] or 'Base Color' in textures[i] or 'basecolor' in textures[i] or 'base' in textures[i]):
            basename = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            p2dname1 = pm.shadingNode('place2dTexture', asUtility=True)
            pm.setAttr(basename + '.fileTextureName',textures[i])
            pm.connectAttr(basename + '.outColor', ai_name + '.baseColor', f=True)
            pm.connectAttr(p2dname1 + '.outUV', basename + '.uvCoord', f=True)
        elif('Roughness' in textures[i] or 'roughness' in textures[i]):
            roughname = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            p2dname2 = pm.shadingNode('place2dTexture', asUtility=True)
            pm.setAttr(roughname + '.fileTextureName',textures[i])
            pm.setAttr(roughname + '.colorSpace',"Raw")
            pm.connectAttr(roughname + '.outAlpha', ai_name + '.specularRoughness', f=True)
            pm.connectAttr(p2dname2 + '.outUV', roughname + '.uvCoord', f=True)
        elif('Metallic' in textures[i] or 'Metalness' in textures[i] or 'metallic' in textures[i]):
            metalname = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            p2dname3 = pm.shadingNode('place2dTexture', asUtility=True)
            pm.setAttr(metalname + '.fileTextureName',textures[i])
            pm.setAttr(metalname + '.colorSpace',"Raw")
            pm.connectAttr(metalname + '.outAlpha', ai_name + '.metalness', f=True)
            pm.connectAttr(p2dname3 + '.outUV', metalname + '.uvCoord', f=True)
        elif('Normal' in textures[i] or 'Normal_OpenGL' in textures[i] or 'normal' in textures[i] or 'Norm' in textures[i]):
            normalname = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            p2dname4 = pm.shadingNode('place2dTexture', asUtility=True)
            bname = pm.shadingNode('bump2d', asUtility=True)
            aibname = pm.shadingNode('aiNormalMap', asUtility=True)
            pm.setAttr(bname + '.bumpInterp',1)
            pm.setAttr(normalname + '.fileTextureName',textures[i])
            pm.setAttr(normalname + '.colorSpace',"Raw")
            pm.connectAttr(normalname + '.outColor', aibname + '.input', f=True)
            pm.connectAttr(p2dname4 + '.outUV', normalname + '.uvCoord', f=True)
            pm.connectAttr(aibname + '.outValue', ai_name + '.normalCamera', f=True)
        elif('Emissive' in textures[i]):
            eminame = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            p2dname5 = pm.shadingNode('place2dTexture', asUtility=True)
            pm.setAttr(eminame + '.fileTextureName',textures[i])
            pm.connectAttr(eminame + '.outAlpha', ai_name + '.emission', f=True)
            pm.connectAttr(p2dname5 + '.outUV', eminame + '.uvCoord', f=True)
        elif('Height' in textures[i] or 'height' in textures[i]):
            disname = pm.shadingNode('file', asTexture=True, isColorManaged=True)
            disshader = pm.shadingNode('displacementShader', asShader=True)
            p2dname6 = pm.shadingNode('place2dTexture', asUtility=True)
            pm.setAttr(disname + '.fileTextureName',textures[i])
            pm.setAttr(disshader + '.scale',0.1)
            pm.connectAttr(p2dname6 + '.outUV', disname + '.uvCoord', f=True)
            pm.connectAttr(disname + '.outAlpha', disshader + '.displacement', f=True)
            pm.connectAttr(disshader + '.displacement', sgname + '.displacementShader', f=True)
            
    return ai_name
        
    
def safe_float(x):
    try:
        return float(x)
    except ValueError:
        return list(x.split(','))
    
def setMatAtt(ai_name, file_attributes):
    attribute_names = file_attributes['name']
    convert_value = list(map(safe_float,file_attributes['value']))

    
    for i in range(len(convert_value)):
        if('base' == attribute_names[i]):
            cmds.setAttr(ai_name + '.base', convert_value[i])
        if('base_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.baseColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('metalness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.metalness', convert_value[i])
        elif('diffuse_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.diffuseRoughness', convert_value[i])
        elif('specular' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specular', convert_value[i])
        elif('specular_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specularRoughness', convert_value[i])
        elif('specular_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specularColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('specular_IOR' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specularIOR', convert_value[i])
        elif('specular_anisotropy' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specularAnisotropy', convert_value[i])
        elif('specular_rotation' == attribute_names[i]):
            cmds.setAttr(ai_name + '.specularRotation', convert_value[i])
        elif('transmission' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmission', convert_value[i])
        elif('transmission_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('transmission_depth' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionDepth', convert_value[i])
        elif('transmission_scatter' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionScatter', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('transmission_scatter_anisotropy' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionScatterAnisotropy', convert_value[i])
        elif('transmission_dispersion' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionDispersion', convert_value[i])
        elif('transmission_extra_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.transmissionExtraRoughness', convert_value[i])
        elif('subsurface' == attribute_names[i]):
            cmds.setAttr(ai_name + '.subsurface', convert_value[i])
        elif('subsurface_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.subsurfaceColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('subsurface_radius' == attribute_names[i]):
            cmds.setAttr(ai_name + '.subsurfaceRadius', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('subsurface_scale' == attribute_names[i]):
            cmds.setAttr(ai_name + '.subsurfaceScale', convert_value[i])
        elif('subsurface_anisotropy' == attribute_names[i]):
            cmds.setAttr(ai_name + '.subsurfaceAnisotropy', convert_value[i])
        elif('sheen' == attribute_names[i]):
            cmds.setAttr(ai_name + '.sheen', convert_value[i])
        elif('sheen_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.sheenColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('sheen_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.sheenRoughness', convert_value[i])
        elif('coat' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coat', convert_value[i])
        elif('coat_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('coat_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatRoughness', convert_value[i])
        elif('coat_anisotropy' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatAnisotropy', convert_value[i])
        elif('coat_rotation' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatRotation', convert_value[i])
        elif('coat_IOR' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatIOR', convert_value[i])
        elif('coat_affect_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatAffectColor', convert_value[i])
        elif('coat_affect_roughness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.coatAffectRoughness', convert_value[i])
        elif('thin_film_thickness' == attribute_names[i]):
            cmds.setAttr(ai_name + '.thinFilmThickness', convert_value[i])
        elif('thin_film_IOR' == attribute_names[i]):
            cmds.setAttr(ai_name + '.thinFilmIOR', convert_value[i])
        elif('emission' == attribute_names[i]):
            cmds.setAttr(ai_name + '.emission', convert_value[i])
        elif('emission_color' == attribute_names[i]):
            cmds.setAttr(ai_name + '.emissionColor', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
        elif('opacity' == attribute_names[i]):
            cmds.setAttr(ai_name + '.opacity', float(convert_value[i][0]),float(convert_value[i][1]),float(convert_value[i][2]),type='double3')
    
    
         
with pm.window(title='autofilenode',width=300,height=50):
    with pm.horizontalLayout():
        pm.frameLayout(label='選択したmtlxファイルのアトリビュートをprintし、テクスチャをaistandardsurfaceに割り当てます',labelAlign='top');
        pm.button(label='MaterialX選択',command='createMaterial()')
        
                    
