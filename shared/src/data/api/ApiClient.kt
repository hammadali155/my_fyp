package com.meher.jawhar.data.api

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.patch
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.contentType
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

expect fun createHttpClient(): HttpClient

expect fun defaultApiBaseUrl(): String

expect suspend fun probeLocalBackend(timeoutMs: Int): Boolean

expect fun renderApiBaseUrl(): String

class ApiClient(val baseUrl: String = defaultApiBaseUrl()) {
    val http: HttpClient = createHttpClient()

    var currentBaseUrl: String = baseUrl
        private set

    var isUsingLocalBackend: Boolean = true
        private set

    suspend fun resolveBaseUrl() {
        if (probeLocalBackend(3000)) {
            currentBaseUrl = defaultApiBaseUrl()
            isUsingLocalBackend = true
        } else {
            currentBaseUrl = renderApiBaseUrl()
            isUsingLocalBackend = false
        }
    }

    suspend fun getSurahs(): List<SurahDto> =
        http.get("$currentBaseUrl/api/v1/quran/surahs").body<SurahListDto>().items

    suspend fun getSurah(surahId: Int): SurahDto =
        http.get("$currentBaseUrl/api/v1/quran/surahs/$surahId").body()

    suspend fun getVerseByRef(surah: Int, ayah: Int): VerseDto =
        http.get("$currentBaseUrl/api/v1/quran/surahs/$surah/verses/$ayah").body()

    suspend fun getVerse(verseId: Int): VerseDto =
        http.get("$currentBaseUrl/api/v1/quran/verses/$verseId").body()

    suspend fun getVerses(surahId: Int, page: Int = 1, pageSize: Int = 50): VerseListDto =
        http.get("$currentBaseUrl/api/v1/quran/verses?surah_id=$surahId&page=$page&page_size=$pageSize").body()

    suspend fun analyze(word: String): AnalyzeResponseDto =
        http.post("$currentBaseUrl/api/v1/morphology/analyze") {
            contentType(ContentType.Application.Json)
            setBody(AnalyzeRequestDto(word))
        }.body()

    suspend fun analyzeFull(word: String): MorphologyAnalyzeResponseDto =
        http.post("$currentBaseUrl/api/v1/morphology/analyze") {
            contentType(ContentType.Application.Json)
            setBody(AnalyzeRequestDto(word))
        }.body()

    suspend fun segment(word: String): SegmentationDetailDto =
        http.get("$currentBaseUrl/api/v1/morphology/segment?word=$word").body()

    suspend fun listVerbForms(): List<VerbFormDto> =
        http.get("$currentBaseUrl/api/v1/morphology/forms").body()

    suspend fun conjugate(root: String, form: Int): ConjugateResponseDto =
        http.post("$currentBaseUrl/api/v1/morphology/conjugate") {
            contentType(ContentType.Application.Json)
            setBody(ConjugateRequestDto(root, form))
        }.body()

    suspend fun wordFamily(root: String): WordFamilyResponseDto =
        http.get("$currentBaseUrl/api/v1/morphology/word-family/$root").body()

    suspend fun patterns(): PatternsResponseDto =
        http.get("$currentBaseUrl/api/v1/morphology/patterns").body()

    suspend fun rootConcordance(root: String): RootConcordanceResponseDto =
        http.get("$currentBaseUrl/api/v1/morphology/roots/$root").body()

    fun close() = http.close()
}

suspend fun ApiClient.badges(): List<BadgeDto> =
    authorizedGet("$currentBaseUrl/api/v1/progress/badges").body<BadgeListResponseDto>().items

val apiJson = Json { ignoreUnknownKeys = true; isLenient = true }

object Session {
    var accessToken: String? = null
    var refreshToken: String? = null
    var userName: String? = null
}

object AuthApi {
    suspend fun login(api: ApiClient, email: String, password: String): AuthResponseDto {
        val res: AuthResponseDto = api.http.post("${api.baseUrl}/api/v1/auth/login") {
            contentType(ContentType.Application.Json)
            setBody(LoginRequestDto(email, password))
        }.body()
        Session.accessToken = res.tokens.access_token
        Session.refreshToken = res.tokens.refresh_token
        Session.userName = res.user.name
        return res
    }

