package com.mathoku.ui.rn

import com.facebook.react.bridge.*
import com.mathoku.core.MathokuCore  // from your wrapper

class MathokuNativeModule(private val reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String = "MathokuNative"

    @ReactMethod
    fun greet(name: String, promise: Promise) {
        try {
            val result = MathokuCore.greet(name)
            promise.resolve(result)
        } catch (e: Throwable) {
            promise.reject("GREETING_ERROR", e)
        }
    }
}
