import torch
import numpy as np
from geomloss import SamplesLoss
from pykeops.torch import LazyTensor
from torch import Tensor
from numpy import ndarray
from typing import Callable, Union, Optional

#Global Parameter
N_min=3

def default_distance_expansion(A, B, KeOps):
    #Expanding the dimensions of two tensors for calculating the matrix of default distance 
    dim=A.dim()
    if KeOps:
        packer=LazyTensor
    else:
        packer=lambda x:x
    if dim == 1:
        A_expand = packer(A[:, None, None])  # (N,1,1)
        B_expand = packer(B[None, :, None])  # (1,M,1)
    elif dim >= 2:
        A_expand = packer(A.unsqueeze(dim-1))  # (..B,N,1,D)
        B_expand = packer(B.unsqueeze(dim-2))  # (..B,1,M,D)
    return A_expand, B_expand

def Euclidean_distance(A, B, KeOps=True, p=1):
    A_expand, B_expand=default_distance_expansion(A, B, KeOps)
    if p==1:
        return ((A_expand - B_expand) ** 2).sum(-1) ** (1 / 2)
    elif p==2:
        return ((A_expand - B_expand) ** 2).sum(-1)/2
    else:
        raise ValueError("The value of 'p' can only be 1 or 2.")

def Manhattan_distance(A, B, KeOps=True):
    A_expand, B_expand=default_distance_expansion(A, B, KeOps)
    return ((A_expand - B_expand).abs()).sum(-1)

def Chebyshev_distance(A, B, KeOps=True):
    A_expand, B_expand=default_distance_expansion(A, B, KeOps)
    return ((A_expand - B_expand).abs()).max(-1)

def W1_deb(x1, x2, w1, w2, eps=0.01):
    loss = SamplesLoss(loss="sinkhorn", p=1, blur=eps, debias=True, scaling=0.9)
    index1=int(x1.shape[-2]/2)
    index2=int(x2.shape[-2]/2)
    dim_batch=len(w1.shape)-1
    idx11=(slice(None),)*dim_batch+(slice(None,index1),)
    idx12=(slice(None),)*dim_batch+(slice(index1,None),)
    idx21=(slice(None),)*dim_batch+(slice(None,index2),)
    idx22=(slice(None),)*dim_batch+(slice(index2,None),)
    x11,x12=x1[idx11],x1[idx12]
    x21,x22=x2[idx21],x2[idx22]
    w11,w12=w1[idx11],w1[idx12]
    w21,w22=w2[idx21],w2[idx22]
    w11=w11/(w11.sum(axis=-1).unsqueeze(-1))
    w12=w12/(w12.sum(axis=-1).unsqueeze(-1))
    w21=w21/(w21.sum(axis=-1).unsqueeze(-1))
    w22=w22/(w22.sum(axis=-1).unsqueeze(-1))
    W_x12_1=loss(w11, x11, w21, x21)
    W_x12_2=loss(w12, x12, w22, x22)
    W_x11=loss(w11, x11, w12, x12)
    W_x22=loss(w21, x21, w22, x22)
    W1_deb=abs(W_x12_1**2/2+W_x12_2**2/2-W_x11**2/2-W_x22**2/2)**(1/2)
    return W1_deb

def W2_deb(x1, x2, w1, w2, eps=0.01):
    loss = SamplesLoss(loss="sinkhorn", p=2, blur=eps**(1/2), debias=True, scaling=0.9**(1/2))
    index1=int(x1.shape[-2]/2)
    index2=int(x2.shape[-2]/2)
    dim_batch=len(w1.shape)-1
    idx11=(slice(None),)*dim_batch+(slice(None,index1),)
    idx12=(slice(None),)*dim_batch+(slice(index1,None),)
    idx21=(slice(None),)*dim_batch+(slice(None,index2),)
    idx22=(slice(None),)*dim_batch+(slice(index2,None),)
    x11,x12=x1[idx11],x1[idx12]
    x21,x22=x2[idx21],x2[idx22]
    w11,w12=w1[idx11],w1[idx12]
    w21,w22=w2[idx21],w2[idx22]
    w11=w11/(w11.sum(axis=-1).unsqueeze(-1))
    w12=w12/(w12.sum(axis=-1).unsqueeze(-1))
    w21=w21/(w21.sum(axis=-1).unsqueeze(-1))
    w22=w22/(w22.sum(axis=-1).unsqueeze(-1))
    W_x12_1=loss(w11, x11, w21, x21)
    W_x12_2=loss(w12, x12, w22, x22)
    W_x11=loss(w11, x11, w12, x12)
    W_x22=loss(w21, x21, w22, x22)
    W2_deb=abs(W_x12_1+W_x12_2-W_x11-W_x22)**(1/2)
    return W2_deb