    suspend fun register(api: ApiClient, email: String, name: String, password: String): AuthResponseDto {
        val res: AuthResponseDto = api.http.post("${api.baseUrl}/api/v1/auth/register") {
            contentType(ContentType.Application.Json)
            setBody(RegisterRequestDto(email = email, name = name, password = password))
        }.body()
        Session.accessToken = res.tokens.access_token
        Session.refreshToken = res.tokens.refresh_token
        Session.userName = res.user.name
        return res
    }

    suspend fun refresh(api: ApiClient): TokenDto {
        val refreshToken = Session.refreshToken ?: throw IllegalStateException("No refresh token")
        val res: TokenDto = api.http.post("${api.baseUrl}/api/v1/auth/refresh") {
            contentType(ContentType.Application.Json)
            setBody(RefreshTokenRequestDto(refreshToken))
        }.body()
        Session.accessToken = res.access_token
        Session.refreshToken = res.refresh_token
        return res
    }

    suspend fun logout(api: ApiClient): MessageResponseDto {
        val refreshToken = Session.refreshToken
        val res: MessageResponseDto = api.http.post("${api.baseUrl}/api/v1/auth/logout") {
            contentType(ContentType.Application.Json)
            setBody(RefreshTokenRequestDto(refreshToken ?: ""))
        }.body()
        Session.accessToken = null
        Session.refreshToken = null
        Session.userName = null
        return res
    }
}

suspend fun ApiClient.authorizedGet(url: String): io.ktor.client.statement.HttpResponse =
    http.get(url) {
        Session.accessToken?.let { headers.append(HttpHeaders.Authorization, "Bearer $it") }
    }

suspend fun ApiClient.authorizedPost(url: String, body: Any): io.ktor.client.statement.HttpResponse =
    http.post(url) {
        Session.accessToken?.let { headers.append(HttpHeaders.Authorization, "Bearer $it") }
        contentType(ContentType.Application.Json)
        setBody(body)
    }

suspend fun ApiClient.authorizedPatch(url: String, body: Any): io.ktor.client.statement.HttpResponse =
    http.patch(url) {
        Session.accessToken?.let { headers.append(HttpHeaders.Authorization, "Bearer $it") }
        contentType(ContentType.Application.Json)
        setBody(body)
    }

suspend fun ApiClient.authorizedDelete(url: String): io.ktor.client.statement.HttpResponse =
    http.delete(url) {
        Session.accessToken?.let { headers.append(HttpHeaders.Authorization, "Bearer $it") }
    }

suspend fun ApiClient.me(): UserDto =
    authorizedGet("$currentBaseUrl/api/v1/auth/me").body()

suspend fun ApiClient.updateProfile(req: UserUpdateRequestDto): UserDto =
    authorizedPatch("$currentBaseUrl/api/v1/auth/me", req).body()

// ---------- SRS ----------

suspend fun ApiClient.srsCreateCard(
    itemType: String,
    front: String,
    back: String,
    hint: String? = null,
    wordId: Int? = null,
    surahNumber: Int? = null,
    ayahNumber: Int? = null,
): SrsCardDto =
    authorizedPost("$currentBaseUrl/api/v1/srs/cards", SrsCardCreateDto(itemType, front, back, hint, wordId, surahNumber, ayahNumber)).body()

suspend fun ApiClient.srsDue(): List<SrsCardDto> =
    authorizedGet("$currentBaseUrl/api/v1/srs/due").body<SrsDueDto>().cards.map { card ->
        card.copy(new_card = card.state == "new")
    }

suspend fun ApiClient.srsReview(cardId: Int, rating: Int): SrsReviewResponseDto =
    authorizedPost("$currentBaseUrl/api/v1/srs/review", SrsReviewRequestDto(cardId, rating, null)).body()

suspend fun ApiClient.srsStats(): SrsStatsDto =
    authorizedGet("$currentBaseUrl/api/v1/srs/stats").body()

suspend fun ApiClient.srsDeleteCard(cardId: Int) =
    authorizedDelete("$currentBaseUrl/api/v1/srs/cards/$cardId")

// ---------- Decks ----------

suspend fun ApiClient.getDecks(): List<DeckDto> =
    authorizedGet("$currentBaseUrl/api/v1/decks").body<DeckListDto>().items

suspend fun ApiClient.createDeck(name: String): DeckDto =
    authorizedPost("$currentBaseUrl/api/v1/decks", DeckCreateDto(name)).body()

