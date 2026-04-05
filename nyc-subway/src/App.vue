<template>
  <div class="dashboard">
    <div class="header">
      <h1>纽约地铁脉搏 (NYC Subway Pulse)</h1>
      <p>探索 2026年2月4日 曼哈顿及周边的通勤潮汐现象</p>
      <button class="doc-btn" @click="showDoc = true">📄 项目说明文档</button>
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
<div v-show="tooltip.visible" class="tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
      <strong>{{ tooltip.name }}</strong><br/>
      {{ flowType === 'in_flow' ? '总客流' : flowType === 'omny' ? '刷手机' : '刷卡' }}人数: <span class="highlight">{{ tooltip.val }}</span>
      <div class="click-hint">点击查看全天趋势 📈</div>
    </div>

    <div v-if="showDoc" class="doc-modal-overlay" @click="showDoc = false">
      <div class="doc-modal-content" @click.stop>
        <button class="close-btn" @click="showDoc = false">✖ 关闭</button>
        <h2>项目说明文档</h2>
        
        <h3>1. 旨在解答什么问题？</h3>
        <p>本网站旨在探索纽约地铁通勤潮汐的演变规律。通过可视化 24 小时内的客流数据，解答以下核心问题：</p>
        <ul>
          <li><strong>时空分布特征：</strong>早晚高峰期间，曼哈顿商业区与外围住宅区（如布鲁克林、皇后区）的客流潮汐是如何涌动的？比如在早上</li>
          <li><strong>技术普及率差异：</strong>现代移动支付技术（OMNY）与传统磁条卡（MetroCard）的使用比例在不同行政区、不同时间段是否存在显著差异？是否能反映出不同社区对新技术的接受度或通勤人群的结构差异？</li>
        </ul>

        <h3>2. 设计决策的依据</h3>
        <p>为了让用户能够“引人入胜”地探索上述问题，我采用了以下可视化编码与交互技术：</p>
        
        <h4>可视化编码 (Visual Encoding)：</h4>
        <ul>
          <li><strong>空间映射 (Spatial)：</strong>采用真实地理坐标映射（Mercator 投影），使用户能直观建立物理世界的空间认知。</li>
          <li><strong>面积映射 (Size)：</strong>使用圆点大小（平方根比例尺 <code>scaleSqrt</code>）精确映射绝对客流量，确保视觉面积与数据真实对应。</li>
          <li><strong>颜色映射 (Color)：</strong>使用连续型色带（黄→红）映射拥挤度，红色在暗黑背景下能迅速吸引注意力，有效传达“高峰、拥挤”的语义。</li>
          <li><strong>折线图 (Line Chart)：</strong>在辅视图中使用带有透明填充的平滑折线图，展示 24 小时时间序列，并用三种具有高度对比的颜色（翠绿、橙、蓝）区分总客流与不同支付方式。</li>
        </ul>

        <h4>交互技术 (Interaction)：</h4>
        <ul>
          <li><strong>动态查询：</strong>放弃了静态的“多重小图”，采用了时间滑块 (Slider)。用户拖动滑块时能产生动画效果，直观感受到城市的“脉搏”。</li>
          <li><strong>按需显示细节：</strong>鼠标悬浮 (Hover) 提供精准数值提示，避免全局显示文字导致的视觉杂乱。</li>
          <li><strong>多视图联动：</strong>点击地图上的特定站点，左侧辅助视图会实时生成该站点的 24 小时趋势图，实现从宏观空间到微观时间维度的下钻分析。</li>
          <li><strong>刷选与过滤：</strong>提供行政区下拉菜单与支付方式切换按钮，遵循 Shneiderman 的“先总览，后过滤”原则，帮助用户剥离干扰信息。</li>
          <li><strong>支持缩放与拖拽：</strong>用户可根据需要缩小和放大地图，并进行拖拽，以实现更具体地观察。</li>
        </ul>

        <h4>替代方案与最终决策：</h4>
        <p>最初考虑将进站与出站数据进行对比，但经过数据探索发现 MTA 采取单向计费，无出站数据。因此果断调整方向，挖掘了 <code>payment_method</code> 这一更有叙事价值的维度，使得作品的社会学意义更加丰富。</p>

       <h3>3. 外部资源引用</h3>
        <ul>
          <li><strong>底图地理边界 (GeoJSON)：</strong><a href="https://data.cityofnewyork.us/City-Government/Borough-Boundaries/gthc-hcne" target="_blank" rel="noopener noreferrer">NYC Borough Boundaries</a></li>
          
          <li><strong>地铁站坐标字典 (CSV)：</strong><a href="https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f/data_preview" target="_blank" rel="noopener noreferrer">MTA Subway Stations</a></li>
          
          <li><strong>小时级客流动态数据 (CSV)：</strong><a href="https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj/data_preview" target="_blank" rel="noopener noreferrer">MTA Subway Hourly Ridership</a>（选取了 2026.2.4-2.5 的数据）</li>
        </ul>

        <h3>4. 开发流程概述</h3>
        <ul>
          <li><strong>团队分工：</strong>独立完成（数据清洗、UI 设计、前端交互实现）。</li>
          <li><strong>耗时评估：</strong>总计耗时约 30 工时。</li>
        </ul>
        <h4>开发评述：</h4>
        <ul>
          <li><strong>数据预处理与结构设计（约 8 小时）：</strong>官方 CSV 数据集非常庞大且存在冗余。最耗时的部分是编写 Python 脚本清洗数据，按时间、站点和支付方式进行 <code>groupby</code> 与透视，并最终将其转化为对 D3 友好的嵌套 JSON 结构。同时还需要将包含行政区的 CSV 元数据与 JSON 动态数据在前端进行主键合并 (Join)。</li>
          <li><strong>D3 交互与生命周期控制（约 12 小时）：</strong>确保拖动时间滑块时，散点的 Enter/Update/Exit 动画能够流畅过渡而不卡顿。初期由于过渡动画堆叠导致浏览器渲染延迟，后续通过优化数据绑定和取消高频触发时的动画延迟解决了性能瓶颈。</li>
          <li><strong>UI 调优（约 10 小时）：</strong>确定暗色主题，地图大小、缩放比例、位置，站点的大小、展现形式以及多视图（包括折线图、仪表盘、弹窗等）间的排版布局，确保最终界面符合“简洁优雅”的设计目标。</li>
        </ul>
      </div>
    </div>
    </div> </template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import * as d3 from 'd3';