def directional_derivative(x1, x2, x1_grad, x2_grad):
    x1_,x2_=default_distance_expansion(x1, x2, KeOps=True)
    diff=x1_-x2_
    dis=(diff**2).sum(-1)**(1/2)+1e-9    #For now, only use European distances.
    direction_vector=diff/dis
    if x1_grad is not None and x2_grad is not None:
        x1_grad_,x2_grad_=default_distance_expansion(x1_grad, x2_grad, KeOps=True)
        x1_dir_d=(x1_grad_*direction_vector).sum(-1).abs()
        x2_dir_d=(x2_grad_*direction_vector).sum(-1).abs()
        dir_d=(x1_dir_d.concat(x2_dir_d)).max(-1)
    else:
        if x1_grad is not None:
            dim=x1_grad.dim()
            grad_=LazyTensor(x1_grad.unsqueeze(dim-1)) if dim >= 2 else LazyTensor(x1_grad[:, None, None])
        elif x2_grad is not None:
            dim=x2_grad.dim()
            grad_=LazyTensor(x2_grad.unsqueeze(dim-2)) if dim >= 2 else LazyTensor(x2_grad[None, :, None])
        else:
            raise ValueError("The input values 'x1_grad' and 'x2_grad' cannot both be None.")
        dir_d=(grad_*direction_vector).sum(-1).abs()
    return dir_d

def ensure_no_grad(x, dataname):
    if isinstance(x, Tensor):
        if x.requires_grad:
            return x.detach(),True 
        else:
            return x,False
    elif isinstance(x, ndarray):
        return x,False
    else:
        raise TypeError("'%s' must be an instance of either torch.Tensor or numpy.ndarray."%dataname)

def check_class(x1, x2, y1, y2, weights1, weights2, grad1, grad2):
    requires_grad={}
    x1_,requires_grad["x1"]=ensure_no_grad(x1, "x1")
    x2_,requires_grad["x2"]=ensure_no_grad(x2, "x2")
    y1_,requires_grad["y1"]=ensure_no_grad(y1, "y1")
    y2_,requires_grad["y2"]=ensure_no_grad(y2, "y2")
    if weights1 is None:
        weights1_,requires_grad["weights1"]=None,None
    else:
        weights1_,requires_grad["weights1"]=ensure_no_grad(weights1, "weights1")
    if weights2 is None:
        weights2_,requires_grad["weights2"]=None,None
    else:
        weights2_,requires_grad["weights2"]=ensure_no_grad(weights2, "weights2")
    if grad1 is None:
        grad1_,requires_grad["grad1"]=None,None
    else:
        grad1_,requires_grad["grad1"]=ensure_no_grad(grad1, "grad1")
    if grad2 is None:
        grad2_,requires_grad["grad2"]=None,None
    else:
        grad2_,requires_grad["grad2"]=ensure_no_grad(grad2, "grad2")
    return x1_, x2_, y1_, y2_, weights1_, weights2_, grad1_, grad2_, requires_grad

