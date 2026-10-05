package com.meher.jawhar.data.api

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import kotlinx.serialization.json.Json

expect fun createHttpClient(): HttpClient

expect fun defaultApiBaseUrl(): String

class ApiClient(val baseUrl: String = defaultApiBaseUrl()) {
    val http: HttpClient = createHttpClient()

    suspend fun getSurahs(): List<SurahDto> =
        http.get("$baseUrl/api/v1/quran/surahs").body<SurahListDto>().items

    suspend fun getVerseByRef(surah: Int, ayah: Int): VerseDto =
        http.get("$baseUrl/api/v1/quran/surahs/$surah/verses/$ayah").body()

    suspend fun getVerses(surahId: Int, page: Int = 1, pageSize: Int = 50): VerseListDto =
        http.get("$baseUrl/api/v1/quran/verses?surah_id=$surahId&page=$page&page_size=$pageSize").body()

    suspend fun analyze(word: String): AnalyzeResponseDto =
        http.post("$baseUrl/api/v1/morphology/analyze") {
            contentType(ContentType.Application.Json)
            setBody(AnalyzeRequestDto(word))
        }.body()

    fun close() = http.close()
}

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
}

suspend fun ApiClient.authorizedGet(url: String): io.ktor.client.statement.HttpResponse =
    http.get(url) {
        Session.accessToken?.let { headers.append(io.ktor.http.HttpHeaders.Authorization, "Bearer $it") }
    }

suspend fun ApiClient.authorizedPost(url: String, body: Any): io.ktor.client.statement.HttpResponse =
    http.post(url) {
        Session.accessToken?.let { headers.append(io.ktor.http.HttpHeaders.Authorization, "Bearer $it") }
        contentType(ContentType.Application.Json)
        setBody(body)
    }

suspend fun ApiClient.srsDue(): SRSDueDto =
    authorizedGet("$baseUrl/api/v1/srs/due").body()

suspend fun ApiClient.srsReview(cardId: Int, rating: Int): SRSReviewResponseDto =
    authorizedPost("$baseUrl/api/v1/srs/review", SRSReviewRequestDto(cardId, rating, null)).body()

suspend fun ApiClient.srsStats(): SRSStatsDto =
    authorizedGet("$baseUrl/api/v1/srs/stats").body()

suspend fun ApiClient.search(q: String, page: Int = 1, pageSize: Int = 20): QuranSearchResponseDto =
    http.get("$baseUrl/api/v1/quran/search?q=$q&page=$page&page_size=$pageSize").body()

suspend fun ApiClient.roots(minCount: Int? = null, posTag: String? = null, surahNumber: Int? = null, limit: Int = 50): RootRankResponseDto {
    val params = buildList {
        if (minCount != null) add("min_count=$minCount")
        if (posTag != null) add("pos_tag=$posTag")
        if (surahNumber != null) add("surah_number=$surahNumber")
        add("limit=$limit")
    }.joinToString("&")
    return http.get("$baseUrl/api/v1/quran/roots?$params").body()
}

suspend fun ApiClient.conjugate(root: String, form: Int): ConjugateResponseDto =
    http.post("$baseUrl/api/v1/morphology/conjugate") {
        contentType(ContentType.Application.Json)
        setBody(ConjugateRequestDto(root, form))
    }.body()

suspend fun ApiClient.wordFamily(root: String): WordFamilyResponseDto =
    http.get("$baseUrl/api/v1/morphology/word-family/$root").body()

suspend fun ApiClient.patterns(): PatternsResponseDto =
    http.get("$baseUrl/api/v1/morphology/patterns").body()

suspend fun ApiClient.badges(): BadgeListResponseDto =
    authorizedGet("$baseUrl/api/v1/progress/badges").body()
