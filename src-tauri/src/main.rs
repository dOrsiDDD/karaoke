// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use std::fs;

#[tauri::command]
fn save_audio(filename: String, data: Vec<u8>) -> Result<(), String> {
    fs::write(filename, data).map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![save_audio])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}