use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LLMConfig {
    pub api_key: String,
    pub base_url: Option<String>,
    pub model: String,
}

impl Default for LLMConfig {
    fn default() -> Self {
        Self {
            api_key: String::new(),
            base_url: Some("https://api.openai.com/v1".to_string()),
            model: "gpt-4".to_string(),
        }
    }
}

impl LLMConfig {
    pub fn load() -> Result<Self, String> {
        let config_path = Self::config_path()?;
        
        if !config_path.exists() {
            return Ok(Self::default());
        }
        
        let content = std::fs::read_to_string(&config_path)
            .map_err(|e| format!("Failed to read config: {}", e))?;
        
        let config: LLMConfig = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse config: {}", e))?;
        
        Ok(config)
    }
    
    pub fn save(&self) -> Result<(), String> {
        let config_path = Self::config_path()?;
        
        if let Some(parent) = config_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create config dir: {}", e))?;
        }
        
        let content = serde_json::to_string_pretty(self)
            .map_err(|e| format!("Failed to serialize config: {}", e))?;
        
        std::fs::write(&config_path, content)
            .map_err(|e| format!("Failed to write config: {}", e))?;
        
        Ok(())
    }
    
    fn config_path() -> Result<PathBuf, String> {
        let home = dirs::home_dir()
            .ok_or("Failed to get home directory")?;
        Ok(home.join(".config").join("stloop").join("config.json"))
    }
    
    pub fn validate(&self) -> Result<(), String> {
        if self.api_key.is_empty() {
            return Err("API key is required. Please set it in settings.".to_string());
        }
        Ok(())
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMRequest {
    pub prompt: String,
    pub board: String,
}

#[derive(Debug, Deserialize)]
struct OpenAIResponse {
    choices: Vec<Choice>,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: Message,
}

#[derive(Debug, Deserialize)]
struct Message {
    content: String,
}

pub async fn generate_code(prompt: &str, board: &str, config: &LLMConfig) -> Result<String, String> {
    config.validate()?;
    
    let client = reqwest::Client::new();
    let base_url = config.base_url.as_deref().unwrap_or("https://api.openai.com/v1");
    
    let system_prompt = format!(
        "You are a Zephyr RTOS expert for {}. Generate C code following these rules:\n\n\
        1. Headers: #include <zephyr/kernel.h>, #include <zephyr/drivers/gpio.h>\n\
        2. Use GPIO_DT_SPEC_GET for hardware access\n\
        3. Use k_msleep for delays\n\
        4. Output only valid C code, no markdown or explanations",
        board
    );
    
    let response = client
        .post(format!("{}/chat/completions", base_url))
        .header("Authorization", format!("Bearer {}", config.api_key))
        .json(&serde_json::json!({
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }))
        .send()
        .await
        .map_err(|e| handle_request_error(e))?;
    
    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(format!("API error ({}): {}", status, text));
    }
    
    let data: OpenAIResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    let code = data
        .choices
        .get(0)
        .map(|c| c.message.content.clone())
        .ok_or("No response from API")?;
    
    let code = extract_code_block(&code);
    
    Ok(code.trim().to_string())
}

fn extract_code_block(text: &str) -> String {
    if text.contains("```c") {
        text.split("```c")
            .nth(1)
            .and_then(|s| s.split("```").next())
            .unwrap_or(text)
            .to_string()
    } else if text.contains("```") {
        text.split("```")
            .nth(1)
            .and_then(|s| s.split("```").next())
            .unwrap_or(text)
            .to_string()
    } else {
        text.to_string()
    }
}

fn handle_request_error(e: reqwest::Error) -> String {
    if e.is_connect() {
        "Connection failed. Please check your internet connection.".to_string()
    } else if e.is_timeout() {
        "Request timed out. Please try again.".to_string()
    } else if e.status().map(|s| s == 401).unwrap_or(false) {
        "Invalid API key. Please check your settings.".to_string()
    } else if e.status().map(|s| s == 429).unwrap_or(false) {
        "Rate limit exceeded. Please wait a moment.".to_string()
    } else {
        format!("Request failed: {}", e)
    }
}
