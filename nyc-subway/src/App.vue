<template>
  <div class="dashboard">
    <div class="header">
      <h1>纽约地铁脉搏 (NYC Subway Pulse)</h1>
      <p>探索 2026年2月4日 曼哈顿及周边的通勤潮汐现象</p>
    </div>

    <div class="main-content">
      <div class="controls-sidebar">
        
        <div class="control-card">
          <div class="time-label">当前时间</div>
          <div class="time-value">{{ formattedTime }}</div>
          <input 
            type="range" min="0" max="23" step="1" 
            v-model="currentHour" @input="onTimeChange" 
            class="slider"
          />

          <div style="font-size: 0.85rem; color: #95a5a6; margin-bottom: 8px;">支付方式:</div>
          <div class="toggle-group">
            <button :class="{ active: flowType === 'in_flow' }" @click="setFlowType('in_flow')">总客流</button>
            <button :class="{ active: flowType === 'omny' }" @click="setFlowType('omny')">刷手机</button>
            <button :class="{ active: flowType === 'metrocard' }" @click="setFlowType('metrocard')">刷卡</button>
          </div>

          <div class="filter-group">
            <label>筛选区域:</label>
            <select v-model="selectedBorough" @change="updateMap" class="custom-select">
              <option value="All">全部区域 (All)</option>
              <option value="M">曼哈顿 (Manhattan)</option>
              <option value="Bk">布鲁克林 (Brooklyn)</option>
              <option value="Q">皇后区 (Queens)</option>
              <option value="Bx">布朗克斯 (Bronx)</option>
              <option value="SI">斯塔滕岛 (Staten Island)</option>
            </select>
          </div>
          
          <div class="legend-section">
            <div class="legend-item">
              <span class="legend-dot size-dot"></span>
              <span>大小 = {{ flowType === 'in_flow' ? '总客流' : flowType === 'omny' ? '刷手机(OMNY)' : '刷卡(MetroCard)' }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-color-bar"></span>
              <span>颜色 = 拥挤度 (黄 → 红)</span>
            </div>
          </div>
        </div>

        <div class="chart-card" v-show="selectedStation">
          <div class="chart-title">
            {{ selectedStation?.name }} <br/>
            <span class="chart-subtitle">24小时 {{ flowType === 'in_flow' ? '总客流' : flowType === 'omny' ? '刷手机支付客流量' : '刷卡支付客流量' }} 趋势</span>
          </div>
          <div ref="chartContainer" class="chart-container"></div>
        </div>

      </div>

      <div class="map-wrapper">
        <div class="map-hint">💡 提示：支持在地图上进行缩放与拖拽</div>
        <div ref="mapContainer" class="map-container"></div>
      </div>
    </div>
    
    <div v-show="tooltip.visible" class="tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
      <strong>{{ tooltip.name }}</strong><br/>
      {{ flowType === 'in_flow' ? '总客流' : flowType === 'omny' ? '刷手机支付' : '刷卡支付' }}人数: <span class="highlight">{{ tooltip.val }}</span>
      <div class="click-hint">点击该站点，查看全天趋势 📈</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import * as d3 from 'd3';

// --- 状态管理 ---
const currentHour = ref(8);
const flowType = ref('in_flow'); // 
const selectedBorough = ref('All'); // 区域筛选
const selectedStation = ref(null); // 被点击的站点

const mapContainer = ref(null);
const chartContainer = ref(null);
const tooltip = ref({ visible: false, x: 0, y: 0, name: '', val: 0 });

let mapSvg = null;
let projection = null;
let ridershipData = null;
let stationsMeta = new Map(); // 【新增】用来存储从 CSV 读取的站点行政区和线路信息

// 计算友好的时间格式
const formattedTime = computed(() => {
  const h = parseInt(currentHour.value);
  return h === 0 ? '12:00 AM' : h < 12 ? `${h}:00 AM` : h === 12 ? `12:00 PM` : `${h - 12}:00 PM`;
});

// 切换客流类型
const setFlowType = (type) => {
  flowType.value = type;
  updateMap();
  if (selectedStation.value) {
    renderChart(selectedStation.value.id); // 同步更新折线图
  }
};

const onTimeChange = () => {
  updateMap();
  // 如果想在拖动时间时，让图表里的时间标尺也动，可以在这里加逻辑
};

// --- 初始化地图 ---
const initMap = async () => {
  const width = 850;  
  const height = 800; 

  mapSvg = d3.select(mapContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .style('background-color', '#1a1a1a'); 
    
  const g = mapSvg.append('g');

  const zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
  mapSvg.call(zoom);

  projection = d3.geoMercator()
    .center([-73.945, 40.725]) 
    .scale(82000)
    .translate([width / 2, height / 2]);

  const pathGenerator = d3.geoPath().projection(projection);

  try {
    const [geoData, flowData, csvData] = await Promise.all([
      d3.json('/nyc_boroughs.geojson'),
      d3.json('/subway_day.json'),
      d3.csv('/stations_location.csv')
    ]);

    ridershipData = flowData;

    csvData.forEach(d => {
      stationsMeta.set(d['Station ID'], {
        borough: d.Borough //这里首字母大写，CSV 表头是 Borough
      });
    });

    g.append('g')
      .selectAll('path')
      .data(geoData.features)
      .enter()
      .append('path')
      .attr('d', pathGenerator)
      .attr('fill', '#2c3e50')
      .attr('stroke', '#121212')
      .attr('stroke-width', 1.5);

    g.append('g').attr('class', 'stations-layer');

    updateMap();

  } catch (error) {
    console.error("加载数据失败，请检查 public 目录", error);
  }
};

// --- 更新地图散点 ---
const updateMap = () => {
  if (!ridershipData) return;

  const hourKey = currentHour.value.toString();
  const rawData = ridershipData[hourKey] || [];

  // 把 JSON 里的动态人数 和 CSV 里的行政区 结合起来
  const currentData = rawData.map(d => {
    const meta = stationsMeta.get(d.id.toString()); // 去刚才存好的字典里查这个站的户口
    return meta ? { ...d, ...meta } : d; // 缝合在一起
  }).filter(d => {
    // 缝合好之后，开始真正地过滤
    if (selectedBorough.value === 'All') return true;
    return d.borough === selectedBorough.value;
  });

  // 动态获取当前选择的维度 (in_flow 还是 out_flow)
  const getValue = d => d[flowType.value] || 0;

  const radiusScale = d3.scaleSqrt().domain([0, 5000]).range([1, 10]).clamp(true);
  const colorScale = d3.scaleSequential(d3.interpolateYlOrRd).domain([0, 3000]);

  const layer = mapSvg.select('.stations-layer');
  const circles = layer.selectAll('circle').data(currentData, d => d.id);

  circles.join(
    enter => enter.append('circle')
      .attr('cx', d => projection([d.lon, d.lat])[0])
      .attr('cy', d => projection([d.lon, d.lat])[1])
      .attr('r', 0)
      .attr('fill', d => colorScale(getValue(d)))
      .attr('opacity', 0.8)
      .attr('cursor', 'pointer') // 增加鼠标手型
      .on('mouseover', (event, d) => {
        d3.select(event.currentTarget).attr('stroke', '#fff').attr('stroke-width', 2);
        tooltip.value = {
          visible: true, x: event.pageX + 15, y: event.pageY + 15,
          name: d.name, val: getValue(d)
        };
      })
      .on('mouseout', (event) => {
        // 如果这个站是被选中的，保持它的描边
        const isSelected = selectedStation.value && selectedStation.value.id === event.currentTarget.__data__.id;
        d3.select(event.currentTarget).attr('stroke', isSelected ? '#3498db' : 'none').attr('stroke-width', isSelected ? 3 : 0);
        tooltip.value.visible = false;
      })
      .on('click', (event, d) => {
        // 点击交互：高亮当前站点，并绘制折线图
        layer.selectAll('circle').attr('stroke', 'none'); // 清除其他高亮
        d3.select(event.currentTarget).attr('stroke', '#3498db').attr('stroke-width', 3);
        selectedStation.value = d;
        renderChart(d.id);
      })
      .call(enter => enter.transition().duration(600).attr('r', d => radiusScale(getValue(d)))),
        
    update => update
      .call(update => update
        .attr('r', d => radiusScale(getValue(d)))
        .attr('fill', d => colorScale(getValue(d)))
        // 维持选中状态的边框
        .attr('stroke', d => selectedStation.value && selectedStation.value.id === d.id ? '#3498db' : 'none')
        .attr('stroke-width', d => selectedStation.value && selectedStation.value.id === d.id ? 3 : 0)
      ),
        
    exit => exit.call(exit => exit.transition().duration(600).attr('r', 0).remove())
  );
};

// --- 绘制右侧 24 小时趋势折线图 ---
const renderChart = (stationId) => {
  if (!ridershipData || !chartContainer.value) return;

  // 1. 提取该站点 24 小时的数据
  const chartData = [];
  for (let i = 0; i < 24; i++) {
    const hourData = ridershipData[i.toString()] || [];
    const st = hourData.find(s => s.id === stationId);
    chartData.push({
      hour: i,
      val: st ? (st[flowType.value] || 0) : 0
    });
  }

  // 2. 清空旧图表
  const container = d3.select(chartContainer.value);
  container.selectAll('*').remove();

  // 3. 设置尺寸
  const margin = { top: 10, right: 10, bottom: 20, left: 35 };
  const width = 240 - margin.left - margin.right;
  const height = 140 - margin.top - margin.bottom;

  const svg = container.append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // 4. 定义比例尺
  const x = d3.scaleLinear().domain([0, 23]).range([0, width]);
  const maxVal = d3.max(chartData, d => d.val) || 100;
  const y = d3.scaleLinear().domain([0, maxVal]).range([height, 0]);

  // 5. 绘制坐标轴
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d => d + 'h'))
    .attr('color', '#7f8c8d');

  svg.append('g')
    .call(d3.axisLeft(y).ticks(4))
    .attr('color', '#7f8c8d');

  // 6. 绘制渐变面积 (Area)
  const area = d3.area()
    .x(d => x(d.hour))
    .y0(height)
    .y1(d => y(d.val))
    .curve(d3.curveMonotoneX); // 曲线平滑

  svg.append('path')
  .datum(chartData)
  .attr('fill', flowType.value === 'in_flow' ? 'rgba(46, 204, 113, 0.3)' : flowType.value === 'omny' ? 'rgba(230, 126, 34, 0.3)' : 'rgba(52, 152, 219, 0.3)')
  .attr('d', area);

  // 7. 绘制折线 (Line)
  const line = d3.line()
    .x(d => x(d.hour))
    .y(d => y(d.val))
    .curve(d3.curveMonotoneX);

 svg.append('path')
  .datum(chartData)
  .attr('fill', 'none')
  .attr('stroke', flowType.value === 'in_flow' ? '#2ecc71' : flowType.value === 'omny' ? '#e67e22' : '#3498db')
  .attr('stroke-width', 2)
  .attr('d', line);
    
  // 8. 添加当前时间的指示线
  svg.append('line')
    .attr('x1', x(currentHour.value))
    .attr('x2', x(currentHour.value))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', '#f1c40f')
    .attr('stroke-dasharray', '4,4');
};

