from __future__ import annotations
import usdex.rtx._usdex_rtx
import typing
import pxr.Gf
import pxr.Sdf
import pxr.Usd
import pxr.UsdShade
import pxr.Vt
import usdex.core._usdex_core

__all__ = [
    "addDiffuseTextureToPbrMaterial",
    "addMetallicTextureToPbrMaterial",
    "addNormalTextureToPbrMaterial",
    "addOpacityTextureToPbrMaterial",
    "addOrmTextureToPbrMaterial",
    "addRoughnessTextureToPbrMaterial",
    "computeEffectiveMdlSurfaceShader",
    "createMdlShader",
    "createMdlShaderInput",
    "defineGlassMaterial",
    "definePbrMaterial"
]


def addDiffuseTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add a diffuse texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Note:
        The material prim's "Color" input will be removed and replaced with "DiffuseTexture".
        Due to the input removal this function should be used at initial authoring time rather than in a stronger layer.

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def addMetallicTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add a metallic texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Note:
        The material prim's "Metallic" input will be removed and replaced with "MetallicTexture".
        Due to the input removal this function should be used at initial authoring time rather than in a stronger layer.

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def addNormalTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add a normal texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def addOpacityTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add an Opacity texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Note:
        The material prim's "Opacity" input will be removed and replaced with "OpacityTexture".
        Due to the input removal this function should be used at initial authoring time rather than in a stronger layer.

    These shader parameters will be set to produce better masked geometry:
    - MDL OmniPBR: ``opacity_threshold = float_epsilon`` (just greater than zero)
    - UsdPreviewSurface: ``ior = 1.0``
    - UsdPreviewSurface: ``opacityThreshold = float_epsilon`` (just greater than zero)

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def addOrmTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add an ORM texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Note:
        The material prim's "Roughness" and "Metallic" inputs will be removed and replaced with "ORMTexture".
        Due to the input removal this function should be used at initial authoring time rather than in a stronger layer.

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def addRoughnessTextureToPbrMaterial(material: pxr.UsdShade.Material, texturePath: pxr.Sdf.AssetPath) -> bool:
    """
    Add a roughness texture to a PBR material

    It is expected that the material was created by ``usdex.rtx.definePbrMaterial()``.

    Note:
        The material prim's "Roughness" input will be removed and replaced with "RoughnessTexture".
        Due to the input removal this function should be used at initial authoring time rather than in a stronger layer.

    Args:
        material: The UsdShade.Material prim to add the texture
        texturePath: The Sdf.AssetPath for the texture

    Returns:
        Whether or not the texture was added to the material
    """
def computeEffectiveMdlSurfaceShader(material: pxr.UsdShade.Material) -> pxr.UsdShade.Shader:
    """
    Get the effective surface Shader of a Material for the MDL render context.

    If no valid Shader is connected to the MDL render context then the universal render context will be considered.

    Args:
        material: The Material to consider

    Returns:
        The connected Shader. Returns an invalid object on error.
    """
def createMdlShader(material: pxr.UsdShade.Material, name: str, mdlPath: pxr.Sdf.AssetPath, module: str, connectMaterialOutputs: bool = True) -> pxr.UsdShade.Shader:
    """
    Create a UsdShade.Shader as a child of the UsdShade.Material argument with the specified MDL

    Args:
        material: Parent UsdShade.Material for the shader to be created
        name: Name of the shader to be created
        mdlPath: Absolute or relative path to the MDL asset
        module: Name of the MDL module to set as source asset sub-identifier for the shader
        connectMaterialOutputs: If true, it creates the surface, volume and displacement outputs of the material and connects them to the shader output
    Returns:
        the newly created UsdShade.Shader. Returns an Invalid prim on error.
    """
def createMdlShaderInput(material: pxr.UsdShade.Material, name: str, value: pxr.Vt.Value, typeName: pxr.Sdf.ValueTypeName, colorSpace: typing.Optional[usdex.core._usdex_core.ColorSpace] = None) -> pxr.UsdShade.Input:
    """
    Create an MDL shader input

    If the shader input already exists and is a different type, defined in the current edit target layer -> it will be removed and recreated

    If the shader input already exists and has a connected source -> the source will be disconnected before being set

    Note:
        When creating texture asset inputs (diffuse, normal, roughness, etc.) it is important to set the colorSpace parameter so that
        the textures are sampled correctly.  Typically, diffuse is "auto", which resolves to "sRGB".  Normal, roughness, and other textures
        should be "raw".

    Args:
        material: The UsdShade.Material prim that contains the MDL shader
        name: Name of the input to be created
        value: The value assigned to the input
        typeName: The Sdf.ValueTypeName of the input
        colorSpace: If set, the newly created input's colorSpace attribute

    Returns:
        The newly created Usd.Shade.Input input.  Returns an Invalid Usd.Shade.Input on error.
    """
