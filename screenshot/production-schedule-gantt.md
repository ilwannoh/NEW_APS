import React, { useState } from 'react';

const ProductionScheduler = () => {
  // 간소화된 스케줄 데이터 - 4구간(각 2시간), 공정 순서대로 연결
  const [scheduleData, setScheduleData] = useState([
    {
      equipment: "칭량기1",
      tasks: [
        { id: 1, product: "기넥신에프정 001", batch: "B001", slot: 0, duration: 1, color: "#3B82F6" },
        { id: 2, product: "페브릭정 001", batch: "B002", slot: 2, duration: 1, color: "#EF4444" }
      ]
    },
    {
      equipment: "혼합기1", 
      tasks: [
        { id: 3, product: "기넥신에프정 001", batch: "B001", slot: 1, duration: 1, color: "#3B82F6" },
        { id: 4, product: "페브릭정 001", batch: "B002", slot: 3, duration: 1, color: "#EF4444" }
      ]
    },
    {
      equipment: "타정기1",
      tasks: [
        { id: 5, product: "기넥신에프정 001", batch: "B001", slot: 2, duration: 2, color: "#3B82F6" }
      ]
    }
  ]);

  // 4개 시간 구간 (각 2시간씩)
  const timeSlots = ['1구간', '2구간', '3구간', '4구간'];
  
  // 드래그 상태 관리
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverSlot, setDragOverSlot] = useState(null);

  // 배치 연결선 그리기를 위한 함수
  const getConnectionLines = () => {
    const lines = [];
    const batches = {};
    
    // 배치별로 작업들을 그룹화
    scheduleData.forEach((equipment, equipmentIndex) => {
      equipment.tasks.forEach(task => {
        if (!batches[task.batch]) {
          batches[task.batch] = [];
        }
        batches[task.batch].push({
          ...task,
          equipmentIndex,
          equipment: equipment.equipment
        });
      });
    });

    // 각 배치의 공정 순서에 따른 연결선 생성
    Object.values(batches).forEach(batchTasks => {
      const sortedTasks = batchTasks.sort((a, b) => {
        const equipmentOrder = { "칭량기1": 0, "혼합기1": 1, "타정기1": 2 };
        return equipmentOrder[a.equipment] - equipmentOrder[b.equipment];
      });

      for (let i = 0; i < sortedTasks.length - 1; i++) {
        const current = sortedTasks[i];
        const next = sortedTasks[i + 1];
        
        lines.push({
          from: { 
            equipment: current.equipmentIndex, 
            slot: current.slot + current.duration - 1,
            color: current.color
          },
          to: { 
            equipment: next.equipmentIndex, 
            slot: next.slot,
            color: next.color
          }
        });
      }
    });

    return lines;
  };

  // 드래그 시작
  const handleDragStart = (e, task, equipmentIndex) => {
    setDraggedTask({ ...task, equipmentIndex });
    e.dataTransfer.effectAllowed = 'move';
  };

  // 드래그 오버
  const handleDragOver = (e, equipmentIndex, slotIndex) => {
    e.preventDefault();
    setDragOverSlot({ equipmentIndex, slotIndex });
  };

  // 드롭 처리 - 테트리스처럼 연결 검증
  const handleDrop = (e, equipmentIndex, slotIndex) => {
    e.preventDefault();
    if (!draggedTask) return;

    // 같은 배치의 이전/다음 공정과의 연결성 검증
    const canPlace = validatePlacement(draggedTask, equipmentIndex, slotIndex);
    
    if (canPlace) {
      const newData = [...scheduleData];
      
      // 기존 위치에서 제거
      newData[draggedTask.equipmentIndex].tasks = newData[draggedTask.equipmentIndex].tasks.filter(
        task => task.id !== draggedTask.id
      );
      
      // 새 위치에 추가
      const updatedTask = { ...draggedTask, slot: slotIndex };
      newData[equipmentIndex].tasks.push(updatedTask);
      
      setScheduleData(newData);
    }
    
    setDraggedTask(null);
    setDragOverSlot(null);
  };

  // 배치 가능성 검증 (테트리스 룰)
  const validatePlacement = (task, equipmentIndex, slotIndex) => {
    const equipmentNames = ["칭량기1", "혼합기1", "타정기1"];
    const currentEquipment = equipmentNames[equipmentIndex];
    
    // 같은 배치의 다른 작업들 찾기
    const sameBatchTasks = [];
    scheduleData.forEach((equipment, eqIndex) => {
      equipment.tasks.forEach(t => {
        if (t.batch === task.batch && t.id !== task.id) {
          sameBatchTasks.push({
            ...t,
            equipmentName: equipmentNames[eqIndex]
          });
        }
      });
    });

    // 공정 순서 검증
    const equipmentOrder = { "칭량기1": 0, "혼합기1": 1, "타정기1": 2 };
    const currentOrder = equipmentOrder[currentEquipment];
    
    for (const otherTask of sameBatchTasks) {
      const otherOrder = equipmentOrder[otherTask.equipmentName];
      
      if (currentOrder === otherOrder + 1) {
        // 다음 공정인 경우: 이전 공정이 끝나는 시점과 연결되어야 함
        if (slotIndex !== otherTask.slot + otherTask.duration) {
          return false;
        }
      } else if (currentOrder === otherOrder - 1) {
        // 이전 공정인 경우: 다음 공정 시작 전에 끝나야 함
        if (slotIndex + task.duration !== otherTask.slot) {
          return false;
        }
      }
    }
    
    return true;
  };

  const connectionLines = getConnectionLines();

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">생산계획 스케줄링 (테트리스 스타일)</h1>
        
        {/* 범례 */}
        <div className="flex gap-6 mb-6">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded shadow-sm"></div>
            <span className="text-sm font-medium">기넥신에프정 (B001)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded shadow-sm"></div>
            <span className="text-sm font-medium">페브릭정 (B002)</span>
          </div>
        </div>

        {/* 스케줄 그리드 */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden relative">
          {/* 시간 헤더 */}
          <div className="flex border-b border-gray-200">
            <div className="w-32 p-4 bg-gray-50 font-semibold text-gray-700 border-r border-gray-200">
              공정설비
            </div>
            <div className="flex-1 flex">
              {timeSlots.map((slot, index) => (
                <div key={index} className="flex-1 p-4 text-center font-medium text-gray-600 border-r border-gray-200 last:border-r-0">
                  {slot}
                </div>
              ))}
            </div>
          </div>

          {/* 스케줄 행들 */}
          {scheduleData.map((equipment, equipmentIndex) => (
            <div key={equipment.equipment} className="flex border-b border-gray-200 last:border-b-0">
              {/* 설비명 */}
              <div className="w-32 p-4 bg-gray-50 font-medium text-gray-700 border-r border-gray-200 flex items-center">
                {equipment.equipment}
              </div>
              
              {/* 시간 슬롯들 */}
              <div className="flex-1 relative h-20 bg-white">
                {/* 그리드 셀들 */}
                {timeSlots.map((_, slotIndex) => (
                  <div
                    key={slotIndex}
                    className={`absolute top-0 h-full border-r border-gray-100 ${
                      dragOverSlot?.equipmentIndex === equipmentIndex && dragOverSlot?.slotIndex === slotIndex 
                        ? 'bg-blue-50' : ''
                    }`}
                    style={{ 
                      left: `${(slotIndex / timeSlots.length) * 100}%`, 
                      width: `${100 / timeSlots.length}%` 
                    }}
                    onDragOver={(e) => handleDragOver(e, equipmentIndex, slotIndex)}
                    onDrop={(e) => handleDrop(e, equipmentIndex, slotIndex)}
                  />
                ))}
                
                {/* 작업 블록들 (테트리스 스타일) */}
                {equipment.tasks.map(task => {
                  const leftPosition = (task.slot / timeSlots.length) * 100;
                  const width = (task.duration / timeSlots.length) * 100;
                  
                  return (
                    <div
                      key={task.id}
                      className="absolute top-2 h-16 rounded-lg shadow-xl cursor-move transform transition-all duration-200 hover:scale-105 border-2 border-white"
                      style={{
                        left: `${leftPosition}%`,
                        width: `${width}%`,
                        backgroundColor: task.color,
                        background: `linear-gradient(135deg, ${task.color} 0%, ${task.color}dd 100%)`
                      }}
                      draggable
                      onDragStart={(e) => handleDragStart(e, task, equipmentIndex)}
                    >
                      {/* 테트리스 블록 스타일 */}
                      <div className="relative h-full rounded-lg overflow-hidden">
                        {/* 레고 점들 */}
                        <div className="absolute top-1 left-2 right-2 flex justify-center gap-1">
                          {Array.from({ length: Math.min(4, task.duration * 2) }).map((_, i) => (
                            <div
                              key={i}
                              className="w-1.5 h-1.5 bg-white bg-opacity-40 rounded-full"
                            />
                          ))}
                        </div>
                        
                        {/* 배치 정보 */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className="text-white text-xs font-bold">
                            {task.batch}
                          </span>
                          <span className="text-white text-xs opacity-90">
                            {task.product.replace(' 001', '')}
                          </span>
                        </div>
                        
                        {/* 입체감 효과 */}
                        <div className="absolute inset-0 bg-gradient-to-br from-white from-0% via-transparent via-40% to-black to-100% opacity-15 rounded-lg"></div>
                        <div className="absolute top-0 left-0 right-0 h-2 bg-white opacity-20 rounded-t-lg"></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* 연결선들 */}
          <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 10 }}>
            {connectionLines.map((line, index) => {
              const fromX = ((line.from.slot + 1) / timeSlots.length) * 100;
              const fromY = (line.from.equipment + 0.5) * 84 + 40; // 헤더 높이 + 행 높이의 중간
              const toX = (line.to.slot / timeSlots.length) * 100;
              const toY = (line.to.equipment + 0.5) * 84 + 40;
              
              return (
                <g key={index}>
                  <defs>
                    <marker
                      id={`arrowhead-${index}`}
                      markerWidth="10"
                      markerHeight="7"
                      refX="9"
                      refY="3.5"
                      orient="auto"
                    >
                      <polygon
                        points="0 0, 10 3.5, 0 7"
                        fill={line.from.color}
                        opacity="0.8"
                      />
                    </marker>
                  </defs>
                  <path
                    d={`M ${fromX}% ${fromY} Q ${(fromX + toX) / 2}% ${fromY - 20} ${toX}% ${toY}`}
                    stroke={line.from.color}
                    strokeWidth="3"
                    fill="none"
                    opacity="0.8"
                    markerEnd={`url(#arrowhead-${index})`}
                    className="drop-shadow-sm"
                  />
                </g>
              );
            })}
          </svg>
        </div>

        {/* 공정 흐름 안내 */}
        <div className="mt-6 bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-2">공정 흐름</h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="bg-blue-100 px-3 py-1 rounded">칭량기1</span>
            <span>→</span>
            <span className="bg-green-100 px-3 py-1 rounded">혼합기1</span>
            <span>→</span>
            <span className="bg-purple-100 px-3 py-1 rounded">타정기1</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            * 동일 배치는 공정 순서에 따라 연결되어야 합니다 (테트리스 규칙)
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProductionScheduler;