import {
  Dices,
  Gamepad2,
  LayoutDashboard,
  Package,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react';
import { Brand } from './Brand.jsx';

export const NAV_ITEMS = [
  { id: 'overview', label: '概览', icon: LayoutDashboard },
  { id: 'games', label: '游戏管家', icon: Gamepad2 },
  { id: 'pack', label: '文件打包', icon: Package },
  { id: 'wheel', label: '游戏转盘', icon: Dices },
  { id: 'settings', label: '设置', icon: Settings },
];

export function Sidebar({
  page,
  onNavigate,
  mobileOpen,
  onClose,
  activeJobs = 0,
  connection = 'connecting',
  version,
}) {
  const statusText =
    connection === 'ready'
      ? '本地服务已连接'
      : connection === 'error'
        ? '本地服务连接异常'
        : '正在连接本地服务';

  return (
    <>
      {mobileOpen ? <div className="sidebar-scrim" onClick={onClose} aria-hidden="true" /> : null}
      <aside className={`sidebar ${mobileOpen ? 'is-open' : ''}`.trim()} aria-label="主导航">
        <div className="sidebar__top">
          <Brand />
          <button type="button" className="sidebar__close" onClick={onClose} aria-label="关闭导航">
            <X size={19} aria-hidden="true" />
          </button>
        </div>

        <nav className="sidebar__nav">
          <div className="sidebar__nav-label">工作台</div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = page === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${active ? 'is-active' : ''}`.trim()}
                onClick={() => onNavigate(item.id)}
                aria-current={active ? 'page' : undefined}
                title={item.label}
              >
                <span className="nav-item__icon" aria-hidden="true">
                  <Icon size={19} strokeWidth={active ? 2.15 : 1.9} />
                </span>
                <span className="nav-item__label">{item.label}</span>
                {item.id === 'pack' && activeJobs > 0 ? (
                  <span className="nav-item__count" aria-label={`${activeJobs} 个进行中的任务`}>
                    {activeJobs}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>

        <div className="sidebar__spacer" />

        <div className="sidebar__privacy">
          <ShieldCheck size={16} aria-hidden="true" />
          <span>本地运行，不上传文件</span>
        </div>

        <div className="sidebar__footer">
          <span className={`connection-dot connection-dot--${connection}`} aria-hidden="true" />
          <div className="sidebar__status">
            <span>{statusText}</span>
            {version ? <small>版本 {version}</small> : null}
          </div>
        </div>
      </aside>
    </>
  );
}
