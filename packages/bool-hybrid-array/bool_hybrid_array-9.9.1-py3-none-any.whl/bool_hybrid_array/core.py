from __future__ import annotations
import builtins
import array,bisect,numpy as np
from collections.abc import MutableSequence,Iterable,Generator,Iterator,Sequence
import itertools,copy,sys,math,weakref,random
from functools import reduce
import operator,ctypes,gc,abc,types
from functools import lru_cache
from typing import Union,_GenericAlias
hybrid_array_cache = []
if 'UnionType' in types.__dict__:
    class Union:
        def __getitem__(self,*args):
            return reduce(operator.or_, args)
    Union = Union()
if 'GenericAlias' in types.__dict__:
    _GenericAlias = types.GenericAlias
class ResurrectMeta(abc.ABCMeta,metaclass=abc.ABCMeta):
    def __new__(cls, name, bases, namespace):
        meta_bases = tuple(type(base) for base in bases)
        if cls not in meta_bases:
            meta_bases = (cls,) + meta_bases
        obj = super().__new__(cls, name, bases, namespace)
        super_cls = super(ResurrectMeta, obj)
        super_cls.__setattr__('x',None)
        super_cls.__setattr__('name', name)
        super_cls.__setattr__('bases', bases)
        super_cls.__setattr__('namespace', namespace)
        super_cls.__setattr__('original_dict', dict(obj.__dict__))
        del obj.original_dict["__abstractmethods__"]
        del obj.original_dict["_abc_impl"]
        return obj
    @lru_cache
    def __str__(cls):
        return super().__repr__()[8:][:-2]
    @lru_cache
    def __repr__(cls,detailed = False):
        if detailed:
            name, bases, namespace = cls.name,cls.bases,cls.namespace
            return f'ResurrectMeta(cls = {cls},{name = },{bases = },{namespace = })'
        return str(cls)
    def __del__(cls):
        exec(f"builtins.{cls.__name__} = cls")
        if not sys.is_finalizing():
            print(f'警告：禁止删除常变量：{cls}！')
            raise TypeError(f'禁止删除常变量：{cls}')
    def __hash__(cls):
        return hash(cls.name)
    def __setattr__(cls,name,value):
        if not hasattr(cls, 'x'):
            super().__setattr__(name,value)
            return
        if hasattr(cls, 'name') and cls.name == 'BHA_Bool' and repr(value) in {'T','F'} and name in {'T','F'}:
            super().__setattr__(name,value)
            return
        if hasattr(cls, 'original_dict') and name in cls.original_dict:
            raise AttributeError(f'禁止修改属性：{name}')
        else:
            super().__setattr__(name,value)
    def __delattr__(cls,name):
        if name in cls.original_dict:
            raise AttributeError(f'禁止删除属性：{name}')
        else:
            super().__delattr__(name)
    def __or__(self,other):
        return Union[self,other]
    def __getitem__(self,*args):
        return _GenericAlias(self,args)
    __ror__ = __or__
class BHA_Function(metaclass=ResurrectMeta):
    def __init__(self,v):
        self.data,self.module = v,__name__
    def __call__(self,*a,**b):
        return self.data(*a,**b)
    def __getattr__(self,name):
        return getattr(self.data,name)
    @classmethod
    def string_define(cls, name, text, positional, default):
        param_strs = list(positional)
        param_strs.extend([f"{k}={v!r}" for k, v in default.items()])
        params = ", ".join(param_strs)
        func_code = f"""
def {name}({params}):
    {text}
        """
        local_namespace = {}
        exec(func_code, globals(), local_namespace)
        dynamic_func = local_namespace[name]
        return cls(dynamic_func)
