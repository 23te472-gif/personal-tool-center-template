import { useEffect, useRef, useState } from 'react';
import {
  CELL,
  canPlace,
  cellFromPoint,
  footprintFor,
  placementsFor,
  safePartnerImage,
} from '../lib/town.js';
import { FurnitureGlyph } from './Furniture.jsx';

function Tree({ x, y, fruit = false, scale = 1 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} className="scene-tree">
      <ellipse cx="0" cy="50" rx="34" ry="9" fill="#7f916f" opacity=".2" />
      <path d="M-3 46c3-15-2-27-6-35h12c-3 14 2 22 5 35Z" fill="#a77e59" />
      <circle cx="-17" cy="4" r="22" fill="#70916d" />
      <circle cx="16" cy="1" r="25" fill="#7fa079" />
      <circle cx="-1" cy="-17" r="23" fill="#88a97f" />
      <circle cx="-22" cy="-12" r="16" fill="#93b187" />
      <circle cx="15" cy="-18" r="15" fill="#9ab88b" />
      {fruit && (
        <>
          <circle cx="-15" cy="3" r="4" fill="#d98972" />
          <circle cx="17" cy="-8" r="4" fill="#e0a568" />
          <circle cx="3" cy="-25" r="3.6" fill="#d98972" />
        </>
      )}
    </g>
  );
}

function Flower({ x, y, color = '#dda6a2', scale = 1 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} aria-hidden="true">
      {[0, 72, 144, 216, 288].map((angle) => (
        <circle
          key={angle}
          cx={Math.cos((angle * Math.PI) / 180) * 4}
          cy={Math.sin((angle * Math.PI) / 180) * 4}
          r="3.2"
          fill={color}
        />
      ))}
      <circle r="2.2" fill="#f3dc93" />
    </g>
  );
}

function HomeScene() {
  return (
    <g>
      <path d="M0 330c115-20 212-8 330 8 120 16 206 6 310-10v72H0Z" fill="#d9e2c8" />
      <path d="M270 400c9-52 18-82 42-112h26c18 33 24 64 29 112Z" fill="#e4d4b3" />
      <path d="M286 400c5-42 10-72 22-99h8c10 29 14 58 16 99Z" fill="#eee0c4" />
      <g className="scene-cottage">
        <ellipse cx="175" cy="254" rx="112" ry="18" fill="#718368" opacity=".2" />
        <path d="M78 145L174 62l102 83v93H78Z" fill="#f2e4c6" stroke="#c8b190" strokeWidth="2" />
        <path d="M63 149L174 47l118 102-17 14-101-82-97 82Z" fill="#b97d69" stroke="#9f6757" strokeWidth="2" />
        <path d="M88 148l86-71 88 71Z" fill="#c88d77" />
        <path d="M146 95h59v105h-59Z" fill="#c99570" stroke="#a97554" strokeWidth="2" />
        <path d="M157 100h37v100h-37Z" fill="#8d735d" />
        <circle cx="187" cy="155" r="3" fill="#f3d28e" />
        <rect x="99" y="119" width="33" height="34" rx="3" fill="#fff2d3" stroke="#b59d7e" strokeWidth="2" />
        <path d="M115 119v34M99 136h33" stroke="#b59d7e" strokeWidth="1.5" />
        <rect x="217" y="119" width="33" height="34" rx="3" fill="#fff2d3" stroke="#b59d7e" strokeWidth="2" />
        <path d="M233 119v34M217 136h33" stroke="#b59d7e" strokeWidth="1.5" />
        <rect x="97" y="166" width="38" height="12" rx="4" fill="#b88d67" />
        <rect x="216" y="166" width="38" height="12" rx="4" fill="#b88d67" />
        <Flower x={106} y={164} color="#d9a1a0" scale={.65} />
        <Flower x={116} y={162} color="#e1c17e" scale={.55} />
        <Flower x={126} y={164} color="#c5a8c2" scale={.65} />
        <Flower x={225} y={164} color="#d9a1a0" scale={.65} />
        <Flower x={235} y={162} color="#e1c17e" scale={.55} />
        <Flower x={245} y={164} color="#c5a8c2" scale={.65} />
        <rect x="231" y="55" width="18" height="38" rx="3" fill="#a97c64" />
        <path d="M236 55v-13h8v13" fill="#d8c4a5" />
        <path d="M79 239h192" stroke="#a88866" strokeWidth="3" strokeLinecap="round" />
      </g>
      <Tree x={500} y={117} scale={1.15} />
      <Tree x={574} y={280} scale={.82} />
      <Tree x={52} y={303} scale={.72} />
      <Flower x={318} y={314} color="#d9a1a0" />
      <Flower x={338} y={330} color="#e5c77f" />
      <Flower x={354} y={304} color="#c9a9c1" />
      <Flower x={302} y={356} color="#e4b2a4" />
      <Flower x={388} y={350} color="#d7b982" />
      <Flower x={430} y={313} color="#c9a9c1" />
      <g opacity=".6" stroke="#b5c9a2" strokeWidth="2" strokeLinecap="round">
        <path d="M334 256l5-8m5 8-5-8" />
        <path d="M41 231l6-9m5 9-6-9" />
        <path d="M584 203l5-8m5 8-5-8" />
      </g>
    </g>
  );
}

