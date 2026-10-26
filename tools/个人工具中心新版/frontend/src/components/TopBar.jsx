import { useEffect, useId, useMemo, useRef, useState } from 'react';
import {
  Dices,
  FileText,
  Gamepad2,
  Menu,
  Moon,
  RefreshCw,
  Search,
  Sun,
  Wrench,
  X,
} from 'lucide-react';
import { searchAll, SEARCH_TYPE_LABELS } from '../lib/search.js';
import { formatDateTime } from '../lib/format.js';
import { Kbd, Spinner } from './ui.jsx';
import { PetButton } from './PetButton.jsx';

const RESULT_ICONS = {
  tool: Wrench,
  game: Gamepad2,
  material: FileText,
  wheel: Dices,
};

export function GlobalSearch({ data, onSelect }) {
  const inputRef = useRef(null);
  const wrapRef = useRef(null);
  const listId = useId();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const results = useMemo(() => searchAll(query, data, 10), [query, data]);
  const trimmed = query.trim();

  useEffect(() => {
    const onKeyDown = (event) => {
      const key = String(event.key || '').toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === 'k') {
        if (document.querySelector('[role="dialog"][aria-modal="true"]')) return;
        event.preventDefault();
        const input = inputRef.current;
        if (!input) return;
        input.focus();
        input.select();
        setOpen(true);
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    const onPointerDown = (event) => {
      if (wrapRef.current && !wrapRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, []);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    if (activeIndex >= results.length) setActiveIndex(Math.max(0, results.length - 1));
  }, [results.length, activeIndex]);

  const choose = (result) => {
    if (!result) return;
    onSelect(result);
    setQuery('');
    setOpen(false);
    inputRef.current?.blur();
  };

  const onInputKeyDown = (event) => {
    if (event.key === 'Escape') {
      setOpen(false);
      inputRef.current?.blur();
      return;
    }
    if (!trimmed) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => (results.length ? (index + 1) % results.length : 0));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) =>
        results.length ? (index - 1 + results.length) % results.length : 0
      );
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (open && results[activeIndex]) choose(results[activeIndex]);
    }
  };

  const showPanel = open && (trimmed || document.activeElement === inputRef.current);

  return (
    <div
      className="global-search"
      ref={wrapRef}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
    >
      <div className={`global-search__box ${open ? 'is-focused' : ''}`.trim()}>
        <Search size={18} className="global-search__icon" aria-hidden="true" />
        <input
          ref={inputRef}
          type="search"
          value={query}
          placeholder="搜索工具、游戏、资料或候选…"
          aria-label="全局搜索"
          role="combobox"
          aria-expanded={showPanel}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={
            showPanel && results[activeIndex] ? `${listId}-option-${activeIndex}` : undefined
          }
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onInputKeyDown}
        />
        {query ? (
          <button
            type="button"
            className="global-search__clear"
            onClick={() => {
              setQuery('');
              setActiveIndex(0);
              inputRef.current?.focus();
            }}
            aria-label="清空搜索"
          >
            <X size={15} aria-hidden="true" />
          </button>
        ) : (
          <span className="global-search__hint" aria-hidden="true">
            <Kbd>Ctrl</Kbd>
            <Kbd>K</Kbd>
          </span>
        )}
      </div>

      {showPanel ? (
        <div className="search-panel" role="presentation">
          {!trimmed ? (
            <div className="search-panel__empty">
              <p className="search-panel__title">全站搜索</p>
              <p>支持工具名称、游戏中文名 / 英文名 / 别名、论文与 PPT 资料、转盘候选。</p>
              <p className="search-panel__tip">
                <Kbd>↑</Kbd>
                <Kbd>↓</Kbd> 选择，<Kbd>Enter</Kbd> 跳转，<Kbd>Esc</Kbd> 关闭
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="search-panel__empty" role="status">
              <p className="search-panel__title">没有匹配“{trimmed}”的结果</p>
              <p>试试更短的关键词，或到对应页面查看全部内容。</p>
            </div>
          ) : (
            <>
              <div className="search-panel__meta">
                <span>找到 {results.length} 项</span>
                <span>搜索不会启动任何程序</span>
              </div>
              <div className="search-panel__list" role="listbox" id={listId} aria-label="搜索结果">
                {results.map((result, index) => {
                  const Icon = RESULT_ICONS[result.type] || Search;
                  return (
                    <div
                      key={`${result.type}-${result.id}-${index}`}
                      id={`${listId}-option-${index}`}
                      role="option"
                      aria-selected={index === activeIndex}
                      className={`search-result ${index === activeIndex ? 'is-active' : ''}`.trim()}
                      onMouseEnter={() => setActiveIndex(index)}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => choose(result)}
                    >
                      <span className={`search-result__icon search-result__icon--${result.type}`}>
                        <Icon size={17} aria-hidden="true" />
                      </span>
                      <span className="search-result__text">
                        <strong>{result.title}</strong>
                        <small>{result.subtitle}</small>
                      </span>
                      <span className="search-result__type">{SEARCH_TYPE_LABELS[result.type]}</span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}

export function TopBar({
  data,
  onSearchSelect,
  onOpenMenu,
  theme,
  onToggleTheme,
  themeBusy,
  onRefresh,
  refreshing,
  connection,
  lastUpdated,
  call,
}) {
  const connectionLabel =
    connection === 'ready' ? '已连接' : connection === 'error' ? '连接异常' : '连接中';

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button type="button" className="topbar__menu" onClick={onOpenMenu} aria-label="打开导航">
          <Menu size={20} aria-hidden="true" />
        </button>
      </div>

      <GlobalSearch data={data} onSelect={onSearchSelect} />
      <PetButton call={call}/>

      <div className="topbar__right">
        <span className={`connection-pill connection-pill--${connection}`} title="本地服务连接状态">
          <span className="connection-dot" aria-hidden="true" />
          {connectionLabel}
        </span>
        <button
          type="button"
          className="icon-btn icon-btn--ghost"
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="刷新数据"
          title={lastUpdated ? `刷新数据（上次 ${formatDateTime(lastUpdated)}）` : '刷新数据'}
        >
          {refreshing ? <Spinner size={17} /> : <RefreshCw size={17} aria-hidden="true" />}
        </button>
        <button
          type="button"
          className="icon-btn icon-btn--ghost"
          onClick={onToggleTheme}
          disabled={themeBusy}
          aria-label={theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
          title={theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
        >
          {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
        </button>
      </div>
    </header>
  );
}
