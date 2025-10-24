
<p align="center">
  <H2>Memory Management 3.6.7 for the GPU Poor by DeepBeepMeep</H2>	
</p>


This module contains multiples optimisations so that models such as Flux (and derived), Mochi, CogView, HunyuanVideo, ...  can run smoothly on a 12 to 24 GB GPU limited card. 
This a replacement for the accelerate library that should in theory manage offloading, but doesn't work properly with models that are loaded / unloaded several
times in a pipe (eg VAE).

Requirements:
- VRAM: minimum 6 GB, recommended 24 GB (RTX 3090/ RTX 4090) 
- RAM: minimum 24 GB, recommended 48 GB 

This module features 5 profiles in order to able to run the model at a decent speed on a low end consumer config (24 GB of RAM and 6 VRAM) and to run it at a very good speed (if not the best) on a high end consumer config (48 GB of RAM and 24 GB of VRAM).\
These RAM requirements are for Linux systems. Due to different memory management Windows will require an extra 16 GB of RAM to run the corresponding profile.

Each profile may use a combination of the following: 
- Low RAM consumption (thanks to a rewritten safetensors library) that allows low RAM on the fly quantization
- Smart automated loading / unloading of models in the GPU to avoid unloading models that may be needed again soon
- Smart slicing of models to reduce memory occupied by models in the VRAM
- Ability to pin models to reserved RAM to accelerate transfers to VRAM
- Async transfers to VRAM to avoid a pause when loading a new slice of a model
- Automated on the fly quantization or ability to load pre quantized models
- Pretrained Lora support with low RAM requirements
- Support for pytorch compilation on Linux and WSL (supported on pure Windows but requires a complex Triton Installation).

## Sample applications that use mmgp
It is recommended to have a look at these applications to see how mmgp was implemented in each of them:
- Wan2GP: https://github.com/deepbeepmeep/Wan2GP :\
An excellent text to video and image to video generator that supports the best Open Source Video Architectures: Wan, Hunyuan and LTX Video

- Hunyuan3D-2GP: https://github.com/deepbeepmeep/Hunyuan3D-2GP :\
A great image to 3D and text to 3D tool by the Tencent team. Thanks to mmgp it can run with less than 6 GB of VRAM

- HuanyuanVideoGP: https://github.com/deepbeepmeep/HunyuanVideoGP :\
One of the best open source Text to Video generator

- FluxFillGP: https://github.com/deepbeepmeep/FluxFillGP :\
One of the best inpainting / outpainting tools based on Flux that can run with less than 12 GB of VRAM.

- Cosmos1GP: https://github.com/deepbeepmeep/Cosmos1GP :\
This application include two models: a text to world generator and a image / video to world (probably the best open source image to video generator).

- OminiControlGP: https://github.com/deepbeepmeep/OminiControlGP :\
A Flux derived application very powerful that can be used to transfer an object of your choice in a prompted scene. With mmgp you can run it with only 6 GB of VRAM.

- YuE GP: https://github.com/deepbeepmeep/YuEGP :\
A great song generator (instruments + singer's voice) based on prompted Lyrics and a genre description. Thanks to mmgp you can run it with less than 10 GB of VRAM without waiting forever.

## Installation
First you need to install the module in your current project with:
```shell
pip install mmgp
```


## Usage 

It is almost plug and play and just needs to be invoked from the main app just after the model pipeline has been created.
1) First make sure that the pipeline explictly loads the models in the CPU device, for instance:
```
  pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16).to("cpu")
```

2) Once every potential Lora has been loaded and merged, add the following lines for a quick setup:
```
  from mmgp import offload, profile_type
  offload.profile(pipe, profile_type.HighRAM_LowVRAM_Fast)
```

You can choose between 5 profiles depending on your hardware:
- HighRAM_HighVRAM  (1): at least 48 GB of RAM and 24 GB of VRAM : the fastest well suited for a RTX 3090 / RTX 4090 but consumes much more VRAM, adapted for fast shorter video or small batches of pictures
- HighRAM_LowVRAM  (2): at least 48 GB of RAM and 12 GB of VRAM : a bit slower, better suited for RTX 3070/3080/4070/4080 or for RTX 3090 / RTX 4090 with large pictures batches or long videos
- LowRAM_HighVRAM  (3): at least 32 GB of RAM and 24 GB of VRAM : adapted for RTX 3090 / RTX 4090 with limited RAM  but at the cost of VRAM (shorter videos / fewer images)
- LowRAM_LowVRAM  (4): at least 32 GB of RAM and 12 GB of VRAM :  if you have little VRAM or want to generate longer videos / more images
- VerylowRAM_LowVRAM  (5): at least 24 GB of RAM and 10 GB of VRAM : if you don't have much it won't be fast but maybe it will work

