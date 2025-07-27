package com.mathoku.core

object MathokuCore {
    init {
        // The library name is the Rust crate name without "lib" prefix
        System.loadLibrary("mathoku")
    }

    external fun greet(name: String): String
}
