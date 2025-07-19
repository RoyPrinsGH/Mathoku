package com.example.rustbridge

object RustBridge {
    init {
        System.loadLibrary("mathoku_core") // librust_core.so
    }
    private external fun rustcore_greeting(): String
    private external fun rustcore_greeting_for(name: String): String

    fun greeting(): String = rustcore_greeting()
    fun greetingFor(name: String): String = rustcore_greeting_for(name)
}
