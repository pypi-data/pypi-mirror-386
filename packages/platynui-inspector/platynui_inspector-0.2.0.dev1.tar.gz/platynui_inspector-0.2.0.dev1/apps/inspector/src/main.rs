#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() -> Result<(), slint::PlatformError> {
    platynui_inspector::run()
}
