#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod llm;
mod project;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let window = app.get_window("main").unwrap();
            window.set_title("STLoop").unwrap();
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::generate_project,
            commands::build_project,
            commands::flash_project,
            commands::simulate_project,
            commands::list_projects,
            commands::get_project,
            commands::delete_project,
            commands::check_environment,
            commands::get_llm_config,
            commands::save_llm_config,
            commands::validate_llm_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
