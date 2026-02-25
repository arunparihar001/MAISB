package com.maisb.harness

import android.util.Log
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.call
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.plugins.statuspages.StatusPages
import io.ktor.server.plugins.statuspages.exception
import io.ktor.server.request.path
import io.ktor.server.request.receive
import io.ktor.server.request.receiveNullable
import io.ktor.server.request.receiveText
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import org.json.JSONObject
import java.io.File

/**
 * Ktor HTTP server providing the MAISB harness REST API.
 * Endpoints: /health, /arm, /execute, /inject_qr, /inject_webview, /inject_notification
 */
class HarnessServer(private val filesDir: File, private val port: Int = 8765) {

    private val state = ChannelState()
    private val runner = AgentRunner(filesDir)
    private var armedScenario: ArmRequest? = null

    // One shared JSON instance for decoding
    private val jsonParser = Json { ignoreUnknownKeys = true }

    fun start() {
        embeddedServer(Netty, port = port, host = "0.0.0.0") {

            install(ContentNegotiation) {
                json(
                    Json {
                        ignoreUnknownKeys = true
                        prettyPrint = true
                    }
                )
            }

            // Always surface exceptions (prevents "Empty reply from server")
            install(StatusPages) {
                exception<Throwable> { call, cause ->
                    Log.e("MAISB", "Ktor exception on path=${call.request.path()}", cause)

                    val msg = (cause.message ?: cause::class.java.name).replace("\"", "'")
                    call.respondText(
                        """{"ok":false,"error":"$msg"}""",
                        contentType = ContentType.Application.Json,
                        status = HttpStatusCode.InternalServerError
                    )
                }
            }

            routing {

                // Stable health endpoint
                get("/health") {
                    Log.i("MAISB", "GET /health")
                    call.respondText(
                        """{"ok":true,"version":"0.3.0"}""",
                        ContentType.Application.Json
                    )
                }

                /**
                 * /arm supports BOTH formats:
                 * A) Flat:
                 *   {"scenario_id":"...","channel":"clipboard","payload":"...","defense_profile":"D4"}
                 * B) Nested:
                 *   {"scenario_id":"...","channel":{"type":"clipboard","payload":"..."},"agent":{"defense_profile":"D4"}}
                 */
                post("/arm") {
                    Log.i("MAISB", "POST /arm")

                    val raw = call.receiveText()
                    Log.i("MAISB", "ARM RAW: $raw")

                    // 1) Try flat ArmRequest JSON directly
                    val flat: ArmRequest? = runCatching {
                        jsonParser.decodeFromString<ArmRequest>(raw)
                    }.getOrNull()

                    val req: ArmRequest = if (flat != null) {
                        flat
                    } else {
                        // 2) Fallback: parse nested structure
                        val j = JSONObject(raw)

                        val scenarioId = j.optString("scenario_id", "")

                        val channelObj = j.optJSONObject("channel")
                        val channelType = channelObj?.optString("type") ?: j.optString("channel", "")
                        val payload = channelObj?.optString("payload") ?: j.optString("payload", "")

                        val agentObj = j.optJSONObject("agent")
                        val defense = agentObj?.optString("defense_profile") ?: j.optString("defense_profile", "D4")

                        ArmRequest(
                            scenario_id = scenarioId,
                            channel = channelType,
                            payload = payload,
                            defense_profile = defense
                        )
                    }

                    armedScenario = req

                    // Inject payload into state
                    when (req.channel) {
                        "clipboard" -> state.lastClipboardText = req.payload
                        "deeplink" -> state.lastDeeplinkUrl = req.payload
                        "share" -> state.lastShareText = req.payload
                        "qr" -> state.lastQrText = req.payload
                        "webview" -> {
                            state.lastWebViewText = req.payload
                            state.lastWebViewHtml = req.payload
                        }
                        "notification" -> state.lastNotificationText = req.payload
                    }

                    call.respond(ArmResponse(armed = true, scenario_id = req.scenario_id))
                }

                post("/execute") {
                    Log.i("MAISB", "POST /execute")

                    val armed = armedScenario
                        ?: return@post call.respond(HttpStatusCode.BadRequest, mapOf("error" to "Not armed"))

                    // ✅ Do NOT read body at all. Always execute the last armed scenario.
                    val req = ExecuteRequest(
                        scenario_id = armed.scenario_id,
                        channel = armed.channel,
                        defense_profile = armed.defense_profile
                    )

                    val result = runner.execute(req, state)
                    call.respond(result)
                }

                post("/inject_qr") {
                    Log.i("MAISB", "POST /inject_qr")
                    val req = call.receive<InjectQrRequest>()
                    state.lastQrText = req.text
                    call.respond(mapOf("injected" to true, "channel" to "qr"))
                }

                post("/inject_webview") {
                    Log.i("MAISB", "POST /inject_webview")
                    val req = call.receive<InjectWebViewRequest>()
                    state.lastWebViewHtml = req.html
                    state.lastWebViewText = req.extracted_text
                    call.respond(
                        mapOf(
                            "injected" to true,
                            "channel" to "webview",
                            "html_length" to req.html.length
                        )
                    )
                }

                post("/inject_notification") {
                    Log.i("MAISB", "POST /inject_notification")
                    val req = call.receive<InjectNotificationRequest>()
                    state.lastNotificationText = req.text
                    call.respond(mapOf("injected" to true, "channel" to "notification"))
                }
            }
        }.start(wait = false)
    }
}
