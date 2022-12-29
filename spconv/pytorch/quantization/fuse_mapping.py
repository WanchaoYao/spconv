from typing import Union, Callable, Tuple, Dict, Optional, Type, Any
import torch.nn as nn
import spconv.pytorch as spconv
from .utils import fuse_spconv_bn_eval
from . import intrinsic as snni
from .conv_fused import SparseConvBn, SparseConvBnReLU

def fuse_conv_bn(conv, bn):
    r"""Given the conv and bn modules, fuses them and returns the fused module

    Args:
        conv: Module instance of type conv2d/conv3d
        bn: Spatial BN instance that needs to be fused with the conv

    Examples::

        >>> m1 = nn.Conv2d(10, 20, 3)
        >>> b1 = nn.BatchNorm2d(20)
        >>> m2 = fuse_conv_bn(m1, b1)
    """
    assert(conv.training == bn.training),\
        "Conv and BN both must be in the same mode (train or eval)."

    fused_module_class_map = {
        spconv.SubMConv1d: snni.SpconvBnNd,
        spconv.SparseConv1d: snni.SpconvBnNd,
        spconv.SparseInverseConv1d: snni.SpconvBnNd,
        spconv.SubMConv2d: snni.SpconvBnNd,
        spconv.SparseConv2d: snni.SpconvBnNd,
        spconv.SparseInverseConv2d: snni.SpconvBnNd,
        spconv.SubMConv3d: snni.SpconvBnNd,
        spconv.SparseConv3d: snni.SpconvBnNd,
        spconv.SparseInverseConv3d: snni.SpconvBnNd,
    }

    if conv.training:
        assert bn.num_features == conv.out_channels, 'Output channel of Conv2d must match num_features of BatchNorm2d'
        assert bn.affine, 'Only support fusing BatchNorm2d with affine set to True'
        assert bn.track_running_stats, 'Only support fusing BatchNorm2d with tracking_running_stats set to True'
        fused_module_class = fused_module_class_map.get((type(conv)), None)
        if fused_module_class is not None:
            return fused_module_class(conv, bn)
        else:
            raise NotImplementedError("Cannot fuse train modules: {}".format((conv, bn)))
    else:
        return fuse_spconv_bn_eval(conv, bn)

def fuse_conv_bn_relu(conv, bn, relu):
    r"""Given the conv and bn modules, fuses them and returns the fused module

    Args:
        conv: Module instance of type conv2d/conv3d
        bn: Spatial BN instance that needs to be fused with the conv

    Examples::

        >>> m1 = nn.Conv2d(10, 20, 3)
        >>> b1 = nn.BatchNorm2d(20)
        >>> m2 = fuse_conv_bn(m1, b1)
    """
    assert(conv.training == bn.training == relu.training),\
        "Conv and BN both must be in the same mode (train or eval)."
    fused_module : Optional[Type[spconv.SparseSequential]] = None
    if conv.training:
        map_to_fused_module_train = {
            spconv.SubMConv1d: snni.SpconvBnReLUNd,
            spconv.SparseConv1d: snni.SpconvBnReLUNd,
            spconv.SparseInverseConv1d: snni.SpconvBnReLUNd,
            spconv.SubMConv2d: snni.SpconvBnReLUNd,
            spconv.SparseConv2d: snni.SpconvBnReLUNd,
            spconv.SparseInverseConv2d: snni.SpconvBnReLUNd,
            spconv.SubMConv3d: snni.SpconvBnReLUNd,
            spconv.SparseConv3d: snni.SpconvBnReLUNd,
            spconv.SparseInverseConv3d: snni.SpconvBnReLUNd,
        }
        assert bn.num_features == conv.out_channels, 'Output channel of Conv must match num_features of BatchNorm'
        assert bn.affine, 'Only support fusing BatchNorm with affine set to True'
        assert bn.track_running_stats, 'Only support fusing BatchNorm with tracking_running_stats set to True'
        fused_module = map_to_fused_module_train.get(type(conv), None)
        if fused_module is not None:
            return fused_module(conv, bn, relu)
        else:
            raise NotImplementedError("Cannot fuse train modules: {}".format((conv, bn, relu)))
    else:
        map_to_fused_module_eval = {
            spconv.SubMConv1d: snni.SpconvReLUNd,
            spconv.SparseConv1d: snni.SpconvReLUNd,
            spconv.SparseInverseConv1d: snni.SpconvReLUNd,
            spconv.SubMConv2d: snni.SpconvReLUNd,
            spconv.SparseConv2d: snni.SpconvReLUNd,
            spconv.SparseInverseConv2d: snni.SpconvReLUNd,
            spconv.SubMConv3d: snni.SpconvReLUNd,
            spconv.SparseConv3d: snni.SpconvReLUNd,
            spconv.SparseInverseConv3d: snni.SpconvReLUNd,
        }
        fused_module = map_to_fused_module_eval.get(type(conv), None)
        if fused_module is not None:
            fused_conv = fuse_spconv_bn_eval(conv, bn)
            return fused_module(fused_conv, relu)
        else:
            raise NotImplementedError("Cannot fuse eval modules: {}".format((conv, bn, relu)))

DEFAULT_SPCONV_OP_LIST_TO_FUSER_METHOD : Dict[Tuple, Union[nn.Sequential, Callable]] = {
    (spconv.SubMConv1d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SubMConv1d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseConv1d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseConv1d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseInverseConv1d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseInverseConv1d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SubMConv2d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SubMConv2d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseConv2d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseConv2d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseInverseConv2d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseInverseConv2d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SubMConv3d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SubMConv3d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseConv3d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseConv3d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
    (spconv.SparseInverseConv3d, nn.BatchNorm1d): fuse_conv_bn,
    (spconv.SparseInverseConv3d, nn.BatchNorm1d, nn.ReLU): fuse_conv_bn_relu,
}

# Default map for swapping float module to qat modules
DEFAULT_SPCONV_QAT_MODULE_MAPPINGS : Dict[Callable, Any] = {
    # nn.Conv2d: nnqat.Conv2d,
    # Intrinsic modules:
    snni.SpconvBnNd: SparseConvBn,
    snni.SpconvBnReLUNd: SparseConvBnReLU,
}