suspend fun ApiClient.addWordToDeck(deckId: Int, wordId: Int): DeckWordAddResponseDto =
    authorizedPost("$currentBaseUrl/api/v1/decks/$deckId/words", AddWordRequestDto(wordId)).body()

suspend fun ApiClient.addWordsToDeckBulk(deckId: Int, wordIds: List<Int>): DeckWordAddResponseDto =
    authorizedPost("$currentBaseUrl/api/v1/decks/$deckId/words/bulk", BulkAddWordsRequestDto(wordIds)).body()

suspend fun ApiClient.deleteDeck(deckId: Int) =
    authorizedDelete("$currentBaseUrl/api/v1/decks/$deckId")

// ---------- Quran ----------

suspend fun ApiClient.search(q: String, page: Int = 1, pageSize: Int = 20): QuranSearchResponseDto =
    http.get("$currentBaseUrl/api/v1/quran/search?q=$q&page=$page&page_size=$pageSize").body()

suspend fun ApiClient.roots(minCount: Int? = null, posTag: String? = null, surahNumber: Int? = null, limit: Int = 50): RootRankResponseDto {
    val params = buildList {
        if (minCount != null) add("min_count=$minCount")
        if (posTag != null) add("pos_tag=$posTag")
        if (surahNumber != null) add("surah_number=$surahNumber")
        add("limit=$limit")
    }.joinToString("&")
    return http.get("$currentBaseUrl/api/v1/quran/roots?$params").body()
}

// ---------- Bookmarks ----------

suspend fun ApiClient.createBookmark(verseId: Int, note: String? = null, collection: String? = null): BookmarkResponseDto =
    authorizedPost("$currentBaseUrl/api/v1/bookmarks", BookmarkCreateDto(verseId, note, collection)).body()

suspend fun ApiClient.listBookmarks(collection: String? = null): BookmarkListResponseDto {
    val params = if (collection != null) "?collection=$collection" else ""
    return authorizedGet("$currentBaseUrl/api/v1/bookmarks$params").body<BookmarkListResponseDto>()
}

suspend fun ApiClient.deleteBookmark(bookmarkId: Int) =
    authorizedDelete("$currentBaseUrl/api/v1/bookmarks/$bookmarkId")

// ---------- Nahw ----------

suspend fun ApiClient.nahwVerse(surah: Int, ayah: Int): NahwVerseResponseDto =
    http.get("$currentBaseUrl/api/v1/nahw/verse/$surah/$ayah").body()

suspend fun ApiClient.nahwParse(text: String, isQuranic: Boolean = false): NahwParseResponseDto =
    http.post("$currentBaseUrl/api/v1/nahw/parse") {
        contentType(ContentType.Application.Json)
        setBody(NahwParseRequestDto(text, isQuranic))
    }.body()

suspend fun ApiClient.nahwExplain(wordId: Int): NahwExplainResponseDto =
    authorizedGet("$currentBaseUrl/api/v1/nahw/explain/$wordId").body()

// ---------- Tutor ----------

suspend fun ApiClient.tutorChat(message: String, sessionId: Int?, reference: TutorReferenceDto?): TutorChatResponseDto =
    authorizedPost("$currentBaseUrl/api/v1/tutor/chat", TutorChatRequestDto(message, sessionId, reference)).body()

suspend fun ApiClient.tutorSessions(): TutorSessionListDto =
    authorizedGet("$currentBaseUrl/api/v1/tutor/sessions").body()

suspend fun ApiClient.tutorDeleteSession(sessionId: Int) =
    authorizedDelete("$currentBaseUrl/api/v1/tutor/sessions/$sessionId")

// ---------- Health ----------

suspend fun ApiClient.health(): HealthResponseDto =
    http.get("$currentBaseUrl/api/v1/health").body()

suspend fun ApiClient.healthReady(): SimpleProbeResponseDto =
    http.get("$currentBaseUrl/api/v1/health/ready").body()

suspend fun ApiClient.healthLive(): SimpleProbeResponseDto =
    http.get("$currentBaseUrl/api/v1/health/live").body()

// ---------- SRS DTOs (request bodies not yet in ApiModels) ----------

@Serializable
data class SrsCardCreateDto(
    val item_type: String,
    val front: String,
    val back: String,
    val hint: String? = null,
    val word_id: Int? = null,
    val surah_number: Int? = null,
    val ayah_number: Int? = null,
)
