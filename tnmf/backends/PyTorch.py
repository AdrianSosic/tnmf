# TODO: fix numpy to torch dtype
# TODO: it should be possible to reformulate the gradients using
#       https://pytorch.org/docs/stable/autograd.html#torch.autograd.functional.jacobian
# TODO: merge gradient functions into one
# TODO: add device option

from .Backend import Backend
from torch import Tensor
import torch
import numpy as np
from typing import Tuple, Optional

# see https://github.com/pytorch/pytorch/issues/40568#issuecomment-649961327
numpy_to_torch_dtype_dict = {
    np.uint8: torch.uint8,
    np.int8: torch.int8,
    np.int16: torch.int16,
    np.int32: torch.int32,
    np.int64: torch.int64,
    np.float16: torch.float16,
    np.float32: torch.float32,
    np.float64: torch.float64,
    np.dtype('float64'): torch.float64,
    np.complex64: torch.complex64,
    np.complex128: torch.complex128
}

conv_dict = {
    1: torch.nn.functional.conv1d,
    2: torch.nn.functional.conv2d,
    3: torch.nn.functional.conv3d,
}


class PyTorch_Backend(Backend):

    def initialize_matrices(
            self,
            V: np.ndarray,
            atom_shape: Tuple[int, ...],
            n_atoms: int,
            W: Optional[Tensor] = None,
    ) -> Tuple[Tensor, Tensor]:

        self.dtype = numpy_to_torch_dtype_dict[V.dtype]
        H = (1 - torch.rand((self.n_samples, n_atoms, *self._transform_shape), dtype=self.dtype))

        if W is None:
            W = (1 - torch.rand((n_atoms, self.n_channels, *atom_shape), dtype=self.dtype))

        return W, H

    def normalize(self, arr: Tensor, axes: Tuple[int]) -> Tensor:
        return arr / (arr.sum(dim=axes, keepdim=True))

    def reconstruction_gradient_W(self, V: np.ndarray, W: Tensor, H: Tensor) -> Tuple[Tensor, Tensor]:
        W_grad = W.detach().requires_grad_()
        neg_energy, pos_energy = self._energy_terms(V, W_grad, H)
        neg = torch.autograd.grad(neg_energy, W_grad, retain_graph=True)[0]
        pos = torch.autograd.grad(pos_energy, W_grad)[0]
        return neg.detach(), pos.detach()

    def reconstruction_gradient_H(self, V: np.ndarray, W: Tensor, H: Tensor) -> Tuple[Tensor, Tensor]:
        H_grad = H.detach().requires_grad_()
        neg_energy, pos_energy = self._energy_terms(V, W, H_grad)
        neg = torch.autograd.grad(neg_energy, H_grad, retain_graph=True)[0]
        pos = torch.autograd.grad(pos_energy, H_grad)[0]
        return neg.detach(), pos.detach()

    def _energy_terms(self, V: np.ndarray, W: Tensor, H: Tensor) -> Tuple[Tensor, Tensor]:
        V = torch.as_tensor(V)
        R = self._reconstruct_torch(W, H)
        neg = (R * V).sum()
        pos = 0.5 * (V.square().sum() + R.square().sum())
        return neg, pos

    def _reconstruct_torch(self, W: Tensor, H: Tensor) -> Tensor:
        # TODO: support dimensions > 3
        # TODO: remove atom for loop
        # TODO: consider transposed convolution as alternative

        n_samples = H.shape[0]
        n_atoms = W.shape[0]
        n_channels = W.shape[1]
        n_shift_dimensions = W.ndim - 2

        assert n_shift_dimensions <= 3
        conv_fun = conv_dict[n_shift_dimensions]
        flip_dims = list(range(-n_shift_dimensions, 0))
        W_flipped = torch.flip(W, flip_dims)

        R = torch.zeros((n_samples, n_channels, *self._sample_shape), dtype=self.dtype)
        for i_atom in range(n_atoms):
            R += conv_fun(H[:, i_atom, None], W_flipped[i_atom, None])

        return R

    def reconstruct(self, W: Tensor, H: Tensor) -> np.ndarray:
        R = self._reconstruct_torch(W, H)
        return R.detach().numpy()

    def reconstruction_energy(self, V: Tensor, W: Tensor, H: Tensor) -> float:
        V = torch.as_tensor(V)
        R = self._reconstruct_torch(W, H)
        energy = 0.5 * torch.sum(torch.square(V - R))
        return float(energy)