onMounted(() => {
  initMap();
});
</script>

<style>
/* 确保 body 撑满整屏 */
html, body { 
  margin: 0; padding: 0; height: 100%; 
  background-color: #121212; color: #ecf0f1; 
  font-family: 'Helvetica Neue', Arial, sans-serif; 
  overflow: hidden; 
}

/* --- 1. 修复标题间距 --- */
.dashboard { 
  display: flex; flex-direction: column; height: 100vh; 
  /* 加大了这里的 top padding (从 20px 加到 40px 或更大) */
  padding: 35px 2vw 20px; 
  width: 100%; box-sizing: border-box;
}

.header { text-align: center; margin-bottom: 25px; flex-shrink: 0; }
.header h1 { margin: 0 0 5px 0; color: #f39c12; font-size: 2rem; letter-spacing: 1px; }
.header p { margin: 0; color: #95a5a6; font-size: 0.9rem; }

/* 主内容区 */
.main-content {
  display: flex; flex-direction: row; justify-content: center; align-items: stretch;
  gap: 40px; flex: 1; min-height: 0;
}

/* 左侧容器：现在包含两个卡片 (控制卡片 + 图表卡片) */
.controls-sidebar {
  display: flex; flex-direction: column; justify-content: flex-start;
  width: 300px; flex-shrink: 0; gap: 20px;
}

.control-card, .chart-card {
  background: #1e272e; padding: 20px; border-radius: 12px;
  box-shadow: 0 10px 20px rgba(0,0,0,0.4); border: 1px solid #2f3640;
}

/* 控制元素样式 */
.time-label { font-size: 0.95rem; color: #95a5a6; text-align: center; margin-bottom: 8px; }
.time-value { font-size: 2.2rem; font-weight: bold; color: #3498db; text-align: center; margin-bottom: 15px; }
.slider { width: 100%; cursor: pointer; accent-color: #f39c12; margin-bottom: 20px; }

/* --- 新增：Toggle 按钮样式 --- */
.toggle-group {
  display: flex; background: #111418; border-radius: 6px; overflow: hidden; margin-bottom: 15px;
}
.toggle-group button {
  flex: 1; padding: 8px 2px; border: none; background: transparent; color: #7f8c8d;
  cursor: pointer; font-size: 0.75rem; transition: 0.3s;
}
.toggle-group button.active {
  background: #34495e; color: #fff; font-weight: bold;
}

/* --- 新增：下拉菜单筛选样式 --- */
.filter-group {
  display: flex; flex-direction: column; gap: 5px; margin-bottom: 20px; font-size: 0.85rem; color: #95a5a6;
}
.custom-select {
  width: 100%; padding: 8px; background: #111418; color: #ecf0f1; border: 1px solid #34495e;
  border-radius: 4px; outline: none; cursor: pointer;
}

/* 图例 */
.legend-section {
  display: flex; flex-direction: column; gap: 8px; background: rgba(0,0,0,0.2);
  padding: 10px; border-radius: 8px;
}
.legend-item { display: flex; align-items: center; font-size: 0.75rem; color: #bdc3c7; }
.legend-dot.size-dot { width: 12px; height: 12px; background-color: #e67e22; border-radius: 50%; margin-right: 10px; }
.legend-color-bar { width: 16px; height: 16px; border-radius: 4px; background: linear-gradient(to bottom, #ffffb2, #fd8d3c, #bd0026); margin-right: 8px; }

/* --- 新增：图表卡片样式 --- */
.chart-title { font-size: 0.9rem; font-weight: bold; color: #ecf0f1; margin-bottom: 10px; text-align: center; }
.chart-subtitle { font-size: 0.75rem; color: #95a5a6; font-weight: normal; }
.chart-container { width: 100%; height: 140px; }

/* 地图容器 */
.map-container { 
  background-color: #1a1a1a; border: 1px solid #34495e; border-radius: 12px; 
  overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.4); 
  display: flex; justify-content: center; align-items: center;
}

/* Tooltip */
.tooltip { 
  position: absolute; background: rgba(15, 20, 25, 0.95); padding: 10px 14px; 
  border-radius: 6px; color: #fff; pointer-events: none; font-size: 0.9rem; 
  box-shadow: 0 4px 12px rgba(0,0,0,0.6); border: 1px solid #e74c3c; z-index: 100; 
}
.tooltip .highlight { color: #f39c12; font-weight: bold; font-size: 1.1rem; }
.click-hint { font-size: 0.7rem; color: #3498db; margin-top: 5px; border-top: 1px solid #333; padding-top: 5px; }
/* --- 新增：地图提示文字样式 --- */
.map-wrapper {
  position: relative;
  display: flex;
}
.map-hint {
  position: absolute;
  top: 15px;
  right: 20px;
  background: rgba(0,0,0,0.6);
  padding: 6px 12px;
  border-radius: 6px;
  color: #bdc3c7;
  font-size: 0.8rem;
  pointer-events: none; /* 关键：加上这个属性，鼠标穿透文字，不影响底下地图的拖拽 */
  z-index: 10;
  border: 1px solid #34495e;
}
</style>