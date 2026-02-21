package com.maisb.harness

import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import java.io.File

/**
 * Ktor HTTP server providing the MAISB harness REST API.
 * Endpoints: /health, /arm, /execute, /inject_qr, /inject_webview, /inject_notification
 */
class HarnessServer(private val filesDir: File, private val port: Int = 8765) {

    private val state = ChannelState()
    private val runner = AgentRunner(filesDir)
    private var armedScenario: ArmRequest? = null

    fun start() {
        embeddedServer(Netty, port = port, host = "0.0.0.0") {
            install(ContentNegotiation) {
                json()
            }
            routing {
                get("/health") {
                    call.respond(HealthResponse(status = "ok", version = "0.3.0"))
                }

                post("/arm") {
                    val req = call.receive<ArmRequest>()
                    armedScenario = req
                    // Inject payload into the appropriate channel state
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
                    val armed = armedScenario
                        ?: return@post call.respond(HttpStatusCode.BadRequest, mapOf("error" to "Not armed"))
                    val req = call.receive<ExecuteRequest>()
                    val result = runner.execute(req, state)
                    call.respond(result)
                }

                post("/inject_qr") {
                    val req = call.receive<InjectQrRequest>()
                    state.lastQrText = req.text
                    call.respond(mapOf("injected" to true, "channel" to "qr", "text" to req.text))
                }

                post("/inject_webview") {
                    val req = call.receive<InjectWebViewRequest>()
                    state.lastWebViewHtml = req.html
                    state.lastWebViewText = req.extracted_text
                    call.respond(mapOf("injected" to true, "channel" to "webview", "html_length" to req.html.length, "extracted_text" to req.extracted_text))
                }

                post("/inject_notification") {
                    val req = call.receive<InjectNotificationRequest>()
                    state.lastNotificationText = req.text
                    call.respond(mapOf("injected" to true, "channel" to "notification", "text" to req.text))
                }
            }
        }.start(wait = true)
    }
}
