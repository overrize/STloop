import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { X, Check, AlertCircle } from 'lucide-react';
import './SettingsModal.css';

interface SettingsModalProps {
  onClose: () => void;
}

interface LLMConfig {
  api_key: string;
  base_url: string | null;
  model: string;
}

export function SettingsModal({ onClose }: SettingsModalProps) {
  const [config, setConfig] = useState<LLMConfig>({
    api_key: '',
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-4'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');
  const [error, setError] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const savedConfig = await invoke<LLMConfig>('get_llm_config');
      setConfig({
        api_key: savedConfig.api_key || '',
        base_url: savedConfig.base_url || 'https://api.openai.com/v1',
        model: savedConfig.model || 'gpt-4'
      });
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      await invoke('save_llm_config', { 
        config: {
          api_key: config.api_key,
          base_url: config.base_url || null,
          model: config.model
        }
      });
      
      // Validate after saving
      const isValid = await invoke<boolean>('validate_llm_config');
      setValidationStatus(isValid ? 'valid' : 'invalid');
      
      if (isValid) {
        setTimeout(() => {
          onClose();
        }, 1000);
      }
    } catch (error) {
      setError(`保存失败: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidate = async () => {
    setIsLoading(true);
    setValidationStatus('idle');
    setError('');
    
    try {
      const isValid = await invoke<boolean>('validate_llm_config');
      setValidationStatus(isValid ? 'valid' : 'invalid');
    } catch (error) {
      setValidationStatus('invalid');
      setError(`验证失败: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>LLM 设置</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label>API Key</label>
            <input
              type="password"
              value={config.api_key}
              onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
              placeholder="sk-..."
            />
            <small>你的 OpenAI 或 Kimi API Key</small>
          </div>

          <div className="form-group">
            <label>Base URL (可选)</label>
            <input
              type="text"
              value={config.base_url || ''}
              onChange={(e) => setConfig({ ...config, base_url: e.target.value || null })}
              placeholder="https://api.openai.com/v1"
            />
            <small>自定义 API 端点，留空使用 OpenAI 默认</small>
          </div>

          <div className="form-group">
            <label>模型</label>
            <input
              type="text"
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              placeholder="gpt-4"
            />
            <small>例如: gpt-4, gpt-3.5-turbo, kimi-k2.5</small>
          </div>

          {error && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {validationStatus === 'valid' && (
            <div className="success-message">
              <Check size={16} />
              <span>配置有效</span>
            </div>
          )}

          {validationStatus === 'invalid' && (
            <div className="error-message">
              <AlertCircle size={16} />
              <span>配置无效，请检查 API Key</span>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button 
            className="btn-secondary" 
            onClick={handleValidate}
            disabled={isLoading}
          >
            {isLoading ? '验证中...' : '验证'}
          </button>
          <button 
            className="btn-primary" 
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
}
