package com.meher.jawhar.design

import androidx.compose.animation.core.FiniteAnimationSpec
import androidx.compose.animation.core.SpringSpec
import androidx.compose.animation.core.snap
import androidx.compose.animation.core.spring

/**
 * Material 3 Expressive motion physics.
 *
 * Two families, and picking the wrong one is the usual mistake:
 *  - **spatial** moves something on screen (position, size, shape, rotation) and is
 *    allowed to overshoot and settle.
 *  - **effects** animates colour and opacity, where an overshoot would read as a bug,
 *    so damping is 1 and it lands dead on target.
 *
 * Values are the `expressive` scheme from https://m3.material.io/styles/motion/overview/specs
 * (`md.sys.motion.spring.*.expressive`), not eyeballed. They are generic in `T` because the
 * same spring drives `Float`, `Dp` and `Color`.
 */
object JawharMotion {

    /** Spatial, fast — small elements: press scale, icon nudge. */
    fun <T> spatialFast(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 0.6f, stiffness = 800f, visibilityThreshold = threshold)

    /** Spatial, default — most on-screen movement. */
    fun <T> spatialDefault(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 0.8f, stiffness = 380f, visibilityThreshold = threshold)

    /** Spatial, slow — large surfaces: sheets, full-screen panels. */
    fun <T> spatialSlow(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 0.8f, stiffness = 200f, visibilityThreshold = threshold)

    /** Effects, fast — hover and small colour shifts. */
    fun <T> effectsFast(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 1f, stiffness = 3800f, visibilityThreshold = threshold)

    /** Effects, default — colour and opacity on state change. */
    fun <T> effectsDefault(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 1f, stiffness = 1600f, visibilityThreshold = threshold)

    /** Effects, slow — colour and opacity on larger surfaces. */
    fun <T> effectsSlow(threshold: T? = null): SpringSpec<T> =
        spring(dampingRatio = 1f, stiffness = 800f, visibilityThreshold = threshold)

    /**
     * When true every `motion(...)` spec collapses to an instant snap, leaving colour and
     * opacity transitions intact but dropping all movement.
     *
     * Compose Multiplatform does not expose the platform "remove animations" setting to
     * common code, so nothing sets this yet. Wire it from the Appearance settings screen.
     */
    var reduced: Boolean = false
}

/** [spec], or an instant snap when motion is turned off. Not composable: transition specs can't be. */
fun <T> motion(spec: FiniteAnimationSpec<T>): FiniteAnimationSpec<T> =
    if (JawharMotion.reduced) snap() else spec