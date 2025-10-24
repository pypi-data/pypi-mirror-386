# ------------------ Safetensors2 1.3 by DeepBeepMeep (mmgp)------------------
#
# This module entirely written in Python is a replacement for the safetensor library which requires much less RAM to load models.
# It can be conveniently used to keep a low RAM consumption when handling  transit data (for instance when quantizing or transferring tensors to reserver RAM)
# You are free to use my module for non commercial use as long you give me proper credits. You may contact me on twitter @deepbeepmeep


from typing import Optional, Dict, List, Iterator, Tuple
from pathlib import Path
import torch
import mmap
import struct
import json
import base64
import safetensors
import accelerate
import os
from collections import OrderedDict
import warnings

warnings.filterwarnings("ignore", ".*The given buffer is not writable, and PyTorch does not support non-writable tensors*")

_old_torch_load_file = None
_old_safe_open = None

all_tensors_are_read_only = False 

mmm = {}
verboseLevel = 1

import weakref

_map_to_dtype =  { 'BF16':  torch.bfloat16,  'U8': torch.uint8 , 'U16': torch.uint16, 'U32' : torch.uint32 , 'U64' : torch.uint64,
            'I8': torch.int8, 'I16': torch.int16, 'I32' : torch.int32 , 'I64' : torch.int64, 
            'F64' : torch.float64,  'F32': torch.float32, 'F16': torch.float16, 'BOOL' : torch.bool, "F8_E5M2" : torch.float8_e5m2, "F8_E4M3" : torch.float8_e4m3fn }


class MmapTracker:
    def __init__(self, file_path):
        self._maps = {}
        self._already_released = 0
        from pathlib import Path
        s = Path(file_path).parts
        if len(s)>2: 
            s = s[-2:]
        file_path = os.path.join(*s)
        self.file_path = file_path # os.path.abspath(file_path) 
        self.count = 0
        key = file_path
        i = 1
        while True:
            if key not in mmm:
                mmm[key] = self
                break
            i +=1
            key = key + "#" + str(i)
        self.mmm_key = key
        # print(f"MMAP Add: {file_path}: {mmm.keys()}")

    def register(self, mmap_obj, map_id, start, size):

        self.count += 1
        def finalizer(ref):
            self._already_released += 1
            if verboseLevel >=2:
                if self.count == self._already_released:
                    text =" (all the mmaps have been released)"
                else:
                    text =f" ({self.count-self._already_released:} left)"

                print(f"MMap Manager of file '{self.file_path}' : MMap no {map_id} has been released" + text)
            if self.count == self._already_released:
                # print(f"MMAP Del: {self.file_path}: {mmm.keys()}")
                del mmm[self.mmm_key ]

            self._maps.pop(map_id, None)

        wr = weakref.ref(mmap_obj, finalizer)
        self._maps[map_id] = {
            'mmap' : wr,
            'start': start,
            'size': size,
            'end': start + size
        }
        return wr
       
    def get_active_maps(self):
        return dict(self._maps)

class tensor_slice:
    catalog = None
    value = None
    name = None

    def __init__(self, catalog, name, value):
        self.catalog = catalog
        self.value = value
        self.name = name

    def __getitem__(self, s):
        return self.value[s]
 
    def get_dtype(self):
        return self.catalog[self.name]["dtype"]

    def get_shape(self):
        return self.catalog[self.name]["shape"]

class cached_metadata:
    file_path = None
    file_length = 0
    file_date = None
    catalog = None
    metadata = None
    skip_bytes = 0

    def __init__(self, file_path, catalog, metadata, skip_bytes):
        self.catalog = catalog
        self.metadata = metadata
        self.skip_bytes = skip_bytes
        file_stats = os.stat(file_path)
        self.file_path = os.path.abspath(file_path)
        self.file_length = file_stats.st_size        
        self.file_date = file_stats.st_ctime

    def get_metadata(self, file_path):
        file_stats = os.stat(file_path)
        file_length = file_stats.st_size        
        file_date = file_stats.st_ctime
        file_path = os.path.abspath(file_path)
        if self.file_path != file_path or self.file_length != file_length or self.file_date != file_date:
            return None, None, None
        return self.catalog, self.metadata, self.skip_bytes
        
_cached_entry = None # ideally we should create a dict of the last n entries but one entry covers most cases