function PlazaScene() {
  return (
    <g>
      <circle cx="320" cy="211" r="166" fill="#e3d7bd" opacity=".55" />
      <circle cx="320" cy="211" r="143" fill="none" stroke="#cfc0a1" strokeWidth="2" strokeDasharray="3 8" />
      <path d="M320 0v400M0 211h640" stroke="#ded1b7" strokeWidth="26" opacity=".55" />
      <g className="scene-fountain">
        <ellipse cx="320" cy="239" rx="97" ry="29" fill="#72908a" opacity=".25" />
        <ellipse cx="320" cy="226" rx="92" ry="39" fill="#b9cbc2" stroke="#94aaa0" strokeWidth="3" />
        <ellipse cx="320" cy="222" rx="76" ry="29" fill="#dce8df" stroke="#a8bcb1" strokeWidth="2" />
        <ellipse cx="320" cy="220" rx="63" ry="23" fill="#9ccbcb" />
        <ellipse cx="320" cy="215" rx="42" ry="15" fill="#d8f0e8" opacity=".72" />
        <path d="M313 203h14v-48h-14Z" fill="#aabbb1" />
        <ellipse cx="320" cy="153" rx="29" ry="10" fill="#c5d4ca" stroke="#91a89e" strokeWidth="2" />
        <ellipse cx="320" cy="148" rx="22" ry="7" fill="#b5d9d4" />
        <path d="M320 150c-14-7-28-1-38 8 14 4 29 1 38-8Zm0 0c14-7 28-1 38 8-14 4-29 1-38-8Z" fill="#bfe7dd" opacity=".85" />
        <path d="M320 146c-5-17-4-32 3-43 7 13 7 28-3 43Z" fill="#d3eee5" opacity=".8" />
      </g>
      <path d="M126 104c14-10 23-9 37 0M458 301c15-10 24-9 38 0" stroke="#b9c8a7" strokeWidth="3" strokeLinecap="round" opacity=".65" />
      <Tree x={83} y={102} scale={.8} />
      <Tree x={548} y={102} scale={.92} />
      <Tree x={535} y={326} scale={.7} />
      <g className="scene-bench">
        <path d="M73 268h62v9H73z" fill="#b88963" />
        <path d="M77 251h55v14H77z" fill="#cfa67d" stroke="#9d7755" />
        <path d="M83 257h42M83 262h42" stroke="#e7c39a" strokeWidth="1.5" />
        <path d="M84 277v13M124 277v13" stroke="#6b7e6f" strokeWidth="3" strokeLinecap="round" />
      </g>
      <Flower x={214} y={330} color="#dca1a0" />
      <Flower x={238} y={345} color="#e3c57c" />
      <Flower x={430} y={331} color="#c9a8c1" />
      <Flower x={456} y={348} color="#dca1a0" />
      <Flower x={185} y={141} color="#e3c57c" />
      <Flower x={460} y={143} color="#dca1a0" />
      <g fill="#b9cbaa" opacity=".8">
        <circle cx="183" cy="278" r="8" />
        <circle cx="199" cy="286" r="6" />
        <circle cx="449" cy="272" r="7" />
        <circle cx="465" cy="281" r="5.5" />
      </g>
    </g>
  );
}

function OrchardScene() {
  return (
    <g>
      <path d="M0 325c125-18 211 2 326 10 113 8 209-7 314-18v83H0Z" fill="#d8e2c6" />
      <path d="M0 190h640" stroke="#d8c7a5" strokeWidth="3" strokeDasharray="1 12" strokeLinecap="round" opacity=".6" />
      <Tree x={120} y={118} fruit scale={1.12} />
      <Tree x={320} y={119} fruit scale={1.2} />
      <Tree x={520} y={118} fruit scale={1.08} />
      <Tree x={92} y={310} fruit scale={.65} />
      <Tree x={548} y={310} fruit scale={.68} />
      <Flower x={191} y={162} color="#e4c479" />
      <Flower x={215} y={178} color="#dca1a0" />
      <Flower x={405} y={166} color="#c9a8c1" />
      <Flower x={429} y={181} color="#e4c479" />
      <Flower x={263} y={322} color="#dca1a0" />
      <Flower x={290} y={338} color="#e4c479" />
      <Flower x={353} y={327} color="#c9a8c1" />
      <path d="M43 224v96M597 224v96M43 257h554M43 299h554" stroke="#b99972" strokeWidth="4" strokeLinecap="round" opacity=".5" />
      <g opacity=".7" stroke="#b5c9a2" strokeWidth="2" strokeLinecap="round">
        <path d="M78 213l5-9m5 9-5-9" />
        <path d="M501 238l5-9m5 9-5-9" />
        <path d="M229 277l6-9m5 9-6-9" />
      </g>
    </g>
  );
}

