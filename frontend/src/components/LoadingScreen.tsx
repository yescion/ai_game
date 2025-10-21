/**
 * Loading Screen - API检测和游戏启动屏幕
 */
import { useEffect, useState } from 'react'
import './LoadingScreen.css'

interface ApiCheckResult {
  backend: string
  deepseek_configured: boolean
  deepseek_working: boolean
  error: string | null
}

interface LoadingScreenProps {
  onReady: () => void
}

export function LoadingScreen({ onReady }: LoadingScreenProps) {
  const [status, setStatus] = useState<'checking' | 'success' | 'error'>('checking')
  const [checkResult, setCheckResult] = useState<ApiCheckResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [retrying, setRetrying] = useState(false)

  const checkAPI = async () => {
    setStatus('checking')
    setRetrying(false)

    try {
      const response = await fetch('http://localhost:8000/api/check', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`后端服务器响应错误: ${response.status}`)
      }

      const result: ApiCheckResult = await response.json()
      setCheckResult(result)

      // 检查所有服务是否正常
      if (result.deepseek_configured && result.deepseek_working) {
        setStatus('success')
        // 延迟1秒后启动游戏，让用户看到成功提示
        setTimeout(() => {
          onReady()
        }, 1000)
      } else {
        setStatus('error')
        setErrorMessage(result.error || '未知错误')
      }
    } catch (error) {
      console.error('API检测失败:', error)
      setStatus('error')
      setErrorMessage(
        error instanceof Error 
          ? error.message 
          : '无法连接到后端服务器，请确保后端服务已启动'
      )
    }
  }

  useEffect(() => {
    checkAPI()
  }, [])

  const handleRetry = () => {
    setRetrying(true)
    setTimeout(() => {
      checkAPI()
    }, 500)
  }

  return (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="loading-header">
          <h1>🎮 模拟像素</h1>
          <p className="subtitle">AI驱动的模拟人生游戏</p>
        </div>

        <div className="loading-body">
          {status === 'checking' && (
            <div className="checking-animation">
              <div className="spinner"></div>
              <p className="status-text">
                {retrying ? '正在重试...' : '正在检测API服务...'}
              </p>
              <div className="loading-steps">
                <div className="step">
                  <span className="step-icon">🔗</span>
                  <span>连接后端服务器</span>
                </div>
                <div className="step">
                  <span className="step-icon">🔑</span>
                  <span>验证AI API配置</span>
                </div>
                <div className="step">
                  <span className="step-icon">🤖</span>
                  <span>测试AI服务可用性</span>
                </div>
              </div>
            </div>
          )}

          {status === 'success' && (
            <div className="success-animation">
              <div className="success-icon">✅</div>
              <p className="status-text success">所有服务正常！</p>
              <p className="sub-text">正在启动游戏...</p>
            </div>
          )}

          {status === 'error' && (
            <div className="error-animation">
              <div className="error-icon">❌</div>
              <p className="status-text error">API检测失败</p>
              
              <div className="error-details">
                <div className="error-box">
                  <h3>错误信息</h3>
                  <p className="error-message">{errorMessage}</p>
                </div>

                {checkResult && (
                  <div className="check-results">
                    <h3>检测结果</h3>
                    <div className="result-item">
                      <span className="result-label">后端服务器:</span>
                      <span className={`result-value ${checkResult.backend === 'ok' ? 'success' : 'error'}`}>
                        {checkResult.backend === 'ok' ? '✓ 正常' : '✗ 异常'}
                      </span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">AI API配置:</span>
                      <span className={`result-value ${checkResult.deepseek_configured ? 'success' : 'error'}`}>
                        {checkResult.deepseek_configured ? '✓ 已配置' : '✗ 未配置'}
                      </span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">AI API可用性:</span>
                      <span className={`result-value ${checkResult.deepseek_working ? 'success' : 'error'}`}>
                        {checkResult.deepseek_working ? '✓ 正常' : '✗ 异常'}
                      </span>
                    </div>
                  </div>
                )}

                <div className="solution-box">
                  <h3>💡 解决方案</h3>
                  
                  {!checkResult && (
                    <div className="solution-steps">
                      <p><strong>后端服务未运行：</strong></p>
                      <ol>
                        <li>打开项目目录</li>
                        <li>运行 <code>start_backend.bat</code> 或 <code>python backend/run.py</code></li>
                        <li>等待服务启动完成</li>
                        <li>点击"重试检测"</li>
                      </ol>
                    </div>
                  )}
                  
                  {checkResult && !checkResult.deepseek_configured && (
                    <div className="solution-steps">
                      <p><strong>方法1：使用 .env 文件（推荐）</strong></p>
                      <ol>
                        <li>在 <code>backend</code> 目录下编辑或创建 <code>.env</code> 文件</li>
                        <li>添加以下内容：
                          <pre>DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx{'\n'}DEEPSEEK_BASE_URL=https://api.deepseek.com</pre>
                        </li>
                        <li>保存文件</li>
                        <li>重启后端服务</li>
                        <li>点击"重试检测"</li>
                      </ol>
                      
                      <p><strong>方法2：代码中直接设置</strong></p>
                      <ol>
                        <li>打开 <code>backend/app/main.py</code></li>
                        <li>在第28行附近添加：
                          <pre>os.environ['DEEPSEEK_API_KEY'] = 'sk-xxx'{'\n'}os.environ['DEEPSEEK_BASE_URL'] = 'https://api.deepseek.com'</pre>
                        </li>
                        <li>保存文件</li>
                        <li>重启后端服务</li>
                        <li>点击"重试检测"</li>
                      </ol>
                      
                      <div className="tip-box">
                        <strong>🔗 获取API密钥：</strong>
                        <a href="https://platform.deepseek.com" target="_blank" rel="noopener noreferrer">
                          https://platform.deepseek.com
                        </a>
                      </div>
                    </div>
                  )}
                  
                  {checkResult && checkResult.deepseek_configured && !checkResult.deepseek_working && (
                    <div className="solution-steps">
                      <p><strong>API服务异常，请检查：</strong></p>
                      <ol>
                        <li>API密钥是否正确（登录DeepSeek平台确认）</li>
                        <li>API账户是否有余额</li>
                        <li>网络连接是否正常（尝试访问 api.deepseek.com）</li>
                        <li>DeepSeek服务是否正常（访问官网查看服务状态）</li>
                        <li>查看后端控制台的详细错误信息</li>
                      </ol>
                      
                      <div className="tip-box">
                        <strong>🔗 DeepSeek平台：</strong>
                        <a href="https://platform.deepseek.com" target="_blank" rel="noopener noreferrer">
                          https://platform.deepseek.com
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="error-actions">
                <button onClick={handleRetry} className="retry-btn">
                  🔄 重试检测
                </button>
                <button 
                  onClick={() => window.close()} 
                  className="exit-btn"
                >
                  ❌ 退出
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="loading-footer">
          <p className="version">v1.0.0</p>
          <p className="copyright">Powered by DeepSeek AI</p>
        </div>
      </div>
    </div>
  )
}