def  _parse_metadata(metadata):
    new_metadata= {}
    if metadata != None:
        for k,v in metadata.items():
            if k.endswith("_base64"):
                v_decoded = json.loads(base64.b64decode(v.encode('utf8')).decode('utf8'))
                p = k.rfind("_")
                new_k = k[:p]
                new_metadata[new_k]= v_decoded
            else:
                new_metadata[k] = v
    if "format" not in new_metadata:
        new_metadata["format"] = "pt"
    return new_metadata

def _read_safetensors_header(path, file):
    global _cached_entry
    length_of_header_bytes = file.read(8)
    # Interpret the bytes as a little-endian unsigned 64-bit integer
    length_of_header = struct.unpack('<Q', length_of_header_bytes)[0]

    if _cached_entry != None:
        catalog, metadata, _ = _cached_entry.get_metadata(path)
    else:
        catalog = None

    if catalog == None:
        header_bytes = file.read(length_of_header)
        #catalog = json.loads(header_bytes.decode('utf-8'))
        catalog  = json.loads(header_bytes)
        metadata = catalog.pop("__metadata__", None) 
        metadata = _parse_metadata(metadata)

        _cached_entry = cached_metadata(path, catalog, metadata,length_of_header )        
    else:
        file.seek(length_of_header, 1)
    
    return catalog, metadata, length_of_header + 8

    
def torch_write_file(sd, file_path, quantization_map = None, config = None, extra_meta = None):
    from collections import OrderedDict
    sf_sd = OrderedDict()
 
    map = { torch.bfloat16 : 'BF16'  , torch.int64 : 'I64' , torch.int32 : 'I32' , torch.int16 : 'I16' , torch.int8 : 'I8' , 
           torch.uint64 : 'U64' , torch.uint32 : 'U32' , torch.uint16 : 'U16' , torch.uint8 : 'U8' , 
           torch.bool : 'BOOL' ,  torch.float64 : 'F64' , torch.float32 : 'F32' , torch.float16 : 'F16', torch.float8_e5m2 : "F8_E5M2", torch.float8_e4m3fn: "F8_E4M3" }
    pos = 0
    i = 0
    mx = 100000
    metadata = dict()
    for k , t  in sd.items():
        if torch.is_tensor(t):
            entry = {}
            dtypestr= map[t.dtype]
            entry["dtype"] = dtypestr  
            entry["shape"] = list(t.shape)
            size = torch.numel(t) * t.element_size()
            if size == 0:
                pass
            entry["data_offsets"] = [pos, pos + size]
            pos += size
            sf_sd[k] = entry
        else:
            if isinstance(t, str):
                metadata[k] = t
            else:
                try:
                    b64 = base64.b64encode(json.dumps(t, ensure_ascii=False).encode('utf8')).decode('utf8')
                    metadata[k + "_base64"] = b64 
                except:
                    pass

        i+=1
        if i==mx:
            break
    if not quantization_map is None:
        metadata["quantization_format"] = "quanto"
        metadata["quantization_map_base64"] =  base64.b64encode(json.dumps(quantization_map, ensure_ascii=False).encode('utf8')).decode('utf8')  

    if not config is None:
        metadata["config_base64"] = base64.b64encode(json.dumps(config, ensure_ascii=False).encode('utf8')).decode('utf8')

    if not extra_meta is None:
        for n , m in extra_meta.items():
            if isinstance(m, str):
                metadata[n] = m
            else:
                metadata[n + "_base64"] = base64.b64encode(json.dumps(m, ensure_ascii=False).encode('utf8')).decode('utf8')


    if len(metadata) > 0:
        sf_sd["__metadata__"] = metadata

    header_bytes = json.dumps(sf_sd).encode()
    #header_bytes =json.dumps(config, ensure_ascii=False).encode('utf8')    
    size_header = len(header_bytes)
    import struct

    length_of_header_bytes = struct.pack('<Q', size_header)

    with open(file_path, "wb") as writer:
        bytes_written = writer.write(length_of_header_bytes)        
        bytes_written = writer.write(header_bytes)        

        i = 0
        for k , t  in sd.items():
            if torch.is_tensor(t):
                size = torch.numel(t) * t.element_size()
                if size != 0:
                    dtype = t.dtype
                    # convert in a friendly format, scalars types not supported by numpy
                    if  dtype ==  torch.bfloat16:
                        t = t.view(torch.uint16)
                    elif  dtype ==  torch.float8_e5m2 or dtype ==  torch.float8_e4m3fn:
                        t = t.view(torch.uint8)
                    buffer = t.cpu().numpy().tobytes()
                    bytes_written = writer.write(buffer)            
                    assert bytes_written == size                    
            i+=1
            if i==mx:
                break

