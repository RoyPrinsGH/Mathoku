use std::thread::sleep;

mod ffi;

pub mod models;

fn get_dummy_user_json() -> String {
    let user = models::User {
        id: 1,
        name: "John Doe".to_string(),
        email: "john.doe@example.com".to_string(),
    };

    sleep(std::time::Duration::from_secs(5)); // Simulate some processing delay

    serde_json::to_string(&user).unwrap()
}
