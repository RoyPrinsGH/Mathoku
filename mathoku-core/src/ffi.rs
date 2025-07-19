use std::ffi::{CStr, CString};
use std::os::raw::c_char;

#[unsafe(no_mangle)]
pub extern "C" fn rustcore_greeting() -> *mut c_char {
    let s = CString::new("Hello from Rust core!").unwrap();
    s.into_raw()
}

#[unsafe(no_mangle)]
pub extern "C" fn rustcore_greeting_for(name: *const c_char) -> *mut c_char {
    let cstr = unsafe { CStr::from_ptr(name) };
    let name_str = cstr.to_str().unwrap_or("<invalid>");
    let msg = format!("Hello, {name_str}, from Rust!");
    CString::new(msg).unwrap().into_raw()
}

#[unsafe(no_mangle)]
pub extern "C" fn rustcore_string_free(ptr: *mut c_char) {
    if ptr.is_null() {
        return;
    }
    unsafe {
        let _ = CString::from_raw(ptr);
    }
}
