# PostgreSQL 与 Redis：生产数据库升级与多 worker 解禁

日期：2026-10-10

生产 v1 是 SQLite + `InMemoryChannelLayer` + 单 ASGI worker（[ADR-0015](0015-channels-without-redis.md)）。本次把生产数据面推到 **PostgreSQL**（与站点同机、只监听 `127.0.0.1`）与 **Redis**（缓存 + Channels 频道层），并据此把 ASGI worker 数改为环境变量 `GUNICORN_WORKERS`（默认仍 1）。**全部开关缺省中性**：不设 `DB_ENGINE` / `REDIS_URL` / `GUNICORN_WORKERS` 时行为与 v1 完全一致。

## 决策

1. **数据库可切 PostgreSQL**：`DB_ENGINE=postgresql` + `DB_*` 连接项启用（`.env.example` 已列全）；缺省仍 SQLite（本地开发、测试、裸机安装不变）。理由：SQLite 多写者受限、备份与恢复工具链单薄，规模上来后需要一次到位的关系库。
2. **Redis 双用途**：配置 `REDIS_URL` 后，Django 缓存（`RedisCache`）与 Channels 频道层（`channels_redis`，前缀 `club`）一并切换。频道层跨进程扇出是**多 worker 的前置条件**——这正是 ADR-0015 禁止 worker>1 的原因。
3. **worker 数走环境变量**：`start.sh` 读 `GUNICORN_WORKERS`（默认 1）。**未配 `REDIS_URL` 的部署不得 >1**；同机 SQLite 部署同样不建议 >1（多写者）。2 vCPU 机器建议 2–3（每个 worker 约 120MB 内存量级）。
4. **更新器 DB 快照支持双引擎**：apply 前的数据库快照与失败回滚按引擎分派——SQLite 走 `sqlite3.backup`（`db-<时间戳>.sqlite3`）；PostgreSQL 走 `pg_dump --clean --if-exists`（`db-<时间戳>.pg.sql`，恢复走 `psql -f`）。没有这一步，PG 部署下的自动更新一旦失败将无法恢复数据。
5. **参考部署基线**：PostgreSQL（PGDG 官方源）+ Redis（发行版源），均只监听 `127.0.0.1`；PG `shared_buffers=256MB`（2GB 内存机型）、Redis `maxmemory=128mb` + `allkeys-lru`（缓存可丢、频道消息为瞬态）。

## 被否的方案

- **继续 SQLite、只加 Redis**：worker 可加，但数据库短板仍在；数据面一次升级到位比两轮迁移省事。否。
- **只切缓存、不切频道层**：多 worker 下缓存一致了，但 WebSocket 扇出仍会跨进程丢消息。否。
- **PG 部署下让更新器跳过快照**：会静默失去「apply 失败自动恢复数据库」的能力。否。

## 兼容与迁移

- 缺省中性：不配新变量 = v1 行为；切换只动 `.env`，回滚 = 改回 `.env`。
- SQLite → PostgreSQL 迁移：维护窗口内 `dumpdata` / `loaddata`（或等价手段）+ 行数核对；SQLite 文件保留为兜底。
- 相关文档：[配置参考](../configuration.md)、[部署指南](../operations/deployment.md)。
