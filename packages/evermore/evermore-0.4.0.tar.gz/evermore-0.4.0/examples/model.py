from __future__ import annotations

import typing as tp

import jax
import jax.numpy as jnp
from flax import nnx
from jaxtyping import Array, Float, PyTree

import evermore as evm

jax.config.update("jax_enable_x64", True)


Hist1D: tp.TypeAlias = Float[Array, " nbins"]  # type: ignore[name-defined]


def model(
    params: nnx.Module[evm.Parameter],
    hists: PyTree[Hist1D],
) -> PyTree[Hist1D]:
    expectations = {}

    # signal process
    sig_mod = params.mu.scale()
    expectations["signal"] = sig_mod(hists["nominal"]["signal"])

    # bkg1 process
    bkg1_lnN = params.norm1.scale_log(up=jnp.array([1.1]), down=jnp.array([0.9]))
    bkg1_shape = params.shape.morphing(
        up_template=hists["shape_up"]["bkg1"],
        down_template=hists["shape_down"]["bkg1"],
    )
    # combine modifiers
    bkg1_mod = bkg1_lnN @ bkg1_shape
    expectations["bkg1"] = bkg1_mod(hists["nominal"]["bkg1"])

    # bkg2 process
    bkg2_lnN = params.norm2.scale_log(up=jnp.array([1.05]), down=jnp.array([0.95]))
    bkg2_shape = params.shape.morphing(
        up_template=hists["shape_up"]["bkg2"],
        down_template=hists["shape_down"]["bkg2"],
    )
    # combine modifiers
    bkg2_mod = bkg2_lnN @ bkg2_shape
    expectations["bkg2"] = bkg2_mod(hists["nominal"]["bkg2"])

    # return the modified expectations
    return expectations


hists = {
    "nominal": {
        "signal": jnp.array([3.0]),
        "bkg1": jnp.array([10.0]),
        "bkg2": jnp.array([20.0]),
    },
    "shape_up": {
        "bkg1": jnp.array([12.0]),
        "bkg2": jnp.array([23.0]),
    },
    "shape_down": {
        "bkg1": jnp.array([8.0]),
        "bkg2": jnp.array([19.0]),
    },
}


# dataclass like container for parameters
class Params(nnx.Pytree):
    def __init__(
        self,
        mu: evm.Parameter,
        norm1: evm.NormalParameter,
        norm2: evm.NormalParameter,
        shape: evm.NormalParameter,
    ):
        self.mu = mu
        self.norm1 = norm1
        self.norm2 = norm2
        self.shape = shape


params = Params(
    mu=evm.Parameter(name="mu"),
    norm1=evm.NormalParameter(name="norm1"),
    norm2=evm.NormalParameter(name="norm2"),
    shape=evm.NormalParameter(name="shape"),
)


observation = jnp.array([37.0])
expectations = model(params, hists)


@nnx.jit
def loss(
    params: Params,
    *,
    hists: PyTree[Hist1D],
    observation: Hist1D,
) -> Float[Array, ""]:
    expectations = model(params, hists)
    constraints = evm.loss.get_log_probs(params)
    loss_val = (
        evm.pdf.PoissonContinuous(evm.util.sum_over_leaves(expectations))
        .log_prob(observation)
        .sum()
    )
    # add constraint
    loss_val += evm.util.sum_over_leaves(constraints)
    return -jnp.sum(loss_val)
