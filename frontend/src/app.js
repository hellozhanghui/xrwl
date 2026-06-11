const state = {
  token: localStorage.getItem("xr_token") || "",
  user: null,
  vehicles: [],
  orders: [],
  users: [],
  devices: [],
  tickets: [],
  vehicleWarningPreview: [],
  summary: {},
  alerts: [],
  screenRoutes: [],
  ticketFilters: {},
  pricingRates: [],
  workflowTasks: [],
  chartInstances: {},
  settings: {},
  mapConfigs: [],
  live: [],
  selectedRoute: [],
  selectedReturnRoute: [],
  selectedRouteLabel: "未选择路线",
  selectedRouteStops: [],
  mapZoomAdjust: 0,
  verificationCenter: null,
  routePlanner: {
    stations: [],
    lastResult: null,
    addressSearchSeq: 0,
  },
  selectedVehicleId: null,
  selectedOrderId: null,
  orderView: "list",
  editingVehicleId: null,
  pendingTicketOrder: null,
  orderPage: 1,
  orderPageSize: 5,
};

const statusText = {
  active: "启用",
  disabled: "停用",
  idle: "空闲",
  available: "可用",
  assigned: "已派车",
  confirmed: "已确认",
  pending: "待确认",
  not_submitted: "未提交",
  approved: "已审核",
  rejected: "已驳回",
  in_transit: "运输中",
  completed: "已完成",
  maintenance: "维修中",
  offline: "离线",
  online: "在线",
};

const pageMeta = {
  dashboard: ["总览", "车辆、订单、告警和调度状态"],
  "realtime-screen": ["实时大屏", "车辆位置、运输线路和运行态势"],
  vehicles: ["车辆档案", "基础信息、维护保养、证照保险税费"],
  "warning-preview": ["告警预览", "车辆档案超期、临期和关注项"],
  orders: ["运输订单", "订单创建、路线、站点、确认与流转"],
  dispatch: ["配货调度", "按货物、车辆能力和状态推荐车辆"],
  tracking: ["轨迹设备", "设备接入、实时定位与温湿度采集"],
  tickets: ["票据费用", "过路费、油费、维修、保险、税费和发票"],
  workflow: ["工作流", "流程定义、我的待办、流程实例和处理记录"],
  reports: ["统计报表", "车辆利用率、订单里程、费用和异常"],
  admin: ["系统管理", "用户角色、地图配置、设备厂商适配"],
};

const optionSets = {
  vehicleTypes: ["鸡苗恒温车", "雏鸡配送车", "冷链保温车", "厢式通风车", "应急保障车"],
  boxTypes: ["恒温通风", "保温通风", "冷藏保温", "普通厢体"],
  cargoTypes: ["鸡苗", "种蛋", "鸡苗筐", "疫苗冷链", "饲料", "养殖物资"],
  returnStrategies: [
    ["same_route", "同路返回"],
    ["highway", "高速返回"],
    ["empty_return_discount", "空返折算"],
    ["none", "不计返程"],
  ],
  vehicleStatuses: [["idle", "空闲"], ["assigned", "已派车"], ["in_transit", "运输中"], ["maintenance", "维修中"], ["disabled", "停用"], ["inspection", "年检中"]],
  boxDeviceTypes: [["gps", "GPS定位"], ["temperature", "温湿度"], ["camera", "视频"], ["other", "其他"]],
  certificateTypes: [["insurance", "保险"], ["tax", "车船税"], ["license", "行驶证"], ["transport_permit", "道路运输证"], ["inspection", "年检"]],
  ticketTypes: [["toll", "过路费"], ["fuel", "燃油费"], ["repair", "维修费"], ["insurance", "保险费"], ["tax", "税费"], ["invoice", "发票"]],
  userRoles: [["admin", "系统管理员"], ["fleet_manager", "车队管理员"], ["dispatcher", "调度员"], ["driver", "司机"], ["customer", "客户"], ["finance", "财务"]],
  recordStatuses: [["pending", "待处理"], ["approved", "已通过"], ["rejected", "已驳回"]],
  routePreferences: [["fastest", "最快路线"], ["highway", "高速优先"], ["shortest", "最短路线"], ["cost", "费用优先"]],
  deviceProtocols: [["http", "HTTP"], ["mqtt", "MQTT"], ["tcp", "TCP"]],
  provinces: ["河北省", "山东省", "河南省", "山西省", "北京市", "天津市", "辽宁省", "江苏省", "安徽省", "陕西省", "内蒙古自治区"],
  citiesByProvince: {
    "河北省": ["保定市", "石家庄市", "衡水市", "邢台市", "邯郸市", "沧州市", "唐山市", "廊坊市", "张家口市", "承德市", "秦皇岛市"],
    "山东省": ["济南市", "青岛市", "德州市", "聊城市", "济宁市", "临沂市", "潍坊市"],
    "河南省": ["郑州市", "安阳市", "新乡市", "鹤壁市", "濮阳市", "洛阳市"],
    "山西省": ["太原市", "大同市", "阳泉市", "长治市", "晋中市"],
    "北京市": ["北京市"],
    "天津市": ["天津市"],
    "辽宁省": ["沈阳市", "大连市", "锦州市", "营口市"],
    "江苏省": ["南京市", "徐州市", "苏州市", "盐城市", "连云港市"],
    "安徽省": ["合肥市", "宿州市", "阜阳市", "亳州市"],
    "陕西省": ["西安市", "咸阳市", "渭南市"],
    "内蒙古自治区": ["呼和浩特市", "包头市", "赤峰市", "通辽市"],
  },
};

const displayMaps = {
  cargo: { general: "普货", cold_chain: "冷链", dangerous: "危险品", food: "食品", medicine: "药品" },
  device: { gps: "GPS定位", temperature: "温湿度", camera: "视频", other: "其他" },
  ticket: { toll: "过路费", fuel: "燃油费", repair: "维修费", insurance: "保险费", tax: "税费", invoice: "发票" },
  role: Object.fromEntries(optionSets.userRoles),
  cert: Object.fromEntries(optionSets.certificateTypes),
};

const screenRouteColors = ["#38bdf8", "#22d3ee", "#60a5fa", "#0ea5e9", "#67e8f9", "#2563eb", "#2dd4bf", "#93c5fd"];