def check_coupling_format(data1, data2, Dis, axis, N_max, dataname):
    if Dis!="L2":
        #pass
        raise ValueError("Currently the 'Dis_%s' value is only supported for 'L2', other distances will be supported in subsequent releases."%dataname)
    
    if Dis in ["L1","L2","inf"]:
        original_dis=True
    elif isinstance(Dis, Callable):
        original_dis=False
    elif isinstance(Dis, str):
        raise ValueError("Parameter 'Dis_%s'=\'%s\': distance metric is unknown. Built‑in options are 'L1' (Manhattan), 'L2' (Euclidean), and 'inf' (Chebyshev). You can also supply a function handle that takes '%s1' and '%s2' as inputs and returns their distance matrix, allowing a custom metric."%(dataname,Dis,dataname,dataname))
    else:
        raise TypeError("Parameter 'Dis_%s' is an instance of %s: distance metric is unknown. Built‑in options are 'L1' (Manhattan), 'L2' (Euclidean), and 'inf' (Chebyshev). You can also supply a function handle that takes '%s1' and '%s2' as inputs and returns their distance matrix, allowing a custom metric."%(dataname,str(type(Dis)),dataname,dataname))
    
    shape_data1=tuple(data1.shape)
    shape_data2=tuple(data2.shape)
    shape_batch=None
    N_data1=None
    N_data2=None
    if original_dis:
        if len(shape_data1)>=2 and len(shape_data2)>=2 and shape_data1[:-2]==shape_data2[:-2] and shape_data1[-1]==shape_data2[-1]:
            shape_batch=shape_data1[:-2]
            N_data1=shape_data1[-2]
            N_data2=shape_data2[-2]
            if N_data1<N_min or N_data2<N_min:
                raise ValueError("Sample size is too small: '%s1' and '%s2' must each have shape (Batch_size, Num_samples, Dim) or (Num_samples, Dim), and each data set must contain at least the global parameter 'N_min'=%d samples."%(dataname,dataname,N_min))
        else:
            raise ValueError("When a built‑in distance metric is used, '%s1' and '%s2' must each have shape (Batch_size, Num_samples, Dim) or (Num_samples, Dim), and their' 'Batch_size' and 'Dim' must be identical."%(dataname,dataname))
        
        dim=shape_data1[-1]
        if len(shape_batch)>0:
            batchs=(torch.cumprod(torch.tensor(shape_batch),dim=0)).item()
        else:
            batchs=1
        estimated_space=4*min(N_data1,N_max)*min(N_data2,N_max)*dim*batchs
        if torch.cuda.is_available():
            allowed_space=1024**3
            if estimated_space<=allowed_space:
                KeOps=False
            else:
                KeOps=True
        else:
            KeOps=True
    else:
        if axis is None:
            raise ValueError("Parameter 'axis_%s' is unknown: when providing a custom 'Dis_%s', '%s1' and '%s2' must each have shape (Batch_size, Num_samples, Dim1, Dim2..) or (Num_samples, Dim1, Dim2..). Supply 'axis_%s' to specify which axis in the '%s1' and '%s2' corresponds to the 'Num_samples' dimension, so that sampling and indexing work correctly."%(dataname,dataname,dataname,dataname,dataname,dataname,dataname))
        elif not isinstance(axis, int):
            raise TypeError("Parameter 'axis_%s' must be an int."%dataname)
        
        if shape_data1[:axis]==shape_data2[:axis] and shape_data1[axis+1:]==shape_data2[axis+1:]:
            shape_batch=shape_data1[:axis]
            N_data1=shape_data1[axis]
            N_data2=shape_data2[axis]
            if N_data1<N_min or N_data2<N_min:
                raise ValueError("Sample size is too small: '%s1' and '%s2' must each contain at least the global parameter 'N_min'=%d samples."%(dataname,dataname,N_min))
        else:
            raise ValueError("When providing a custom 'Dis_%s', '%s1' and '%s2' must each have shape (Batch_size, Num_samples, Dim1, Dim2..) or (Num_samples, Dim1, Dim2..), and their 'Batch_size' and 'Dim1, Dim2..' must be identical."%(dataname,dataname,dataname))
        
        try:
            idx1=(slice(None),)*axis+(slice(0,N_min),)
            idx2=(slice(None),)*axis+(slice(0,N_min-1),)
            C=Dis(data1[idx1],data2[idx2])
        except Exception as e:
            raise RuntimeError("The function handle provided for 'Dis_%s' raised an error upon receiving '%s1' and '%s2' as inputs."%(dataname,dataname,dataname)) from e
        
        if isinstance(C, Tensor) or isinstance(C, ndarray):
            KeOps=False
        elif isinstance(C, LazyTensor):
            KeOps=True
        else:
            raise TypeError("The function handle provided for 'Dis_%s' must output a an instance of either torch.Tensor, pykeops.torch.LazyTensor, or numpy.ndarray."%dataname)
        
        shape_C=tuple(C.shape)
        if shape_C[:axis]==shape_batch and shape_C[axis:]==(N_min,N_min-1):
            pass
        else:
            raise ValueError("The distance matrix output by the function handle for 'Dis_%s' must have shape (Batch_size, Num_samples_%s1, Num_samples_%s2) or (Num_samples_%s1, Num_samples_%s2), and its 'Batch_size' must be identical to that of '%s1' and '%s2'."%(dataname,dataname,dataname,dataname,dataname,dataname,dataname))
    return shape_batch, N_data1, N_data2, KeOps, original_dis