class SafeTensorFile:
    """Main class for accessing safetensors files that provides memory-efficient access"""
    
    def __init__(self, file_path, metadata, catalog, skip_bytes, lazy_loading = True, writable_tensors = True):
        self._file_path = file_path
        self._metadata = metadata
        self._catalog = catalog
        self._skip_bytes = skip_bytes
        self._keys = None
        self.sd = None
        self.mtracker = None
        self.lazy_loading = lazy_loading
        self.writable_tensors = writable_tensors

    @classmethod
    def load_metadata(cls, file_path, lazy_loading = True, writable_tensors = True):
        with open(file_path, 'rb') as f:
            catalog, metadata, skip_bytes = _read_safetensors_header(file_path, f)

        return cls(file_path, metadata, catalog, skip_bytes, lazy_loading, writable_tensors )

    def init_tensors(self, lazyTensors = True, writable_tensors = True):
        if self.sd is None:
            self.lazy_loading = lazyTensors
            if lazyTensors:
                self.sd = self.create_tensors_with_mmap(writable_tensors)
            else:
                self.sd = self.create_tensors_without_mmap()
        # else:
        #     if not self.lazy_loading and lazyTensors:
        #         raise Exception("Every tensor should be either lazy loaded or not lazy loaded")

        return self.sd
    
            
    def create_tensors_with_mmap(self, writable_tensors = True):
 
        self.mtracker = MmapTracker(self._file_path)
        import mmap

        PAGE_SIZE =  mmap.ALLOCATIONGRANULARITY 
        MMAP_SIZE = 1024 * 1024 * 1024  # 1GB
        # MMAP_SIZE = 256 * 1024 * 1024  # 1GB

        # First pass: find optimal aligned map boundaries
        skip_bytes = self._skip_bytes
        tensor_map_indexes  = []
        maps_info = []
        current_pos = skip_bytes
        current_map_start = (skip_bytes // PAGE_SIZE) * PAGE_SIZE
        current_map_size = skip_bytes - current_map_start
        idx = 0
        for k,v in self._catalog.items():
            data_offsets = v["data_offsets"]
            length = data_offsets[1]-data_offsets[0]
            if current_map_size + length > MMAP_SIZE:
                maps_info.append((current_map_start, current_map_size))
                current_map_start = (current_pos // PAGE_SIZE) * PAGE_SIZE
                current_map_size = current_pos - current_map_start
                idx += 1
            tensor_map_indexes.append(idx)
            current_map_size += length
            current_pos += length
    
        maps_info.append((current_map_start, current_map_size))
        
        # Second pass: create maps and tensors
        maps = []
        sd = OrderedDict()    
        
        current_pos = skip_bytes
        with open(self._file_path, 'rb') as f:
            i = 0
            for map_start, map_size in maps_info:
                mm = mmap.mmap(f.fileno(), map_size, offset=map_start, access=  mmap.ACCESS_COPY  if writable_tensors else mmap.ACCESS_READ) 
                maps.append((mm, map_start, map_size))
                self.mtracker.register(mm, i, map_start, map_size)
                i = i+ 1

            iter_tensor_no = iter(tensor_map_indexes)
            for k,v in self._catalog.items():
                dtypestr =  v["dtype"]
                dtype= _map_to_dtype[dtypestr]
                shape = v["shape"]
                data_offsets = v["data_offsets"]
                length = data_offsets[1]-data_offsets[0]
                map_idx = next(iter_tensor_no)
                offset = current_pos - maps[map_idx][1]
                if length == 0: 
                    t = torch.empty(shape, dtype=dtype)
                elif len(shape) == 0:
                    # don't waste a memory view for a scalar
                    t = torch.frombuffer(bytearray(maps[map_idx][0][offset:offset + length]), dtype=torch.uint8)
                    t = t.view(dtype)                        
                else:
                    mv = memoryview(maps[map_idx][0])[offset:offset + length]                
                    t = torch.frombuffer(mv, dtype=dtype)
                    t = torch.reshape(t, shape)
                # t._mmap = maps[map_idx][0]
                sd[k] = t
                current_pos += length

        return sd
        

    def create_tensors_without_mmap(self):
        sd = OrderedDict()    
        
        with open(self._file_path, 'rb') as f:
            f.seek(self._skip_bytes, 0)
            for k,v in self._catalog.items():
                dtypestr =  v["dtype"]
                dtype= _map_to_dtype[dtypestr]
                shape = v["shape"]
                data_offsets = v["data_offsets"]
                length = data_offsets[1]-data_offsets[0]
                buffer = f.read(length)
                if length == 0: 
                    t = torch.empty(0, dtype=dtype)
                elif len(shape) == 0:
                    t = torch.frombuffer(bytearray(buffer), dtype=torch.uint8)
                    t = t.view(dtype)                        
                else:
                    t = torch.frombuffer(bytearray(buffer), dtype=dtype)
                    t = torch.reshape(t, shape)
                sd[k] = t
        return sd

    def get_slice(self, name: str) -> torch.tensor:
        return tensor_slice(self._catalog, name, self.get_tensor(name))
    
    def get_tensor(self, name: str) -> torch.tensor:
        """Get a tensor by name"""
        # To do : switch to a JIT tensor creation per tensor
        self.init_tensors(self.lazy_loading, writable_tensors= self.writable_tensors)
        return self.sd[name]
 
    def keys(self) -> List[str]:
        """Get list of tensor names"""
        if self._keys is None:
            self._keys = list(self._catalog)
        return self._keys
        
    def names(self) -> List[str]:
        """Alias for keys()"""
        return self.keys()
        
    def tensors(self) -> Dict[str, torch.tensor]:
        """Get dictionary of all tensors"""
        self.init_tensors(self.lazy_loading, writable_tensors= self.writable_tensors)
        return self.sd
        
    def metadata(self) -> Optional[Dict[str, str]]:
        """Get metadata dictionary"""
        return self._metadata
        
    def __len__(self) -> int:
        """Get number of tensors"""
        self.init_tensors(self.lazy_loading, writable_tensors= self.writable_tensors)
        return len(self.keys())
        
    def __contains__(self, key: str) -> bool:
        """Check if tensor exists"""
        return key in self.keys()
        
    def __iter__(self) -> Iterator[Tuple[str, torch.tensor ]]:
        """Iterate over (name, tensor) pairs"""
        return ((name, self.get_tensor(name)) for name in self.keys())

    def _free_resources(self):
        del self.sd
        del self._catalog 
        
class _SafeTensorLoader:
    """Context manager for loading SafeTensorFile"""
    
    def __init__(self, filename: str, writable_tensors = True ):
        self.filename = Path(filename)
        self.writable_tensors = writable_tensors
        self.sft = None
        if not self.filename.exists():
            raise FileNotFoundError(f"File not found: {filename}")
            
    def __enter__(self) -> SafeTensorFile:
        """Open file and return SafeTensorFile instance"""
        writable_tensors = self.writable_tensors

        if all_tensors_are_read_only:
            writable_tensors = False

        try:
            self.sft = SafeTensorFile.load_metadata(self.filename, writable_tensors= writable_tensors)
            return self.sft 
            
        except Exception as e:
            self.close()
            raise Exception(f"Failed to load safetensors file: {e}") from e
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up resources"""        
        self.close()

    def get_tensor(self, name):
        if self.sft == None:
            self.__enter__()
        return self.sft.get_tensor(name)

    def get_slice(self, name):
        if self.sft == None:
            self.__enter__()
        return self.sft.get_slice(name)

    def close(self) -> None:
        if self.sft != None:
            self.sft._free_resources()
        pass


def safe_open(filename: str, framework: str = "pt",device = "cpu", writable_tensors = True) -> _SafeTensorLoader:
    if device != "cpu" or framework !="pt":
        return _old_safe_open(filename =filename, framework=framework, device=device)
    return _SafeTensorLoader(filename, writable_tensors = writable_tensors)

def torch_load_file( filename, device = 'cpu', writable_tensors = True) -> Dict[str, torch.Tensor]:
    sd = {}
    with safe_open(filename, framework="pt", device = device, writable_tensors =writable_tensors  ) as f:
        for k in f.keys():
            sd[k] = f.get_tensor(k)
        return sd

_old_torch_load_file = safetensors.torch.load_file  
safetensors.torch.load_file = torch_load_file
_old_safe_open = safetensors.safe_open
safetensors.safe_open = safe_open
accelerate.utils.modeling.safe_open = safe_open
accelerate.utils.modeling.safe_load_file = torch_load_file
try:
    import transformers
    transformers.modeling_utils.safe_open = safe_open
    transformers.modeling_utils.safe_load_file = torch_load_file
except:
    pass