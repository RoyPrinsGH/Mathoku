@Suppress("UnstableApiUsage")
plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    `maven-publish`
}

android {
    namespace = "com.mathoku.core"
    compileSdk = 34

    defaultConfig {
        minSdk = 24
        targetSdk = 34
        consumerProguardFiles("consumer-rules.pro")
    }

    buildTypes {
        release { isMinifyEnabled = false }
        debug { }
    }

    sourceSets {
        getByName("main") {
            // jniLibs auto-detected if in src/main/jniLibs, but we can be explicit:
            jniLibs.srcDirs("src/main/jniLibs")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

kotlin {
    jvmToolchain(17)   // Ensures Kotlin uses same
}

dependencies {
    // optional; plugin would add it
    implementation(kotlin("stdlib"))
}

publishing {
    publications {
        create<MavenPublication>("release") {
            groupId = "com.mathoku"
            artifactId = "kotlin-rust-wrapper"
            version = "0.1.0"
            afterEvaluate { from(components["release"]) }
        }
    }
}
