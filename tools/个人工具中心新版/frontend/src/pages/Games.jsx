import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  Gamepad2,
  Grid3X3,
  List,
  Plus,
  RefreshCw,
  Search,
  Star,
  X,
} from 'lucide-react';
import { filterGames } from '../lib/search.js';
import { useToast } from '../components/Toasts.jsx';
import {
  Badge,
  Button,
  EmptyState,
  IconButton,
  InlineAlert,
  PageHeader,
  Spinner,
} from '../components/ui.jsx';
import { GameAvatar } from '../components/ToolIcon.jsx';
import { AddGameDialog } from '../components/AddGameDialog.jsx';
import { GameDetailDialog } from '../components/GameDetailDialog.jsx';

function toolCount(game) {
  if (Number.isFinite(Number(game.tool_count))) return Number(game.tool_count);
  return Array.isArray(game.tools) ? game.tools.length : 0;
}

function AliasChips({ aliases }) {
  if (!Array.isArray(aliases) || aliases.length === 0) return null;
  const visible = aliases.slice(0, 3);
  return (
    <div className="alias-chips alias-chips--small" aria-label="游戏别名">
      {visible.map((alias) => (
        <span className="alias-chip" key={alias}>
          {alias}
        </span>
      ))}
      {aliases.length > visible.length ? (
        <span className="alias-chip alias-chip--more">+{aliases.length - visible.length}</span>
      ) : null}
    </div>
  );
}

