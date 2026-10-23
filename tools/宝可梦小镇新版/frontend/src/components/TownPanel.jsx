import { useEffect, useMemo, useState } from 'react';
import {
  Check,
  Gift,
  Heart,
  Home,
  Leaf,
  ShoppingBasket,
  Sparkles,
  Sprout,
  Star,
  Trophy,
  Undo2,
} from 'lucide-react';
import {
  areaName,
  inventoryEntries,
  placedLocation,
  shopEntry,
  taskRows,
  todayDaily,
  todayStats,
  weekTotals,
  weeklySeries,
} from '../lib/town.js';
import { FurnitureIcon } from './Furniture.jsx';
import { PartnerAvatar } from './PartnerAvatar.jsx';

const TABS = [
  { id: 'partner', label: '伙伴', icon: Heart },
  { id: 'furniture', label: '家具', icon: Home },
  { id: 'shop', label: '商店', icon: ShoppingBasket },
  { id: 'tasks', label: '任务', icon: Gift },
  { id: 'stats', label: '统计', icon: Trophy },
];

const ACHIEVEMENTS = {
  place: { label: '安家啦', icon: Home },
  friend: { label: '新朋友', icon: Heart },
  focus: { label: '专注萌芽', icon: Sprout },
};

function EmptyNote({ children }) {
  return <p className="panel-empty">{children}</p>;
}

