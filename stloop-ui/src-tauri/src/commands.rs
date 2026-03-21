use crate::project::{BuildResult, EnvCheck, GenerateRequest, ProjectInfo, ProjectStatus};
use std::path::PathBuf;
use std::process::Command;
use std::time::SystemTime;
use tauri::api::path::document_dir;

#[tauri::command]
pub async fn generate_project(request: GenerateRequest) -> Result<ProjectInfo, String> {
    let projects_dir = get_projects_dir()?;
    let project_id = uuid::Uuid::new_v4().to_string();
    let project_name = request.name.unwrap_or_else(|| {
        request.prompt.split_whitespace().take(3).collect::<Vec<_>>().join("_")
    });
    let project_dir = projects_dir.join(&project_id);
    
    std::fs::create_dir_all(&project_dir).map_err(|e| e.to_string())?;
    
    // 调用 Python stloop 生成项目
    let output = Command::new("python")
        .args(&[
            "-m", "stloop",
            "generate",
            &request.prompt,
            "--board", &request.board,
            "--output", &project_dir.to_string_lossy(),
        ])
        .output()
        .map_err(|e| format!("Failed to generate: {}", e))?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok(ProjectInfo {
        id: project_id,
        name: project_name,
        path: project_dir.to_string_lossy().to_string(),
        board: request.board,
        created_at: format_time(),
        status: ProjectStatus::Created,
    })
}

#[tauri::command]
pub async fn build_project(project_id: String) -> Result<BuildResult, String> {
    let projects_dir = get_projects_dir()?;
    let project_dir = projects_dir.join(&project_id);
    
    let output = Command::new("west")
        .args(&[
            "build",
            "-p", "auto",
            "-b", "nucleo_f411re", // TODO: get from project config
            &project_dir.to_string_lossy(),
        ])
        .output()
        .map_err(|e| format!("Failed to build: {}", e))?;
    
    let success = output.status.success();
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    
    let build_output = if success { stdout } else { format!("{}\\n{}", stdout, stderr) };
    
    let elf_path = if success {
        Some(format!("{}/build/zephyr/zephyr.elf", project_dir.to_string_lossy()))
    } else {
        None
    };
    
    Ok(BuildResult {
        success,
        elf_path,
        output: build_output,
    })
}

#[tauri::command]
pub async fn flash_project(project_id: String) -> Result<(), String> {
    let projects_dir = get_projects_dir()?;
    let project_dir = projects_dir.join(&project_id);
    let build_dir = project_dir.join("build");
    
    let output = Command::new("west")
        .args(&["flash", "-d", &build_dir.to_string_lossy()])
        .output()
        .map_err(|e| format!("Failed to flash: {}", e))?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok(())
}

#[tauri::command]
pub async fn simulate_project(project_id: String) -> Result<(), String> {
    let projects_dir = get_projects_dir()?;
    let project_dir = projects_dir.join(&project_id);
    let elf_path = project_dir.join("build").join("zephyr").join("zephyr.elf");
    
    // TODO: Implement Renode integration
    println!("Simulating: {:?}", elf_path);
    Ok(())
}

#[tauri::command]
pub async fn list_projects() -> Result<Vec<ProjectInfo>, String> {
    let projects_dir = get_projects_dir()?;
    let mut projects = Vec::new();
    
    if let Ok(entries) = std::fs::read_dir(&projects_dir) {
        for entry in entries.flatten() {
            if let Ok(metadata) = entry.metadata() {
                if metadata.is_dir() {
                    // TODO: Read project metadata
                    let id = entry.file_name().to_string_lossy().to_string();
                    projects.push(ProjectInfo {
                        id,
                        name: "Unknown".to_string(),
                        path: entry.path().to_string_lossy().to_string(),
                        board: "nucleo_f411re".to_string(),
                        created_at: format_time(),
                        status: ProjectStatus::Created,
                    });
                }
            }
        }
    }
    
    Ok(projects)
}

#[tauri::command]
pub async fn get_project(project_id: String) -> Result<ProjectInfo, String> {
    let projects_dir = get_projects_dir()?;
    let project_dir = projects_dir.join(&project_id);
    
    if !project_dir.exists() {
        return Err("Project not found".to_string());
    }
    
    Ok(ProjectInfo {
        id: project_id,
        name: "Project".to_string(),
        path: project_dir.to_string_lossy().to_string(),
        board: "nucleo_f411re".to_string(),
        created_at: format_time(),
        status: ProjectStatus::Created,
    })
}

#[tauri::command]
pub async fn delete_project(project_id: String) -> Result<(), String> {
    let projects_dir = get_projects_dir()?;
    let project_dir = projects_dir.join(&project_id);
    
    std::fs::remove_dir_all(&project_dir).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn check_environment() -> Result<EnvCheck, String> {
    let west_available = which::which("west").is_ok();
    let zephyr_base = std::env::var("ZEPHYR_BASE").ok();
    let renode_available = which::which("renode").is_ok();
    
    Ok(EnvCheck {
        west_available,
        zephyr_base,
        renode_available,
    })
}

fn get_projects_dir() -> Result<PathBuf, String> {
    let docs = document_dir().ok_or("Cannot get documents directory")?;
    let projects_dir = docs.join("STLoop").join("Projects");
    std::fs::create_dir_all(&projects_dir).map_err(|e| e.to_string())?;
    Ok(projects_dir)
}

fn format_time() -> String {
    use std::time::UNIX_EPOCH;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    format!("{}", now)
}
