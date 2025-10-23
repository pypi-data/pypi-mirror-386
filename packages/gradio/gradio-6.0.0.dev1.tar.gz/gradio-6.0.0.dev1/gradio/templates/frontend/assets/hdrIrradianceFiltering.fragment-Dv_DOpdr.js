import{j as r}from"./index-CeDTB2V5.js";import"./helperFunctions-BAklCeaM.js";import"./hdrFilteringFunctions-DAx8t8En.js";import"./index-CtRY-svv.js";import"./svelte/svelte.js";const e="hdrIrradianceFilteringPixelShader",i=`#include<helperFunctions>
#include<importanceSampling>
#include<pbrBRDFFunctions>
#include<hdrFilteringFunctions>
var inputTextureSampler: sampler;var inputTexture: texture_cube<f32>;
#ifdef IBL_CDF_FILTERING
var icdfTextureSampler: sampler;var icdfTexture: texture_2d<f32>;
#endif
uniform vFilteringInfo: vec2f;uniform hdrScale: f32;varying direction: vec3f;@fragment
fn main(input: FragmentInputs)->FragmentOutputs {var color: vec3f=irradiance(inputTexture,inputTextureSampler,input.direction,uniforms.vFilteringInfo
#ifdef IBL_CDF_FILTERING
,icdfTexture,icdfTextureSampler
#endif
);fragmentOutputs.color= vec4f(color*uniforms.hdrScale,1.0);}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=i);const c={name:e,shader:i};export{c as hdrIrradianceFilteringPixelShaderWGSL};
//# sourceMappingURL=hdrIrradianceFiltering.fragment-Dv_DOpdr.js.map
