plugins {
    id("com.android.library")
    kotlin("android")
}

android {
    namespace = "com.example.rustbridge"
    compileSdk = 34
    defaultConfig {
        minSdk = 24
        targetSdk = 34
        consumerProguardFiles("consumer-rules.pro")
    }
    sourceSets { getByName("main").jniLibs.srcDirs("src/main/jniLibs") }
}

dependencies { }