@typing.overload
def defineGlassMaterial(stage: pxr.Usd.Stage, path: pxr.Sdf.Path, color: pxr.Gf.Vec3f, indexOfRefraction: float = 1.4910000562667847) -> pxr.UsdShade.Material:
    """
    Defines a Glass ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context.

    The resulting Material prim will have "Interface" ``UsdShade.Inputs`` which drive both render contexts. See
    `UsdShadeNodeGraph <https://openusd.org/release/api/class_usd_shade_node_graph.html#UsdShadeNodeGraph_Interfaces>`_ for explanations
    of Interfaces.

    Note:
        The use of MDL shaders inside this Material interface is considered an implementation detail of the RTX Renderer.
        Once the RTX Renderer supports OpenPBR or MaterialX shaders we may change the implementation to author those shaders instead of MDL.

    Parameters:
        - **stage** - The stage on which to define the Material
        - **path** - The absolute prim path at which to define the Material
        - **color** - The color of the Material
        - **indexOfRefraction** - The Index of Refraction to set, 1.0-4.0 range

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error



    Defines a Glass ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context.

    This is an overloaded member function, provided for convenience. It differs from the above function only in what arguments it accepts.

    Parameters:
        - **parent** - Prim below which to define the Material
        - **name** - Name of the Material
        - **color** - The color of the Material
        - **indexOfRefraction** - The Index of Refraction to set, 1.0-4.0 range

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error



    Defines a Glass ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context.

    This is an overloaded member function, provided for convenience. It differs from the above function only in what arguments it accepts.

    Parameters:
        - **prim** - Prim to define the Material on
        - **color** - The color of the Material
        - **indexOfRefraction** - The Index of Refraction to set, 1.0-4.0 range

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error
    """
@typing.overload
def defineGlassMaterial(parent: pxr.Usd.Prim, name: str, color: pxr.Gf.Vec3f, indexOfRefraction: float = 1.4910000562667847) -> pxr.UsdShade.Material:
    pass
@typing.overload
def defineGlassMaterial(prim: pxr.Usd.Prim, color: pxr.Gf.Vec3f, indexOfRefraction: float = 1.4910000562667847) -> pxr.UsdShade.Material:
    pass
@typing.overload
def definePbrMaterial(stage: pxr.Usd.Stage, path: pxr.Sdf.Path, color: pxr.Gf.Vec3f, opacity: float = 1.0, roughness: float = 0.5, metallic: float = 0.0) -> pxr.UsdShade.Material:
    """
    Defines a PBR ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context.

    The resulting Material prim will have "Interface" ``UsdShade.Inputs`` which drive both render contexts. See
    `UsdShadeNodeGraph <https://openusd.org/release/api/class_usd_shade_node_graph.html#UsdShadeNodeGraph_Interfaces>`_ for explanations
    of Interfaces.

    Note:

        The use of MDL shaders inside this Material interface is considered an implementation detail of the RTX Renderer.
        Once the RTX Renderer supports OpenPBR or MaterialX shaders we may change the implementation to author those shaders instead of MDL.

    Parameters:
        - **stage** - The stage on which to define the Material
        - **path** - The absolute prim path at which to define the Material
        - **color** - The diffuse color of the Material
        - **opacity** - The Opacity Amount to set, 0.0-1.0 range where 1.0 = opaque and 0.0 = invisible.
          Enable Opacity is set to true and Fractional Opacity is enabled in the RT renderer
        - **roughness** - The Roughness Amount to set, 0.0-1.0 range where 1.0 = flat and 0.0 = glossy
        - **metallic** - The Metallic Amount to set, 0.0-1.0 range where 1.0 = max metallic and 0.0 = no metallic

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error



    Defines a PBR ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context

    This is an overloaded member function, provided for convenience. It differs from the above function only in what arguments it accepts.

    Parameters:
        - **parent** - Prim below which to define the Material
        - **name** - Name of the Material
        - **color** - The diffuse color of the Material
        - **opacity** - The Opacity Amount to set. When less than 1.0, Enable Opacity is set to true and Fractional Opacity is enabled in the RT renderer
        - **roughness** - The Roughness Amount to set, 0.0-1.0 range where 1.0 = flat and 0.0 = glossy
        - **metallic** - The Metallic Amount to set, 0.0-1.0 range where 1.0 = max metallic and 0.0 = no metallic

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error



    Defines a PBR ``UsdShade.Material`` interface that drives both an RTX render context and the universal render context

    This is an overloaded member function, provided for convenience. It differs from the above function only in what arguments it accepts.

    Parameters:
        - **prim** - Prim to define the Material on
        - **color** - The diffuse color of the Material
        - **opacity** - The Opacity Amount to set. When less than 1.0, Enable Opacity is set to true and Fractional Opacity is enabled in the RT renderer
        - **roughness** - The Roughness Amount to set, 0.0-1.0 range where 1.0 = flat and 0.0 = glossy
        - **metallic** - The Metallic Amount to set, 0.0-1.0 range where 1.0 = max metallic and 0.0 = no metallic

    Returns:
        The newly defined UsdShade.Material. Returns an Invalid prim on error
    """
@typing.overload
def definePbrMaterial(parent: pxr.Usd.Prim, name: str, color: pxr.Gf.Vec3f, opacity: float = 1.0, roughness: float = 0.5, metallic: float = 0.0) -> pxr.UsdShade.Material:
    pass
@typing.overload
def definePbrMaterial(prim: pxr.Usd.Prim, color: pxr.Gf.Vec3f, opacity: float = 1.0, roughness: float = 0.5, metallic: float = 0.0) -> pxr.UsdShade.Material:
    pass