const formSchemas = {
  vehicle: {
    title: "新增车辆",
    endpoint: "/api/vehicles",
    method: "POST",
    fields: [
      ["photo_image", "车辆照片", "file", false, { accept: "image/png,image/jpeg,image/webp", hint: "支持 PNG、JPG、WebP，建议使用车辆正侧面照片" }],
      ["plate_no", "车牌号", "text", true],
      ["vehicle_type", "车辆类型", "select", true, optionSets.vehicleTypes],
      ["brand_model", "品牌型号", "text"],
      ["load_capacity", "核定载重(吨)", "number", true],
      ["box_volume", "货箱容积(m3)", "number"],
      ["box_type", "货箱类型", "select", true, optionSets.boxTypes],
      ["status", "车辆状态", "select", true, optionSets.vehicleStatuses],
      ["organization", "所属组织", "text"],
      ["gps_device_id", "GPS设备编号", "text"],
      ["sensor_device_id", "温湿度设备编号", "text"],
    ],
  },
  "vehicle-edit": {
    title: "编辑车辆",
    endpoint: () => `/api/vehicles/${state.editingVehicleId}`,
    method: "PUT",
    fields: [
      ["photo_image", "车辆照片", "file", false, { accept: "image/png,image/jpeg,image/webp", hint: "支持 PNG、JPG、WebP，不选择新文件则保留原照片" }],
      ["plate_no", "车牌号", "text", true],
      ["vehicle_type", "车辆类型", "select", true, optionSets.vehicleTypes],
      ["brand_model", "品牌型号", "text"],
      ["load_capacity", "核定载重(吨)", "number", true],
      ["box_volume", "货箱容积(m3)", "number"],
      ["box_type", "货箱类型", "select", true, optionSets.boxTypes],
      ["status", "车辆状态", "select", true, optionSets.vehicleStatuses],
      ["organization", "所属组织", "text"],
      ["gps_device_id", "GPS设备编号", "text"],
      ["sensor_device_id", "温湿度设备编号", "text"],
    ],
  },
  "vehicle-driver": {
    title: "新增车辆司机",
    endpoint: () => `/api/vehicles/${requireVehicle()}/drivers`,
    method: "POST",
    fields: [
      ["name", "司机姓名", "text", true],
      ["phone", "手机号", "text"],
      ["license_no", "驾驶证号", "text"],
      ["qualification_no", "从业资格证号", "text"],
      ["status", "状态", "select", true, [["active", "可用"], ["disabled", "停用"]]],
      ["is_default", "是否默认司机", "select", true, [[1, "默认司机"], [0, "普通司机"]]],
      ["remark", "备注", "textarea"],
    ],
  },
  maintenance: {
    title: "新增维护记录",
    endpoint: () => `/api/vehicles/${requireVehicle()}/maintenance`,
    method: "POST",
    fields: [
      ["type", "类型", "select", true, ["保养", "维修", "年检", "温控系统检查", "消毒清洗"]],
      ["title", "事项名称", "text", true],
      ["service_date", "服务日期", "date", true],
      ["mileage", "当时里程", "number"],
      ["cost", "费用", "number"],
      ["next_due_date", "下次到期", "date"],
      ["next_due_mileage", "下次里程", "number"],
      ["vendor", "服务商", "text"],
      ["remark", "备注", "textarea"],
    ],
  },
  certificate: {
    title: "新增证照保险税费",
    endpoint: () => `/api/vehicles/${requireVehicle()}/certificates`,
    method: "POST",
    fields: [
      ["cert_type", "类型", "select", true, optionSets.certificateTypes],
      ["cert_no", "编号", "text"],
      ["provider", "机构", "text"],
      ["start_date", "生效日期", "date"],
      ["end_date", "到期日期", "date", true],
      ["amount", "金额", "number"],
      ["status", "状态", "select", true, [["normal", "正常"], ["expired", "已过期"]]],
    ],
  },
  order: {
    title: "创建运输订单",
    endpoint: "/api/orders",
    method: "POST",
    after: (result) => {
      state.selectedOrderId = result.id;
    },
    fields: [
      ["order_no", "发货单号", "text"],
      ["cargo_name", "货物名称", "text", true],
      ["cargo_type", "货物类型", "select", true, optionSets.cargoTypes],
      ["cargo_weight", "重量(吨)", "number", true],
      ["cargo_volume", "体积(m3)", "number", true],
      ["vehicle_id", "车牌号", "select", true, availableVehicleOptions],
      ["driver_id", "司机", "select", true, driverOptions],
    ],
  },
  "order-stop": {
    title: "新增订单站点",
    endpoint: () => `/api/orders/${requireOrder()}/stops`,
    method: "POST",
    fields: [
      ["stop_type", "站点类型", "select", true, [["pickup", "装苗点"], ["delivery", "交付点"], ["waypoint", "途经点"], ["return", "返程点"]]],
      ["sequence_no", "顺序", "number", true],
      ["name", "地址名称", "text", true],
      ["address", "详细地址", "text", true],
      ["lng", "经度", "number"],
      ["lat", "纬度", "number"],
      ["contact", "联系人", "text"],
      ["phone", "电话", "text"],
      ["planned_arrival", "计划到达", "datetime-local"],
    ],
  },
  route: {
    title: "站点路径规划",
    endpoint: "/api/routes/address-plan",
    method: "POST",
    transform: (data) => ({
      order_id: state.selectedOrderId,
      provider: data.provider,
      preference: data.preference,
      vehicle_type: data.vehicle_type,
      cargo_name: data.cargo_name,
      cargo_type: data.cargo_type,
      cargo_weight: data.cargo_weight,
      cargo_volume: data.cargo_volume,
      vehicle_id: data.vehicle_id,
      driver_id: data.driver_id,
      waypoints: parseWaypointLines(data.waypoint_lines || ""),
      destination: {
        province: data.destination_province,
        city: data.destination_city,
        address: data.destination_address,
        name: data.destination_name || data.destination_address,
      },
    }),
    after: renderAddressRouteResult,
    fields: [
      ["cargo_name", "货物名称", "text", true, "鸡苗"],
      ["cargo_type", "货物类型", "select", true, optionSets.cargoTypes],
      ["cargo_weight", "重量(吨)", "number"],
      ["cargo_volume", "体积(m3)", "number"],
      ["vehicle_id", "车牌号", "select", false, availableVehicleOptions],
      ["driver_id", "司机", "select", false, driverOptions],
      ["waypoint_lines", "沿途点(每行：省,市,地名)", "textarea"],
      ["destination_province", "终点省份", "select", true, optionSets.provinces],
      ["destination_city", "终点城市", "text", true],
      ["destination_name", "终点名称", "text"],
      ["destination_address", "终点地名/详细地址", "text", true],
      ["provider", "地图服务商", "select", true, [["tianditu", "天地图"], ["mock", "系统模拟"]]],
      ["vehicle_type", "车型", "select", false, [["", "按订单车辆"], ...optionSets.vehicleTypes]],
      ["preference", "偏好", "select", true, optionSets.routePreferences],
    ],
  },
  "pricing-estimate": {
    title: "运费测算",
    endpoint: "/api/pricing/estimate",
    method: "POST",
    after: renderPricingEstimate,
    fields: [
      ["one_way_distance", "单程公里", "number", true],
      ["vehicle_type", "车辆类型", "select", true, ["*", ...optionSets.vehicleTypes]],
      ["cargo_type", "货物类型", "select", true, ["*", ...optionSets.cargoTypes]],
    ],
  },
  "freight-rate": {
    title: "车型运价设置",
    endpoint: "/api/pricing/rates",
    method: "POST",
    fields: [
      ["vehicle_type", "车辆类型", "select", true, ["*", ...optionSets.vehicleTypes]],
      ["cargo_type", "货物类型", "select", true, ["*", ...optionSets.cargoTypes]],
      ["base_rate_per_km", "公里单价(元/km)", "number", true],
      ["min_fee", "最低收费(元)", "number", true],
      ["loading_fee", "装卸附加费(元)", "number"],
      ["toll_multiplier", "过路费系数", "number", true, "1"],
      ["return_multiplier", "返程系数", "number", true, "1"],
      ["enabled", "启用", "select", true, [["true", "启用"], ["false", "停用"]]],
    ],
  },
  "dispatch-match": {
    title: "按货物匹配车辆",
    endpoint: "/api/dispatch/match-vehicles",
    method: "POST",
    after: renderDispatchMatches,
    fields: [
      ["cargo_type", "货物类型", "select", true, optionSets.cargoTypes],
      ["cargo_weight", "重量(吨)", "number", true],
      ["cargo_volume", "体积(m3)", "number", true],
    ],
  },
  device: {
    title: "新增设备",
    endpoint: "/api/devices",
    method: "POST",
    fields: [
      ["device_no", "设备编号", "text", true],
      ["device_type", "设备类型", "select", true, optionSets.boxDeviceTypes],
      ["protocol", "协议", "select", true, optionSets.deviceProtocols],
      ["vehicle_id", "绑定车辆ID", "number"],
      ["status", "状态", "select", true, [["online", "在线"], ["offline", "离线"], ["disabled", "停用"]]],
      ["firmware", "固件版本", "text"],
      ["battery", "电量", "number"],
    ],
  },
  "gps-report": {
    title: "GPS 上报",
    endpoint: "/api/device/gps/report",
    method: "POST",
    fields: [
      ["device_no", "设备编号", "text", true, "GPS-001"],
      ["vehicle_plate", "车牌号", "text", true, "冀F12345"],
      ["lng", "经度", "number", true, "115.4801"],
      ["lat", "纬度", "number", true, "38.8739"],
      ["speed", "速度", "number", true, "68.5"],
      ["heading", "方向角", "number"],
      ["odometer", "里程", "number"],
      ["device_time", "设备时间", "datetime-local"],
    ],
  },
  "sensor-report": {
    title: "温湿度上报",
    endpoint: "/api/device/sensor/report",
    method: "POST",
    fields: [
      ["device_no", "设备编号", "text", true, "TH-001"],
      ["vehicle_plate", "车牌号", "text", true, "冀F12345"],
      ["box_no", "货箱编号", "text", false, "BOX-1"],
      ["temperature", "鸡苗舱温度", "number", true, "26"],
      ["humidity", "鸡苗舱湿度", "number", true, "60"],
      ["battery", "电量", "number"],
      ["signal", "信号", "number"],
      ["device_time", "设备时间", "datetime-local"],
    ],
  },
  ticket: {
    title: "新增票据",
    endpoint: "/api/tickets",
    method: "POST",
    fields: [
      ["ticket_type", "票据类型", "select", true, optionSets.ticketTypes],
      ["amount", "金额", "number", true],
      ["ticket_no", "票据号", "text"],
      ["order_id", "订单ID", "number"],
      ["vehicle_id", "车辆ID", "number"],
      ["issued_at", "开票日期", "date"],
      ["status", "状态", "select", true, optionSets.recordStatuses],
    ],
  },
  "ticket-generate": {
    title: "生成票据",
    endpoint: "/api/tickets",
    method: "POST",
    transform: (data) => ({
      order_id: state.pendingTicketOrder?.order_id,
      vehicle_id: state.pendingTicketOrder?.vehicle_id,
      ticket_type: data.ticket_type,
      amount: data.amount,
      ticket_no: data.ticket_no,
      issued_at: data.issued_at,
      status: "pending",
    }),
    after: () => {
      state.pendingTicketOrder = null;
    },
    fields: [
      ["ticket_type", "票据类型", "select", true, optionSets.ticketTypes],
      ["amount", "金额", "number", true],
      ["ticket_no", "票据号", "text"],
      ["issued_at", "开票日期", "date", true],
    ],
  },
  user: {
    title: "新增用户",
    endpoint: "/api/users",
    method: "POST",
    fields: [
      ["username", "登录名", "text", true],
      ["password", "初始密码", "password", true],
      ["real_name", "姓名", "text", true],
      ["phone", "手机号", "text"],
      ["role", "角色", "select", true, optionSets.userRoles],
      ["status", "状态", "select", true, [["active", "启用"], ["disabled", "停用"]]],
    ],
  },
  "map-config": {
    title: "地图配置",
    endpoint: "/api/map-configs",
    method: "POST",
    fields: [
      ["provider", "服务商", "select", true, [["tianditu", "天地图"], ["mock", "系统模拟"], ["amap", "高德备用"], ["baidu", "百度备用"]]],
      ["api_key", "API Key", "text"],
      ["secret", "密钥", "text"],
      ["base_url", "调用地址", "text"],
      ["route_path", "路线规划路径", "text"],
      ["geocode_path", "地理编码路径", "text"],
      ["reverse_geocode_path", "逆地理编码路径", "text"],
      ["poi_path", "POI检索路径", "text"],
      ["static_map_path", "静态地图路径", "text"],
      ["quota_limit", "配额", "number"],
      ["enabled", "启用", "select", true, [["true", "启用"], ["false", "停用"]]],
    ],
  },
  "system-settings": {
    title: "默认起点/计价设置",
    endpoint: "/api/system-settings",
    method: "POST",
    fields: [
      ["default_origin_name", "默认起点名称", "text", true],
      ["default_origin_province", "默认起点省份", "select", true, optionSets.provinces],
      ["default_origin_city", "默认起点城市", "text", true],
      ["default_origin_address", "默认起点地名/详细地址", "text", true],
      ["route_highway_priority", "默认高速优先", "select", true, [["true", "是"], ["false", "否"]]],
      ["seal_name", "签章名称", "text"],
      ["seal_image", "红章图片上传", "file", false, { accept: "image/png", hint: "请选择透明 PNG 图片" }],
    ],
  },
  "vendor-adapter": {
    title: "设备厂商适配",
    endpoint: "/api/device-vendor-adapters",
    method: "POST",
    fields: [
      ["vendor_name", "厂商名称", "text", true],
      ["protocol", "协议", "select", true, [["http", "HTTP"], ["mqtt", "MQTT"], ["tcp", "TCP"], ["file", "文件导入"]]],
      ["endpoint", "接口地址", "text"],
      ["auth_type", "认证方式", "select", true, [["none", "无认证"], ["token", "令牌"], ["signature", "签名"], ["basic", "账号密码"]]],
      ["secret", "密钥", "text"],
      ["callback_url", "回调地址", "text"],
      ["enabled", "启用", "select", true, [["true", "启用"], ["false", "停用"]]],
      ["remark", "备注", "textarea"],
    ],
  },
};

const api = async (path, options = {}) => {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(path, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.error || "request failed");
  return data;
};

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    const result = await api("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
    state.token = result.token;
    state.user = result.user;
    localStorage.setItem("xr_token", state.token);
    showApp();
    await loadAll();
  } catch (error) {
    document.getElementById("login-error").textContent = error.message;
  }
});

document.getElementById("logout").addEventListener("click", async () => {
  try {
    await api("/api/auth/logout", { method: "POST", body: "{}" });
  } finally {
    localStorage.removeItem("xr_token");
    state.token = "";
    document.getElementById("app-shell").classList.add("hidden");
    document.getElementById("login-screen").classList.remove("hidden");
  }
});

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.view).classList.add("active");
    const [title, subtitle] = pageMeta[button.dataset.view];
    document.getElementById("page-title").textContent = title;
    document.getElementById("page-subtitle").textContent = subtitle;
    if (button.dataset.view === "orders") setOrderView("list");
    if (button.dataset.view === "vehicles") {
      state.selectedVehicleId = null;
      renderVehicleMaintenancePlaceholder();
    }
    if (button.dataset.view === "reports") {
      window.setTimeout(renderCharts, 80);
    }
    if (button.dataset.view === "realtime-screen") {
      updateRealtimeClock();
      renderRealtimeScreen();
    }
  });
});

document.getElementById("refresh").addEventListener("click", loadAll);
document.getElementById("dialog-close").addEventListener("click", closeDialog);
document.getElementById("form-cancel").addEventListener("click", closeDialog);
document.getElementById("preview-live-map").addEventListener("click", () => {
  state.selectedRoute = [];
  state.selectedReturnRoute = [];
  state.selectedRouteStops = [];
  state.selectedRouteLabel = "车辆实时位置";
  renderMap(state.live);
});
document.getElementById("preview-history-map").addEventListener("click", previewVehicleHistory);
document.querySelectorAll("[data-form]").forEach((button) => {
  button.addEventListener("click", () => openForm(button.dataset.form));
});
document.getElementById("planner-add-station").addEventListener("click", addPlannerStation);
document.getElementById("planner-calc-route").addEventListener("click", calculatePlannerRoute);
document.getElementById("focus-planner").addEventListener("click", () => {
  setOrderView("create");
  document.getElementById("order-planner-panel").scrollIntoView({ behavior: "smooth", block: "start" });
});
document.getElementById("planner-back-list").addEventListener("click", () => setOrderView("list"));
window.setInterval(updateRealtimeClock, 1000);
window.setInterval(() => {
  if (state.token && document.getElementById("realtime-screen")?.classList.contains("active")) {
    loadAll().catch((error) => console.error(error));
  }
}, 30000);
document.getElementById("screen-fullscreen")?.addEventListener("click", toggleRealtimeFullscreen);
document.addEventListener("fullscreenchange", updateRealtimeFullscreenButton);
window.addEventListener("resize", syncTiandituCanvasScale);
document.getElementById("detail-back-list").addEventListener("click", () => setOrderView("list"));
document.getElementById("export-vehicles").addEventListener("click", () => exportRows("车辆档案", vehicleExportRows(state.vehicles)));
document.getElementById("export-orders").addEventListener("click", () => exportRows("运输订单", orderExportRows(state.orders)));
document.getElementById("export-tickets").addEventListener("click", () => exportRows("票据费用", ticketExportRows(state.tickets)));
document.getElementById("ticket-filter-apply").addEventListener("click", async () => {
  state.ticketFilters = {
    plate_no: document.getElementById("ticket-filter-plate").value.trim(),
    driver: document.getElementById("ticket-filter-driver").value.trim(),
    ticket_type: document.getElementById("ticket-filter-type").value,
    start: document.getElementById("ticket-filter-start").value,
    end: document.getElementById("ticket-filter-end").value,
  };
  await loadAll();
});
document.getElementById("seal-upload").addEventListener("change", handleSealUpload);
window.addEventListener("resize", () => {
  Object.values(state.chartInstances).forEach((chart) => chart.resize());
});

document.getElementById("dynamic-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const type = event.currentTarget.dataset.type;
  const schema = formSchemas[type];
  try {
    let data = await collectFormData(event.currentTarget, type);
    data = normalizePayload(data);
    if (schema.transform) data = schema.transform(data);
    const endpoint = typeof schema.endpoint === "function" ? schema.endpoint() : schema.endpoint;
    const result = await api(endpoint, { method: schema.method, body: JSON.stringify(data) });
    if (schema.after) schema.after(result);
    closeDialog();
    await loadAll();
  } catch (error) {
    document.getElementById("form-error").textContent = error.message;
  }
});

async function boot() {
  if (!state.token) return;
  try {
    state.user = await api("/api/auth/me");
    showApp();
    await loadAll();
  } catch {
    localStorage.removeItem("xr_token");
    state.token = "";
  }
}

function showApp() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  document.getElementById("current-user").textContent = `${state.user.real_name} · ${state.user.role}`;
}

async function collectFormData(form, type) {
  const data = {};
  const formData = new FormData(form);
  for (const [key, value] of formData.entries()) {
      if (value instanceof File) {
      if (value.size > 0) {
        if (key === "seal_image" && value.type !== "image/png") {
          throw new Error("签章图片只支持 PNG 格式");
        }
        if (key === "photo_image" && !["image/png", "image/jpeg", "image/webp"].includes(value.type)) {
          throw new Error("车辆照片只支持 PNG、JPG、WebP 格式");
        }
        if (key === "photo_image" && value.size > 3 * 1024 * 1024) {
          throw new Error("车辆照片不能超过 3MB");
        }
        data[key] = await readFileAsDataURL(value);
      } else if (type === "system-settings" && key === "seal_image") {
        data[key] = state.settings.seal_image || "";
      } else if (type === "vehicle-edit" && key === "photo_image") {
        data[key] = state.vehicles.find((item) => item.id === state.editingVehicleId)?.photo_image || "";
      }
      continue;
    }
    data[key] = value;
  }
  return data;
}

function readFileAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function setupPlannerControls() {
  const selectedVehicleId = document.getElementById("planner-vehicle-id")?.value || "";
  const selectedDriverId = document.getElementById("planner-driver-id")?.value || "";
  document.getElementById("planner-province").innerHTML = optionSets.provinces.map((option) => renderOption(option)).join("");
  renderPlannerCities();
  document.getElementById("planner-cargo-type").innerHTML = optionSets.cargoTypes.map((option) => renderOption(option, "鸡苗")).join("");
  document.getElementById("planner-vehicle-id").innerHTML = availableVehicleOptions().map((option) => renderOption(option)).join("");
  document.getElementById("planner-driver-id").innerHTML = driverOptions(selectedVehicleId).map((option) => renderOption(option)).join("");
  if (selectedVehicleId && availableVehicles().some((vehicle) => String(vehicle.id) === selectedVehicleId)) {
    document.getElementById("planner-vehicle-id").value = selectedVehicleId;
  }
  if (selectedDriverId && allVehicleDrivers().some((driver) => String(driver.id) === selectedDriverId)) {
    document.getElementById("planner-driver-id").value = selectedDriverId;
  }
  document.getElementById("planner-province").onchange = renderPlannerCities;
  document.getElementById("planner-vehicle-id").onchange = applyPlannerVehicleDefaults;
  document.getElementById("planner-address").oninput = handlePlannerAddressInput;
  document.getElementById("planner-address").onfocus = handlePlannerAddressInput;
  document.getElementById("planner-address").onblur = () => {
    window.setTimeout(hidePlannerAddressSuggestions, 150);
  };
  applyPlannerVehicleDefaults();
  renderPlanner();
}

function renderPlannerCities() {
  const province = document.getElementById("planner-province")?.value || optionSets.provinces[0];
  const cities = optionSets.citiesByProvince[province] || [];
  const citySelect = document.getElementById("planner-city");
  if (citySelect) citySelect.innerHTML = cities.map((city) => renderOption(city)).join("");
}

function applyPlannerVehicleDefaults() {
  const vehicleId = Number(document.getElementById("planner-vehicle-id").value || 0);
  const vehicle = state.vehicles.find((item) => item.id === vehicleId);
  const weightInput = document.getElementById("planner-cargo-weight");
  const volumeInput = document.getElementById("planner-cargo-volume");
  const driverSelect = document.getElementById("planner-driver-id");
  driverSelect.innerHTML = driverOptions(vehicleId).map((option) => renderOption(option)).join("");
  if (!vehicle) {
    weightInput.value = "";
    volumeInput.value = "";
    return;
  }
  weightInput.value = vehicle.load_capacity ?? "";
  volumeInput.value = vehicle.box_volume ?? "";
  if (vehicle.driver_id) {
    driverSelect.value = String(vehicle.driver_id);
  }
}

function handlePlannerAddressInput() {
  window.clearTimeout(state.routePlanner.addressSearchTimer);
  state.routePlanner.addressSearchTimer = window.setTimeout(searchPlannerAddressSuggestions, 280);
}

async function searchPlannerAddressSuggestions() {
  const input = document.getElementById("planner-address");
  const keyword = input.value.trim();
  if (keyword.length < 2) {
    hidePlannerAddressSuggestions();
    return;
  }
  const seq = ++state.routePlanner.addressSearchSeq;
  const province = document.getElementById("planner-province").value;
  const city = document.getElementById("planner-city").value;
  const provider = document.getElementById("planner-provider").value || "tianditu";
  try {
    const result = await api("/api/maps/search-poi", {
      method: "POST",
      body: JSON.stringify({
        provider,
        keyword,
        city,
        limit: 5,
      }),
    });
    if (seq !== state.routePlanner.addressSearchSeq) return;
    renderPlannerAddressSuggestions((result.items || []).slice(0, 5), province, city, result.message || (result.fallback ? "天地图查询失败，已显示系统候选" : ""));
  } catch (caught) {
    if (seq === state.routePlanner.addressSearchSeq) {
      renderPlannerAddressSuggestions([], province, city, caught.message || "地址查询失败");
    }
  }
}

function renderPlannerAddressSuggestions(items, province, city, message = "") {
  const panel = document.getElementById("planner-address-suggestions");
  const usableItems = items.filter((item) => item.name || item.address);
  if (!usableItems.length && !message) {
    hidePlannerAddressSuggestions();
    return;
  }
  const messageHtml = message ? `<div class="suggestion-message">${escapeHtml(message)}</div>` : "";
  const itemHtml = usableItems.map((item, index) => {
    const title = item.name || item.address;
    const address = item.address || item.name;
    const locationText = [province, city, address].filter(Boolean).join("");
    return `
      <button type="button" data-address-suggestion="${index}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(locationText)}</span>
      </button>
    `;
  }).join("");
  panel.innerHTML = messageHtml || itemHtml ? messageHtml + itemHtml : `<div class="suggestion-message">未找到相关地名</div>`;
  panel.classList.remove("hidden");
  panel.querySelectorAll("[data-address-suggestion]").forEach((button) => {
    button.addEventListener("mousedown", (event) => {
      event.preventDefault();
      const item = usableItems[Number(button.dataset.addressSuggestion)];
      document.getElementById("planner-address").value = item.address || item.name || "";
      document.getElementById("planner-name").value = item.name || item.address || "";
      hidePlannerAddressSuggestions();
    });
  });
}

function hidePlannerAddressSuggestions() {
  const panel = document.getElementById("planner-address-suggestions");
  if (!panel) return;
  panel.classList.add("hidden");
  panel.innerHTML = "";
}

async function loadAll() {
  const [summary, vehicles, orders, live, alerts, reminders, warningPreview, utilization, distance, devices, tickets, users, mapConfigs, adapters, settings, workflowDefinitions, workflowTasks, workflowInstances, pricingRates] = await Promise.all([
    api("/api/summary"),
    api("/api/vehicles"),
    api("/api/orders"),
    api("/api/tracking/live"),
    api("/api/alerts"),
    api("/api/reminders/vehicles?days=30"),
    api("/api/reminders/vehicles?days=90"),
    api("/api/reports/vehicle-utilization"),
    api("/api/reports/order-distance"),
    api("/api/devices"),
    api(`/api/tickets${queryString(state.ticketFilters)}`),
    api("/api/users"),
    api("/api/map-configs"),
    api("/api/device-vendor-adapters"),
    api("/api/system-settings"),
    api("/api/workflows/definitions"),
    api("/api/workflows/tasks"),
    api("/api/workflows/instances"),
    api("/api/pricing/rates"),
  ]);
  state.vehicles = vehicles;
  state.orders = orders;
  state.users = users;
  state.devices = devices;
  state.tickets = tickets;
  state.vehicleWarningPreview = warningPreview;
  state.summary = summary;
  state.alerts = alerts;
  state.pricingRates = pricingRates;
  state.workflowTasks = workflowTasks;
  state.settings = settings;
  state.mapConfigs = mapConfigs;
  state.live = live;
  if (state.selectedVehicleId && !vehicles.some((vehicle) => vehicle.id === state.selectedVehicleId)) {
    state.selectedVehicleId = null;
  }
  renderMetrics(summary);
  renderVehicles(vehicles);
  renderOrders(orders);
  renderLive(live);
  renderAlerts(alerts);
  renderReminders(reminders);
  renderWarningPreview(warningPreview);
  await renderRealtimeScreen();
  renderUtilization(utilization);
  renderDistance(distance);
  renderMap(live);
  renderDevices(devices);
  renderTickets(tickets);
  renderUsers(users);
  renderConfigs(mapConfigs, adapters, settings);
  renderWorkflow(workflowDefinitions, workflowTasks, workflowInstances);
  renderFreightRates(pricingRates);
  renderCharts();
  setupPlannerControls();
  renderPlanner();
  if (state.selectedVehicleId) {
    await renderSelectedVehicle();
  } else {
    renderVehicleMaintenancePlaceholder();
  }
  if (state.orderView === "detail" && state.selectedOrderId) {
    await renderSelectedOrder();
  } else {
    setOrderView(state.orderView || "list");
  }
}

function renderMetrics(summary) {
  const labels = [["vehicles", "车辆"], ["orders", "订单"], ["active_orders", "执行中"], ["open_alerts", "开放告警"], ["revenue", "收入"]];
  document.getElementById("metrics").innerHTML = labels.map(([key, label]) => `<div class="metric"><span>${label}</span><strong>${summary[key] ?? 0}</strong></div>`).join("");
}

function renderCharts() {
  const orderStatus = countBy(state.orders, (row) => statusText[row.status] || row.status);
  const vehicleStatus = countBy(state.vehicles, (row) => statusText[row.status] || row.status);
  const ticketType = sumBy(state.tickets, (row) => displayValue("ticket", row.ticket_type), (row) => Number(row.amount || 0));
  const feeTrend = sumByDate(state.tickets, (row) => row.issued_at || row.completed_at || row.order_created_at, (row) => Number(row.amount || row.estimated_fee || 0));
  if (window.echarts) {
    renderEChart("chart-order-status", pieOption("订单状态", orderStatus));
    renderEChart("chart-vehicle-status", donutOption("车辆状态", vehicleStatus));
    renderEChart("chart-ticket-type", barOption("票据金额", ticketType));
    renderEChart("chart-fee-trend", lineOption("费用趋势", feeTrend));
    return;
  }
  renderBarChart("chart-order-status", orderStatus, "#0f766e");
  renderBarChart("chart-vehicle-status", vehicleStatus, "#2563eb");
  renderBarChart("chart-ticket-type", ticketType, "#b45309");
  renderLineChart("chart-fee-trend", feeTrend);
}

function countBy(rows, keyFn) {
  const data = {};
  rows.forEach((row) => {
    const key = keyFn(row) || "未分类";
    data[key] = (data[key] || 0) + 1;
  });
  return Object.entries(data).map(([label, value]) => ({ label, value }));
}

function sumBy(rows, keyFn, valueFn) {
  const data = {};
  rows.forEach((row) => {
    const key = keyFn(row) || "未分类";
    data[key] = (data[key] || 0) + valueFn(row);
  });
  return Object.entries(data).map(([label, value]) => ({ label, value: Number(value.toFixed(2)) }));
}

function sumByDate(rows, dateFn, valueFn) {
  const data = {};
  rows.forEach((row) => {
    const key = String(dateFn(row) || "").slice(0, 10) || "未填日期";
    data[key] = (data[key] || 0) + valueFn(row);
  });
  return Object.entries(data).sort(([a], [b]) => a.localeCompare(b)).slice(-12).map(([label, value]) => ({ label, value: Number(value.toFixed(2)) }));
}

function renderEChart(id, option) {
  const panel = document.getElementById(id);
  if (!option.dataset?.source?.length && !option.series?.[0]?.data?.length) {
    if (state.chartInstances[id]) {
      state.chartInstances[id].dispose();
      delete state.chartInstances[id];
    }
    panel.innerHTML = `<div class="chart-empty">暂无数据</div>`;
    return;
  }
  let chart = state.chartInstances[id];
  if (!chart) {
    panel.innerHTML = "";
    chart = window.echarts.init(panel);
    state.chartInstances[id] = chart;
  }
  chart.setOption(option, true);
  window.setTimeout(() => chart.resize(), 0);
}

function chartToolbox() {
  return {
    right: 8,
    feature: {
      dataView: { readOnly: true, title: "数据" },
      restore: { title: "还原" },
      saveAsImage: { title: "保存图片" },
    },
  };
}

function pieOption(title, data) {
  return {
    color: ["#0f766e", "#2563eb", "#b45309", "#7c3aed", "#15803d", "#b91c1c"],
    tooltip: { trigger: "item" },
    legend: { bottom: 0, type: "scroll" },
    toolbox: chartToolbox(),
    series: [{
      name: title,
      type: "pie",
      radius: "62%",
      center: ["50%", "45%"],
      roseType: "radius",
      data: data.map((item) => ({ name: item.label, value: item.value })),
      animationDuration: 900,
    }],
  };
}

function donutOption(title, data) {
  return {
    color: ["#2563eb", "#0f766e", "#b45309", "#b91c1c", "#64748b"],
    tooltip: { trigger: "item" },
    legend: { bottom: 0, type: "scroll" },
    toolbox: chartToolbox(),
    series: [{
      name: title,
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "45%"],
      avoidLabelOverlap: true,
      data: data.map((item) => ({ name: item.label, value: item.value })),
      animationType: "scale",
      animationDuration: 900,
    }],
  };
}

function barOption(title, data) {
  return {
    color: ["#b45309"],
    tooltip: { trigger: "axis" },
    toolbox: chartToolbox(),
    grid: { left: 44, right: 18, top: 36, bottom: 46 },
    xAxis: { type: "category", data: data.map((item) => item.label), axisLabel: { interval: 0, rotate: data.length > 4 ? 28 : 0 } },
    yAxis: { type: "value", name: "金额" },
    series: [{ name: title, type: "bar", data: data.map((item) => item.value), barMaxWidth: 42, label: { show: true, position: "top" }, animationDelay: (idx) => idx * 80 }],
  };
}

function lineOption(title, data) {
  return {
    color: ["#0f766e"],
    tooltip: { trigger: "axis" },
    toolbox: chartToolbox(),
    grid: { left: 48, right: 18, top: 36, bottom: 44 },
    xAxis: { type: "category", boundaryGap: false, data: data.map((item) => item.label) },
    yAxis: { type: "value", name: "金额" },
    series: [{
      name: title,
      type: "line",
      smooth: true,
      symbolSize: 8,
      areaStyle: { opacity: 0.18 },
      data: data.map((item) => item.value),
      animationDuration: 1000,
    }],
  };
}

