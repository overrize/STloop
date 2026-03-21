use serde::{Deserialize, Serialize};

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

pub async fn generate_code(prompt: &str, board: &str, api_key: &str) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let system_prompt = format!(
        "You are a Zephyr RTOS expert for {}. Generate C code following these rules:\\n\\n\
        1. Headers: #include <zephyr/kernel.h>, #include <zephyr/drivers/gpio.h>\\n\
        2. Use GPIO_DT_SPEC_GET for hardware access\\n\
        3. Use k_msleep for delays\\n\
        4. Output only valid C code, no markdown or explanations",
        board
    );
    
    let response = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&serde_json::json!({
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }))
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;
    
    let data: OpenAIResponse = response
        .json()
        .await
        .map_err(|e| format!("Parse failed: {}", e))?;
    
    let code = data
        .choices
        .get(0)
        .map(|c| c.message.content.clone())
        .ok_or("No response")?;
    
    // Extract code from markdown if present
    let code = if code.contains("```c") {
        code.split("```c").nth(1).unwrap_or(&code).split("```").next().unwrap_or(&code).to_string()
    } else if code.contains("```") {
        code.split("```").nth(1).unwrap_or(&code).split("```").next().unwrap_or(&code).to_string()
    } else {
        code
    };
    
    Ok(code.trim().to_string())
}
