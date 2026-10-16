package com.meher.jawhar.screens

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PlacementScoreTest {
    private val bank = Mock.placementQuestions

    @Test
    fun bankIsWellFormed() {
        assertTrue(bank.isNotEmpty())
        assertTrue(bank.size >= 4)
        for (q in bank) {
            assertTrue(q.options.size >= 2, "question '${q.prompt}' needs options")
            assertTrue(q.answer in q.options.indices, "answer out of range in '${q.prompt}'")
            assertTrue(Mock.skills.contains(q.skill), "unknown skill '${q.skill}'")
        }
        assertEquals(Mock.skills.toSet(), bank.map { it.skill }.toSet(), "every skill needs questions")
    }

    @Test
    fun allCorrectScoresOne() {
        val perfect = bank.map { it.answer }
        Mock.placementScore(perfect).forEach { (skill, v) ->
            assertEquals(1f, v, 0.0001f, "$skill should be perfect")
        }
    }

    @Test
    fun allWrongScoresZero() {
        val wrong = bank.map { (it.answer + 1) % it.options.size }
        Mock.placementScore(wrong).forEach { (skill, v) ->
            assertEquals(0f, v, 0.0001f, "$skill should be zero")
        }
    }

    @Test
    fun unansweredCountsAsWrong() {
        val blanks = List(bank.size) { null }
        Mock.placementScore(blanks).forEach { (skill, v) ->
            assertEquals(0f, v, 0.0001f, "$skill should be zero")
        }
    }

    @Test
    fun partialScoreIsPerSkill() {
        val picks = bank.map { q -> if (q.skill == "Nahw") q.answer else null }
        val score = Mock.placementScore(picks)
        assertEquals(1f, score["Nahw"]!!, 0.0001f)
        assertEquals(0f, score["Sarf"]!!, 0.0001f)
        assertEquals(0f, score["Vocabulary"]!!, 0.0001f)
    }

    @Test
    fun halfCorrectInOneSkillIsAHalf() {
        val picks = bank.map { q ->
            if (q.skill == "Sarf" && q.options.indexOfFirst { it == q.options[q.answer] } == 0) q.answer else null
        }
        val sarf = bank.count { it.skill == "Sarf" }
        val got = Mock.placementScore(picks)["Sarf"]!!
        assertTrue(got > 0f && got < 1f, "expected a fraction, got $got over $sarf questions")
    }
}