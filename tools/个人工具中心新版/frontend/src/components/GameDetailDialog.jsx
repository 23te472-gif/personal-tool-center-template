import { useEffect, useState } from 'react';
import {
  Check,
  FolderOpen,
  Pencil,
  Play,
  Plus,
  Star,
  TriangleAlert,
  Wrench,
} from 'lucide-react';
import { aliasesToText, isNumericAppId, parseAliases } from '../lib/format.js';
import { Button, Field, InlineAlert } from './ui.jsx';
import { Modal } from './Modal.jsx';
import { GameAvatar } from './ToolIcon.jsx';
import { useToast } from './Toasts.jsx';

export function GameDetailDialog({ open, game, call, onClose, onGames, onAfterLaunch }) {
  const toast = useToast();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: '', english_name: '', aliases: '', notes: '' });
  const [errors, setErrors] = useState({});
  const [selectedTool, setSelectedTool] = useState(0);
  const [pending, setPending] = useState(null);
  const [actionError, setActionError] = useState(null);

  const gameId = game && game.id;

  useEffect(() => {
    if (!open || !game) return;
    setEditing(false);
    setErrors({});
    setActionError(null);
    setPending(null);
    setForm({
      name: game.name || '',
      english_name: game.english_name || '',
      aliases: aliasesToText(game.aliases),
      notes: game.notes || '',
    });
    const tools = Array.isArray(game.tools) ? game.tools : [];
    const firstExisting = tools.findIndex((tool) => tool && tool.exists !== false);
    setSelectedTool(firstExisting >= 0 ? firstExisting : 0);
    // 只在打开或切换游戏时重置表单，避免父级刷新收藏等数据时打断编辑。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, gameId]);

  if (!game) {
    return null;
  }

  const tools = Array.isArray(game.tools) ? game.tools : [];
  const selected = tools[selectedTool] || null;
  const steamReady = isNumericAppId(game.steam_appid);
  const toolsReady = selected && selected.exists !== false;
  const modalBusy = pending === 'save' || pending === 'add-tool';

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined, form: undefined }));
  };

  async function runOpen(kind, extra = {}, pendingKey) {
    setPending(pendingKey);
    setActionError(null);
    const result = await call('game_open', { id: game.id, kind, ...extra });
    setPending(null);
    if (!result.ok) {
      setActionError(result.error);
      toast({ tone: 'error', title: '操作未完成', message: result.error });
      return;
    }
    toast({
      tone: 'success',
      title: kind === 'steam' ? '已请求启动 Steam 游戏' : kind === 'tool' ? '已请求启动修改器' : '已请求打开文件夹',
      message: (result.data && result.data.message) || '请求已交给本地服务。',
    });
    if (onAfterLaunch) onAfterLaunch();
  }

  async function handleToggleFavorite() {
    setPending('favorite');
    setActionError(null);
    const result = await call('game_favorite', {
      id: game.id,
      favorite: !game.favorite,
    });
    setPending(null);
    if (!result.ok) {
      setActionError(result.error);
      toast({ tone: 'error', title: '无法更新收藏', message: result.error });
      return;
    }
    if (result.data && Array.isArray(result.data.games)) onGames(result.data.games);
  }

  async function handleAddTool() {
    setPending('add-tool');
    setActionError(null);
    const result = await call('game_add_tool', { id: game.id });
    setPending(null);
    if (!result.ok) {
      setActionError(result.error);
      toast({ tone: 'error', title: '无法添加修改器', message: result.error });
      return;
    }
    if (result.data && result.data.cancelled) return;
    if (result.data && Array.isArray(result.data.games)) {
      onGames(result.data.games);
      const updated = result.data.games.find((item) => String(item.id) === String(game.id));
      const nextTools = updated && Array.isArray(updated.tools) ? updated.tools : [];
      if (nextTools.length) setSelectedTool(nextTools.length - 1);
    }
    toast({
      tone: 'success',
      title: '修改器已添加',
      message: '已保存到本地游戏库，不会自动启动。',
    });
  }

  async function handleSave() {
    const name = form.name.trim();
    if (!name) {
      setErrors({ name: '中文名不能为空。' });
      return;
    }
    const aliasList = parseAliases(form.aliases);
    setPending('save');
    setActionError(null);
    const result = await call('game_save', {
      id: game.id,
      name,
      english_name: form.english_name.trim(),
      aliases: aliasList,
      notes: form.notes,
    });
    setPending(null);
    if (!result.ok) {
      setErrors({ form: result.error });
      return;
    }
    if (result.data && Array.isArray(result.data.games)) onGames(result.data.games);
    setEditing(false);
    toast({
      tone: 'success',
      title: '游戏资料已保存',
      message: '中文名、英文名、别名与备注已写入本地游戏库。',
    });
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={game.name || game.english_name || '游戏详情'}
      description={game.english_name || '游戏资料、修改器与启动入口'}
      size="lg"
      busy={modalBusy}
    >
      <div className="game-detail">
        {actionError ? (
          <InlineAlert tone="error" title="操作未完成">
            {actionError}
          </InlineAlert>
        ) : null}

        <div className="game-detail__hero">
          <GameAvatar game={game} size="lg" />
          <div className="game-detail__identity">
            <div className="game-detail__name-row">
              <h3>{game.name || '未命名游戏'}</h3>
              <Button
                size="sm"
                variant={game.favorite ? 'soft' : 'ghost'}
                icon={Star}
                loading={pending === 'favorite'}
                onClick={handleToggleFavorite}
                aria-pressed={Boolean(game.favorite)}
                className={game.favorite ? 'is-favorite' : ''}
              >
                {game.favorite ? '已收藏' : '收藏'}
              </Button>
            </div>
            <p className="game-detail__english">{game.english_name || '未填写英文名'}</p>
            {Array.isArray(game.aliases) && game.aliases.length ? (
              <div className="alias-chips" aria-label="游戏别名">
                {game.aliases.map((alias) => (
                  <span key={alias} className="alias-chip">
                    {alias}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          {!editing ? (
            <Button size="sm" variant="secondary" icon={Pencil} onClick={() => setEditing(true)}>
              编辑资料
            </Button>
          ) : null}
        </div>

        <div className="game-detail__meta">
          <span className={`meta-pill ${steamReady ? '' : 'is-muted'}`.trim()}>
            {steamReady ? `Steam AppID ${game.steam_appid}` : '未关联 Steam AppID'}
          </span>
          <span className="meta-pill">{tools.length} 个修改器</span>
          {game.last_used ? <span className="meta-pill">最近使用 {game.last_used}</span> : null}
        </div>

        {editing ? (
          <form
            className="form-stack game-edit-form"
            onSubmit={(event) => {
              event.preventDefault();
              handleSave();
            }}
          >
            {errors.form ? (
              <div className="form-error" role="alert">
                {errors.form}
              </div>
            ) : null}
            <Field label="中文名" htmlFor="edit-game-name" required error={errors.name}>
              <input
                id="edit-game-name"
                data-autofocus
                value={form.name}
                onChange={(event) => updateField('name', event.target.value)}
                maxLength={120}
                autoComplete="off"
              />
            </Field>
            <Field label="英文名" htmlFor="edit-game-english" hint="用于英文搜索。">
              <input
                id="edit-game-english"
                value={form.english_name}
                onChange={(event) => updateField('english_name', event.target.value)}
                maxLength={160}
                autoComplete="off"
              />
            </Field>
            <Field
              label="别名"
              htmlFor="edit-game-aliases"
              hint="用逗号、中文逗号、分号或换行分隔，重复别名会自动合并。"
            >
              <input
                id="edit-game-aliases"
                value={form.aliases}
                onChange={(event) => updateField('aliases', event.target.value)}
                placeholder="例如：星露谷、SDV"
                autoComplete="off"
              />
            </Field>
            <Field label="备注" htmlFor="edit-game-notes">
              <textarea
                id="edit-game-notes"
                value={form.notes}
                onChange={(event) => updateField('notes', event.target.value)}
                rows={4}
                placeholder="记录启动方式、注意事项或修改器说明"
              />
            </Field>
            <div className="form-actions">
              <Button variant="ghost" onClick={() => setEditing(false)} disabled={pending === 'save'}>
                取消
              </Button>
              <Button
                type="submit"
                variant="primary"
                icon={Check}
                loading={pending === 'save'}
              >
                保存资料
              </Button>
            </div>
          </form>
        ) : (
          <>
            <div className="game-actions">
              <Button
                variant="primary"
                icon={Play}
                loading={pending === 'steam'}
                disabled={!steamReady}
                onClick={() => runOpen('steam', {}, 'steam')}
                title={steamReady ? '通过 Steam 启动已关联的游戏' : '此游戏未关联 Steam AppID'}
              >
                启动 Steam 游戏
              </Button>
              <Button
                variant="secondary"
                icon={FolderOpen}
                loading={pending === 'folder'}
                onClick={() => runOpen('folder', {}, 'folder')}
                title="打开已配置的 Steam 安装目录、修改器目录或存档目录"
              >
                打开文件夹
              </Button>
              <Button
                variant="secondary"
                icon={Plus}
                loading={pending === 'add-tool'}
                onClick={handleAddTool}
              >
                添加修改器
              </Button>
            </div>

            <section className="game-section" aria-labelledby="game-notes-title">
              <h4 id="game-notes-title">备注</h4>
              {game.notes ? (
                <p className="game-notes">{game.notes}</p>
              ) : (
                <p className="muted">暂无备注。点击“编辑资料”可补充。</p>
              )}
            </section>

            <section className="game-section" aria-labelledby="game-tools-title">
              <div className="game-section__head">
                <div>
                  <h4 id="game-tools-title">修改器</h4>
                  <p className="muted small">先勾选一个可用修改器，再点击下方启动按钮。</p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  icon={Plus}
                  loading={pending === 'add-tool'}
                  onClick={handleAddTool}
                >
                  添加
                </Button>
              </div>

              {tools.length ? (
                <div className="trainer-list" role="radiogroup" aria-label="选择修改器">
                  {tools.map((tool, index) => {
                    const missing = tool.exists === false;
                    return (
                      <label
                        key={`${tool.path || tool.name || 'tool'}-${index}`}
                        className={`trainer-row ${selectedTool === index ? 'is-selected' : ''} ${missing ? 'is-missing' : ''}`.trim()}
                      >
                        <input
                          type="radio"
                          name="trainer"
                          value={index}
                          checked={selectedTool === index}
                          disabled={missing}
                          onChange={() => setSelectedTool(index)}
                        />
                        <span className="trainer-row__icon" aria-hidden="true">
                          <Wrench size={17} />
                        </span>
                        <span className="trainer-row__body">
                          <strong>{tool.name || `修改器 ${index + 1}`}</strong>
                          <code title={tool.path || ''}>{tool.path || '路径未提供'}</code>
                        </span>
                        <span className={`badge badge--${missing ? 'danger' : 'success'}`}>
                          {missing ? '文件缺失' : '可用'}
                        </span>
                      </label>
                    );
                  })}
                </div>
              ) : (
                <div className="trainer-empty">
                  <TriangleAlert size={18} aria-hidden="true" />
                  <div>
                    <strong>尚未添加修改器</strong>
                    <p>使用原生 EXE 选择器添加后，可在这里手动启动。</p>
                  </div>
                  <Button size="sm" variant="secondary" icon={Plus} loading={pending === 'add-tool'} onClick={handleAddTool}>
                    选择 EXE
                  </Button>
                </div>
              )}

              <div className="trainer-launch">
                <Button
                  variant="soft"
                  icon={Play}
                  loading={pending === 'tool'}
                  disabled={!toolsReady}
                  onClick={() => runOpen('tool', { tool_index: selectedTool }, 'tool')}
                  title={toolsReady ? '启动当前选中的修改器' : '请选择一个可用修改器'}
                >
                  启动选定修改器
                </Button>
                {selected && selected.exists === false ? (
                  <span className="text-danger small">选中的修改器文件不存在。</span>
                ) : null}
              </div>
            </section>

            <p className="game-detail__privacy">
              启动操作只在点击按钮时发生；页面加载或输入搜索不会启动任何程序。
            </p>
          </>
        )}
      </div>
    </Modal>
  );
}
