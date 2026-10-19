package com.meher.jawhar.screens

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LessonScoreTest {
    private val lesson = Mock.lessonFormI

    @Test
    fun lessonIsWellFormed() {
        assertTrue(lesson.steps.isNotEmpty())
        assertTrue(lesson.quiz.isNotEmpty())
        assertTrue(lesson.goals.isNotEmpty())
        for (q in lesson.quiz) {
            assertTrue(q.options.size >= 2, "question '${q.prompt}' needs options")
            assertTrue(q.answer in q.options.indices, "answer out of range in '${q.prompt}'")
            assertTrue(q.explain.isNotBlank(), "question '${q.prompt}' needs an explanation")
        }
        for (s in lesson.steps) {
            assertTrue(s.title.isNotBlank() && s.body.isNotBlank(), "content step needs a title and body")
        }
    }

    @Test
    fun noDuplicateOptions() {
        lesson.quiz.forEach { q ->
            assertEquals(q.options.size, q.options.toSet().size, "duplicate option in '${q.prompt}'")
        }
    }

    @Test
    fun allCorrectScoresOne() {
        val perfect = lesson.quiz.map { it.answer }
        assertEquals(1f, Mock.lessonScore(lesson.quiz, perfect), 0.0001f)
    }

    @Test
    fun allWrongScoresZero() {
        val wrong = lesson.quiz.map { (it.answer + 1) % it.options.size }
        assertEquals(0f, Mock.lessonScore(lesson.quiz, wrong), 0.0001f)
    }

    @Test
    fun unansweredCountsAsWrong() {
        assertEquals(0f, Mock.lessonScore(lesson.quiz, List(lesson.quiz.size) { null }), 0.0001f)
    }

    @Test
    fun partialScoreIsAProportion() {
        val half = lesson.quiz.mapIndexed { i, q -> if (i % 2 == 0) q.answer else null }
        val v = Mock.lessonScore(lesson.quiz, half)
        assertTrue(v > 0f && v < 1f, "expected a fraction, got $v")
    }
}