export function TownPanel({
  snapshot,
  area,
  panel,
  onPanelChange,
  selectedItem,
  onSelectItem,
  onAction,
  onStartPlace,
  onStartMove,
  onCancelEdit,
  edit,
  busy,
}) {
  const town = snapshot.town;
  const catalog = snapshot.catalog;
  const today = snapshot.today;
  const [partnerChoice, setPartnerChoice] = useState(town.partner);
  const entries = useMemo(() => inventoryEntries(town), [town]);
  const daily = todayDaily(town, today);
  const tasks = taskRows(town, today);
  const currentPartner =
    catalog.partners.find((partner) => partner.id === town.partner) || catalog.partners[0];
  const stats = todayStats(town, today);
  const week = weekTotals(town.stats, today);
  const series = weeklySeries(town.stats, today);
  const selected = entries.find((entry) => entry.id === selectedItem) || null;
  const selectedLocation = selected ? placedLocation(town, selected.id) : null;
  const selectedShop = selected ? shopEntry(catalog, selected.kind) : null;
  const orchard = catalog.areas.find((candidate) => candidate.id === 'orchard');
  const orchardUnlocked = town.areas.includes('orchard');
  const maxMinutes = Math.max(1, ...series.map((day) => day.minutes));

  useEffect(() => {
    setPartnerChoice(town.partner);
  }, [town.partner]);

  function selectPartner(id) {
    setPartnerChoice(id);
  }

  return (
    <aside className="town-panel" aria-label="小镇面板">
      <div className="town-panel__tabs" role="tablist" aria-label="小镇功能">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const active = panel === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              className={`town-tab ${active ? 'is-active' : ''}`.trim()}
              onClick={() => onPanelChange(tab.id)}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="town-panel__body">
        {panel === 'partner' && (
          <section className="panel-section" aria-labelledby="town-partner-heading">
            <div className="partner-feature">
              <PartnerAvatar partner={currentPartner} size={74} />
              <div className="partner-feature__text">
                <span className="eyebrow">今日伙伴</span>
                <h2 id="town-partner-heading">{currentPartner?.name || '伙伴'}</h2>
                <div className="affinity-line">
                  <span>亲密度</span>
                  <strong>{town.affinity[town.partner] || 0}/100</strong>
                </div>
                <div className="affinity-track" aria-hidden="true">
                  <span style={{ width: `${Math.min(100, town.affinity[town.partner] || 0)}%` }} />
                </div>
              </div>
            </div>
            <div className="action-row">
              <button
                type="button"
                className="button button--primary"
                disabled={Boolean(busy) || daily.greeted.includes(town.partner)}
                onClick={() => onAction('town_action', { action: 'greet', args: { partner: town.partner } })}
              >
                <Heart size={16} aria-hidden="true" />
                {daily.greeted.includes(town.partner) ? '今天问候过啦' : '问候伙伴'}
              </button>
              <button
                type="button"
                className="button button--soft"
                disabled={Boolean(busy) || daily.watered}
                onClick={() => onAction('town_action', { action: 'water', args: {} })}
              >
                <Leaf size={16} aria-hidden="true" />
                {daily.watered ? '树已喝饱水' : '照顾庭院树'}
              </button>
            </div>
            <div className="section-heading">
              <div>
                <span className="eyebrow">选择伙伴</span>
                <h3>谁陪你逛逛？</h3>
              </div>
              <span className="muted">{catalog.partners.length} 位伙伴</span>
            </div>
            <div className="partner-grid" role="list">
              {catalog.partners.map((partner) => (
                <button
                  key={partner.id}
                  type="button"
                  role="listitem"
                  className={`partner-card ${partnerChoice === partner.id ? 'is-chosen' : ''} ${town.partner === partner.id ? 'is-current' : ''}`.trim()}
                  onClick={() => selectPartner(partner.id)}
                  aria-pressed={partnerChoice === partner.id}
                >
                  <PartnerAvatar partner={partner} size={52} />
                  <span>{partner.name}</span>
                  {town.partner === partner.id && <small>正在陪伴</small>}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="button button--ink button--wide"
              disabled={
                Boolean(busy) ||
                partnerChoice === town.partner ||
                !catalog.partners.some((partner) => partner.id === partnerChoice)
              }
              onClick={() =>
                onAction('town_action', {
                  action: 'set_partner',
                  args: { partner: partnerChoice },
                })
              }
            >
              <Sparkles size={16} aria-hidden="true" />
              邀请到小镇
            </button>
          </section>
        )}

        {panel === 'furniture' && (
          <section className="panel-section" aria-labelledby="furniture-heading">
            <div className="section-heading">
              <div>
                <span className="eyebrow">我的收藏</span>
                <h2 id="furniture-heading">家具与布置</h2>
              </div>
              <span className="muted">{entries.length} 件</span>
            </div>
            {entries.length ? (
              <div className="inventory-list">
                {entries.map((entry) => {
                  const shop = shopEntry(catalog, entry.kind);
                  const isChosen = selectedItem === entry.id;
                  return (
                    <button
                      type="button"
                      key={entry.id}
                      className={`inventory-row ${isChosen ? 'is-selected' : ''}`.trim()}
                      onClick={() => onSelectItem(entry.id)}
                    >
                      <span className="inventory-row__art">
                        <FurnitureIcon kind={entry.kind} size={36} />
                      </span>
                      <span className="inventory-row__text">
                        <strong>{shop?.name || entry.kind}</strong>
                        <small>{entry.area ? `摆在${areaName(catalog, entry.area)}` : '在库存里'}</small>
                      </span>
                      {isChosen && <Check size={16} className="inventory-row__check" aria-label="已选中" />}
                    </button>
                  );
                })}
              </div>
            ) : (
              <EmptyNote>还没有家具。去商店挑一件喜欢的吧。</EmptyNote>
            )}

            {selected && (
              <div className="selection-card">
                <div className="selection-card__top">
                  <span className="selection-card__art">
                    <FurnitureIcon kind={selected.kind} size={42} />
                  </span>
                  <div>
                    <strong>{selectedShop?.name || selected.kind}</strong>
                    <p>{selectedShop?.description || '给小镇添一点生活气。'}</p>
                  </div>
                </div>
                {selectedLocation && (
                  <p className="selection-card__where">
                    <Home size={14} aria-hidden="true" />
                    正在{areaName(catalog, selectedLocation.area)}摆放
                  </p>
                )}
                <div className="action-row">
                  {!selectedLocation ? (
                    <button
                      type="button"
                      className="button button--primary"
                      disabled={Boolean(busy)}
                      onClick={() => onStartPlace(selected.id)}
                    >
                      摆放这件
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="button button--primary"
                      disabled={Boolean(busy)}
                      onClick={() => onStartMove(selected.id)}
                    >
                      移动
                    </button>
                  )}
                  <button
                    type="button"
                    className="button button--soft"
                    disabled={Boolean(busy) || !selectedLocation}
                    onClick={() =>
                      onAction('town_action', { action: 'recall', args: { item_id: selected.id } })
                    }
                  >
                    <Undo2 size={16} aria-hidden="true" />
                    收回
                  </button>
                </div>
                {edit && (
                  <button type="button" className="text-button" onClick={onCancelEdit}>
                    取消本次布置
                  </button>
                )}
              </div>
            )}
            <p className="panel-hint">
              选中家具后，在{areaName(catalog, area)}地图上点一个格子。绿色可以摆，红色会碰撞。
            </p>
          </section>
        )}

        {panel === 'shop' && (
          <section className="panel-section" aria-labelledby="shop-heading">
            <div className="section-heading">
              <div>
                <span className="eyebrow">小镇杂货铺</span>
                <h2 id="shop-heading">添置一点新意</h2>
              </div>
              <span className="berry-price">
                <Leaf size={14} aria-hidden="true" /> {town.berries}
              </span>
            </div>
            <div className="shop-list">
              {catalog.shop.map((item) => (
                <article className="shop-row" key={item.id}>
                  <span className="shop-row__art">
                    <FurnitureIcon kind={item.id} size={42} />
                  </span>
                  <div className="shop-row__text">
                    <strong>{item.name}</strong>
                    <p>{item.description}</p>
                  </div>
                  <button
                    type="button"
                    className="button button--small"
                    disabled={Boolean(busy) || town.berries < item.cost}
                    onClick={() =>
                      onAction('town_action', { action: 'buy', args: { kind: item.id } })
                    }
                  >
                    {item.cost} 树果
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        {panel === 'tasks' && (
          <section className="panel-section" aria-labelledby="tasks-heading">
            <div className="section-heading">
              <div>
                <span className="eyebrow">今天的小目标</span>
                <h2 id="tasks-heading">慢慢来，也有收获</h2>
              </div>
            </div>
            <div className="task-list">
              {tasks.map((task) => (
                <article className={`task-row ${task.claimed ? 'is-done' : ''}`.trim()} key={task.id}>
                  <span className={`task-check ${task.ready ? 'is-ready' : ''}`.trim()}>
                    {task.claimed ? <Check size={15} /> : task.ready ? <Star size={15} /> : null}
                  </span>
                  <div className="task-row__text">
                    <strong>{task.label}</strong>
                    <small>{task.claimed ? '奖励已领取' : task.hint}</small>
                  </div>
                  <button
                    type="button"
                    className="button button--small"
                    disabled={Boolean(busy) || !task.claimable}
                    onClick={() =>
                      onAction('town_action', { action: 'claim', args: { task: task.id } })
                    }
                  >
                    {task.claimed ? '已领取' : `+${task.reward}`}
                  </button>
                </article>
              ))}
            </div>
            <article className="garden-card">
              <div className="garden-card__icon">
                <Leaf size={22} aria-hidden="true" />
              </div>
              <div>
                <strong>{orchardUnlocked ? '果园的果子熟了' : '果园还在小路尽头'}</strong>
                <p>
                  {orchardUnlocked
                    ? daily.harvested
                      ? '今天已经采过，明天再来看看。'
                      : '每天可以采一次，收获 3 枚树果。'
                    : `用 ${orchard?.unlock_cost ?? 12} 枚树果打开果园，每天多一份收获。`}
                </p>
              </div>
              {orchardUnlocked ? (
                <button
                  type="button"
                  className="button button--small"
                  disabled={Boolean(busy) || daily.harvested}
                  onClick={() => onAction('town_action', { action: 'harvest', args: {} })}
                >
                  {daily.harvested ? '已采过' : '采果'}
                </button>
              ) : (
                <button
                  type="button"
                  className="button button--small"
                  disabled={Boolean(busy) || town.berries < (orchard?.unlock_cost ?? 12)}
                  onClick={() =>
                    onAction('town_action', { action: 'unlock', args: { area: 'orchard' } })
                  }
                >
                  解锁
                </button>
              )}
            </article>
            <p className="panel-hint">任务奖励每天每项一次。不要求连续签到，也不和专注奖励冲突。</p>
          </section>
        )}

        {panel === 'stats' && (
          <section className="panel-section" aria-labelledby="stats-heading">
            <div className="section-heading">
              <div>
                <span className="eyebrow">最近的脚印</span>
                <h2 id="stats-heading">专注与成长</h2>
              </div>
            </div>
            <div className="stat-summary">
              <div>
                <span>今天</span>
                <strong>{stats.minutes}<small>分钟</small></strong>
                <p>{stats.sessions} 次专注</p>
              </div>
              <div>
                <span>近七天</span>
                <strong>{week.minutes}<small>分钟</small></strong>
                <p>{week.sessions} 次专注</p>
              </div>
            </div>
            <div className="week-chart" aria-label="最近七天专注分钟">
              {series.map((day) => (
                <div className="week-chart__day" key={day.day}>
                  <span className="week-chart__bar-track">
                    <span
                      className={`week-chart__bar ${day.minutes ? 'has-value' : ''}`.trim()}
                      style={{ height: `${Math.max(day.minutes ? 10 : 2, (day.minutes / maxMinutes) * 100)}%` }}
                    />
                  </span>
                  <small>{day.label}</small>
                </div>
              ))}
            </div>
            <div className="achievement-list">
              {Object.entries(ACHIEVEMENTS).map(([id, achievement]) => {
                const Icon = achievement.icon;
                const unlocked = town.achievements.includes(id);
                return (
                  <div className={`achievement ${unlocked ? 'is-unlocked' : ''}`.trim()} key={id}>
                    <span className="achievement__icon">
                      <Icon size={18} aria-hidden="true" />
                    </span>
                    <span>
                      <strong>{achievement.label}</strong>
                      <small>{unlocked ? '已经点亮' : '继续生活就会遇见'}</small>
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="stats-footer">
              <Star size={15} aria-hidden="true" />
              树果 {town.berries} · {town.origin === 'new' ? '新的小镇故事' : '小镇故事'}
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}
