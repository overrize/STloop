use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct ProjectInfo {
    pub id: String,
    pub name: String,
    pub path: String,
    pub board: String,
    pub created_at: String,
    pub status: ProjectStatus,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ProjectStatus {
    Created,
    Built,
    Flashed,
    Error(String),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GenerateRequest {
    pub prompt: String,
    pub board: String,
    pub name: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BuildResult {
    pub success: bool,
    pub elf_path: Option<String>,
    pub output: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EnvCheck {
    pub west_available: bool,
    pub zephyr_base: Option<String>,
    pub renode_available: bool,
}
