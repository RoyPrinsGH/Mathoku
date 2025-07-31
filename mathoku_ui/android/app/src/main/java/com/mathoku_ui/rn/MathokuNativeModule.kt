package com.mathoku.ui.rn

import com.facebook.react.bridge.*
import com.mathoku.core.MathokuCore // from your wrapper
import kotlinx.coroutines.*

class MathokuNativeModule(private val reactContext: ReactApplicationContext) :
        ReactContextBaseJavaModule(reactContext), LifecycleEventListener {

    override fun getName(): String = "MathokuNative"

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    init {
        reactContext.addLifecycleEventListener(this)
    }

    @ReactMethod
    fun greet(name: String, promise: Promise) {
        try {
            val result = MathokuCore.greet(name)
            promise.resolve(result)
        } catch (e: Throwable) {
            promise.reject("GREETING_ERROR", e)
        }
    }

    @ReactMethod
    fun getDummyUserJson(promise: Promise) {
        scope.launch {
            try {
                val json = MathokuCore.getDummyUserJson()
                withContext(Dispatchers.Main) { promise.resolve(json) }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { promise.reject("DUMMY_USER_ERROR", e) }
            }
        }
    }

    override fun onHostDestroy() {
        scope.cancel()
        reactContext.removeLifecycleEventListener(this)
    }

    override fun onHostResume() {}
    override fun onHostPause() {}
}
