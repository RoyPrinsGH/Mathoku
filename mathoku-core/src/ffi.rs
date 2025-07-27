use jni::JNIEnv;
use jni::objects::{JClass, JString};
use jni::sys::jstring;

#[unsafe(no_mangle)]
pub extern "system" fn Java_com_mathoku_core_MathokuCore_greet(
    mut env: JNIEnv,
    _class: JClass,
    name: JString,
) -> jstring {
    let input: String = env.get_string(&name).expect("invalid string").into();
    let response = format!("Hello, {input} from Rust!");
    env.new_string(response)
        .expect("Couldn't create java string")
        .into_raw()
}