def shuffling_and_sampling(weights, N ,N_max, shape_batch, generator, verbose, dataname):
    #Use torch.multinomial only if weights is not None and N > N_max; otherwise, use torch.randperm.
    #By default, all index tensors are first placed on the CPU.
    if isinstance(weights, ndarray):
        #If weights is a numpy.ndarray, convert it to a torch.tensor so that sampling can be handled uniformly with torch.multinomial.
        weights_=torch.tensor(weights,dtype=torch.float32,device="cpu")
    else:
        weights_=weights
    if N>N_max:
        sampling=True
        if verbose:
            print("The sample size of (x%s,y%s,w%s) is larger than parameter 'N_max'=%d, sampling strategy is used."%(dataname,dataname,dataname,N_max))
    else:
        sampling=False
    if weights_ is None:
        Index=torch.randperm(N, generator=generator,device="cpu")
        if sampling:
            Index=Index[:N_max]
    else:
        if sampling:
            if len(shape_batch)!=0:
                flat_batch=int(torch.prod(torch.tensor(shape_batch)))
                weights_flat = weights_.reshape(flat_batch, C)
                Index=torch.multinomial(weights_flat, N_max, replacement=False, generator=generator)
                Index=Index.reshape(*shape_batch, N_max)
            else:
                Index=torch.multinomial(weights_, N_max, replacement=False, generator=generator)
            ReIndex=torch.randperm(Index.shape[-1], generator=generator,device=Index.device)
            Index=Index[(slice(None),)*len(shape_batch)+(ReIndex,)]
        else:
            #When weights is not None and N ≤ N_max, additionally verify that the weights are all non‑negative and not all zeros.
            if (weights_.min(axis=-1)[0]>=0).all() and (weights_.max(axis=-1)[0]>0).any():
                pass
            else:
                raise ValueError("The input 'weights%s' must have all elements non‑negative and include at least one positive value."%dataname)
            Index=torch.randperm(N, generator=generator,device=weights_.device)
    #Return a 1‑D tensor or an N‑dimensional tensor.
    return Index

def one_dimension_indexing(data, Index, d):
    if isinstance(data, Tensor):
        if len(Index.shape)==1:
            idx=(slice(None),)*d+(Index.to(data.device),)
            samples=data[idx]
        else:
            samples=torch.gather(data,d,Index.to(data.device))
    else:
        Index_=Index.cpu().numpy()
        if len(Index.shape)==1:
            idx=(slice(None),)*d+(Index_,)
            samples=data[idx]
        else:
            samples=np.take_along_axis(data,Index_,d)
    return samples

def tensorized(data, Cuda):
    if isinstance(data, ndarray):
        return torch.tensor(data, dtype=torch.float32, device="cuda") if Cuda else torch.tensor(data, dtype=torch.float32, device="cpu")
    else:
        return data.to("cuda") if Cuda else data.to("cpu")