function SceneBase({ area }) {
  return (
    <>
      <rect width="640" height="400" fill={area === 'plaza' ? '#dbcbb0' : '#dce7cc'} />
      <defs>
        <pattern id="grassDots" width="28" height="28" patternUnits="userSpaceOnUse">
          <circle cx="5" cy="7" r="1.1" fill="#afc49b" opacity=".55" />
          <circle cx="20" cy="21" r=".8" fill="#bfd0aa" opacity=".7" />
          <path d="M14 5l2-4m0 4-2-4" stroke="#b8caa1" strokeWidth="1" opacity=".55" />
        </pattern>
        <pattern id="stoneTiles" width="44" height="44" patternUnits="userSpaceOnUse">
          <path d="M0 22h44M22 0v44" stroke="#c9b99c" strokeWidth="1" opacity=".35" />
        </pattern>
        <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#63705e" floodOpacity=".14" />
        </filter>
      </defs>
      <rect width="640" height="400" fill={area === 'plaza' ? 'url(#stoneTiles)' : 'url(#grassDots)'} />
      {area === 'home' ? <HomeScene /> : area === 'plaza' ? <PlazaScene /> : <OrchardScene />}
    </>
  );
}

export function TownScene({
  snapshot,
  area,
  motion,
  hidden,
  edit,
  selectedItem,
  onCellClick,
  onSelectPlaced,
  onCancelEdit,
}) {
  const [hoverCell, setHoverCell] = useState(null);
  const [keyCell, setKeyCell] = useState({ x: 7, y: 6 });
  const [focused, setFocused] = useState(false);
  const lastCell = useRef('');
  const svgRef = useRef(null);
  const town = snapshot.town;
  const catalog = snapshot.catalog;
  const map = catalog.map || { width: 16, height: 10 };
  const partner =
    catalog.partners.find((candidate) => candidate.id === town.partner) ||
    catalog.partners[0] ||
    null;
  const image = safePartnerImage(partner);
  const positions = placementsFor(town, area);
  const previewCell = hoverCell || (focused && edit ? keyCell : null);
  const preview =
    edit && previewCell
      ? {
          cell: previewCell,
          ...canPlace({
            town,
            catalog,
            area,
            itemId: edit.itemId,
            x: previewCell.x,
            y: previewCell.y,
            ignoreItemId: edit.itemId,
          }),
        }
      : null;

  useEffect(() => {
    setHoverCell(null);
    setFocused(false);
    setKeyCell({ x: 7, y: 6 });
    lastCell.current = '';
  }, [area, edit && edit.itemId]);

  function updateHover(event) {
    if (!edit) return;
    const rect = svgRef.current && svgRef.current.getBoundingClientRect();
    const cell = cellFromPoint(event.clientX, event.clientY, rect, map);
    const key = cell ? `${cell.x},${cell.y}` : '';
    if (key !== lastCell.current) {
      lastCell.current = key;
      setHoverCell(cell);
    }
  }

  function activateCell(cell) {
    if (!edit || !cell) return;
    onCellClick(cell);
  }

  function handleKeyDown(event) {
    if (!edit) return;
    const key = event.key;
    if (key === 'Escape') {
      event.preventDefault();
      onCancelEdit();
      return;
    }
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      activateCell(keyCell);
      return;
    }
    const dx = key === 'ArrowRight' ? 1 : key === 'ArrowLeft' ? -1 : 0;
    const dy = key === 'ArrowDown' ? 1 : key === 'ArrowUp' ? -1 : 0;
    if (!dx && !dy) return;
    event.preventDefault();
    setHoverCell(null);
    lastCell.current = '';
    setFocused(true);
    setKeyCell((cell) => ({
      x: Math.max(0, Math.min(map.width - 1, cell.x + dx)),
      y: Math.max(0, Math.min(map.height - 1, cell.y + dy)),
    }));
  }

  const partnerPoint =
    area === 'home' ? { x: 369, y: 288 } : area === 'plaza' ? { x: 396, y: 306 } : { x: 196, y: 332 };

  return (
    <div className={`town-scene ${edit ? 'is-editing' : ''}`}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${map.width * CELL} ${map.height * CELL}`}
        className="town-scene__svg"
        role="group"
        aria-label={`${area === 'home' ? '家园' : area === 'plaza' ? '广场' : '果园'}地图${edit ? '，使用方向键选择格子，回车放置，Esc 取消' : ''}`}
        tabIndex={edit ? 0 : -1}
        onPointerMove={updateHover}
        onPointerLeave={() => {
          lastCell.current = '';
          setHoverCell(null);
        }}
        onClick={(event) => {
          if (!edit) return;
          const rect = svgRef.current.getBoundingClientRect();
          activateCell(cellFromPoint(event.clientX, event.clientY, rect, map));
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      >
        <SceneBase area={area} />
        {Object.entries(positions).map(([itemId, position]) => {
          const kind = town.inventory[itemId];
          if (!kind || !Array.isArray(position)) return null;
          const { width, height } = footprintFor(catalog, kind);
          const designWidth = kind === 'rug' ? 80 : 40;
          return (
            <g
              key={itemId}
              transform={`translate(${position[0] * CELL} ${position[1] * CELL})`}
              className={`placed-furniture ${selectedItem === itemId ? 'is-selected' : ''}`}
              role="button"
              tabIndex="0"
              aria-label={`已摆放的${catalog.shop.find((item) => item.id === kind)?.name || '家具'}`}
              onClick={(event) => {
                event.stopPropagation();
                onSelectPlaced(itemId);
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  event.stopPropagation();
                  onSelectPlaced(itemId);
                }
              }}
            >
              <rect
                x="1"
                y="1"
                width={width * CELL - 2}
                height={height * CELL - 2}
                rx="7"
                fill={selectedItem === itemId ? 'rgba(255,255,255,.22)' : 'transparent'}
                stroke={selectedItem === itemId ? '#d9a86b' : 'transparent'}
                strokeWidth="2"
                strokeDasharray={selectedItem === itemId ? '5 4' : undefined}
              />
              <g transform={`scale(${(width * CELL) / designWidth} ${(height * CELL) / 40})`}>
                <FurnitureGlyph kind={kind} />
              </g>
            </g>
          );
        })}
        <g
          transform={`translate(${partnerPoint.x} ${partnerPoint.y})`}
          className={`scene-partner ${motion && !hidden ? 'is-swishing' : ''}`}
          aria-label={partner ? partner.name : '伙伴'}
        >
          <ellipse cx="0" cy="24" rx="27" ry="6" fill="#6c806b" opacity=".2" />
          <g className="scene-partner__bob">
            {image ? (
              <image href={image} x="-33" y="-44" width="66" height="66" preserveAspectRatio="xMidYMax meet" />
            ) : (
              <circle cx="0" cy="-6" r="22" fill="#eef0df" stroke="#9db295" />
            )}
          </g>
          <path d="M-8 -59c1-7 4-11 8-11s7 4 8 11" fill="none" stroke="#9db295" strokeWidth="2" opacity=".45" />
        </g>
        {edit && (
          <g className="scene-grid" aria-hidden="true">
            {Array.from({ length: map.width + 1 }, (_, index) => (
              <line key={`x${index}`} x1={index * CELL} y1="0" x2={index * CELL} y2={map.height * CELL} />
            ))}
            {Array.from({ length: map.height + 1 }, (_, index) => (
              <line key={`y${index}`} x1="0" y1={index * CELL} x2={map.width * CELL} y2={index * CELL} />
            ))}
          </g>
        )}
        {preview && (
          <g className={`placement-preview ${preview.ok ? 'is-valid' : 'is-invalid'}`} aria-hidden="true">
            <rect
              x={preview.cell.x * CELL + 2}
              y={preview.cell.y * CELL + 2}
              width={(preview.width || 1) * CELL - 4}
              height={(preview.height || 1) * CELL - 4}
              rx="8"
            />
            {!preview.ok && (
              <path
                d={`M${preview.cell.x * CELL + 15} ${preview.cell.y * CELL + 15}l10 10m0-10l-10 10`}
                stroke="#a75e52"
                strokeWidth="3"
                strokeLinecap="round"
              />
            )}
          </g>
        )}
      </svg>
      {edit && (
        <div className="scene-edit-note" role="status">
          <span>{preview && !preview.ok ? preview.reason : '点击格子放下家具'}</span>
          <span className="scene-edit-note__key">方向键移动 · 回车确认 · Esc 取消</span>
        </div>
      )}
    </div>
  );
}
