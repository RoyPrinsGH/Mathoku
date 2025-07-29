package com.mathoku.core

object MathokuCore {
    init {
        System.loadLibrary("mathoku")
    }

    external fun greet(name: String): String
    external fun getDummyUserJson(): String
}