export function GamesPage({
  data,
  call,
  updateGames,
  focusGameId,
  onFocusConsumed,
  onAfterLaunch,
}) {
  const toast = useToast();
  const [query, setQuery] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [view, setView] = useState('grid');
  const [selectedId, setSelectedId] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pageError, setPageError] = useState(null);
  const [favoritePending, setFavoritePending] = useState(null);

  const games = data.games || [];
  const filtered = useMemo(
    () => filterGames(games, query, { favoritesOnly }),
    [games, query, favoritesOnly]
  );
  const favoritesCount = games.filter((game) => game.favorite).length;
  const selectedGame = games.find((game) => String(game.id) === String(selectedId)) || null;

  useEffect(() => {
    if (!focusGameId) return;
    const exists = games.some((game) => String(game.id) === String(focusGameId));
    if (exists) setSelectedId(focusGameId);
    if (onFocusConsumed) onFocusConsumed();
    // 只在外部深链变化时处理。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusGameId]);

  async function handleRefreshGames() {
    setRefreshing(true);
    setPageError(null);
    const result = await call('game_list', {});
    setRefreshing(false);
    if (!result.ok) {
      setPageError(result.error);
      return;
    }
    if (result.data && Array.isArray(result.data.games)) updateGames(result.data.games);
    toast({ tone: 'success', title: '游戏列表已刷新', message: '显示本地游戏库中的最新资料。' });
  }

  async function handleToggleFavorite(game) {
    const pendingKey = String(game.id);
    setFavoritePending(pendingKey);
    setPageError(null);
    const result = await call('game_favorite', {
      id: game.id,
      favorite: !game.favorite,
    });
    setFavoritePending(null);
    if (!result.ok) {
      setPageError(result.error);
      toast({ tone: 'error', title: '无法更新收藏', message: result.error });
      return;
    }
    if (result.data && Array.isArray(result.data.games)) updateGames(result.data.games);
  }

  function clearFilters() {
    setQuery('');
    setFavoritesOnly(false);
  }

  const hasFilters = Boolean(query.trim()) || favoritesOnly;

  return (
    <div className="page games-page">
      <PageHeader
        eyebrow="游戏管家"
        title="游戏与修改器"
        description="按中文名、英文名或别名查找本地游戏；收藏、备注与修改器都保存在本机。启动按钮只在点击时生效。"
        actions={
          <>
            <Button variant="secondary" icon={RefreshCw} loading={refreshing} onClick={handleRefreshGames}>
              刷新列表
            </Button>
            <Button variant="primary" icon={Plus} onClick={() => setAddOpen(true)}>
              添加游戏
            </Button>
          </>
        }
      />

      {pageError ? (
        <InlineAlert tone="error" title="游戏数据暂时不可用" onDismiss={() => setPageError(null)}>
          {pageError}
        </InlineAlert>
      ) : null}

      <div className="games-toolbar">
        <div className="filter-search">
          <Search size={17} aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索中文名、英文名或别名…"
            aria-label="搜索游戏"
            autoComplete="off"
            spellCheck={false}
          />
          {query ? (
            <button type="button" className="filter-search__clear" onClick={() => setQuery('')} aria-label="清空游戏搜索">
              <X size={15} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        <div className="games-toolbar__controls">
          <button
            type="button"
            className={`filter-chip ${favoritesOnly ? 'is-active' : ''}`.trim()}
            aria-pressed={favoritesOnly}
            onClick={() => setFavoritesOnly((value) => !value)}
          >
            <Star size={15} aria-hidden="true" /> 只看收藏
            <span>{favoritesCount}</span>
          </button>
          <div className="view-toggle" role="group" aria-label="切换显示方式">
            <IconButton
              label="卡片视图"
              icon={Grid3X3}
              size={17}
              variant={view === 'grid' ? 'soft' : 'ghost'}
              aria-pressed={view === 'grid'}
              onClick={() => setView('grid')}
            />
            <IconButton
              label="列表视图"
              icon={List}
              size={17}
              variant={view === 'list' ? 'soft' : 'ghost'}
              aria-pressed={view === 'list'}
              onClick={() => setView('list')}
            />
          </div>
        </div>
      </div>

      <div className="results-summary">
        <span>
          显示 <strong>{filtered.length}</strong> / {games.length} 款游戏
        </span>
        {hasFilters ? (
          <button type="button" className="link-button" onClick={clearFilters}>
            清除筛选
          </button>
        ) : null}
      </div>

      {filtered.length === 0 ? (
        games.length === 0 ? (
          <EmptyState
            icon={Gamepad2}
            title="游戏库还是空的"
            description="先添加一款游戏，填写中文名后即可在本地维护英文名、别名、备注与修改器。"
            action={
              <Button variant="primary" icon={Plus} onClick={() => setAddOpen(true)}>
                添加第一款游戏
              </Button>
            }
          />
        ) : (
          <EmptyState
            icon={Search}
            title={favoritesOnly && !query.trim() ? '还没有收藏游戏' : `没有匹配“${query.trim()}”的游戏`}
            description={
              favoritesOnly && !query.trim()
                ? '在游戏卡片或详情中点击星标即可收藏。'
                : '试试中文名、英文名或别名的一部分，或清除筛选查看全部。'
            }
            action={
              <Button variant="secondary" onClick={clearFilters}>
                清除筛选
              </Button>
            }
          />
        )
      ) : view === 'grid' ? (
        <div className="game-grid">
          {filtered.map((game) => (
            <article className="game-card" key={game.id}>
              <div className="game-card__top">
                <GameAvatar game={game} />
                <button
                  type="button"
                  className={`favorite-button ${game.favorite ? 'is-active' : ''}`.trim()}
                  onClick={() => handleToggleFavorite(game)}
                  aria-pressed={Boolean(game.favorite)}
                  aria-label={game.favorite ? `取消收藏 ${game.name || ''}` : `收藏 ${game.name || ''}`}
                  title={game.favorite ? '取消收藏' : '收藏'}
                  disabled={favoritePending === String(game.id)}
                >
                  {favoritePending === String(game.id) ? (
                    <Spinner size={15} />
                  ) : (
                    <Star size={17} fill={game.favorite ? 'currentColor' : 'none'} aria-hidden="true" />
                  )}
                </button>
              </div>
              <div className="game-card__body">
                <h3>{game.name || game.english_name || '未命名游戏'}</h3>
                <p className="game-card__english">{game.english_name || '未填写英文名'}</p>
                <AliasChips aliases={game.aliases} />
                <div className="game-card__meta">
                  <Badge tone={toolCount(game) > 0 ? 'success' : 'neutral'}>
                    {toolCount(game)} 个修改器
                  </Badge>
                  <Badge tone={game.steam_appid ? 'info' : 'neutral'}>
                    {game.steam_appid ? `Steam ${game.steam_appid}` : '未关联 Steam'}
                  </Badge>
                </div>
              </div>
              <div className="game-card__footer">
                <Button variant="secondary" size="sm" icon={ArrowRight} onClick={() => setSelectedId(game.id)}>
                  查看与启动
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="game-list">
          {filtered.map((game) => (
            <article className="game-list-row" key={game.id}>
              <GameAvatar game={game} />
              <div className="game-list-row__identity">
                <div className="game-list-row__name">
                  <h3>{game.name || game.english_name || '未命名游戏'}</h3>
                  {game.favorite ? (
                    <Star size={14} className="text-warning" fill="currentColor" aria-label="已收藏" />
                  ) : null}
                </div>
                <p>{game.english_name || '未填写英文名'}</p>
                <AliasChips aliases={game.aliases} />
              </div>
              <div className="game-list-row__meta">
                <Badge tone={toolCount(game) > 0 ? 'success' : 'neutral'}>
                  {toolCount(game)} 个修改器
                </Badge>
                <span className="muted small">{game.steam_appid ? `Steam ${game.steam_appid}` : '未关联 Steam'}</span>
              </div>
              <div className="game-list-row__actions">
                <button
                  type="button"
                  className={`favorite-button favorite-button--small ${game.favorite ? 'is-active' : ''}`.trim()}
                  onClick={() => handleToggleFavorite(game)}
                  aria-pressed={Boolean(game.favorite)}
                  aria-label={game.favorite ? `取消收藏 ${game.name || ''}` : `收藏 ${game.name || ''}`}
                  disabled={favoritePending === String(game.id)}
                >
                  {favoritePending === String(game.id) ? (
                    <Spinner size={14} />
                  ) : (
                    <Star size={16} fill={game.favorite ? 'currentColor' : 'none'} aria-hidden="true" />
                  )}
                </button>
                <Button size="sm" variant="secondary" icon={ArrowRight} onClick={() => setSelectedId(game.id)}>
                  详情
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}

      <AddGameDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        call={call}
        onGames={updateGames}
      />
      <GameDetailDialog
        open={Boolean(selectedGame)}
        game={selectedGame}
        call={call}
        onClose={() => setSelectedId(null)}
        onGames={updateGames}
        onAfterLaunch={onAfterLaunch}
      />
    </div>
  );
}