function renderBarChart(id, data, color) {
  const panel = document.getElementById(id);
  if (!data.length) {
    panel.innerHTML = `<div class="chart-empty">暂无数据</div>`;
    return;
  }
  const max = Math.max(...data.map((item) => item.value), 1);
  const width = 520;
  const height = 190;
  const barWidth = Math.max(24, Math.floor((width - 80) / data.length) - 12);
  const bars = data.map((item, index) => {
    const x = 50 + index * (barWidth + 12);
    const h = Math.round((height - 55) * item.value / max);
    const y = height - 32 - h;
    return `
      <rect x="${x}" y="${y}" width="${barWidth}" height="${h}" rx="4" fill="${color}"></rect>
      <text x="${x + barWidth / 2}" y="${y - 6}" text-anchor="middle" font-size="12" fill="#1d2935">${item.value}</text>
      <text x="${x + barWidth / 2}" y="${height - 10}" text-anchor="middle" font-size="11" fill="#667789">${escapeHtml(item.label).slice(0, 6)}</text>
    `;
  }).join("");
  panel.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-label="${id}">${bars}</svg>`;
}

function renderLineChart(id, data) {
  const panel = document.getElementById(id);
  if (!data.length) {
    panel.innerHTML = `<div class="chart-empty">暂无数据</div>`;
    return;
  }
  const width = 520;
  const height = 190;
  const max = Math.max(...data.map((item) => item.value), 1);
  const points = data.map((item, index) => {
    const x = data.length === 1 ? width / 2 : 44 + index * ((width - 80) / (data.length - 1));
    const y = height - 32 - ((height - 58) * item.value / max);
    return { ...item, x, y };
  });
  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const nodes = points.map((point) => `
    <circle cx="${point.x}" cy="${point.y}" r="4" fill="#0f766e"></circle>
    <text x="${point.x}" y="${height - 10}" text-anchor="middle" font-size="10" fill="#667789">${escapeHtml(point.label.slice(5))}</text>
  `).join("");
  panel.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-label="${id}"><polyline points="${line}" fill="none" stroke="#0f766e" stroke-width="3"></polyline>${nodes}</svg>`;
}

function renderVehicles(rows) {
  document.getElementById("vehicle-table").innerHTML = rows.map((row) => `
    <tr>
      <td>${vehiclePhotoHtml(row)}</td><td>${row.plate_no}</td><td>${row.vehicle_type}</td><td>${row.brand_model || "-"}</td>
      <td>${row.load_capacity} 吨</td><td>${row.box_volume || "-"} m3</td><td>${row.box_type}</td>
      <td>${row.default_driver_name || findVehicleDriver(row.driver_id)?.name || "-"}</td><td>${row.organization || "-"}</td><td><span class="badge">${statusText[row.status] || row.status}</span></td>
      <td><button data-edit-vehicle="${row.id}">编辑</button><button data-select-vehicle="${row.id}">维护</button></td>
    </tr>
  `).join("");
  document.querySelectorAll("[data-edit-vehicle]").forEach((button) => {
    button.addEventListener("click", () => {
      const vehicle = state.vehicles.find((item) => item.id === Number(button.dataset.editVehicle));
      state.editingVehicleId = vehicle?.id || null;
      openForm("vehicle-edit", vehicle || {});
    });
  });
  document.querySelectorAll("[data-select-vehicle]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedVehicleId = Number(button.dataset.selectVehicle);
      await renderSelectedVehicle();
    });
  });
}

function vehiclePhotoHtml(row) {
  if (row.photo_image) {
    return `<img class="vehicle-photo" src="${escapeHtml(row.photo_image)}" alt="${escapeHtml(row.plate_no)}车辆照片">`;
  }
  return `<div class="vehicle-photo placeholder" aria-label="未上传车辆照片">${escapeHtml(row.plate_no || "车辆").slice(0, 1)}</div>`;
}

async function renderSelectedVehicle() {
  if (!state.selectedVehicleId) {
    renderVehicleMaintenancePlaceholder();
    return;
  }
  const detail = await api(`/api/vehicles/${state.selectedVehicleId}`);
  document.getElementById("vehicle-driver-list").innerHTML = (detail.drivers || []).map((row) => `
    <div class="item"><strong>${row.name} ${row.is_default ? "· 默认" : ""}</strong><span>${row.phone || "-"} · 驾驶证 ${row.license_no || "-"} · 从业资格 ${row.qualification_no || "-"} · ${statusText[row.status] || row.status}</span></div>
  `).join("") || `<div class="item"><strong>暂无司机资料</strong><span>请在车辆档案中新增司机后再创建订单</span></div>`;
  document.getElementById("maintenance-list").innerHTML = detail.maintenance.map((row) => `
    <div class="item"><strong>${row.title} · ${row.type}</strong><span>${row.service_date} · ${row.mileage || 0} km · ${row.cost || 0} 元 · ${row.vendor || ""}</span></div>
  `).join("");
  const reminders = await api("/api/reminders/vehicles?days=365");
  const relevant = reminders.filter((row) => row.vehicle_id === state.selectedVehicleId);
  document.getElementById("certificate-reminders").innerHTML = relevant.map((row) => `
    <div class="item"><strong>${row.plate_no} · ${displayValue("cert", row.type)}</strong><span class="badge ${row.level}">${row.end_date} · 剩余 ${row.days_left} 天 · ${row.message || ""}</span></div>
  `).join("") || `<div class="item"><strong>暂无证照保险税费提醒</strong><span>该车辆暂无到期提醒</span></div>`;
}

function renderVehicleMaintenancePlaceholder() {
  const placeholder = `<div class="item"><strong>请选择车辆</strong><span>点击车辆档案列表中的“维护”，查看该车辆对应信息</span></div>`;
  document.getElementById("vehicle-driver-list").innerHTML = placeholder;
  document.getElementById("maintenance-list").innerHTML = placeholder;
  document.getElementById("certificate-reminders").innerHTML = placeholder;
}

function setOrderView(view) {
  state.orderView = view;
  document.getElementById("order-planner-panel").classList.toggle("hidden", view !== "create");
  document.getElementById("order-detail-panel").classList.toggle("hidden", view !== "detail");
  document.getElementById("order-map-panel").classList.toggle("hidden", view !== "detail");
  if (view === "list") {
    state.selectedRoute = [];
    state.selectedReturnRoute = [];
    state.selectedRouteStops = [];
    state.selectedRouteLabel = "未选择路线";
    document.getElementById("order-detail").innerHTML = "";
    document.getElementById("order-logs").innerHTML = "";
    renderMap(state.live);
  }
}