def DataShifts(
                x1:Union[Tensor,ndarray], 
                x2:Union[Tensor,ndarray], 
                y1:Union[Tensor,ndarray], 
                y2:Union[Tensor,ndarray], 
                weights1:Union[Tensor,ndarray]=None, 
                weights2:Union[Tensor,ndarray]=None, 
                grad1:Union[Tensor,ndarray]=None, 
                grad2:Union[Tensor,ndarray]=None, 
                P:int=1, 
                eps:float=0.01, 
                N_max:int=5000, 
                device:Optional[str]=None, 
                seed:Optional[int]=None, 
                verbose:bool=True, 
              ):
    r"""
    Compute covariate shift and concept shift between two labeled sample sets.

    This routine estimates, from finite samples, (i) the **covariate shift** in the
    X-space and (ii) the **concept shift** in the Y|X-space between two
    distributions. Covariate shift is computed as the **entropic optimal transport**
    in the feature space; concept shift is computed as the **expected label-space 
    distance under the entropic optimal transport coupling** inferred from dual 
    Sinkhorn potentials. The function supports batching, importance weights, 
    automatic sub-sampling for scalability, and transparent GPU execution.

    Parameters
    ----------
    x1, x2 : torch.Tensor or numpy.ndarray
        Covariate samples from the two domains. Shapes accepted:
        ``(Batch, Num, Dim_x)`` or ``(Num, Dim_x)``. Batch dimensions of `x1` and
        `x2` must match, and their last (feature) dimensions must be equal.
    y1, y2 : torch.Tensor or numpy.ndarray
        Corresponding label samples. Shapes accepted:
        ``(Batch, Num, Dim_y)`` or ``(Num, Dim_y)``. Must match `x*` in both
        ``Batch`` and ``Num``. If the label space is effectively 1-D, a singleton
        dimension is added internally for consistency.
    weights1, weights2 : torch.Tensor or numpy.ndarray, optional
        Optional per-sample weights with shapes ``(Batch, Num)`` or ``(Num,)``.
        If provided, they are validated to be non-negative and are **normalized
        per batch** internally to sum to 1. If omitted, uniform weights are used.
    eps : float, default 0.01
        Entropic regularization for optimal transport; smaller is more faithful but
        slower/noisier, larger is smoother/faster.
    N_max : int, default 5000
        Upper bound on the number of samples retained per domain. If
        ``Num > N_max``, the data are **shuffled** and (weighted) **sub-sampled
        without replacement**. Shuffling is applied even without sub-sampling to 
        avoid group-specific bias.
    device : {"cpu","cuda","gpu"} or None, default None
        Target device. If ``None``, the routine uses CUDA automatically when
        available (and prints a note if all inputs were on CPU).
    seed : int or None, default None
        Random seed for shuffling/sampling. Two independent RNGs are used
        (one per domain) for reproducible yet uncorrelated draws.
    verbose : bool, default True
        Whether to print informative messages (sampling strategy, auto-device).

    Returns
    -------
    covariate_shift : torch.Tensor
        Debiased entropic optimal transport ``W_1^deb(x1,x2)`` in X-space. The tensor has
        shape ``Batch`` (or is a scalar 0-D tensor if there is no batch).
    concept_shift : torch.Tensor
        Expected label-space distance under the optimal coupling. Same shape semantics as above.

    Algorithmic details
    -------------------
    * **Covariate shift** uses a debiased entropic optimal transport (p=1), implemented by
      combining OT costs on random splits to remove entropic bias.
    * **Concept shift** first fits dual potentials (with entropic OT, p=1), turns
      them into a soft coupling ``π* = w1 · exp((g1 − C_x + g2)/eps) · w2``, then
      averages Euclidean distances in Y-space under ``π*``.
    * The routine heuristically selects a **KeOps LazyTensor** backend for large
      problems to control memory, otherwise uses dense tensors on GPU/CPU.

    Notes
    -----
    * **Distance metric:** currently **Euclidean ("L2")** is the only built-in
      metric for both X and Y; hooks for user-defined metrics are in place and will
      be enabled in a future release.
    * **Gradients:** all input gradient tracking is detached; this function is intended for
      measurement/diagnostics rather than backpropagation through OT.
    * **Shapes:** both outputs follow the leading batch dimensions of the inputs.

    Raises
    ------
    TypeError
        If `eps`/`N_max` are non-numeric; if any input is neither a Tensor nor a
        NumPy array; if `verbose` is not bool; or for invalid custom-metric handles.
    ValueError
        If sample counts are below the global minimum; if shapes are inconsistent
        between domains or between X and Y; if weights have negatives or are all 0;
        or if an unsupported distance is requested.
    RuntimeError
        If a user-provided distance function (future pathway) raises during checks.

    Examples
    --------
    >>> covariate_shift, concept_shift = DataShifts(x1, x2, y1, y2, N_max=2048, eps=0.01)
    >>> covariate_shift, concept_shift
    (tensor(..., device='cuda:0'), tensor(..., device='cuda:0'))
    """
    
    #Dis_x:Union[str,Callable]="L2", 
    #Dis_y:Union[str,Callable]="L2", 
    #axis_x:Optional[int]=None, 
    #axis_y:Optional[int]=None, 
    #KeOps:Optional[bool]=None, 
    
    Dis_x="L2"
    Dis_y="L2"
    axis_x=None
    axis_y=None
    KeOps=None
    
    #Perform class validation and gradient detachment.
    x1_, x2_, y1_, y2_, weights1_, weights2_, grad1_, grad2_, requires_grad=check_class(x1, x2, y1, y2, weights1, weights2, grad1, grad2,)
    #Verify that N_max is numeric and that N_max ≥ N_min.
    if isinstance(N_max, float) or isinstance(N_max, int):
        N_max=int(N_max)
        if N_max<N_min:
            raise ValueError("Parameter 'N_max'=%d must be greater than or at least equal to the global parameter 'N_min'=%d."%(N_max,N_min))
    else:
        raise TypeError("Parameter 'N_max' must be numeric.")
    #Verify that the shapes of x1 and x2 match Dis_x.
    shape_batch, N1, N2, KeOps_x, original_dis_x=check_coupling_format(x1_, x2_, Dis_x, axis_x, N_max, "x")
    #When original_dis_y is True and the label space is 1‑D, add a singleton dimension to y1 and y2 to restore the omitted axis.
    if Dis_y in ["L1","L2","inf"]:
        shape_y1=tuple(y1_.shape)
        if shape_y1[:-1]==shape_batch:
            idx=(slice(None),)*len(shape_y1)+(None,)
            y1_=y1_[idx]
        shape_y2=tuple(y2_.shape)
        if shape_y2[:-1]==shape_batch:
            idx=(slice(None),)*len(shape_y2)+(None,)
            y2_=y2_[idx]
    #Verify that the shapes of y1 and y2 match Dis_y.
    shape_batch_y, N1_y, N2_y, KeOps_y, original_dis_y=check_coupling_format(y1_, y2_, Dis_y, axis_y, N_max, "y")
    #Verify that x and y have matching batches, N1 and N2.
    if shape_batch_y!=shape_batch:
        raise ValueError("'y1' and 'y2' must have an identical batch size to 'x1' and 'x2'.")
    if N1_y!=N1:
        raise ValueError("'y1' must have an identical number of samples to 'x1'.")
    if N2_y!=N2:
        raise ValueError("'y2' must have an identical number of samples to 'x2'.")
    #Verify the device parameter.
    if device is None:
        pass
    elif device[:4].lower() in ["cpu","gpu","cuda"]:
        pass
    else:
        raise ValueError("Parameter 'device' must be 'cpu', 'gpu', 'cuda', or None.")
    #If weights1 or weights2 is provided, verify that its shape match x1 or x2.
    if weights1_ is not None:
        shape_weights1=tuple(weights1_.shape)
        if shape_weights1[:-1]!=shape_batch:
            raise ValueError("'weights1' must have shape (Batch_size, Num_samples) or (Num_samples), and its 'Batch_size' must be identical to 'x1'.")
        if shape_weights1[-1]!=N1:
            raise ValueError("'weights1' must have shape (Batch_size, Num_samples) or (Num_samples), and its 'Num_samples' must be identical to 'x1'.")
    if weights2_ is not None:
        shape_weights2=tuple(weights2_.shape)
        if shape_weights2[:-1]!=shape_batch:
            raise ValueError("'weights2' must have shape (Batch_size, Num_samples) or (Num_samples), and its 'Batch_size' must be identical to 'x2'.")
        if shape_weights2[-1]!=N2:
            raise ValueError("'weights2' must have shape (Batch_size, Num_samples) or (Num_samples), and its 'Num_samples' must be identical to 'x2'.")
    #If grad1 or grad2 is provided, verify that its shape match x1 or x2.
    if grad1_ is not None:
        if tuple(grad1_.shape)!=tuple(x1_.shape):
            raise ValueError("'grad1' must have the same shape as 'x1'.")
    if grad2_ is not None:
        if tuple(grad2_.shape)!=tuple(x2_.shape):
            raise ValueError("'grad2' must have the same shape as 'x2'.")
    #Handle the random seed.
    if isinstance(weights1_, Tensor):
        g_device=weights1_.device
    else:
        g_device="cpu"
    if isinstance(weights2_, Tensor):
        g2_device=weights2_.device
    else:
        g2_device="cpu"
    g=torch.Generator(device=g_device)
    g.seed()
    g2=torch.Generator(device=g2_device)
    g2.seed()
    if seed is not None:
        g.manual_seed(seed)
        g2.manual_seed(seed^0x9E3779B97F4A7C15)
    #Sampling and gradient tracking are mutually exclusive.
    #Even if sampling is not performed, automatically shuffle the data so that the subsequent W1_deb function computes covariate shift on randomly grouped samples.
    if not isinstance(verbose, bool):
        raise TypeError("Parameter 'verbose' must be a boolean.")
    index1=shuffling_and_sampling(weights1_, N1, N_max, shape_batch, g, verbose, "1")
    N1_used=index1.shape[-1]
    index2=shuffling_and_sampling(weights2_, N2, N_max, shape_batch, g2, verbose, "2")
    N2_used=index2.shape[-1]
    if torch.cuda.is_available():
        if device is None:
            Cuda=True
            any_on_gpu=any(isinstance(t, torch.Tensor) and t.is_cuda for t in (x1_, x2_, y1_, y2_, weights1_, weights2_, grad1_, grad2_,))
            if verbose and not any_on_gpu:  #Report only when all tensors are on the CPU.
                print("Automatically use the GPU for computation.")
        elif device[:4].lower() in ["gpu","cuda"]:
            Cuda=True
        elif device[:4].lower()=="cpu":
            Cuda=False
    else:
        Cuda=False
    #Perform indexing to obtain the data ultimately used by the algorithm.
    if original_dis_x:
        x1_used=one_dimension_indexing(x1_,index1,len(shape_batch))
        x2_used=one_dimension_indexing(x2_,index2,len(shape_batch))
        if weights1_ is None:
            weights1_used=torch.ones(shape_batch+(N1_used,),dtype=torch.float32,device="cpu")
        else:
            weights1_used=one_dimension_indexing(weights1_,index1,len(shape_batch))
        if weights2_ is None:
            weights2_used=torch.ones(shape_batch+(N2_used,),dtype=torch.float32,device="cpu")
        else:
            weights2_used=one_dimension_indexing(weights2_,index2,len(shape_batch))
        x1_used=tensorized(x1_used,Cuda)
        x2_used=tensorized(x2_used,Cuda)
        weights1_used=tensorized(weights1_used,Cuda)
        weights2_used=tensorized(weights2_used,Cuda)
        if grad1_ is not None:
            grad1_used=one_dimension_indexing(grad1_,index1,len(shape_batch))
            grad1_used=tensorized(grad1_used,Cuda)
        else:
            grad1_used=None
        if grad2_ is not None:
            grad2_used=one_dimension_indexing(grad2_,index2,len(shape_batch))
            grad2_used=tensorized(grad2_used,Cuda)
        else:
            grad2_used=None
    else:
        pass
    if original_dis_y:
        y1_used=one_dimension_indexing(y1_,index1,len(shape_batch))
        y2_used=one_dimension_indexing(y2_,index2,len(shape_batch))
        y1_used=tensorized(y1_used,Cuda)
        y2_used=tensorized(y2_used,Cuda)
    else:
        pass
    #Normalize the weights.
    weights1_used=weights1_used/(weights1_used.sum(axis=-1).unsqueeze(-1))
    weights2_used=weights2_used/(weights2_used.sum(axis=-1).unsqueeze(-1))
    #Verify that eps is numeric.
    if isinstance(eps, float) or isinstance(eps, int):
        eps=float(eps)
        if eps<=0:
            raise ValueError("Parameter 'eps' must be positive.")
    else:
        raise TypeError("Parameter 'eps' must be numeric.")
    #With preprocessing complete, run the DataShifts algorithm.
    if P==1:
        covariate_shift=W1_deb(x1_used, x2_used, weights1_used, weights2_used, eps=eps)
    elif P==2:
        covariate_shift=W2_deb(x1_used, x2_used, weights1_used, weights2_used, eps=eps)
    else:
        raise ValueError("The value of 'P' can only be 1 or 2.")
    loss = SamplesLoss(loss="sinkhorn", p=P, blur=(eps)**(1/P), potentials=True, debias=False, scaling=(0.9)**(1/P))
    g1,g2=loss(weights1_used, x1_used, weights2_used, x2_used)
    if len(shape_batch)==0 and g1.shape[0]==1:
        g1=g1.squeeze(0)
        g2=g2.squeeze(0)    
    g1_=LazyTensor(g1.unsqueeze(-1).unsqueeze(-1))
    g2_=LazyTensor(g2.unsqueeze(-2).unsqueeze(-1))
    weights1_used_=LazyTensor(weights1_used.unsqueeze(-1).unsqueeze(-1))
    weights2_used_=LazyTensor(weights2_used.unsqueeze(-2).unsqueeze(-1))
    Cx=Euclidean_distance(x1_used,x2_used,KeOps=True,p=P)
    Cy=Euclidean_distance(y1_used,y2_used,KeOps=True)    
    Pi=weights1_used_*(((g1_-Cx+g2_)/eps).exp())*weights2_used_
    concept_shift=(Pi*Cy).sum(axis=len(shape_batch)).sum(axis=len(shape_batch)).squeeze(-1)
    if grad1_used is None and grad2_used is None:
        return covariate_shift, concept_shift
    else:
        dir_d=directional_derivative(x1_used,x2_used,grad1_used,grad2_used)
        if P==1:
            covariate_factor=dir_d.max(axis=len(shape_batch)).max(axis=len(shape_batch))[0].squeeze(-1)
        else:
            covariate_factor=((Pi*(dir_d**2)).sum(axis=len(shape_batch)).sum(axis=len(shape_batch)).squeeze(-1))**(1/2)
        return covariate_shift, concept_shift, covariate_factor

