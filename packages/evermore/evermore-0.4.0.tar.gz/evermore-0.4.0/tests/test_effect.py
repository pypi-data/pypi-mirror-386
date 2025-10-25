# mypy: disable-error-code="arg-type"

from __future__ import annotations

import jax
import jax.numpy as jnp

from evermore import Parameter
from evermore.binned.effect import (
    AsymmetricExponential,
    Identity,
    Linear,
    OffsetAndScale,
    VerticalTemplateMorphing,
)

jax.config.update("jax_enable_x64", True)


def compare_offset_and_scale(a: OffsetAndScale, b: OffsetAndScale) -> bool:
    return jnp.array_equal(a.offset, b.offset) and jnp.array_equal(a.scale, b.scale)


def test_Identity():
    effect = Identity()

    hist = jnp.array([1.0, 2.0, 3.0])

    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=(Parameter(), Parameter()), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )


def test_Linear():
    effect: Linear = Linear(slope=1.0, offset=0.0)

    hist = jnp.array([1.0, 2.0, 3.0])

    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.zeros_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )

    effect = Linear(slope=0.0, offset=1.0)
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )

    effect = Linear(slope=1.0, offset=1.0)
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.full_like(hist, 2.0)
        ).broadcast(),
    )


def test_AsymmetricExponential():
    effect: AsymmetricExponential = AsymmetricExponential(up=1.2, down=0.9)

    hist = jnp.array([1.0])

    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=+1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.full_like(hist, 1.2)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=-1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.full_like(hist, 0.9)
        ).broadcast(),
    )


def test_VerticalTemplateMorphing():
    effect: VerticalTemplateMorphing = VerticalTemplateMorphing(
        up_template=jnp.array([12]), down_template=jnp.array([7])
    )

    hist = jnp.array([10.0])

    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=0.0), hist=hist),
        OffsetAndScale(
            offset=jnp.zeros_like(hist), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=+1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.full_like(hist, 2.0), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
    assert compare_offset_and_scale(
        effect(parameter=Parameter(value=-1.0), hist=hist),
        OffsetAndScale(
            offset=jnp.full_like(hist, -3.0), scale=jnp.ones_like(hist)
        ).broadcast(),
    )