Profile 2 (High RAM) and 4 (Low RAM) are the most recommended profiles since they are versatile (support for long videos for a slight performance cost).\
If you use Flux derived applciation profile 1 and 3 will offer much faster generation times.
In any case, a safe approach is to start from profile 5 (default profile) and then go down progressively to profile 4 and then to profile 2 as long as the app remains responsive or doesn't trigger any out of memory error.

By default the model named 'transformer' will be quantized to 8 bits for all profiles. If you don't want that you may specify the optional parameter *quantizeTransformer = False*.

Every parameter set automatically by a profile can be overridden with one or multiple parameters accepted by *offload.all* (see below):
```
  from mmgp import offload, profile_type
  offload.profile(pipe, profile_type.HighRAM_LowVRAM, budgets = 1000)
```
If you want to know which parameter are set by one specific profile you can use the parameter *verboseLevel=2*

**It is highly recommended to put the *from mmgp import offload, profile_type* at the top of your main python file (that is as the first import) so that all the existing safetensors calls are redirected to mmpg.**
 

## Alternatively you may want to create your own profile with specific parameters:

For example:
```
  from mmgp import offload
  offload.all(pipe, pinnedMemory=True, ExtraModelsToQuantize = ["text_encoder_2"] )
```  
- pinnedMemory: Boolean (for all models) or List of models ids to pin to RAM. Every model pinned to RAM will load much faster (up to 2 times) but this requires more RAM
- quantizeTransformer: boolean by default True. The 'transformer' model in the pipe contains usually the video or image generator is by defaut; quantized on the fly by default to 8 bits. If you want to save time on disk and reduce the loading time, you may want to load directly a prequantized model. If you don't want to quantize the image generator, you need to set the option *quantizeTransformer* to *False* to turn off on the fly quantization.
- extraModelsToQuantize: list of additional modelids of models to quantize on the fly. If the corresponding model is already quantized, this option will be ignored.
- budgets: either a number in mega bytes,  (for all models, if 0 unlimited budget) a string that is perecentage of the total VRAM or a dictionary that maps model ids to mega bytes : define the approximate budget in mega bytes that is allocated in  VRAM for a model. Try not to allocate all the available VRAM so that the rest can be used to process the data. To define the default value in the dictionary, you may add entry named "*".
The smaller this number, the more VRAM left for image data / longer video but also the slower because there will be lots of loading / unloading between the RAM and the VRAM. If model is too big to fit in a budget, it will be broken down in multiples parts that will be unloaded / loaded consequently. The speed of low budget can be  increased (up to 2 times) by turning on the options pinnedMemory and asyncTransfers.
- workingVRAM: either a number in mega bytes, a string that is perecentage of the total VRAM or a dictionary that maps a model ids to a number in mega bytes that corresponds to a minimum amount of VRAM that should be left for the data processed by the model. This number will prevail if it is in conflict with a too high budget defined for the same model.
- asyncTransfers: boolean, load to the GPU the next model part while the current part is being processed. This requires twice the budget if any is defined. This may increase speed by 20% (mostly visible on fast modern GPUs).
- verboseLevel: number between 0 and 2 (1 by default), provides various level of feedback of the different processes
- compile: list of model ids to compile, may accelerate up x2 depending on the type of GPU. It makes sense to compile only the model that is frequently used such as the "transformer" model in the case of video or image generation. Compilation requires Triton to be installed. Triton is available out of the box on Linux or WSL but requires to be installed with Windows: https://github.com/woct0rdho/triton-windows
- coTenantsMap: a dictionary that maps a model id to a list of other models with which it accepts to share the VRAM at the same time. This is useful to avoid unefficient loading / unloading when two models processes are interleaved. For instance *coTenantsMap = { "text_encoder_2": ["text_encoder"] }* , here when *text_encoder_2* is loaded it won't unload *text_encoder*. Please note that the reverse is not true as these maps by design are not symetrical to allow tailored workflows. If you need to have as well *text_encoder* that won't unload *text_encoder_2* if it is already loaded *coTenantsMap = { "text_encoder_2": ["text_encoder"], "text_encoder": ["text_encoder_2"] }*

If you are short on RAM and plan to work with quantized models, it is recommended to load pre-quantized models direclty rather than using on the fly quantization, it will be faster and consume slightly less RAM.
 
##  Going further

The module includes several tools to package a light version of your favorite video / image generator:
- *extract_models(string prefix,  obj to explore)*\
This tool will try to detect for you models that are embedded in a pipeline or in some custom class. It will save you time by building a pipe dictionary required by *offload.all* or "offload.profile*. The prefix correponds to the text that will appear before the name of each model in the dictionary.

