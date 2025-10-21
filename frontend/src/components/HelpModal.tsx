/**
 * Help Modal - 游戏操作帮助说明
 */
import './HelpModal.css'

interface HelpModalProps {
  onClose: () => void
}

export function HelpModal({ onClose }: HelpModalProps) {
  return (
    <div className="help-modal-overlay" onClick={onClose}>
      <div className="help-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="help-modal-header">
          <h2>❓ 游戏操作帮助</h2>
          <button onClick={onClose} className="help-close-btn">✕</button>
        </div>

        <div className="help-modal-body">
          {/* 游戏画布操作 */}
          <section className="help-section">
            <h3>🎮 游戏画布操作</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">🖱️</div>
                <div className="help-text">
                  <strong>鼠标滚轮</strong>
                  <p>向上滚动放大地图，向下滚动缩小地图（0.5x - 3.0x）</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">👆</div>
                <div className="help-text">
                  <strong>鼠标拖拽</strong>
                  <p>按住鼠标左键拖动可以平移地图视角</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">👥</div>
                <div className="help-text">
                  <strong>点击NPC</strong>
                  <p>点击地图上的NPC角色可以选中并查看其详细信息</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">📦</div>
                <div className="help-text">
                  <strong>点击资源点</strong>
                  <p>点击树木🌲、石头🪨、浆果丛🌿等资源点查看资源信息</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🐺</div>
                <div className="help-text">
                  <strong>点击野兽</strong>
                  <p>点击野兽可以查看其状态、生命值和攻击性</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🏗️</div>
                <div className="help-text">
                  <strong>点击建筑</strong>
                  <p>点击建筑可以查看建造进度和建筑详情</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🔄</div>
                <div className="help-text">
                  <strong>重置视图按钮</strong>
                  <p>点击右下角的🔄按钮可以重置地图缩放和位置到初始状态</p>
                </div>
              </div>
            </div>
          </section>

          {/* NPC面板 */}
          <section className="help-section">
            <h3>👥 居民状态面板（右侧）</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">📋</div>
                <div className="help-text">
                  <strong>NPC列表</strong>
                  <p>显示所有居民的状态，包括健康度❤️和饥饿度🍖</p>
                  <p className="help-note">💡 提示：存活的NPC排在前面，死亡的标记为💀</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🔍</div>
                <div className="help-text">
                  <strong>点击NPC查看详情</strong>
                  <p>点击列表中的任意NPC可以展开详细信息面板</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">📍</div>
                <div className="help-text">
                  <strong>详细信息包括</strong>
                  <ul>
                    <li>位置坐标</li>
                    <li>当前行动和状态</li>
                    <li>🤖 AI思考过程和决策理由</li>
                    <li>属性：健康、饥饿、体力</li>
                    <li>技能等级</li>
                    <li>背包物品</li>
                    <li>装备工具及耐久度</li>
                    <li>职业角色</li>
                    <li>📋 当前待办事项</li>
                    <li>📜 行动日志（最近10条）</li>
                    <li>💭 记忆（最近8条）</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* 事件时间轴 */}
          <section className="help-section">
            <h3>📜 世界事件（左侧）</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">⏱️</div>
                <div className="help-text">
                  <strong>事件流</strong>
                  <p>实时显示游戏中发生的所有事件，按时间顺序自动滚动</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🔎</div>
                <div className="help-text">
                  <strong>NPC筛选</strong>
                  <p>使用顶部下拉菜单可以筛选特定NPC的相关事件</p>
                  <p className="help-note">选择"所有事件"查看完整事件流</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🎨</div>
                <div className="help-text">
                  <strong>事件图标</strong>
                  <p>不同类型的事件有不同的图标：</p>
                  <ul>
                    <li>🤖 AI思考决策</li>
                    <li>⛏️ 采集资源</li>
                    <li>🏗️ 建造建筑</li>
                    <li>😴 休息</li>
                    <li>🍖 进食</li>
                    <li>💬 交流对话</li>
                    <li>⚔️ 战斗</li>
                    <li>💀 死亡</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* 顶部信息栏 */}
          <section className="help-section">
            <h3>🎯 顶部信息栏</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">⏰</div>
                <div className="help-text">
                  <strong>游戏时间</strong>
                  <p>显示当前游戏内的日期和时间（游戏时间流速是现实的60倍）</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🌸</div>
                <div className="help-text">
                  <strong>季节</strong>
                  <p>显示当前季节：春夏秋冬（影响环境和NPC行为）</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🌦️</div>
                <div className="help-text">
                  <strong>天气</strong>
                  <p>显示当前天气状况：</p>
                  <ul>
                    <li>☀️ 晴天 - 正常状态</li>
                    <li>☁️ 阴天 - 轻微影响</li>
                    <li>🌧️ 雨天 - 降低体力恢复</li>
                    <li>⛈️ 暴风雨 - 危险天气</li>
                  </ul>
                  <p className="help-note">💡 天气会影响NPC的体力和健康恢复速度</p>
                </div>
              </div>
            </div>
          </section>

          {/* 特殊功能 */}
          <section className="help-section">
            <h3>⚡ 特殊功能按钮（右下角）</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">🔮</div>
                <div className="help-text">
                  <strong>上帝指令控制台（底部）</strong>
                  <p>点击紫蓝色按钮打开上帝模式，可以：</p>
                  <ul>
                    <li>为NPC添加记忆</li>
                    <li>修改指定NPC的某条记忆</li>
                    <li>清除NPC的所有记忆</li>
                  </ul>
                  <p className="help-note">⚠️ 这是调试功能，会影响AI行为</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">📊</div>
                <div className="help-text">
                  <strong>管理面板（上方）</strong>
                  <p>点击粉紫色按钮打开详细的游戏数据面板</p>
                  <p>包含7个标签页：</p>
                  <ul>
                    <li>📊 概览 - 统计数据和全局资源</li>
                    <li>👥 NPC - 详细NPC数据和AI思考记录</li>
                    <li>🐺 野兽 - 所有野兽信息</li>
                    <li>📦 资源 - 资源点分布和数量</li>
                    <li>🏗️ 建筑 - 建筑信息和进度</li>
                    <li>📜 事件 - 完整事件历史</li>
                    <li>⚙️ 配置 - 游戏参数和运行状态</li>
                  </ul>
                  <p className="help-note">💡 支持自动刷新，可查看天气变化倒计时</p>
                </div>
              </div>
            </div>
          </section>

          {/* 游戏机制 */}
          <section className="help-section">
            <h3>🎲 核心游戏机制</h3>
            <div className="help-content">
              <div className="help-item">
                <div className="help-icon">🤖</div>
                <div className="help-text">
                  <strong>AI驱动</strong>
                  <p>所有NPC由AI自主决策，每30秒（游戏时间）做一次决策</p>
                  <p className="help-note">可在管理面板中查看完整的AI思考过程</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">⏳</div>
                <div className="help-text">
                  <strong>时间系统</strong>
                  <p>时间缩放：1秒现实时间 = 60秒游戏时间</p>
                  <p>昼夜循环：影响NPC行为和危险程度</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">💪</div>
                <div className="help-text">
                  <strong>属性系统</strong>
                  <ul>
                    <li>❤️ 健康：受伤或饥饿会降低，归零则死亡</li>
                    <li>🍖 饥饿：随时间增加，需要进食，过高会掉血</li>
                    <li>⚡ 体力：工作消耗，休息恢复，影响行动效率</li>
                  </ul>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🎯</div>
                <div className="help-text">
                  <strong>技能成长</strong>
                  <p>NPC通过执行相关行动提升技能等级</p>
                  <p>技能影响行动效率和成功率</p>
                </div>
              </div>
              <div className="help-item">
                <div className="help-icon">🏠</div>
                <div className="help-text">
                  <strong>建筑系统</strong>
                  <p>NPC可以建造庇护所、工作站等建筑</p>
                  <p>建筑提供各种增益效果（如恶劣天气保护）</p>
                </div>
              </div>
            </div>
          </section>

          {/* 快捷提示 */}
          <section className="help-section help-section-tips">
            <h3>💡 实用技巧</h3>
            <div className="help-content">
              <div className="tip-item">
                <span className="tip-icon">🎯</span>
                <span>选中NPC后，地图会自动聚焦到该NPC位置</span>
              </div>
              <div className="tip-item">
                <span className="tip-icon">👁️</span>
                <span>NPC头顶的视野锥表示他们的观察范围</span>
              </div>
              <div className="tip-item">
                <span className="tip-icon">⚠️</span>
                <span>夜间更危险，NPC会优先寻找庇护所</span>
              </div>
              <div className="tip-item">
                <span className="tip-icon">🌧️</span>
                <span>恶劣天气下，建筑内的NPC不受影响</span>
              </div>
              <div className="tip-item">
                <span className="tip-icon">📊</span>
                <span>使用管理面板可以深入了解游戏运作机制</span>
              </div>
              <div className="tip-item">
                <span className="tip-icon">🔮</span>
                <span>上帝指令可以引导NPC的行为和发展</span>
              </div>
            </div>
          </section>
        </div>

        <div className="help-modal-footer">
          <p>🎮 享受你的模拟人生之旅！作者微信：DreamingKingdom</p>
          <button onClick={onClose} className="help-ok-btn">我知道了</button>
        </div>
      </div>
    </div>
  )
}

