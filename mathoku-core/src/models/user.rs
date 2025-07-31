use serde::{
    Deserialize,
    Serialize,
};

// Just a simple user model for demonstration purposes
#[typeshare::typeshare]
#[derive(Serialize, Deserialize)]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
}