class BoolHybridArray(MutableSequence,Exception,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    class _CompactBoolArray(Sequence,Exception):
        def __init__(self, size: int):
            self.size = size
            self.n_uint8 = (size + 7) >> 3
            self.data = np.zeros(self.n_uint8, dtype=np.uint8)
        def __setitem__(self, index: int | slice, value):
            ctypes_arr = self.data.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            if isinstance(index, slice):
                start, stop, step = index.indices(self.size)
                indices = list(range(start, stop, step))
                if isinstance(value, (list, tuple)):
                    if len(value)!= len(indices):
                        raise ValueError("值的数量与切片长度不匹配")
                    for i, val in zip(indices, value):
                        self._set_single(i, bool(val), ctypes_arr)
                else:
                    val_bool = bool(value)
                    for i in indices:
                        self._set_single(i, val_bool, ctypes_arr)
                self.data = np.ctypeslib.as_array(ctypes_arr, shape=(self.n_uint8,))
                return
            if not (0 <= index < self.size):
                raise IndexError(f"密集区索引 {index} 超出范围 [0, {self.size})")
            self._set_single(index, bool(value), ctypes_arr)
            self.data = np.ctypeslib.as_array(ctypes_arr, shape=(self.n_uint8,))
            self.data = self.data.view()
        def _set_single(self, index: int, value: bool, ctypes_arr):
            uint8_pos = index >> 3
            bit_offset = index & 7
            ctypes_arr[uint8_pos] &= ~(1 << bit_offset) & 0xFF
            if value:
                ctypes_arr[uint8_pos] |= (1 << bit_offset)
        def __getitem__(self, index: int | slice) -> bool | list[bool]:
            if isinstance(index, slice):
                start, stop, step = index.indices(self.size)
                result = []
                for i in range(start, stop, step):
                    uint8_pos = i >> 3
                    bit_offset = i & 7
                    result.append(bool((self.data[uint8_pos] >> bit_offset) & 1))
                return result
            if not (0 <= index < self.size):
                raise IndexError(f"密集区索引 {index} 超出范围 [0, {self.size})")
            uint8_pos = index >> 3
            bit_offset = index & 7
            return bool((self.data[uint8_pos] >> bit_offset) & 1)
        def __len__(self):
            return self.size
        def set_all(self, value: bool):
            ctypes_arr = self.data.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
            length = len(self.data)
            if value:ctypes.memset(ctypes_arr, 0xff, length)
            else:ctypes.memset(ctypes_arr, 0, length)
        def copy(self):
            new_instance = self.__class__(size=self.size)
            new_instance.data = self.data.copy()
            return new_instance
    def __init__(self, split_index: int, size=None, is_sparse=False ,Type:Callable = None,hash_ = True) -> None:
        self.Type = Type if Type is not None else builtins.BHA_Bool
        self.split_index = int(split_index)
        self.size = size or 0
        self.is_sparse = is_sparse
        self.small = self._CompactBoolArray(self.split_index + 1)
        self.small.set_all(not is_sparse)
        self.large = array.array('I') if size < 1<<32 else array.array('Q')
        self.generator = iter(self)
        self.hash_ = hash_
        if hash_:
            global hybrid_array_cache
            hybrid_array_cache = [
                (ref, h) for ref, h in hybrid_array_cache 
                if ref() is not None
            ]
            for ref, existing_hash in hybrid_array_cache:
                existing_array = ref()
                try:
                    if self.size != existing_array.size:
                        continue
                    elif self == existing_array:
                        self._cached_hash = existing_hash
                        return
                except Exception:
                    continue
        new_hash = id(self)
        self._cached_hash = new_hash
        hybrid_array_cache.append((weakref.ref(self), new_hash))
    def __call__(self, func):
        func.self = self
        def wrapper(*args, **kwargs):
            return func(self, *args, **kwargs)
        setattr(self, func.__name__, wrapper)
        return func
    def __hash__(self):
        return self._cached_hash
    def accessor(self, i: int, value: bool|None = None) -> bool|None:
        def _get_sparse_info(index: int) -> tuple[int, bool]:
            pos = bisect.bisect_left(self.large, index)
            exists = pos < len(self.large) and self.large[pos] == index
            return pos, exists
        if value is None:
            if i <= self.split_index:
                return self.small[i]
            else:
                _, exists = _get_sparse_info(i)
                return exists if self.is_sparse else not exists
        else:
            if i <= self.split_index:
                self.small[i] = value
                return None
            else:
                pos, exists = _get_sparse_info(i)
                condition = not value or exists
                if self.is_sparse != condition:
                    self.large.insert(pos, i)
                else:
                    if pos < len(self.large):
                        del self.large[pos]
                return None
    def __getitem__(self, key:int|slice) -> BoolHybridArray:
        if isinstance(key, slice):
            start, stop, step = key.indices(self.size)
            return BoolHybridArr((self[i] for i in range(start, stop, step)),hash_ = self.hash_)
        key = key if key >=0 else key + self.size
        if 0 <= key < self.size:
            return self.Type(self.accessor(key))
        raise IndexError("索引超出范围")
    def __setitem__(self, key: int | slice, value) -> None:
        if isinstance(key, int):
            adjusted_key = key if key >= 0 else key + self.size
            if not (0 <= adjusted_key < self.size):
                raise IndexError("索引超出范围")
            self.accessor(adjusted_key, bool(value))
            return
        if isinstance(key, slice):
            original_size = self.size
            start, stop, step = key.indices(original_size)
            value_list = list(value)
            new_len = len(value_list)
            if step != 1:
                slice_indices = list(range(start, stop, step))
                if new_len != len(slice_indices):
                    raise ValueError(f"值长度与切片长度不匹配：{new_len} vs {len(slice_indices)}")
                for i, val in zip(slice_indices, value_list):
                    self[i] = val
                return
            for i in range(stop - 1, start - 1, -1):
                if i <= self.split_index:
                    if i >= len(self.small):
                        self.small = np.pad(
                            self.small, 
                            (0, i - len(self.small) + 1),
                            constant_values=not self.is_sparse
                        )
                del self[i]
            for idx, val in enumerate(value_list):
                self.insert(start + idx, bool(val))
            return
        raise TypeError("索引必须是整数或切片")
    def __repr__(self) -> str:
        return(f"BoolHybridArray(split_index={self.split_index}, size={self.size}, "
        +f"is_sparse={self.is_sparse}, small_len={len(self.small)}, large_len={len(self.large)})")
    def __delitem__(self, key: int) -> None:
        key = key if key >= 0 else key + self.size
        if not (0 <= key < self.size):
            raise IndexError(f"索引 {key} 超出范围 [0, {self.size})")
        if key <= self.split_index:
            if key >= len(self.small):
                raise IndexError(f"小索引 {key} 超出small数组范围（长度{len(self.small)}）")
            self.small = np.delete(self.small, key)
            self.small = np.append(self.small, not self.is_sparse)
            self.split_index = min(self.split_index, len(self.small) - 1)
        else:
            pos = bisect.bisect_left(self.large, key)
            if pos < len(self.large) and self.large[pos] == key:
                del self.large[pos]
            adjust_pos = bisect.bisect_right(self.large, key)
            for i in range(adjust_pos, len(self.large)):
                self.large[i] -= 1
        self.size -= 1
    def __str__(self) -> str:
        return f"BoolHybridArr([{','.join(map(str,self))}])"
    def insert(self, key: int, value: bool) -> None:
        value = bool(value)
        key = key if key >= 0 else key + self.size
        key = max(0, min(key, self.size))
        if key <= self.split_index:
            if key > len(self.small):
                self.small = np.pad(
                    self.small, 
                    (0, key - len(self.small) + 1),
                    constant_values=not self.is_sparse
                )
            self.small = np.insert(self.small, key, value)
            self.split_index = min(self.split_index + 1, len(self.small) - 1)
        else:
            pos = bisect.bisect_left(self.large, key)
            for i in range(pos, len(self.large)):
                self.large[i] += 1
            if (self.is_sparse and value) or (not self.is_sparse and not value):
                self.large.insert(pos, key)
        self.size += 1
    def __len__(self) -> int:
        return self.size
    def __iter__(self):
        return BHA_Iterator(map(self.__getitem__,range(self.size)))
    def __next__(self):
        return next(self.generator)
    def __contains__(self, value) -> bool:
        for i in range(10):
            if self[random.randint(0,self.size-1)] == value:
                return True
        if not isinstance(value, (bool,np.bool_,self.Type,BHA_bool)):return False
        b = any(1 for i in range(self.small.size>>1) if value==self.small[i] or value==self.small[self.small.size-i-1])
        if value == self.is_sparse:
            return self.large or b
        else:
            return len(self.large) == self.size-self.split_index-1 or b
    def __bool__(self) -> bool:
        return self.size > 0
    def __any__(self):
        return self.count(True)>0
    def __all__(self):
        return self.count(True)==len(self)
    def __eq__(self, other) -> bool:
        if not isinstance(other, (BoolHybridArray, list, tuple, np.ndarray, array.array)):
            return False
        if len(self) != len(other):
            return False
        return all(a == b for a, b in zip(self, other))
    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
    def __and__(self, other) -> BoolHybridArray:
        if type(other) == int:
            other = abs(other)
            other = bin(other)[2:]
        if len(self) != len(other):
            raise ValueError(f"与运算要求数组长度相同（{len(self)} vs {len(other)}）")
        return BoolHybridArr(map(operator.and_, self, other),hash_ = self.hash_)
    def __int__(self):
        if self.size == 0:
            return 0
        return reduce(lambda acc, val: operator.or_(operator.lshift(acc, 1), int(val)),self,0)
    def __or__(self, other) -> BoolHybridArray:
        if type(other) == int:
            other = bin(other)[2:]
        if self.size != len(other):
            raise ValueError(f"或运算要求数组长度相同（{len(self)} vs {len(other)}）")
        return BoolHybridArr(map(operator.or_, self, other),hash_ = self.hash_)
    def __ror__(self, other) -> BoolHybridArray:
        if type(other) == int:
            other = abs(other)
            other = bin(other)[2:]
        return self | other
    def __rshift__(self, other) -> BoolHybridArray:
        arr = BoolHybridArr(self)
        arr >>= other
        return arr
    def __irshift__(self, other) -> BoolHybridArray:
        if int(other) < 0:
            self <<= -other
            return self
        for i in range(int(other)):
            if self.size < 1:
                return self
            self.pop(-1)
        return self
    def __ilshift__(self ,other) -> BoolHybridArray:
        if int(other) < 0:
            self >>= -other
            return self
        if not self.is_sparse:
            self += FalsesArray(int(other))
            self.optimize()
        else:
            self.size += int(other)
        return self
    def __lshift__(self ,other) -> BoolHybridArray:
        if int(other) < 0:
            return self >> -other
        return self+FalsesArray(int(other))
    def __add__(self, other) -> BoolHybridArray:
        arr = self.copy()
        arr += other
        arr.optimize()
        return arr
    def __invert__(self) -> BoolHybridArray:
        return BoolHybridArr(not val for val in self)
    def __rand__(self, other) -> BoolHybridArray:
        if type(other) == int:
            other = bin(other)[2:]
        return self & other
    def __xor__(self, other) -> BoolHybridArray:
        if len(self) != len(other):
            raise ValueError(f"异或运算要求数组长度相同（{len(self)} vs {len(other)}）")
        return BoolHybridArr(map(operator.xor, self, other),hash_ = self.hash_)
    def __rxor__(self, other) -> BoolHybridArray:
        return self^other
    def __invert__(self) -> BoolHybridArray:
        return BoolHybridArr(not a for a in self)
    def copy(self) -> BoolHybridArray:
        arr = BoolHybridArray(split_index = self.split_index,size = self.size)
        arr.large,arr.small,arr.split_index,arr.is_sparse,arr.Type,arr.size = (array.array(self.large.typecode, self.large),self.small.copy(),
        self.split_index,BHA_Bool(self.is_sparse),self.Type,self.size)
        return arr
    def __copy__(self) -> BoolHybridArray:
        return self.copy()
    def find(self,value):
        return BHA_List([i for i in range(len(self)) if self[i]==value])
    def extend(self, iterable:Iterable) -> None:
        if isinstance(iterable, (Iterator, Generator, map)):
            iterable,copy = itertools.tee(iterable, 2)
            len_ = sum(1 for _ in copy)
        else:
            len_ = len(iterable)
        self.size += len_
        for i,j in zip(range(len_),iterable):
            self[-i-1] = j
    def append(self,v):
        self.size += 1
        self[-1] = v
    def index(self, value) -> int:
        if self.size == 0:
            raise ValueError('无法在空的 BoolHybridArray 中查找元素！')
        value = bool(value)
        x = 'not find'
        for i in range(self.size):
            if self[i] == value:
                return i
            if self[-i] == value:
                x = self.size-i
            if len(self)-i == i:
                break
        if x != 'not find':
            return x
        raise ValueError(f"{value} not in BoolHybridArray")
    def rindex(self, value) -> int:
        if self.size == 0:
            raise ValueError('无法在空的 BoolHybridArray 中查找元素！')
        value = bool(value)
        x = 'not find'
        for i in range(self.size):
            if self[-i] == value:
                return -i
            if self[i] == value:
                x = -(self.size-i)
            if len(self)-i == i:
                break
        if x != 'not find':
            return x
        raise ValueError(f"{value} not in BoolHybridArray")
    def count(self, value) -> int:
        value = bool(value)
        return sum(v == value for v in self)
    def optimize(self) -> None:
        arr = BoolHybridArr(self)
        self.large,self.small,self.split_index,self.is_sparse = (arr.large,arr.small,
        arr.split_index,arr.is_sparse)
        gc.collect()
        return self
    def memory_usage(self, detail=False) -> dict | int:
        small_mem = self.small.size // 8 + 32
        large_mem = len(self.large) * 4 + 32
        equivalent_list_mem = 40 + 8 * self.size
        equivalent_numpy_mem = 96 + self.size
        total = small_mem+large_mem
        if not detail:
            return total
        need_optimize = False
        optimize_reason = ""
        sparse_ratio = len(self.large) / max(len(self), 1)
        if sparse_ratio > 0.4 and len(self) > 500:  # 阈值可根据测试调整
            need_optimize = True
            optimize_reason = "稀疏区索引密度过高，优化后可转为密集存储提升速度"
        elif len(self) < 32 and total > len(self):
            need_optimize = True
            optimize_reason = "小尺寸数组存储冗余，优化后将用int位存储进一步省内存"
        elif np.count_nonzero(np.array(self.small)) / max(len(self.small), 1) < 0.05 and len(self) > 1000:
            need_optimize = True
            optimize_reason = "密集区有效值占比过低，优化后可转为稀疏存储节省内存"
        return {
            "总占用(字节)": total,
            "密集区占用": small_mem,
            "稀疏区占用": large_mem,
            "对比原生list节省": f"{(1 - total/equivalent_list_mem)*100:.6f}%",
            "对比numpy节省": f"{(1 - total/equivalent_numpy_mem)*100:.6f}%" if equivalent_numpy_mem > 0 else "N/A",
            "是否需要优化": "是" if need_optimize else "否",
            "优化理由/说明": optimize_reason if need_optimize else "当前存储模式已适配数据特征，无需优化"
        }
    def get_shape(self):
        return (self.size,)
    def __array__(self,dtype = np.bool_,copy = None):
        arr = np.fromiter(map(np.bool_,self), dtype=np.bool_)
        return arr.copy() if copy else arr.view()
    def view(self):
        arr = TruesArray(0)
        arr.__dict__ = self.__dict__
        return arr
class BoolHybridArr(BoolHybridArray,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    def __new__(cls, lst: Iterable, is_sparse=None, Type = None, hash_ = True) -> BoolHybridArray:
        a = isinstance(lst, (Iterator, Generator, map))
        if a:
            lst, copy1, copy2 = itertools.tee(lst, 3)
            size = sum(1 for _ in copy1)
            true_count = sum(bool(val) for val in copy2)
        else:
            size = len(lst)
            true_count = sum(bool(val) for val in lst)
        if size == 0:
            return BoolHybridArray(0, 0, is_sparse=False if is_sparse is None else is_sparse)
        if is_sparse is None:
            is_sparse = true_count <= (size - true_count)
        split_index = int(min(size * 0.8, math.sqrt(size) * 100))
        split_index = math.isqrt(size) if true_count>size/3*2 or true_count<size/3 else max(split_index, 1)
        split_index = int(split_index) if split_index < 150e+7*2 else int(145e+7*2)
        arr = BoolHybridArray(split_index, size, is_sparse, Type, hash_ = F)
        small_max_idx = min(split_index, size - 1)
        if a:
            small_data = []
            large_indices = []
            for i, val in enumerate(lst):
                val_bool = bool(val)
                if i <= small_max_idx:
                    small_data.append(val_bool)
                else:
                    if (is_sparse and val_bool) or (not is_sparse and not val_bool):
                        large_indices.append(i)
            if small_data:
                arr.small[:len(small_data)] = small_data
            if large_indices:
                arr.large.extend(large_indices)
        else:
            if small_max_idx >= 0:
                arr.small[:small_max_idx + 1] = [bool(val) for val in lst[:small_max_idx + 1]]
            large_indices = [
                i for i in range(split_index + 1, size)
                if (is_sparse and bool(lst[i])) or (not is_sparse and not bool(lst[i]))
            ]
            arr.large.extend(large_indices)
        arr.large = sorted(arr.large)
        type_ = 'I' if size < 1 << 32 else 'Q'
        arr.large = array.array(type_, arr.large)
        if hash_:
            global hybrid_array_cache
            hybrid_array_cache = [
                (ref, h) for ref, h in hybrid_array_cache 
                if ref() is not None
            ]
            for ref, existing_hash in hybrid_array_cache:
                existing_array = ref()
                try:
                    if arr.size != existing_array.size:
                        continue
                    elif arr == existing_array:
                        arr._cached_hash = existing_hash
                        return arr
                except Exception:
                    continue
        return arr
def TruesArray(size, Type = None, hash_ = True):
    split_index = min(size//10, math.isqrt(size))
    split_index = max(split_index, 1)
    split_index = int(split_index) if split_index < 150e+7*2 else int(145e+7*2)
    return BoolHybridArray(split_index,size,Type = Type,hash_ = hash_)
def FalsesArray(size, Type = None,hash_ = True):
    split_index = min(size//10, math.isqrt(size))
    split_index = max(split_index, 1)
    split_index = int(split_index) if split_index < 150e+7*2 else int(145e+7*2)
    return BoolHybridArray(split_index,size,True,Type = Type,hash_ = hash_)
Bool_Array = np.arange(2,dtype = np.uint8)
class BHA_bool(int,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    def __new__(cls, value):
        core_value = bool(value)
        instance = super().__new__(cls, core_value)
        instance.data = Bool_Array[1] if core_value else Bool_Array[0]
        instance.value = core_value
        return instance
    @lru_cache
    def __str__(self):
        return 'True' if self else 'False'
    @lru_cache
    def __repr__(self):
        return 'T' if self else 'F'
    @lru_cache
    def __bool__(self):
        return self.value
    @lru_cache
    def __int__(self):
        return int(self.data)
    @lru_cache
    def __or__(self,other):
        return BHA_Bool(self.value|other)
    @lru_cache
    def __and__(self,other):
        return BHA_Bool(self.value&other)
    @lru_cache
    def __xor__(self,other):
        return BHA_Bool(self.value^other)
    def __hash__(self):
        return hash(self.data)
    def __len__(self):
        raise TypeError("'BHA_bool' object has no attribute '__len__'")
    def __del__(self):
        if not sys.is_finalizing():
            print(f'你删除或修改了1个常变量：{repr(self)}！')
            if self:builtins.T = BHA_bool(1)
            else:builtins.F = BHA_bool(0)
            raise TypeError(f'禁止删除或修改常变量{repr(self)}！')
    __rand__,__ror__,__rxor__ = __and__,__or__,__xor__
class BHA_Bool(BHA_bool,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    @lru_cache
    def __new__(cls,v):
        if(builtins.T == True)and(builtins.F == False):
            return builtins.T if v else builtins.F
        else:
            builtins.T,builtins.F = BHA_Bool.T,BHA_Bool.F
            return BHA_Bool.T if v else BHA_Bool.F
class BHA_List(list,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    def __init__(self,arr):
        def Temp(v):
            if isinstance(v,(list,tuple)):
                v = (BoolHybridArr(v) if all(isinstance(i,
                    (bool,BHA_bool,np.bool_)) for i in v)
                     else BHA_List(v))
            if isinstance(v,BoolHybridArray):
                return v
            elif isinstance(v,(bool,np.bool_)):
                return BHA_Bool(v)
            else:
                return v
        super().__init__(map(Temp,arr))
        try:self.hash_value = sum(map(hash,self))
        except Exception as e:return hash(e)
    def __hash__(self):
        return self.hash_value
    def __call__(self, func):
        func.self = self
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        setattr(self, func.__name__, wrapper)
        return wrapper
    def __str__(self):
        def Temp(v):
            if isinstance(v,(BoolHybridArray,np.ndarray,BHA_List,array.array)):
                return str(v)+',\n'
            else:
                return repr(v)+','
        return f"BHA_List([\n{''.join(map(Temp,self))}])"
    def __repr__(self):
        return str(self)
    def __or__(self,other):
        return BHA_List(map(operator.or_, self, other))
    def __and__(self,other):
        return BHA_List(map(operator.and_, self, other))
    def __xor__(self,other):
        return BHA_List(map(operator.xor, self, other))
    def __rxor__(self,other):
        return self^other
    def __ror__(self,other):
        return self|other
    def __rand__(self,other):
        return self&other
    def optimize(self):
        for val in self:
            val.optimize()
    def memory_usage(self,detail=False):
        total = sum(val.memory_usage() for val in self) + 32
        if not detail:
            return total
        else:
            temp = sum(val.size for val in self)
            return {
            "占用(字节)": total,
            "对比原生list节省": f"{(1 - total / (temp * 8 + 40))*100:.6f}%",
            "对比numpy节省": f"{(1 - total / (temp + 96)) * 100:.6f}%"}
    def __iter__(self):
        return BHA_Iterator(super().__iter__())
class BHA_Iterator(Iterator,metaclass=ResurrectMeta):
    __module__ = 'bool_hybrid_array'
    def __init__(self,data):
        self.data,self.copy_data = itertools.tee(iter(data),2)
    def __next__(self):
        try:return next(self.data)
        except Exception as e:
            self.__init__(self.copy_data)
            raise e
    def __iter__(self):
        return self
    def __or__(self,other):
        return BHA_Iterator(map(operator.or_, self, other))
    def __and__(self,other):
        return BHA_Iterator(map(operator.and_, self, other))
    def __xor__(self,other):
        return BHA_Iterator(map(operator.xor, self, other))
    def __array__(self,dtype = np.bool_,copy = None):
        arr = np.fromiter(map(np.bool_,self), dtype=np.bool_)
        return arr.copy() if copy else arr.view()
    __rand__,__ror__,__rxor__ = __and__,__or__,__xor__
class ProtectedBuiltinsDict(dict,metaclass=ResurrectMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.__dict__ = self
            self.builtins = self
            self.__builtins__ = self
        except Exception:
            pass
        self.protected_names = ["T", "F", "BHA_Bool", "BHA_List", "BoolHybridArray", "BoolHybridArr",
                                "TruesArray", "FalsesArray", "ProtectedBuiltinsDict", "builtins",
                                "__builtins__", "__dict__","ResurrectMeta","itertools","copy","sys","math",
                                "weakref","random","array","np","operator","ctypes","types","bisect","protected_names","BHA_Function",
                                "__class__","Iterator","BHA_Iterator","Generator","Union","_GenericAlias"]
    def __setitem__(self, name, value):
        if name in ["T", "F"]:
            current_T = self.get("T")
            current_F = self.get("F")
            if isinstance(current_T, BHA_bool) and isinstance(current_F, BHA_bool):
                is_swap = (name == "T" and isinstance(value, BHA_bool) and value.value == current_F.value)or(name == "F" and isinstance(value, BHA_bool) and value.value == current_T.value)
                if is_swap:
                    print(f"""警告：禁止交换内置常量 __builtins__["{name}"] 和 __builtins__["{'F' if name == 'T' else 'T'}"]！""")
                    raise AttributeError(f"""禁止交换内置常量 __builtins__["{name}"] 和 __builtins__["{'F' if name == 'T' else 'T'}"]""")
        if name in self.protected_names and name not in ["T", "F"]:
            print(f"警告：禁止修改内置常量 __builtins__['{name}']！")
            raise AttributeError(f"禁止修改内置常量 __builtins__['{name}']")
        super().__setitem__(name, value)
    def __delitem__(self, name):
        if name in self.protected_names:
            print(f"警告：禁止删除内置常量 __builtins__['{name}']！")
            raise AttributeError(f"禁止删除内置常量 __builtins__['{name}']")
        if name in self:
            super().__delitem__(name)
    def __delattr__(self, name):
        if name in self.protected_names:
            raise AttributeError(f'禁止删除内置常量：{self.name}.{name}')
        else:
            del self[name]
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"module 'builtins' has no attribute '{name}'")
    def __setattr__(self,name,value):
        try:protected = self.protected_names
        except Exception:protected = self
        if(name in protected)and(not sys.is_finalizing())and(name != '_'):
            raise AttributeError(f'禁止修改内置常量：{self.name}.{name}')
        else:
            super().__setattr__(name,value)
builtins.np = np
builtins.T = BHA_bool(1)
builtins.F = BHA_bool(0)
builtins.BHA_Bool = BHA_Bool
builtins.BHA_List = BHA_List
builtins.FalsesArray =  FalsesArray
builtins.TruesArray = TruesArray
builtins.BoolHybridArr = BoolHybridArr
builtins.BHA_Iterator = BHA_Iterator
builtins.BoolHybridArray = BoolHybridArray
builtins.BHA_Bool.T,builtins.BHA_Bool.F = BHA_bool(1),BHA_bool(0)
builtins.ResurrectMeta = ResurrectMeta
builtins.ProtectedBuiltinsDict = ProtectedBuiltinsDict
builtins.BHA_Function = BHA_Function
Tid,Fid = id(T),id(F)
original_id = builtins.id
def fake_id(obj):
    if isinstance(obj, BHA_bool):return Tid if obj else Fid
    else:return original_id(obj)
builtins.id = fake_id
original_builtins_dict = builtins.__dict__.copy()
__builtins__ = ProtectedBuiltinsDict(original_builtins_dict)
builtins = __builtins__
sys.modules['builtins'] = builtins
builtins.name = 'builtins'
try:
    sys.flags.optimize = 2
except Exception:
    pass