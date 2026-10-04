/**
 * 全局常量（前端单一来源）。
 *
 * 校园全景图静态页路径说明：
 * - 按钮固定指向 Django 静态目录下的全景页，与仓库 static/panorama/ 一一对应；
 * - 该目录已被 scripts/pack-release.sh 纳入 Release 打包清单（发布侧联动），
 *   改名 / 移动时必须同步修改 static/panorama/ 与 scripts/pack-release.sh；
 * - 全景页内资源（marzipano.js、pano_*.jpg）一律使用相对路径，勿改绝对路径。
 */
export const PANORAMA_PAGE_URL = "/static/panorama/index.html";
