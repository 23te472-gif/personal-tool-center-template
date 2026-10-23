import { useEffect, useMemo, useState } from 'react';
import {
  Clock3,
  Coffee,
  Leaf,
  Pause,
  Play,
  RotateCcw,
  Sparkles,
  Square,
  Sun,
  Wind,
} from 'lucide-react';
import {
  displayReward,
  formatClock,
  partnerName,
  todayStats,
  weekTotals,
  weeklySeries,
} from '../lib/town.js';
import { FocusRoom } from './FocusRoom.jsx';
import { PartnerAvatar } from './PartnerAvatar.jsx';

export function FocusView({ snapshot, busy, motion, hidden, onAction }) {
  const focus = snapshot.focus;
  const town = snapshot.town;
  const catalog = snapshot.catalog;
  const partner =
    catalog.partners.find((candidate) => candidate.id === town.partner) || catalog.partners[0];
  const [task, setTask] = useState(focus.task || '');
  const [minutes, setMinutes] = useState(focus.duration || 25);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const today = todayStats(town, snapshot.today);
  const week = weekTotals(town.stats, snapshot.today);
  const series = useMemo(() => weeklySeries(town.stats, snapshot.today), [town.stats, snapshot.today]);
  const maxMinutes = Math.max(1, ...series.map((day) => day.minutes));
  const reward = displayReward(focus.active ? focus.duration : minutes);

  useEffect(() => {
    if (focus.active) return;
    setTask(focus.task || '');
    setMinutes(focus.duration || 25);
    setConfirmEnd(false);
  }, [focus.active, focus.task, focus.duration]);

  function start() {
    if (busy || focus.active) return;
    onAction('focus_start', { task: task.trim(), minutes: Number(minutes) });
  }

  function endNow() {
    if (busy) return;
    onAction('focus_end', {});
    setConfirmEnd(false);
  }

  return (
    <div className="focus-layout">
      <section className="focus-stage" aria-labelledby="focus-heading">
        <div className="focus-stage__head">
          <div>
            <span className="eyebrow">
              <Sun size={14} aria-hidden="true" /> 安静小屋
            </span>
            <h1 id="focus-heading">
              {focus.active ? (focus.running ? '正在专注' : '先歇一小会儿') : '把心放在一件事上'}
            </h1>
          </div>
          <span className={`focus-state ${focus.active ? 'is-live' : ''}`.trim()}>
            <span aria-hidden="true" />
            {focus.active ? (focus.running ? '计时中' : '已暂停') : '准备开始'}
          </span>
        </div>
        <FocusRoom
          partner={partner}
          inventory={town.inventory}
          motion={motion}
          hidden={hidden}
        />
      </section>

      <section className="focus-console" aria-label="专注控制台">
        <div className="focus-console__card">
          <div className="focus-console__top">
            <span className="eyebrow">
              <Clock3 size={14} aria-hidden="true" /> 专注计时
            </span>
            <span className="reward-chip">
              <Leaf size={14} aria-hidden="true" /> 完成 +{reward}
            </span>
          </div>

          <div
            className={`timer ${focus.active ? 'is-active' : ''} ${focus.running ? 'is-running' : ''}`.trim()}
            aria-label={`剩余时间 ${formatClock(focus.active ? focus.remaining : minutes * 60)}`}
          >
            {formatClock(focus.active ? focus.remaining : minutes * 60)}
          </div>

          {focus.active ? (
            <>
              <div className="focus-task-display">
                <span>正在做</span>
                <strong>{focus.task || '一段安静的专注'}</strong>
                <small>{focus.duration} 分钟 · 完成后由小镇发放 {displayReward(focus.duration)} 枚树果</small>
              </div>
              <div className="focus-controls">
                {focus.running ? (
                  <button
                    type="button"
                    className="button button--soft button--large"
                    disabled={Boolean(busy)}
                    onClick={() => onAction('focus_pause', {})}
                  >
                    <Pause size={18} aria-hidden="true" /> 暂停
                  </button>
                ) : (
                  <button
                    type="button"
                    className="button button--primary button--large"
                    disabled={Boolean(busy)}
                    onClick={() => onAction('focus_resume', {})}
                  >
                    <Play size={18} aria-hidden="true" /> 继续专注
                  </button>
                )}
                {!confirmEnd ? (
                  <button
                    type="button"
                    className="button button--ghost button--large"
                    disabled={Boolean(busy)}
                    onClick={() => setConfirmEnd(true)}
                  >
                    <Square size={16} aria-hidden="true" /> 提前结束
                  </button>
                ) : (
                  <div className="end-confirm" role="group" aria-label="确认提前结束">
                    <span>提前结束不会获得树果</span>
                    <button type="button" className="text-button" onClick={() => setConfirmEnd(false)}>
                      继续专注
                    </button>
                    <button
                      type="button"
                      className="button button--danger button--small"
                      disabled={Boolean(busy)}
                      onClick={endNow}
                    >
                      确定结束
                    </button>
                  </div>
                )}
              </div>
              <p className="focus-note">
                <Wind size={14} aria-hidden="true" />
                切到小镇不会重启计时；关闭窗口由本地服务暂停并保存。
              </p>
            </>
          ) : (
            <>
              <label className="field">
                <span>今天想专注做什么？</span>
                <input
                  type="text"
                  value={task}
                  maxLength={500}
                  placeholder="写下一件小事，比如：读十页书"
                  onChange={(event) => setTask(event.target.value)}
                  disabled={Boolean(busy)}
                />
              </label>
              <div className="duration-group" role="group" aria-label="专注时长">
                {catalog.durations.map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={`duration-pill ${Number(minutes) === value ? 'is-selected' : ''}`.trim()}
                    disabled={Boolean(busy)}
                    onClick={() => setMinutes(value)}
                    aria-pressed={Number(minutes) === value}
                  >
                    {value}
                    <small>分钟</small>
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="button button--primary button--large button--wide"
                disabled={Boolean(busy) || !task.trim()}
                onClick={start}
              >
                <Play size={18} aria-hidden="true" /> 开始这一段
              </button>
              <p className="focus-note">
                <Sparkles size={14} aria-hidden="true" />
                每 5 分钟收获 1 枚树果，完成时由小镇统一结算。
              </p>
            </>
          )}
        </div>

        <div className="focus-side-grid">
          <div className="focus-mini-card">
            <div className="focus-mini-card__head">
              <span>今天的节奏</span>
              <Coffee size={16} aria-hidden="true" />
            </div>
            <strong>
              {today.minutes}
              <small>分钟</small>
            </strong>
            <p>{today.sessions} 次专注 · 近七天 {week.minutes} 分钟</p>
            <div className="mini-bars" aria-hidden="true">
              {series.map((day) => (
                <span key={day.day} className="mini-bars__col">
                  <span
                    className={`mini-bars__bar ${day.minutes ? 'has-value' : ''}`.trim()}
                    style={{ height: `${Math.max(day.minutes ? 12 : 3, (day.minutes / maxMinutes) * 100)}%` }}
                  />
                </span>
              ))}
            </div>
          </div>
          <div className="focus-mini-card focus-partner-card">
            <div className="focus-mini-card__head">
              <span>陪你的人</span>
              <Leaf size={16} aria-hidden="true" />
            </div>
            <div className="focus-partner">
              <PartnerAvatar partner={partner} size={58} />
              <div>
                <strong>{partnerName(catalog, town.partner)}</strong>
                <p>亲密度 {town.affinity[town.partner] || 0} / 100</p>
              </div>
            </div>
            <p className="focus-partner__line">它就坐在小屋窗边，不催你，也不离开。</p>
          </div>
        </div>

        <button
          type="button"
          className="focus-reset"
          disabled={Boolean(busy) || focus.active}
          onClick={() => {
            setTask('');
            setMinutes(25);
          }}
        >
          <RotateCcw size={14} aria-hidden="true" /> 重新写一段
        </button>
      </section>
    </div>
  );
}