- *load_loras_into_model(model, lora_path, lora_multi, activate_all_loras = True)*\
Load in a model a list of Lora described by a list of path *lora_path* and a list of *weights coefficients*.
The Lora file must be in the *diffusers* format. This function works also on non diffusers models. However if there is already an official Lora support for a model it is recommended to use the official diffusers functions. By default all the load loras will be activated or they can be activated later using *activate_loras*.

-*activate_loras(model, lora_nos, lora_multi = None )*\
Activate the loras whose nos are in the list of nos. Every lora that is not this list and that was activated previously will be disactivated.

- *save_model(model, file_path, do_quantize = False, quantizationType = qint8 )*\
Save tensors of a model already loaded in memory in a safetensor format (much faster to reload). You can save it in a quantized format (default qint8 quantization recommended).
The resulting safetensor file will contain extra fields in its metadata such as the quantization map and its configuration, so you will be able to move the file around without files such as *config.json* or *file_map.json*.
You will need *load_model_data* or *fast_load_transformers_model* to read the file again . You may also load it using the default *safetensor* librar however you will need to provide in the same directory any complementary file that are usually requested (for instance *config.json*)

- *load_model_data(model, file_path: str, do_quantize = False, quantizationType = qint8, pinToRAM = False, partialPin = False)*\
Load the tensors data of a model in RAM of a model already initialized with no data. Detect and handle quantized models saved previously with *save_model*.A model can also be quantized on the fly while being loaded. The model which is loaded can be pinned to RAM while it is loaded, this is more RAM efficient than pinning tensors later using *offline.all* or *offline.profile*

- *fast_load_transformers_model(model_path: str, do_quantize = False, quantizationType = qint8, pinToRAM = False, partialPin = False)*\
Initialize (build the model hierarchy in memory) and fast load the corresponding tensors of a 'transformers' or 'diffusers' library model.
The advantages over the original *from_pretrained* method is that a full model can fit into a single file with a filename of your choosing (thefore you can have multiple 'transformers' versions of the same model in the same directory) and prequantized models are processed in a transparent way. 
Last but not least, you can also on the fly pin to RAM the whole model or the most important part of it (partialPin = True) in a more efficient way (faster and requires less RAM) than if you did through *offload.all* or *offload.profile*.


The typical workflow wil be:
1) temporarly insert the *save_model* function just after a model has been fully loaded to save a copy of the model / quantized model.
2) replace the full initalizing / loading logic with *fast_load_transformers_model* (if there is a *from_pretrained* call to a transformers object) or only the tensor loading functions (*torch.load_model_file* and *torch.load_state_dict*) with *load_model_data after* the initializing logic.

## Special cases
Sometime there isn't an explicit pipe object as each submodel is loaded separately in the main app. If this is the case, you may try to use *extract_models* or create a dictionary that manually maps all the models.\
For instance :


- for flux derived models: 
```
pipe = { "text_encoder": clip, "text_encoder_2": t5, "transformer": model, "vae":ae }
```
- for mochi: 
```
pipe = { "text_encoder": self.text_encoder, "transformer": self.dit, "vae":self.decoder }
```


Please note it is recommended to have always one model whose Id is 'transformer' so that you can leverage predefined profiles. The 'transformer' corresponds to the main image / video model which usually needs to be quantized (this is done on the fly by default when loading the model).

Be careful, lots of models use the T5 XXL as a text encoder. However, quite often their corresponding pipeline configurations point at the official Google T5 XXL repository 
where there is a huge 40GB model to download and load. It is cumbersorme as it is a 32 bits model and contains the decoder part of T5 that is not used. 
I suggest you use instead one of the 16 bits encoder only version available around, for instance:
```
text_encoder_2 = T5EncoderModel.from_pretrained("black-forest-labs/FLUX.1-dev", subfolder="text_encoder_2", torch_dtype=torch.float16)
```

Sometime just providing the pipe won't be sufficient as you will need to change the content of the core model: 
- For instance you may need to disable an existing CPU offload logic that already exists (such as manual calls to move tensors between cuda and the cpu)
- mmpg to tries to fake the device as being "cuda" but sometimes some code won't be fooled and it will create tensors in the cpu device and this may cause some issues.

You are free to use my module for non commercial use as long you give me proper credits. You may contact me on twitter @deepbeepmeep

Thanks to
---------
- Huggingface / accelerate for the hooking examples
- Huggingface / quanto for their very useful quantizer
- gau-nernst for his Pinnig RAM samples