// --- 状态管理 ---
const currentHour = ref(8);
const flowType = ref('in_flow'); // 
const selectedBorough = ref('All'); // 区域筛选
const selectedStation = ref(null); // 被点击的站点
const showDoc = ref(false);//控制说明文档的弹窗

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
      d3.json('./nyc_boroughs.geojson'),
      d3.json('./subway_day.json'),
      d3.csv('./stations_location.csv')
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
/* --- 说明文档弹窗样式--- */
.doc-modal-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.85); /* 稍微加深遮罩，突出便签 */
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
}

.doc-modal-content {
  background: #1a202c; /* 更现代的深色护眼背景 */
  padding: 40px 55px;  /* 增加内边距，让文字呼吸感更强 */
  border-radius: 16px;
  width: 850px;        /* 【调大】大幅加宽便签 */
  max-width: 92vw; 
  max-height: 85vh;    /* 【调大】加高便签 */
  overflow-y: auto;
  border: 1px solid #2d3748;
  box-shadow: 0 20px 50px rgba(0,0,0,0.9);
  position: relative;
  text-align: left;    /* 强制整体左对齐 */
}

/* 标题层次与对齐优化 */
.doc-modal-content h2 { 
  color: #f39c12; margin-top: 0; margin-bottom: 25px; 
  font-size: 1.8rem; text-align: center; 
  border-bottom: 1px solid #2d3748; padding-bottom: 15px;
}
.doc-modal-content h3 { 
  color: #3498db; margin-top: 30px; margin-bottom: 15px; 
  font-size: 1.35rem; border-left: 4px solid #3498db; padding-left: 12px;
}
.doc-modal-content h4 { 
  color: #e1b12c; margin-top: 20px; margin-bottom: 12px; font-size: 1.15rem;
}

/* 正文与列表段落优化 */
.doc-modal-content p { 
  color: #e2e8f0; line-height: 1.8; font-size: 1.05rem; 
  margin-top: 0; margin-bottom: 15px; text-align: justify; /* 两端对齐更美观 */
}
.doc-modal-content ul { 
  padding-left: 25px; margin-top: 0; margin-bottom: 20px; 
}
.doc-modal-content li { 
  color: #e2e8f0; line-height: 1.8; font-size: 1.05rem; margin-bottom: 10px; 
}
.doc-modal-content strong { color: #fff; font-weight: 600;} /* 加粗重点全白发亮 */
.doc-modal-content code { 
  background: #2d3748; padding: 2px 6px; border-radius: 4px; 
  font-family: monospace; color: #a0aec0;
}

/* 关闭按钮优化 */
.close-btn {
  position: absolute; top: 20px; right: 25px;
  background: #e53e3e; color: white; border: none; 
  padding: 8px 16px; border-radius: 6px;
  cursor: pointer; font-weight: bold; font-size: 0.95rem; transition: background 0.2s;
}
.close-btn:hover { background: #c53030; }

/* 顶部触发说明文档的按钮样式 */
.doc-btn {
  background: #3498db; color: white; border: none;
  padding: 5px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: bold;
  cursor: pointer; margin-left: 15px; vertical-align: middle; transition: 0.2s;
}
.doc-btn:hover { background: #2980b9; transform: scale(1.05); }

/* --- 专属暗黑模式自定义滚动条 --- */
.doc-modal-content::-webkit-scrollbar { width: 8px; }
.doc-modal-content::-webkit-scrollbar-track { background: #1a202c; border-radius: 4px; }
.doc-modal-content::-webkit-scrollbar-thumb { background: #4a5568; border-radius: 4px; }
.doc-modal-content::-webkit-scrollbar-thumb:hover { background: #718096; }
/* 说明文档中的超链接样式 */
.doc-modal-content a {
  color: #63b3ed; /* 亮蓝色，适合暗色背景 */
  text-decoration: none; /* 去掉默认的下划线 */
  font-weight: 500;
  border-bottom: 1px dashed #63b3ed; /* 换成虚线下划线，更显精致 */
  transition: all 0.2s ease;
}
.doc-modal-content a:hover {
  color: #90cdf4; /* 鼠标悬浮时变亮 */
  border-bottom-color: #90cdf4;
}
</style>