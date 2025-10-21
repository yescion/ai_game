/**
 * Object Info Panel - Displays information about selected resources and beasts
 */
import { useGameStore } from '../store/gameStore'
import './ObjectInfoPanel.css'

export function ObjectInfoPanel() {
  const resources = useGameStore((state) => state.resources)
  const beasts = useGameStore((state) => state.beasts)
  const buildings = useGameStore((state) => state.buildings)
  const selectedResourceId = useGameStore((state) => state.selectedResourceId)
  const selectedBeastId = useGameStore((state) => state.selectedBeastId)
  const selectedBuildingId = useGameStore((state) => state.selectedBuildingId)
  const selectResource = useGameStore((state) => state.selectResource)
  const selectBeast = useGameStore((state) => state.selectBeast)
  const selectBuilding = useGameStore((state) => state.selectBuilding)

  const selectedResource = resources.find((r) => r.id === selectedResourceId)
  const selectedBeast = beasts.find((b) => b.id === selectedBeastId)
  const selectedBuilding = buildings.find((b) => b.id === selectedBuildingId)

  if (!selectedResource && !selectedBeast && !selectedBuilding) {
    return null
  }

  const handleClose = () => {
    selectResource(null)
    selectBeast(null)
    selectBuilding(null)
  }

  // 🎯 点击背景关闭面板
  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }

  // 资源信息显示
  if (selectedResource) {
    const resourceTypeNames: Record<string, string> = {
      wood: '🌳 树木',
      stone: '🪨 石头',
      berry: '🫐 浆果',
      water: '💧 水源',
    }

    const resourceName = resourceTypeNames[selectedResource.type] || selectedResource.type

    return (
      <div className="object-info-panel-overlay" onClick={handleBackgroundClick}>
        <div className="object-info-panel">
          <div className="panel-header">
            <h3>{resourceName}</h3>
            <button className="close-button" onClick={handleClose}>
              ✕
            </button>
          </div>

        <div className="panel-content">
          <div className="info-section">
            <strong>📍 位置:</strong>
            <div className="info-value">
              ({selectedResource.position.x.toFixed(1)}, {selectedResource.position.y.toFixed(1)})
            </div>
          </div>

          <div className="info-section">
            <strong>📦 资源量:</strong>
            <div className="info-value">
              {selectedResource.quantity.toFixed(0)} / {selectedResource.max_quantity}
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${(selectedResource.quantity / selectedResource.max_quantity) * 100}%`,
                    backgroundColor: selectedResource.is_depleted ? '#ff4444' : '#44ff44',
                  }}
                />
              </div>
            </div>
          </div>

          <div className="info-section">
            <strong>⚡ 状态:</strong>
            <div className="info-value">
              {selectedResource.is_depleted ? (
                <span className="status-depleted">❌ 已枯竭</span>
              ) : selectedResource.quantity < selectedResource.max_quantity * 0.3 ? (
                <span className="status-low">⚠️ 资源稀少</span>
              ) : (
                <span className="status-normal">✅ 资源充足</span>
              )}
            </div>
          </div>

          <div className="info-section">
            <strong>🔄 再生速度:</strong>
            <div className="info-value">{selectedResource.regeneration_rate.toFixed(1)} / 秒</div>
          </div>

          <div className="info-section">
            <strong>⭐ 品质:</strong>
            <div className="info-value">{'★'.repeat(selectedResource.quality)}</div>
          </div>
        </div>
        </div>
      </div>
    )
  }

  // 野兽信息显示
  if (selectedBeast) {
    const beastIcon = selectedBeast.is_aggressive ? '🐺' : '🐰'
    const beastType = selectedBeast.is_aggressive ? '攻击性' : '温和'

    return (
      <div className="object-info-panel-overlay" onClick={handleBackgroundClick}>
        <div className="object-info-panel">
          <div className="panel-header">
            <h3>
              {beastIcon} {selectedBeast.name || '野兽'}
            </h3>
            <button className="close-button" onClick={handleClose}>
              ✕
            </button>
          </div>

        <div className="panel-content">
          <div className="info-section">
            <strong>📍 位置:</strong>
            <div className="info-value">
              ({selectedBeast.position.x.toFixed(1)}, {selectedBeast.position.y.toFixed(1)})
            </div>
          </div>

          <div className="info-section">
            <strong>🏷️ 类型:</strong>
            <div className="info-value">
              <span className={selectedBeast.is_aggressive ? 'aggressive' : 'passive'}>
                {beastType}
              </span>
            </div>
          </div>

          <div className="info-section">
            <strong>💪 生命值:</strong>
            <div className="info-value">
              {selectedBeast.health.toFixed(0)} / {selectedBeast.max_health}
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${(selectedBeast.health / selectedBeast.max_health) * 100}%`,
                    backgroundColor: '#ff6666',
                  }}
                />
              </div>
            </div>
          </div>

          <div className="info-section">
            <strong>⚔️ 攻击力:</strong>
            <div className="info-value">{selectedBeast.damage}</div>
          </div>

          <div className="info-section">
            <strong>🎯 行动:</strong>
            <div className="info-value">{selectedBeast.action || '休息中'}</div>
          </div>
        </div>
        </div>
      </div>
    )
  }

  // 🏗️ 建筑信息显示
  if (selectedBuilding) {
    const buildingIcon = selectedBuilding.is_complete ? '🏠' : '🔨'
    const statusText = selectedBuilding.is_complete 
      ? '✅ 已完成' 
      : `🔨 建造中 (${Math.round(selectedBuilding.construction_progress * 100)}%)`

    return (
      <div className="object-info-panel-overlay" onClick={handleBackgroundClick}>
        <div className="object-info-panel">
          <div className="panel-header">
            <h3>
              {buildingIcon} {selectedBuilding.name}
            </h3>
            <button className="close-button" onClick={handleClose}>
              ✕
            </button>
          </div>

          <div className="panel-content">
            <div className="info-section">
              <strong>📍 位置:</strong>
              <div className="info-value">
                ({selectedBuilding.position.x.toFixed(1)}, {selectedBuilding.position.y.toFixed(1)})
              </div>
            </div>

            <div className="info-section">
              <strong>📏 尺寸:</strong>
              <div className="info-value">
                {selectedBuilding.size.x} × {selectedBuilding.size.y}
              </div>
            </div>

            <div className="info-section">
              <strong>⚡ 状态:</strong>
              <div className="info-value">
                <span className={selectedBuilding.is_complete ? 'status-normal' : 'status-low'}>
                  {statusText}
                </span>
                {!selectedBuilding.is_complete && (
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${selectedBuilding.construction_progress * 100}%`,
                        backgroundColor: '#ffaa00',
                      }}
                    />
                  </div>
                )}
              </div>
            </div>

            {selectedBuilding.builders && selectedBuilding.builders.length > 0 && (
              <div className="info-section">
                <strong>👷 建造者:</strong>
                <div className="info-value">
                  {selectedBuilding.builders.length} 人正在建造
                </div>
              </div>
            )}

            {selectedBuilding.description && (
              <div className="info-section">
                <strong>📝 描述:</strong>
                <div className="info-value">{selectedBuilding.description}</div>
              </div>
            )}

            {selectedBuilding.provides_shelter && (
              <div className="info-section">
                <strong>🏠 功能:</strong>
                <div className="info-value">
                  {selectedBuilding.provides_shelter && '✓ 提供庇护所'}
                  {selectedBuilding.provides_warmth && ' ✓ 提供温暖'}
                  {selectedBuilding.provides_cooking && ' ✓ 可以烹饪'}
                </div>
              </div>
            )}

            {(selectedBuilding.health_regen_bonus > 0 || selectedBuilding.stamina_regen_bonus > 0) && (
              <div className="info-section">
                <strong>💪 加成:</strong>
                <div className="info-value">
                  {selectedBuilding.health_regen_bonus > 0 && 
                    `生命恢复 +${(selectedBuilding.health_regen_bonus * 100).toFixed(0)}% `}
                  {selectedBuilding.stamina_regen_bonus > 0 && 
                    `体力恢复 +${(selectedBuilding.stamina_regen_bonus * 100).toFixed(0)}%`}
                </div>
              </div>
            )}

            {selectedBuilding.capacity > 0 && (
              <div className="info-section">
                <strong>👥 容量:</strong>
                <div className="info-value">{selectedBuilding.capacity} 人</div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return null
}

