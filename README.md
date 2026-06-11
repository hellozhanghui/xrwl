# 兴芮物流车辆管理系统 MVP

这是根据 `物流车辆管理系统架构.md` 落地的轻量化首版实现，使用 Python 标准库 HTTP 服务和 SQLite，便于在无依赖环境中直接启动。

## 启动

```bash
python3 backend/server.py
```

默认地址：

```text
http://127.0.0.1:8000
```

## 已实现

- 车辆档案、维护记录、证照到期提醒。
- 登录鉴权、用户角色、会话令牌。
- 订单创建、确认、派车、发车、完成。
- 地图适配层，第一版使用天地图做地图展示、地址搜索、驾车路线和公里数测算，系统自研多点排序、回程测算、订单公里统计和车型配货。
- GPS 和温湿度设备 HTTP 上报。
- 实时位置、历史轨迹、温湿度异常和超速告警。
- 车型配货推荐。
- 车辆利用率、订单里程、费用和告警报表。
- 静态管理页面。

## 目录

```text
backend/app/api            API 路由
backend/app/services       业务服务
backend/app/repositories   SQLite 仓储
backend/app/map_providers  地图适配层
backend/data               SQLite 数据库
frontend/src               静态管理页面
```

## 天地图配置

系统管理页面里打开“地图配置”，选择 `tianditu`，填写：

```text
provider: tianditu
base_url: https://api.tianditu.gov.cn
api_key: 天地图服务端 Key，也就是接口参数 tk
route_path: /drive
geocode_path: /geocoder
reverse_geocode_path: /geocoder
poi_path: /v2/search
static_map_path: /DataServer
enabled: true
```

当前默认已启用 `tianditu`，但未写入真实 Key。未配置 Key 或接口调用失败时，系统会记录地图 API 错误并自动使用 Mock 路线，避免订单流程中断。

第一版职责划分：

- 天地图：地图展示、地址搜索、驾车路线、单程公里数测算。
- 系统自研：多点排序、回程测算、订单公里数统计、车型配货。

也可以用接口配置：

```bash
curl -X POST http://127.0.0.1:8000/api/map-configs \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"provider":"tianditu","base_url":"https://api.tianditu.gov.cn","api_key":"<tk>","route_path":"/drive","enabled":true}'
```