function renderOrders(rows) {
  const vehicleName = new Map(state.vehicles.map((item) => [item.id, item.plate_no]));
  const totalPages = Math.max(1, Math.ceil(rows.length / state.orderPageSize));
  state.orderPage = Math.min(state.orderPage, totalPages);
  const start = (state.orderPage - 1) * state.orderPageSize;
  const pageRows = rows.slice(start, start + state.orderPageSize);
  document.getElementById("order-table").innerHTML = pageRows.map((row) => `
    <tr>
      <td>${row.order_no}</td><td>${row.cargo_name}</td><td>${displayValue("cargo", row.cargo_type)}</td><td>${row.cargo_weight} 吨</td>
      <td>${row.cargo_volume} m3</td><td>${vehicleName.get(row.vehicle_id) || "-"}</td><td>${row.planned_distance || 0}</td>
      <td>${row.return_distance || 0}</td><td>${row.billable_distance || row.planned_distance || 0}</td>
      <td>${row.estimated_fee || row.actual_fee || 0}</td><td><span class="badge">${statusText[row.status] || row.status}</span>${row.ticket_exception ? `<span class="badge warning">${escapeHtml(row.ticket_exception)}</span>` : ""}</td>
      <td>${orderActions(row)} <button data-select-order="${row.id}">详情</button></td>
    </tr>
  `).join("");
  document.querySelectorAll("[data-action]").forEach((button) => button.addEventListener("click", () => changeOrder(button.dataset.id, button.dataset.action)));
  document.querySelectorAll("[data-select-order]").forEach((button) => button.addEventListener("click", async () => {
    state.selectedOrderId = Number(button.dataset.selectOrder);
    setOrderView("detail");
    await renderSelectedOrder();
    document.getElementById("order-detail-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
  renderOrderPagination(rows.length, totalPages);
}

function renderOrderPagination(total, totalPages) {
  const pager = document.getElementById("order-pagination");
  pager.innerHTML = `
    <button type="button" data-order-page="${state.orderPage - 1}" ${state.orderPage <= 1 ? "disabled" : ""}>上一页</button>
    <span>第 ${state.orderPage} / ${totalPages} 页 · 共 ${total} 单</span>
    <button type="button" data-order-page="${state.orderPage + 1}" ${state.orderPage >= totalPages ? "disabled" : ""}>下一页</button>
  `;
  document.querySelectorAll("[data-order-page]").forEach((button) => {
    button.addEventListener("click", () => {
      state.orderPage = Number(button.dataset.orderPage);
      renderOrders(state.orders);
    });
  });
}

function orderActions(row) {
  if (row.status === "pending" && canRunOrderAction(row, "confirm")) return `<button data-id="${row.id}" data-action="confirm">确认</button>`;
  if ((row.status === "confirmed" || row.status === "assigned") && canRunOrderAction(row, "start")) return `<button data-id="${row.id}" data-action="start">发车</button>`;
  if (row.status === "in_transit" && canRunOrderAction(row, "complete")) return `<button data-id="${row.id}" data-action="complete">完成</button>`;
  return "";
}

function canRunOrderAction(row, action) {
  if (state.user?.role === "admin") return true;
  const allowedSteps = action === "start" ? ["assign", "start"] : [action];
  return state.workflowTasks.some((task) => task.biz_type === "order" && Number(task.biz_id) === Number(row.id) && allowedSteps.includes(task.step_code));
}

async function renderSelectedOrder() {
  if (!state.selectedOrderId) return;
  const detail = await api(`/api/orders/${state.selectedOrderId}`);
  const logs = await api(`/api/orders/${state.selectedOrderId}/logs`);
  const vehicle = state.vehicles.find((item) => item.id === detail.vehicle_id);
  const driver = findVehicleDriver(detail.driver_id);
  const routes = detail.routes.map((route) => ({ ...route, polyline: parsePolyline(route.polyline) }));
  const forwardRoute = routes.find((route) => !String(route.preference || "").startsWith("return_")) || routes[0];
  const returnRoute = routes.find((route) => String(route.preference || "").startsWith("return_"));
  if (forwardRoute?.polyline?.length) {
    state.selectedRoute = forwardRoute.polyline;
    state.selectedReturnRoute = returnRoute?.polyline || [];
    state.selectedRouteStops = orderStopPoints(detail.stops);
    state.selectedRouteLabel = `${detail.order_no} · 去程 ${forwardRoute.planned_distance}km · 回程 ${returnRoute?.planned_distance || detail.return_distance || 0}km`;
    renderMap(state.live);
  }
  document.getElementById("order-detail").innerHTML = [
    `<div class="item"><strong>发货单号 ${detail.order_no} · ${detail.cargo_name}</strong><span>${detail.status} · 下单时间 ${detail.created_at || "-"} · 车牌 ${vehicle?.plate_no || "-"} · 司机 ${driver?.name || "-"} · 单程 ${detail.planned_distance || 0} km · 返程 ${detail.return_distance || 0} km · 计费 ${detail.billable_distance || 0} km · 运费 ${detail.estimated_fee || 0}</span></div>`,
    detail.ticket_exception ? `<div class="item"><strong>异常请核实</strong><span>${escapeHtml(detail.ticket_exception)}</span></div>` : "",
    detail.order_description ? `<div class="item"><strong>订单描述</strong><span>${escapeHtml(detail.order_description)}</span></div>` : "",
    ...detail.stops.map((stop) => `<div class="item"><strong>${stop.sequence_no}. ${stop.name} · ${stop.stop_type}</strong><span>${stop.address} · ${stop.contact || ""} ${stop.phone || ""}</span></div>`),
    ...routes.map((route, index) => `<div class="item"><strong>路线 ${route.provider} · ${route.preference}</strong><span>单程 ${route.planned_distance} km · 返程 ${route.return_distance || 0} km · 计费 ${route.billable_distance || route.planned_distance} km · 运费 ${route.freight_fee || 0} · 过路费 ${route.toll_fee}</span><div class="actions"><button data-route-preview="${index}">预览路线</button></div></div>`),
  ].join("");
  document.getElementById("order-logs").innerHTML = logs.map((log) => `<div class="item"><strong>${log.action}</strong><span>${log.before_status} -> ${log.after_status} · ${log.changed_by_name || "-"} · ${log.created_at}</span></div>`).join("");
  document.querySelectorAll("[data-route-preview]").forEach((button) => {
    button.addEventListener("click", () => {
      const route = routes[Number(button.dataset.routePreview)];
      state.selectedRoute = route.polyline;
      state.selectedReturnRoute = String(route.preference || "").startsWith("return_") ? [] : (returnRoute?.polyline || []);
      state.selectedRouteStops = orderStopPoints(detail.stops);
      state.selectedRouteLabel = `${detail.order_no} · ${route.provider} · ${route.planned_distance}km`;
      renderMap(state.live);
    });
  });
}

async function changeOrder(id, action) {
  let payload = { confirmed_by: state.user.real_name };
  if (action === "complete") {
    const completedBy = window.prompt("请输入完成订单确认人员");
    if (!completedBy) return;
    payload = { actual_distance: 198.6, actual_fee: 4300, completed_confirmed_by: completedBy, remark: `完成确认人员：${completedBy}` };
  }
  await api(`/api/orders/${id}/${action}`, { method: "POST", body: JSON.stringify(payload) });
  await loadAll();
}

function renderLive(rows) {
  document.getElementById("live-table").innerHTML = rows.map((row) => `
    <tr><td>${row.plate_no}</td><td>${statusText[row.status] || row.status}</td><td>${row.speed ?? "-"} km/h</td>
    <td>${row.lng && row.lat ? `${Number(row.lng).toFixed(4)}, ${Number(row.lat).toFixed(4)}` : "-"}</td><td>${row.received_at || "-"}</td></tr>
  `).join("");
}

function renderAlerts(rows) {
  document.getElementById("alerts").innerHTML = rows.slice(0, 8).map((row) => `<div class="item"><strong>${row.title}</strong><span>${row.level} · ${row.message} · ${row.created_at}</span></div>`).join("");
}

function renderReminders(rows) {
  document.getElementById("vehicle-reminders").innerHTML = rows.slice(0, 8).map((row) => `
    <div class="item"><strong>${row.plate_no} · ${displayValue("cert", row.type)}</strong><span class="badge ${row.level}">${row.end_date} · 剩余 ${row.days_left} 天 · ${row.message || ""}</span></div>
  `).join("");
  if (state.selectedVehicleId) return;
  renderVehicleMaintenancePlaceholder();
}

function renderWarningPreview(rows) {
  const sorted = [...rows].sort((a, b) => Number(a.days_left || 0) - Number(b.days_left || 0));
  const counts = sorted.reduce((acc, row) => {
    acc[warningLevel(row).level] += 1;
    return acc;
  }, { critical: 0, warning: 0, attention: 0 });
  document.getElementById("warning-summary").innerHTML = [
    warningSummaryCard("critical", "已超期", counts.critical),
    warningSummaryCard("warning", "7 天内到期", counts.warning),
    warningSummaryCard("attention", "90 天内关注", counts.attention),
  ].join("");
  document.getElementById("warning-preview-list").innerHTML = sorted.map((row) => {
    const level = warningLevel(row);
    const vehicle = state.vehicles.find((item) => Number(item.id) === Number(row.vehicle_id));
    return `
      <article class="warning-card ${level.level}">
        <div>
          <span class="badge ${level.level}">${level.label}</span>
          <strong>${escapeHtml(row.plate_no || vehicle?.plate_no || "-")} · ${escapeHtml(displayValue("cert", row.type))}</strong>
        </div>
        <span>${escapeHtml(row.title || row.message || "车辆档案提醒")}</span>
        <dl>
          <div><dt>到期日期</dt><dd>${escapeHtml(row.end_date || "-")}</dd></div>
          <div><dt>剩余天数</dt><dd>${Number(row.days_left || 0)} 天</dd></div>
          <div><dt>提醒类型</dt><dd>${row.category === "maintenance" ? "维护保养" : "证照保险税费"}</dd></div>
          <div><dt>车辆组织</dt><dd>${escapeHtml(vehicle?.organization || "-")}</dd></div>
        </dl>
      </article>
    `;
  }).join("") || `<div class="item"><strong>暂无车辆档案告警</strong><span>未来 90 天内没有超期或临期条目</span></div>`;
}

function warningSummaryCard(level, label, count) {
  return `<div class="warning-stat ${level}"><span>${label}</span><strong>${count}</strong></div>`;
}

function warningLevel(row) {
  const daysLeft = Number(row.days_left || 0);
  if (daysLeft < 0) return { level: "critical", label: "已超期" };
  if (daysLeft <= 7) return { level: "warning", label: "即将到期" };
  return { level: "attention", label: "关注提醒" };
}

function updateRealtimeClock() {
  const clock = document.getElementById("screen-clock");
  if (!clock) return;
  clock.textContent = new Date().toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

async function toggleRealtimeFullscreen() {
  const shell = document.querySelector("#realtime-screen .screen-shell");
  if (!shell) return;
  if (document.fullscreenElement) {
    await document.exitFullscreen();
  } else {
    await shell.requestFullscreen();
  }
  updateRealtimeFullscreenButton();
}

function updateRealtimeFullscreenButton() {
  const button = document.getElementById("screen-fullscreen");
  if (!button) return;
  const isFullscreen = Boolean(document.fullscreenElement);
  button.textContent = isFullscreen ? "退出全屏" : "全屏";
  button.classList.toggle("active", isFullscreen);
  window.setTimeout(syncTiandituCanvasScale, 80);
}

async function renderRealtimeScreen() {
  if (!document.getElementById("screen-map")) return;
  updateRealtimeClock();
  const activeOrders = state.orders
    .filter((order) => ["assigned", "confirmed", "in_transit"].includes(order.status))
    .slice(0, 8);
  state.screenRoutes = await buildScreenPlannedRoutes(activeOrders);
  renderScreenKpis(activeOrders);
  renderScreenStatusList();
  renderScreenAlerts();
  renderScreenVehicleList();
  renderScreenOrders(activeOrders);
  renderScreenMap(state.screenRoutes);
  renderScreenRouteLegend(state.screenRoutes);
}

async function buildScreenPlannedRoutes(activeOrders) {
  const details = await Promise.all(activeOrders.map((order) => api(`/api/orders/${order.id}`).catch(() => null)));
  return details
    .filter(Boolean)
    .map((detail, index) => {
      const routes = (detail.routes || []).map((route) => ({ ...route, polyline: parsePolyline(route.polyline) }));
      const forwardRoute = routes.find((route) => !String(route.preference || "").startsWith("return_")) || routes[0] || {};
      const vehicle = state.vehicles.find((item) => Number(item.id) === Number(detail.vehicle_id));
      return {
        id: `planned-${detail.id}`,
        kind: "planned",
        orderNo: detail.order_no,
        cargoName: detail.cargo_name || "规划线路",
        plateNo: vehicle?.plate_no || detail.plate_no || "-",
        status: detail.status,
        distance: forwardRoute.planned_distance || detail.planned_distance || 0,
        points: (forwardRoute.polyline || []).filter((point) => point.lng && point.lat).map((point) => ({
          lng: Number(point.lng),
          lat: Number(point.lat),
          label: point.name || detail.order_no,
        })),
        stops: orderStopPoints(detail.stops),
        color: screenRouteColors[index % screenRouteColors.length],
      };
    })
    .filter((route) => route.points.length > 1);
}

function renderScreenKpis(activeOrders) {
  const kpis = [
    ["车辆总数", state.summary.vehicles ?? state.vehicles.length, "台"],
    ["执行中订单", state.summary.active_orders ?? activeOrders.length, "单"],
    ["在线车辆", state.live.length, "台"],
    ["开放告警", state.summary.open_alerts ?? state.alerts.length, "条"],
  ];
  document.getElementById("screen-kpis").innerHTML = kpis.map(([label, value, unit]) => `
    <div class="screen-kpi">
      <span>${label}</span>
      <strong>${value}</strong>
      <em>${unit}</em>
    </div>
  `).join("");
}

function renderScreenStatusList() {
  const vehicleCounts = countBy(state.vehicles, (row) => statusText[row.status] || row.status || "未知");
  const items = vehicleCounts.slice(0, 5);
  document.getElementById("screen-status-list").innerHTML = items.map((item) => `
    <div class="screen-row">
      <span>${escapeHtml(item.label)}</span>
      <strong>${item.value}</strong>
    </div>
  `).join("") || `<div class="screen-empty">暂无车辆状态</div>`;
}

function renderScreenAlerts() {
  const rows = (state.alerts || []).slice(0, 5);
  document.getElementById("screen-alerts").innerHTML = rows.map((row) => `
    <div class="screen-alert ${escapeHtml(row.level || "info")}">
      <strong>${escapeHtml(row.title || "系统告警")}</strong>
      <span>${escapeHtml(row.message || "-")}</span>
    </div>
  `).join("") || `<div class="screen-empty">当前无开放告警</div>`;
}

function renderScreenVehicleList() {
  const rows = state.live.slice(0, 7);
  document.getElementById("screen-vehicle-list").innerHTML = rows.map((row) => `
    <div class="screen-vehicle">
      <div>
        <strong>${escapeHtml(row.plate_no || "-")}</strong>
        <span>${escapeHtml(row.received_at || "暂无时间")}</span>
      </div>
      <em>${row.speed ?? "-"} km/h</em>
    </div>
  `).join("") || `<div class="screen-empty">暂无实时车辆定位</div>`;
}

function renderScreenOrders(activeOrders) {
  document.getElementById("screen-orders").innerHTML = activeOrders.slice(0, 6).map((order) => `
    <div class="screen-order">
      <strong>${escapeHtml(order.order_no || "-")}</strong>
      <span>${escapeHtml(order.cargo_name || "运输订单")} · ${escapeHtml(statusText[order.status] || order.status || "-")}</span>
    </div>
  `).join("") || `<div class="screen-empty">暂无执行中订单</div>`;
}

function renderScreenMap(routes) {
  const livePoints = state.live.filter((row) => row.lng && row.lat).map((row) => ({
    lng: Number(row.lng),
    lat: Number(row.lat),
    label: row.plate_no || "车辆",
    speed: row.speed,
  }));
  const stopPoints = routes.flatMap((route) => route.stops.map((stop) => ({ ...stop, color: route.color, orderNo: route.orderNo })));
  const allPoints = [...routes.flatMap((route) => route.points), ...stopPoints, ...livePoints];
  if (!allPoints.length) {
    document.getElementById("screen-map").innerHTML = `<div class="screen-map-empty">暂无可展示的车辆位置或运输线路</div>`;
    return;
  }
  const bounds = calcBounds(allPoints);
  const project = (point) => projectPoint(point, bounds);
  const routeLines = routes.map((route) => {
    const projected = route.points.map(project);
    return projected.length > 1 ? `<polyline class="screen-route-line planned" points="${projected.map((point) => `${point.x},${point.y}`).join(" ")}" style="stroke:${route.color}"></polyline>` : "";
  }).join("");
  const stops = stopPoints.map((stop) => {
    const point = project(stop);
    return `
      <g class="screen-stop">
        <circle cx="${point.x}" cy="${point.y}" r="5" style="stroke:${stop.color}"></circle>
        <text x="${point.x + 9}" y="${point.y - 8}">${escapeHtml(stop.label || stop.name || "站点")}</text>
      </g>
    `;
  }).join("");
  const vehicles = livePoints.map((vehicle) => {
    const point = project(vehicle);
    return `
      <g class="screen-vehicle-node">
        <circle class="screen-vehicle-pulse" cx="${point.x}" cy="${point.y}" r="18"></circle>
        <circle cx="${point.x}" cy="${point.y}" r="7"></circle>
        <text x="${point.x}" y="${point.y - 24}" text-anchor="middle">${escapeHtml(vehicle.label)}</text>
      </g>
    `;
  }).join("");
  if (isTiandituEnabled()) {
    document.getElementById("screen-map").innerHTML = buildScreenTiandituMap(routes, stopPoints, livePoints);
    syncTiandituCanvasScale();
    return;
  }
  const baseMap = buildScreenBaseMap();
  document.getElementById("screen-map").innerHTML = `
    <svg class="screen-map-svg" viewBox="0 0 1000 520" role="img" aria-label="实时运输车辆位置和线路">
      <defs>
        <pattern id="screen-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(34,211,238,.12)" stroke-width="1"></path>
        </pattern>
        <filter id="screen-glow">
          <feGaussianBlur stdDeviation="4" result="blur"></feGaussianBlur>
          <feMerge><feMergeNode in="blur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge>
        </filter>
      </defs>
      ${baseMap}
      <rect class="screen-blue-mask-svg" width="1000" height="520"></rect>
      ${routeLines}
      ${stops}
      ${vehicles}
    </svg>
  `;
}

function buildScreenTiandituMap(routes, stopPoints, livePoints) {
  const width = 1000;
  const height = 520;
  const allPoints = [...routes.flatMap((route) => route.points), ...stopPoints, ...livePoints];
  const zoom = chooseTileZoom(allPoints, width, height);
  const projected = allPoints.map((point) => lonLatToWorld(point.lng, point.lat, zoom));
  const minX = Math.min(...projected.map((point) => point.x));
  const maxX = Math.max(...projected.map((point) => point.x));
  const minY = Math.min(...projected.map((point) => point.y));
  const maxY = Math.max(...projected.map((point) => point.y));
  const center = { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
  const topLeft = { x: center.x - width / 2, y: center.y - height / 2 };
  const project = (point) => {
    const world = lonLatToWorld(point.lng, point.lat, zoom);
    return { x: Math.round(world.x - topLeft.x), y: Math.round(world.y - topLeft.y) };
  };
  const routeLines = routes.map((route) => {
    const projectedRoute = route.points.map(project);
    return projectedRoute.length > 1 ? `<polyline class="screen-route-line planned" points="${projectedRoute.map((point) => `${point.x},${point.y}`).join(" ")}" style="stroke:${route.color}"></polyline>` : "";
  }).join("");
  const stops = stopPoints.map((stop) => {
    const point = project(stop);
    return `
      <g class="screen-stop">
        <circle cx="${point.x}" cy="${point.y}" r="5" style="stroke:${stop.color}"></circle>
        <text x="${point.x + 9}" y="${point.y - 8}">${escapeHtml(stop.label || stop.name || "站点")}</text>
      </g>
    `;
  }).join("");
  const vehicles = livePoints.map((vehicle) => {
    const point = project(vehicle);
    return `
      <g class="screen-vehicle-node">
        <circle class="screen-vehicle-pulse" cx="${point.x}" cy="${point.y}" r="18"></circle>
        <circle cx="${point.x}" cy="${point.y}" r="7"></circle>
        <text x="${point.x}" y="${point.y - 24}" text-anchor="middle">${escapeHtml(vehicle.label)}</text>
      </g>
    `;
  }).join("");
  return `
    <div class="tdt-map screen-tdt-map" role="img" aria-label="天地图实时运输车辆位置和线路">
      <div class="tdt-canvas">
        ${buildTiandituTiles(topLeft, width, height, zoom)}
        <div class="screen-blue-mask"></div>
        <svg class="map-overlay screen-map-overlay" viewBox="0 0 ${width} ${height}">
          <defs>
            <filter id="screen-glow">
              <feGaussianBlur stdDeviation="4" result="blur"></feGaussianBlur>
              <feMerge><feMergeNode in="blur"></feMergeNode><feMergeNode in="SourceGraphic"></feMergeNode></feMerge>
            </filter>
          </defs>
          ${routeLines}
          ${stops}
          ${vehicles}
        </svg>
      </div>
    </div>
  `;
}

function buildScreenBaseMap() {
  const cities = [
    [140, 116, "保定"], [276, 154, "石家庄"], [430, 112, "沧州"], [574, 184, "衡水"],
    [724, 132, "德州"], [822, 242, "济南"], [650, 338, "邢台"], [458, 390, "邯郸"],
  ];
  const cityNodes = cities.map(([x, y, label]) => `
    <g class="screen-city">
      <circle cx="${x}" cy="${y}" r="4"></circle>
      <text x="${x + 9}" y="${y - 7}">${label}</text>
    </g>
  `).join("");
  return `
    <rect width="1000" height="520" fill="url(#screen-grid)"></rect>
    <path class="screen-map-area" d="M60 110 L220 52 L360 96 L470 60 L642 104 L818 82 L934 170 L902 338 L760 452 L540 426 L376 474 L178 416 L82 286 Z"></path>
    <path class="screen-map-area secondary" d="M220 154 L392 118 L560 174 L688 280 L612 388 L418 382 L292 292 Z"></path>
    <path class="screen-map-river" d="M 40 400 C 220 330, 280 420, 450 350 S 730 270, 960 330"></path>
    <path class="screen-road trunk" d="M94 128 C230 152, 348 152, 482 206 S720 272, 910 214"></path>
    <path class="screen-road trunk" d="M162 438 C268 318, 392 256, 540 196 S746 114, 920 146"></path>
    <path class="screen-road" d="M120 258 C272 232, 426 258, 592 328 S790 386, 918 352"></path>
    <path class="screen-road" d="M306 74 C330 194, 376 292, 480 430"></path>
    <path class="screen-road" d="M662 96 C620 194, 618 310, 684 438"></path>
    ${cityNodes}
  `;
}

function renderScreenRouteLegend(routes) {
  document.getElementById("screen-route-legend").innerHTML = routes.slice(0, 8).map((route) => `
    <div class="screen-legend-item">
      <i style="background:${route.color}"></i>
      <span>规划 · ${escapeHtml(route.orderNo)} · ${escapeHtml(route.plateNo)}</span>
      <em>${Number(route.distance || 0)} km</em>
    </div>
  `).join("") || `<div class="screen-empty">暂无线路图例</div>`;
}

function renderUtilization(rows) {
  document.getElementById("utilization").innerHTML = rows.map((row) => `<div class="item"><strong>${row.plate_no}</strong><span>趟次 ${row.order_count} · 里程 ${row.distance || 0} · 利用率 ${Math.round(row.utilization * 100)}%</span></div>`).join("");
}

function renderDistance(rows) {
  document.getElementById("distance-report").innerHTML = rows.map((row) => `<div class="item"><strong>${row.order_no}</strong><span>${row.cargo_name} · 单程 ${row.planned_distance || 0} km · 实际 ${row.actual_distance || 0} km</span></div>`).join("");
}

function renderFreightRates(rows) {
  document.getElementById("freight-rates").innerHTML = rows.map((row) => `
    <div class="item">
      <strong>${row.vehicle_type} / ${row.cargo_type}</strong>
      <span>${row.base_rate_per_km} 元/km · 最低 ${row.min_fee} 元 · 过路费系数 ${row.toll_multiplier} · 装卸 ${row.loading_fee} 元</span>
    </div>
  `).join("");
}

function renderAddressRouteResult(result) {
  state.selectedOrderId = result.order.id;
  state.selectedRoute = result.forward_route.polyline || [];
  state.selectedReturnRoute = result.return_route.polyline || [];
  state.selectedRouteStops = [result.origin, ...(result.waypoints || []), result.destination].filter((point) => point?.lng && point?.lat).map((point, index) => ({
    lng: point.lng,
    lat: point.lat,
    label: point.name || (index === 0 ? "起点" : "站点"),
    name: point.name || (index === 0 ? "起点" : "站点"),
  }));
  state.selectedRouteLabel = `${result.order.order_no} · 去程 ${result.forward_route.planned_distance}km · 回程 ${result.return_route.planned_distance}km`;
  state.verificationCenter = result.destination || null;
  state.routePlanner.lastResult = result;
  state.routePlanner.stations = [
    ...(result.waypoints || []).map((item) => ({ ...item, type: "waypoint" })),
    { ...(result.destination || {}), type: "destination" },
  ].filter((item) => item.address);
  renderPlanner();
  renderMap(state.live);
}

function renderPricingEstimate(result) {
  document.getElementById("pricing-estimate-result").innerHTML = `
    <div class="item">
      <strong>${result.freight_fee} 元</strong>
      <span>单程 ${result.one_way_distance} km · 返程 ${result.return_distance} km · 计费 ${result.billable_distance} km · ${result.base_rate_per_km} 元/km · 过路费 ${result.toll_fee} 元 · ${result.formula}</span>
    </div>
  `;
}

function renderMap(rows) {
  const livePoints = rows.filter((row) => row.lng && row.lat).map((row) => ({
    lng: Number(row.lng),
    lat: Number(row.lat),
    label: row.plate_no,
    type: "vehicle",
  }));
  const routeLinePoints = (state.selectedRoute || []).filter((point) => point.lng && point.lat).map((point, index) => ({
    lng: Number(point.lng),
    lat: Number(point.lat),
    label: point.name || (index === 0 ? "起点" : (index === state.selectedRoute.length - 1 ? "终点" : `途经${index}`)),
    type: "route",
  }));
  const returnLinePoints = (state.selectedReturnRoute || []).filter((point) => point.lng && point.lat).map((point) => ({
    lng: Number(point.lng),
    lat: Number(point.lat),
    label: point.name || "返程",
    type: "return",
  }));
  let routeStopPoints = (state.selectedRouteStops || []).filter((point) => point.lng && point.lat).map((point, index) => ({
    lng: Number(point.lng),
    lat: Number(point.lat),
    label: point.label || point.name || (index === 0 ? "起点" : "站点"),
    type: "route",
  }));
  if (!routeStopPoints.length && routeLinePoints.length) {
    routeStopPoints = [routeLinePoints[0], routeLinePoints[routeLinePoints.length - 1]];
  }
  const html = buildMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, state.selectedRouteLabel, state.verificationCenter);
  ["map-panel", "order-map-panel"].forEach((id) => {
    const panel = document.getElementById(id);
    if (panel) panel.innerHTML = html;
  });
  syncTiandituCanvasScale();
  document.querySelectorAll("[data-map-zoom]").forEach((button) => {
    button.addEventListener("click", () => {
      state.mapZoomAdjust = Math.max(-4, Math.min(4, state.mapZoomAdjust + Number(button.dataset.mapZoom)));
      renderMap(state.live);
    });
  });
}

function syncTiandituCanvasScale() {
  document.querySelectorAll(".tdt-map").forEach((map) => {
    const width = map.clientWidth || 1000;
    const height = map.clientHeight || 520;
    const fit = map.classList.contains("screen-tdt-map")
      ? Math.max(width / 1000, height / 520)
      : Math.min(1, width / 1000);
    map.style.setProperty("--tdt-scale", String(fit));
  });
}

function orderStopPoints(stops) {
  return (stops || []).filter((stop) => stop.lng && stop.lat).map((stop) => ({
    lng: stop.lng,
    lat: stop.lat,
    label: stop.name || stop.stop_type,
    name: stop.name || stop.stop_type,
  }));
}

function buildMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, title, verificationCenter = null) {
  const points = [...routeLinePoints, ...returnLinePoints, ...routeStopPoints, ...livePoints];
  if (!points.length) {
    return `<div class="map-empty">暂无可预览的位置或路线</div>`;
  }
  if (isTiandituEnabled()) return buildTiandituMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, title, verificationCenter);
  return buildFallbackMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, title);
}

function buildFallbackMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, title) {
  const points = [...routeLinePoints, ...returnLinePoints, ...routeStopPoints, ...livePoints];
  const bounds = calcBounds(points);
  const project = (point) => projectPoint(point, bounds);
  const lineProjected = routeLinePoints.map(project);
  const returnProjected = returnLinePoints.map(project);
  const stopProjected = routeStopPoints.map(project);
  const liveProjected = livePoints.map(project);
  const routeLine = lineProjected.length > 1 ? `<polyline class="route-line" points="${lineProjected.map((p) => `${p.x},${p.y}`).join(" ")}"></polyline>` : "";
  const returnLine = returnProjected.length > 1 ? `<polyline class="return-line" points="${returnProjected.map((p) => `${p.x},${p.y}`).join(" ")}"></polyline>` : "";
  const routeNodes = stopProjected.map((point, index) => `
    <g class="route-node">
      <circle cx="${point.x}" cy="${point.y}" r="${index === 0 || index === stopProjected.length - 1 ? 8 : 5}"></circle>
      <text x="${point.x + 10}" y="${point.y - 10}">${escapeHtml(routeStopPoints[index].label)}</text>
    </g>
  `).join("");
  const liveNodes = liveProjected.map((point, index) => `
    <g class="vehicle-node">
      <rect x="${point.x - 28}" y="${point.y - 15}" width="56" height="30" rx="15"></rect>
      <text x="${point.x}" y="${point.y + 4}" text-anchor="middle">${escapeHtml(livePoints[index].label)}</text>
    </g>
  `).join("");
  return `
    <div class="map-caption">${escapeHtml(title || "地图预览")}</div>
    <div class="map-controls">
      <button type="button" data-map-zoom="1">+</button>
      <button type="button" data-map-zoom="-1">-</button>
    </div>
    <svg class="map-svg" viewBox="0 0 1000 520" role="img" aria-label="地图路线预览">
      <defs>
        <pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse">
          <path d="M 42 0 L 0 0 0 42" fill="none" stroke="rgba(15,118,110,.12)" stroke-width="1"></path>
        </pattern>
      </defs>
      <rect width="1000" height="520" fill="url(#grid)"></rect>
      ${returnLine}
      ${routeLine}
      ${routeNodes}
      ${liveNodes}
    </svg>
  `;
}

function buildTiandituMapPreview(routeLinePoints, returnLinePoints, routeStopPoints, livePoints, title, verificationCenter) {
  const width = 1000;
  const height = 520;
  const points = [...routeLinePoints, ...returnLinePoints, ...routeStopPoints, ...livePoints];
  if (verificationCenter?.lng && verificationCenter?.lat) points.push({ lng: Number(verificationCenter.lng), lat: Number(verificationCenter.lat) });
  const zoom = Math.max(4, Math.min(16, chooseTileZoom(points, width, height) + state.mapZoomAdjust));
  const projected = points.map((point) => lonLatToWorld(point.lng, point.lat, zoom));
  const minX = Math.min(...projected.map((point) => point.x));
  const maxX = Math.max(...projected.map((point) => point.x));
  const minY = Math.min(...projected.map((point) => point.y));
  const maxY = Math.max(...projected.map((point) => point.y));
  const center = { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
  const topLeft = { x: center.x - width / 2, y: center.y - height / 2 };
  const project = (point) => {
    const world = lonLatToWorld(point.lng, point.lat, zoom);
    return { x: Math.round(world.x - topLeft.x), y: Math.round(world.y - topLeft.y) };
  };
  const tiles = buildTiandituTiles(topLeft, width, height, zoom);
  const lineProjected = routeLinePoints.map(project);
  const returnProjected = returnLinePoints.map(project);
  const stopProjected = routeStopPoints.map(project);
  const liveProjected = livePoints.map(project);
  const routeLine = lineProjected.length > 1 ? `<polyline class="route-line" points="${lineProjected.map((p) => `${p.x},${p.y}`).join(" ")}"></polyline>` : "";
  const returnLine = returnProjected.length > 1 ? `<polyline class="return-line" points="${returnProjected.map((p) => `${p.x},${p.y}`).join(" ")}"></polyline>` : "";
  const routeNodes = stopProjected.map((point, index) => `
    <g class="route-node">
      <circle cx="${point.x}" cy="${point.y}" r="${index === 0 || index === stopProjected.length - 1 ? 8 : 5}"></circle>
      <text x="${point.x + 10}" y="${point.y - 10}">${escapeHtml(routeStopPoints[index].label)}</text>
    </g>
  `).join("");
  const liveNodes = liveProjected.map((point, index) => `
    <g class="vehicle-node">
      <rect x="${point.x - 28}" y="${point.y - 15}" width="56" height="30" rx="15"></rect>
      <text x="${point.x}" y="${point.y + 4}" text-anchor="middle">${escapeHtml(livePoints[index].label)}</text>
    </g>
  `).join("");
  let verification = "";
  if (verificationCenter?.lng && verificationCenter?.lat) {
    const centerPoint = project({ lng: Number(verificationCenter.lng), lat: Number(verificationCenter.lat) });
    const metersPerPixel = 156543.03392 * Math.cos(Number(verificationCenter.lat) * Math.PI / 180) / (2 ** zoom);
    const radius = Math.max(8, Math.round(10000 / metersPerPixel));
    verification = `
      <circle class="verify-radius" cx="${centerPoint.x}" cy="${centerPoint.y}" r="${radius}"></circle>
      <text class="verify-label" x="${centerPoint.x + radius + 8}" y="${centerPoint.y}">10公里核实范围</text>
    `;
  }
  return `
    <div class="map-caption">${escapeHtml(title || "天地图路线预览")}</div>
    <div class="map-controls">
      <button type="button" data-map-zoom="1">+</button>
      <button type="button" data-map-zoom="-1">-</button>
    </div>
    <div class="tdt-map" role="img" aria-label="天地图带地名路线预览">
      <div class="tdt-canvas">
        ${tiles}
        <svg class="map-overlay" viewBox="0 0 ${width} ${height}">
          ${verification}
          ${returnLine}
          ${routeLine}
          ${routeNodes}
          ${liveNodes}
        </svg>
      </div>
    </div>
  `;
}

function buildTiandituTiles(topLeft, width, height, zoom) {
  const tileSize = 256;
  const minTileX = Math.floor(topLeft.x / tileSize) - 1;
  const minTileY = Math.floor(topLeft.y / tileSize) - 1;
  const maxTileX = Math.ceil((topLeft.x + width) / tileSize) + 1;
  const maxTileY = Math.ceil((topLeft.y + height) / tileSize) + 1;
  const maxIndex = 2 ** zoom;
  const tiles = [];
  for (let x = minTileX; x <= maxTileX; x += 1) {
    for (let y = minTileY; y <= maxTileY; y += 1) {
      if (y < 0 || y >= maxIndex) continue;
      const wrappedX = ((x % maxIndex) + maxIndex) % maxIndex;
      const left = Math.round(x * tileSize - topLeft.x);
      const top = Math.round(y * tileSize - topLeft.y);
      const params = `x=${wrappedX}&y=${y}&l=${zoom}`;
      tiles.push(`<img class="tdt-tile" alt="" src="/tiles/tianditu?T=vec_w&${params}" style="left:${left}px;top:${top}px">`);
      tiles.push(`<img class="tdt-tile tdt-label" alt="" src="/tiles/tianditu?T=cva_w&${params}" style="left:${left}px;top:${top}px">`);
    }
  }
  return tiles.join("");
}

function chooseTileZoom(points, width, height) {
  if (points.length < 2) return 13;
  for (let zoom = 15; zoom >= 4; zoom -= 1) {
    const projected = points.map((point) => lonLatToWorld(point.lng, point.lat, zoom));
    const spanX = Math.max(...projected.map((point) => point.x)) - Math.min(...projected.map((point) => point.x));
    const spanY = Math.max(...projected.map((point) => point.y)) - Math.min(...projected.map((point) => point.y));
    if (spanX <= width - 160 && spanY <= height - 140) return zoom;
  }
  return 4;
}

function lonLatToWorld(lng, lat, zoom) {
  const sinLat = Math.sin(Math.max(Math.min(Number(lat), 85.05112878), -85.05112878) * Math.PI / 180);
  const scale = 256 * (2 ** zoom);
  return {
    x: (Number(lng) + 180) / 360 * scale,
    y: (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale,
  };
}

function isTiandituEnabled() {
  const config = state.mapConfigs.find((item) => item.provider === "tianditu" && item.enabled);
  return Boolean(config);
}

function calcBounds(points) {
  const lngs = points.map((point) => point.lng);
  const lats = points.map((point) => point.lat);
  let minLng = Math.min(...lngs);
  let maxLng = Math.max(...lngs);
  let minLat = Math.min(...lats);
  let maxLat = Math.max(...lats);
  if (minLng === maxLng) {
    minLng -= 0.01;
    maxLng += 0.01;
  }
  if (minLat === maxLat) {
    minLat -= 0.01;
    maxLat += 0.01;
  }
  return { minLng, maxLng, minLat, maxLat };
}

function projectPoint(point, bounds) {
  const padding = 64;
  const width = 1000 - padding * 2;
  const height = 520 - padding * 2;
  const x = padding + ((point.lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * width;
  const y = padding + ((bounds.maxLat - point.lat) / (bounds.maxLat - bounds.minLat)) * height;
  return { x: Math.round(x), y: Math.round(y) };
}

function parsePolyline(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  try {
    return JSON.parse(value);
  } catch {
    return [];
  }
}

async function previewVehicleHistory() {
  if (!state.selectedVehicleId) throw new Error("请先选择车辆");
  const rows = await api(`/api/tracking/vehicles/${state.selectedVehicleId}/history`);
  state.selectedRoute = rows.map((row) => ({ lng: row.lng, lat: row.lat, name: row.device_time || row.received_at }));
  state.selectedReturnRoute = [];
  state.selectedRouteStops = [];
  const vehicle = state.vehicles.find((item) => item.id === state.selectedVehicleId);
  state.selectedRouteLabel = `${vehicle?.plate_no || "车辆"} · 历史轨迹`;
  renderMap(state.live);
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

function exportRows(name, rows) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((row) => headers.map((key) => csvCell(row[key])).join(",")),
  ].join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${name}-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function vehicleExportRows(rows) {
  return rows.map((row) => ({
    车牌号: row.plate_no,
    车辆类型: row.vehicle_type,
    品牌型号: row.brand_model,
    核定载重吨: row.load_capacity,
    货箱容积: row.box_volume,
    货箱类型: row.box_type,
    默认司机: row.default_driver_name || findVehicleDriver(row.driver_id)?.name || "",
    状态: statusText[row.status] || row.status,
    所属组织: row.organization || "",
  }));
}

function orderExportRows(rows) {
  const vehicleName = new Map(state.vehicles.map((item) => [item.id, item.plate_no]));
  return rows.map((row) => ({
    发货单号: row.order_no,
    货物: row.cargo_name,
    类型: displayValue("cargo", row.cargo_type),
    重量吨: row.cargo_weight,
    体积: row.cargo_volume,
    车牌: vehicleName.get(row.vehicle_id) || "",
    单程公里: row.planned_distance || 0,
    返程公里: row.return_distance || 0,
    计费公里: row.billable_distance || 0,
    运费: row.estimated_fee || row.actual_fee || 0,
    状态: statusText[row.status] || row.status,
    下单时间: row.created_at || "",
    异常: row.ticket_exception || "",
  }));
}

function ticketExportRows(rows) {
  return rows.map((row) => ({
    订单号: row.order_no || "",
    车牌: row.plate_no || "",
    司机: row.driver_name || "",
    类型: displayValue("ticket", row.ticket_type),
    金额: row.amount || 0,
    票据号: row.ticket_no || "",
    日期: row.issued_at || "",
    状态: statusText[row.status] || row.status,
    驳回原因: row.rejection_reason || "",
  }));
}

function renderDevices(rows) {
  document.getElementById("device-table").innerHTML = rows.map((row) => `
    <tr><td>${row.device_no}</td><td>${displayValue("device", row.device_type)}</td><td>${row.protocol}</td><td>${row.plate_no || row.vehicle_id || "-"}</td>
    <td><span class="badge">${statusText[row.status] || row.status}</span></td><td>${row.battery ?? "-"}</td><td>${row.last_seen_at || "-"}</td></tr>
  `).join("");
}

function renderTickets(rows) {
  document.getElementById("ticket-table").innerHTML = rows.map((row) => `
    <tr><td>${row.order_no || row.order_id || "-"}</td><td>${row.plate_no || row.vehicle_id || "-"}</td><td>${row.driver_name || "-"}</td>
    <td>${displayValue("ticket", row.ticket_type)}</td><td>${row.amount || 0}</td><td>${row.billable_distance || 0}</td><td>${row.ticket_no || "-"}</td>
    <td>${row.issued_at || "-"}</td><td><span class="badge">${statusText[row.status] || row.status}</span></td><td>${row.rejection_reason || "-"}</td>
    <td>${ticketActions(row)}</td></tr>
  `).join("");
  document.querySelectorAll("[data-create-ticket]").forEach((button) => {
    button.addEventListener("click", () => {
      const row = state.tickets.find((item) => String(item.order_id) === String(button.dataset.createTicket));
      try {
        createTicketForOrder(row);
      } catch (error) {
        window.alert(error.message || "生成票据失败");
      }
    });
  });
  document.querySelectorAll("[data-ticket]").forEach((button) => {
    button.addEventListener("click", async () => {
      const reason = button.dataset.status === "rejected" ? "票据审核驳回，异常请核实" : "";
      await api(`/api/tickets/${button.dataset.ticket}/review`, { method: "POST", body: JSON.stringify({ status: button.dataset.status, reason }) });
      await loadAll();
    });
  });
  document.querySelectorAll("[data-print-ticket]").forEach((button) => {
    button.addEventListener("click", () => {
      const row = state.tickets.find((item) => String(item.id) === String(button.dataset.printTicket));
      printTicketVoucher(row);
    });
  });
}

function ticketActions(row) {
  if (!row.id) return `<button data-create-ticket="${row.order_id}">生成票据</button>`;
  if (row.status === "pending") return `<button data-ticket="${row.id}" data-status="approved">通过</button><button data-ticket="${row.id}" data-status="rejected">驳回</button>`;
  if (row.status === "approved") return `<button data-print-ticket="${row.id}">打印凭证</button>`;
  if (row.status === "rejected") return `<span class="badge warning">已退回订单核实</span>`;
  return "";
}

function createTicketForOrder(row) {
  if (!row) throw new Error("未找到对应的已完成运输订单");
  if (!["admin", "finance"].includes(state.user?.role)) throw new Error("只有财务人员或管理员可以生成票据");
  state.pendingTicketOrder = row;
  openForm("ticket-generate", {
    ticket_type: "invoice",
    amount: row.amount || row.estimated_fee || 0,
    ticket_no: `PJ${Date.now()}`,
    issued_at: new Date().toISOString().slice(0, 10),
  });
}

function printTicketVoucher(row) {
  if (!row) {
    window.alert("未找到可打印的票据凭证");
    return;
  }
  const seal = state.settings.seal_image ? `<img src="${state.settings.seal_image}" style="position:absolute;right:80px;bottom:70px;width:150px;opacity:.78">` : "";
  const html = `
    <!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>票据凭证 ${escapeHtml(row.order_no)}</title><style>
      body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;padding:40px;color:#1d2935}
      .voucher{position:relative;border:1px solid #111;padding:28px;min-height:420px}
      h1{text-align:center;font-size:24px;margin:0 0 28px}
      table{width:100%;border-collapse:collapse}td{border:1px solid #999;padding:10px}
      .actions{margin-top:20px;text-align:center}.actions button{padding:8px 18px}
    </style></head><body><div class="voucher">
      <h1>兴芮物流票据费用凭证</h1>
      <table>
        <tr><td>发货单号</td><td>${escapeHtml(row.order_no)}</td><td>车牌</td><td>${escapeHtml(row.plate_no)}</td></tr>
        <tr><td>司机</td><td>${escapeHtml(row.driver_name)}</td><td>票据类型</td><td>${escapeHtml(displayValue("ticket", row.ticket_type))}</td></tr>
        <tr><td>金额</td><td>${row.amount || 0}</td><td>票据号</td><td>${escapeHtml(row.ticket_no)}</td></tr>
        <tr><td>日期</td><td>${escapeHtml(row.issued_at)}</td><td>状态</td><td>已审核</td></tr>
      </table>${seal}</div><div class="actions"><button onclick="window.print()">打印</button></div></body></html>
  `;
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const opened = window.open(url, "_blank");
  if (!opened) {
    window.alert("浏览器拦截了打印页面，请允许弹出窗口后重试");
    URL.revokeObjectURL(url);
    return;
  }
  window.setTimeout(() => URL.revokeObjectURL(url), 60000);
}

function renderWorkflow(definitions, tasks, instances) {
  document.getElementById("workflow-graph").innerHTML = definitions.map((row) => `
    <div class="item">
      <strong>${row.name}</strong>
      <span>${row.steps.map((step) => `${step.name}(${step.role || "未设角色"}${step.user_id ? `#${step.user_id}` : ""})`).join(" -> ")}</span>
    </div>
  `).join("");
  document.getElementById("workflow-definitions").innerHTML = definitions.map((row) => `
    <div class="item">
      <strong>${row.name} · ${row.code}</strong>
      <span>${row.biz_type} · ${row.steps.map((step) => `${step.name}/${step.role}`).join(" -> ")}</span>
    </div>
  `).join("");
  document.getElementById("workflow-instances").innerHTML = instances.slice(0, 20).map((row) => `
    <div class="item">
      <strong>${row.title}</strong>
      <span>${row.definition_code} · ${row.biz_type}#${row.biz_id} · ${row.status} · 当前步骤 ${row.current_step || "-"}</span>
    </div>
  `).join("");
}

function renderUsers(rows) {
  const systemUsers = rows.filter((row) => row.role !== "driver");
  document.getElementById("user-table").innerHTML = systemUsers.map((row) => `<tr><td>${row.username}</td><td>${row.real_name}</td><td>${row.phone || "-"}</td><td>${displayValue("role", row.role)}</td><td>${statusText[row.status] || row.status}</td></tr>`).join("");
}

function renderConfigs(mapConfigs, adapters, settings = {}) {
  document.getElementById("config-list").innerHTML = [
    `<div class="item"><strong>默认起点 ${settings.default_origin?.name || "-"}</strong><span>${settings.default_origin?.province || ""}${settings.default_origin?.city || ""}${settings.default_origin?.address || ""} · ${settings.route_highway_priority ? "默认高速优先" : "默认非高速优先"}</span></div>`,
    `<div class="item"><strong>签章 ${settings.seal_name || "-"}</strong><span>${settings.seal_image ? "已配置红章图片" : "未配置红章图片"}</span></div>`,
    ...mapConfigs.map((row) => `<div class="item"><strong>地图 ${row.provider}</strong><span>${row.enabled ? "启用" : "停用"} · ${row.base_url || "-"} · 配额 ${row.quota_limit || 0}</span></div>`),
    ...adapters.map((row) => `<div class="item"><strong>设备厂商 ${row.vendor_name}</strong><span>${row.protocol} · ${row.endpoint || "-"} · ${row.enabled ? "启用" : "停用"}</span></div>`),
  ].join("");
  document.getElementById("seal-preview").innerHTML = settings.seal_image
    ? `<strong>当前签章预览</strong><span>${settings.seal_name || "兴芮物流"}</span><img alt="签章预览" src="${settings.seal_image}" style="max-width:180px;max-height:120px;object-fit:contain">`
    : `<strong>当前签章预览</strong><span>未上传</span>`;
}

function handleSealUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (file.type !== "image/png") {
    window.alert("签章图片只支持 PNG 格式");
    event.target.value = "";
    return;
  }
  const reader = new FileReader();
  reader.onload = async () => {
    await api("/api/system-settings", {
      method: "POST",
      body: JSON.stringify({
        default_origin_name: state.settings.default_origin?.name || "",
        default_origin_province: state.settings.default_origin?.province || "",
        default_origin_city: state.settings.default_origin?.city || "",
        default_origin_address: state.settings.default_origin?.address || "",
        route_highway_priority: state.settings.route_highway_priority,
        seal_name: state.settings.seal_name || "兴芮物流",
        seal_image: reader.result,
      }),
    });
    await loadAll();
  };
  reader.readAsDataURL(file);
}

function renderDispatchMatches(rows) {
  document.getElementById("dispatch-results").innerHTML = rows.map((row) => `
    <div class="card"><strong>${row.plate_no} · ${row.score} 分</strong><span>${row.vehicle_type} · ${row.match_reasons.join(" · ")}</span></div>
  `).join("");
}

function vehicleOptions() {
  return [["", "请选择车牌"], ...state.vehicles.map((vehicle) => [
    vehicle.id,
    `${vehicle.plate_no} · ${vehicle.vehicle_type} · ${statusText[vehicle.status] || vehicle.status}`,
  ])];
}

function availableVehicles() {
  return state.vehicles.filter((vehicle) => ["idle", "available"].includes(vehicle.status));
}

function availableVehicleOptions() {
  return [["", "请选择空闲车牌"], ...availableVehicles().map((vehicle) => [
    vehicle.id,
    `${vehicle.plate_no} · ${vehicle.vehicle_type} · ${statusText[vehicle.status] || vehicle.status}`,
  ])];
}

function driverOptions(vehicleId = null) {
  const drivers = vehicleId
    ? (state.vehicles.find((vehicle) => String(vehicle.id) === String(vehicleId))?.drivers || [])
    : allVehicleDrivers();
  return [["", "请选择司机"], ...drivers.map((driver) => [
    driver.id,
    `${driver.name} · ${driver.phone || "未填手机号"}`,
  ])];
}

function allVehicleDrivers() {
  return state.vehicles.flatMap((vehicle) => (vehicle.drivers || []).map((driver) => ({
    ...driver,
    plate_no: vehicle.plate_no,
  }))).filter((driver) => driver.status !== "disabled");
}

function findVehicleDriver(driverId) {
  if (!driverId) return null;
  return allVehicleDrivers().find((driver) => String(driver.id) === String(driverId)) || null;
}

function addPlannerStation() {
  const type = document.getElementById("planner-stop-type").value;
  const province = document.getElementById("planner-province").value;
  const city = document.getElementById("planner-city").value.trim();
  const address = document.getElementById("planner-address").value.trim();
  const name = document.getElementById("planner-name").value.trim() || address;
  const error = document.getElementById("planner-error");
  error.textContent = "";
  if (!province || !city || !address) {
    error.textContent = "请完整选择省份、填写城市和地名";
    return;
  }
  const station = { type, province, city, address, name };
  if (type === "destination") {
    state.routePlanner.stations = state.routePlanner.stations.filter((item) => item.type !== "destination");
    state.routePlanner.stations.push(station);
  } else {
    const index = Number(document.getElementById("planner-insert-index").value || state.routePlanner.stations.length);
    const destinationIndex = state.routePlanner.stations.findIndex((item) => item.type === "destination");
    const safeIndex = destinationIndex >= 0 ? Math.min(index, destinationIndex) : index;
    state.routePlanner.stations.splice(safeIndex, 0, station);
  }
  document.getElementById("planner-address").value = "";
  document.getElementById("planner-name").value = "";
  hidePlannerAddressSuggestions();
  renderPlanner();
}

async function calculatePlannerRoute() {
  const error = document.getElementById("planner-error");
  error.textContent = "";
  const destination = state.routePlanner.stations.find((item) => item.type === "destination");
  if (!destination) {
    error.textContent = "请先添加终点";
    return;
  }
  const cargoName = document.getElementById("planner-cargo-name").value.trim();
  const vehicleId = document.getElementById("planner-vehicle-id").value;
  const driverId = document.getElementById("planner-driver-id").value;
  if (!cargoName || !vehicleId || !driverId) {
    error.textContent = "请填写货物名称，并选择车牌号和司机";
    return;
  }
  const payload = {
    order_id: null,
    order_no: document.getElementById("planner-order-no").value.trim(),
    provider: document.getElementById("planner-provider").value,
    preference: document.getElementById("planner-preference").value,
    vehicle_id: vehicleId,
    driver_id: driverId,
    cargo_name: cargoName,
    cargo_type: document.getElementById("planner-cargo-type").value || "鸡苗",
    cargo_weight: document.getElementById("planner-cargo-weight").value,
    cargo_volume: document.getElementById("planner-cargo-volume").value,
    order_description: document.getElementById("planner-order-description").value.trim(),
    optimize_waypoints: true,
    waypoints: state.routePlanner.stations.filter((item) => item.type === "waypoint"),
    destination,
  };
  try {
    const result = await api("/api/routes/address-plan", { method: "POST", body: JSON.stringify(payload) });
    state.selectedOrderId = result.order.id;
    resetPlannerOrderFields();
    setOrderView("detail");
    await loadAll();
  } catch (caught) {
    error.textContent = caught.message;
  }
}

function resetPlannerOrderFields() {
  document.getElementById("planner-order-no").value = "";
  document.getElementById("planner-cargo-name").value = "鸡苗";
  document.getElementById("planner-cargo-weight").value = "";
  document.getElementById("planner-cargo-volume").value = "";
  document.getElementById("planner-order-description").value = "";
  state.routePlanner.stations = [];
  renderPlanner();
}

function renderPlanner() {
  const insert = document.getElementById("planner-insert-index");
  if (insert) {
    const stations = state.routePlanner.stations;
    insert.innerHTML = [
      `<option value="${stations.length}">末尾</option>`,
      ...stations.map((station, index) => `<option value="${index}">${index + 1} 号站点前</option>`),
    ].join("");
  }
  const list = document.getElementById("planner-stations");
  if (!list) return;
  if (!state.routePlanner.stations.length) {
    list.innerHTML = `<div class="planner-empty">从系统默认起点出发，请添加沿途点和终点</div>`;
    return;
  }
  list.innerHTML = state.routePlanner.stations.map((station, index) => `
    <div class="planner-station">
      <span class="badge">${station.type === "destination" ? "终点" : "沿途点"}</span>
      <strong>${index + 1}. ${escapeHtml(station.name)}</strong>
      <span>${escapeHtml(station.province)}${escapeHtml(station.city)}${escapeHtml(station.address)}</span>
      <button type="button" data-remove-station="${index}">删除</button>
    </div>
  `).join("");
  document.querySelectorAll("[data-remove-station]").forEach((button) => {
    button.addEventListener("click", () => {
      state.routePlanner.stations.splice(Number(button.dataset.removeStation), 1);
      renderPlanner();
    });
  });
}

function openForm(type, defaults = {}) {
  const schema = formSchemas[type];
  if (type === "system-settings") defaults = state.settings;
  document.getElementById("dialog-title").textContent = schema.title;
  document.getElementById("form-error").textContent = "";
  document.getElementById("dynamic-form").dataset.type = type;
  document.getElementById("form-fields").innerHTML = schema.fields.map((field) => renderField(field, defaults)).join("");
  document.getElementById("form-dialog").showModal();
}

function parseWaypointLines(value) {
  return value.split(/\n+/).map((line) => line.trim()).filter(Boolean).map((line) => {
    const parts = line.split(/[,，\s]+/).filter(Boolean);
    if (parts.length < 3) throw new Error("沿途点格式应为：省,市,地名");
    const [province, city, ...addressParts] = parts;
    const address = addressParts.join("");
    return { province, city, address, name: address };
  });
}

function renderField(field, defaults = {}) {
  const [name, label, type, required, optionsOrDefault] = field;
  const requiredText = required ? "required" : "";
  const wide = type === "textarea" ? "wide" : "";
  const defaultValue = defaults[name] ?? "";
  if (type === "select") {
    const options = typeof optionsOrDefault === "function" ? optionsOrDefault() : optionsOrDefault;
    return `<label class="${wide}">${label}<select name="${name}" ${requiredText}>${options.map((option) => renderOption(option, defaultValue)).join("")}</select></label>`;
  }
  if (type === "textarea") {
    return `<label class="wide">${label}<textarea name="${name}" ${requiredText}>${escapeHtml(defaultValue)}</textarea></label>`;
  }
  if (type === "file") {
    const fileOptions = typeof optionsOrDefault === "object" && !Array.isArray(optionsOrDefault) ? optionsOrDefault : {};
    const accept = fileOptions.accept || "image/png";
    const hint = defaultValue
      ? (fileOptions.currentHint || "已上传图片；不选择新文件则保留原图")
      : (fileOptions.hint || "请选择透明 PNG 图片");
    const preview = defaultValue ? `<img class="form-image-preview" src="${escapeHtml(defaultValue)}" alt="${escapeHtml(label)}预览">` : "";
    return `<label class="wide">${label}<input name="${name}" type="file" accept="${escapeHtml(accept)}" ${requiredText}>${preview}<span class="field-hint">${escapeHtml(hint)}</span></label>`;
  }
  const value = defaultValue || (Array.isArray(optionsOrDefault) ? "" : (optionsOrDefault || ""));
  return `<label class="${wide}">${label}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${requiredText} step="any"></label>`;
}

function renderOption(option, selectedValue = "") {
  const value = Array.isArray(option) ? option[0] : option;
  const label = Array.isArray(option) ? option[1] : option;
  const selected = String(value) === String(selectedValue) ? "selected" : "";
  return `<option value="${escapeHtml(value)}" ${selected}>${escapeHtml(label)}</option>`;
}

function displayValue(type, value) {
  return displayMaps[type]?.[value] || value || "-";
}

function closeDialog() {
  document.getElementById("form-dialog").close();
}

function normalizePayload(data) {
  const payload = {};
  for (const [key, value] of Object.entries(data)) {
    if (value === "") continue;
    if (value === "true") payload[key] = true;
    else if (value === "false") payload[key] = false;
    else payload[key] = value;
  }
  return payload;
}

function requireVehicle() {
  if (!state.selectedVehicleId) throw new Error("请先在车辆表中选择一辆车");
  return state.selectedVehicleId;
}

function requireOrder() {
  if (!state.selectedOrderId) throw new Error("请先在订单表中选择一个订单");
  return state.selectedOrderId;
}

setupPlannerControls();
boot();