def dA_Distance(x1, x2, clf):
    """
    Compute and return the value D, which is defined as the sum of the accuracy of 
    the Logistic Regression model on both classes minus 1.
    
    Explanation:
      - The input x1 represents the sample data for cluster 1 (label assigned as 0), 
        and x2 represents the sample data for cluster 2 (label assigned as 1).
      - Each sample in cluster 1 has a weight of 1/N1, and in cluster 2 a weight of 1/N2.
      - The function uses isinstance() to check the input data type and converts 
        it to a numpy.ndarray (assigning to a new variable) to avoid modifying the original data.
    
    Parameters:
      x1: Sample data of cluster 1, with shape (N1, n_features)
      x2: Sample data of cluster 2, with shape (N2, n_features)
    
    Returns:
      D = (accuracy on cluster 1 + accuracy on cluster 2) - 1
    """
    # Type checking and data conversion
    if not isinstance(x1, ndarray):
        x1_data = np.array(x1.cpu())
    else:
        x1_data = x1.copy()
        
    if not isinstance(x2, ndarray):
        x2_data = np.array(x2.cpu())
    else:
        x2_data = x2.copy()
    
    # Calculate the number of samples in each cluster
    N1 = x1_data.shape[0]
    N2 = x2_data.shape[0]
    
    # Construct the training data X and corresponding labels y
    X = np.vstack((x1_data, x2_data))
    y = np.concatenate((np.zeros(N1), np.ones(N2)))
    
    # Construct the sample weights
    weights1 = np.full(N1, 1.0 / N1)
    weights2 = np.full(N2, 1.0 / N2)
    sample_weight = np.concatenate((weights1, weights2))
    
    # Train the model
    #clf.fit(X, y, sample_weight=sample_weight)
    #The mlp in sklearn does not support defining sample weights, and for the time being requires an equal number of x1 and x2 samples.
    clf.fit(X, y)
    
    # Perform prediction on the training data
    y_pred = clf.predict(X)
    
    # Compute the accuracy on x1 (label 0) and x2 (label 1) separately
    acc_x1 = np.mean(y_pred[:N1] == 0)
    acc_x2 = np.mean(y_pred[N1:] == 1)
    
    # Compute D = (accuracy on cluster 1 + accuracy on cluster 2) - 1
    D = acc_x1 + acc_x2 - 1
    return D

def old_bound(x1, x2, f1, f2, clf):
    concept_shift = min((f1(x1)-f2(x1)).abs().mean().item(),
                       (f1(x2)-f2(x2)).abs().mean().item())
    covariate_shift = dA_Distance(x1, x2, clf)
    return covariate_shift, concept_shift
