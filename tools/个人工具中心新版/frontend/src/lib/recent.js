/** Resolve local history against current entries; stale history never becomes a game action. */
export function resolveRecent(entry,data={}){
 const row=entry&&typeof entry==='object'?entry:{};
 const game=(data.games||[]).find(g=>String(g.id)===String(row.id));
 if(game)return {...row,kind:'game',game,name:row.name||game.name,disabled:false};
 const tool=(data.tools||[]).find(t=>t.id===row.id);
 if(tool)return {...row,kind:'tool',tool,name:row.name||tool.name,disabled:tool.available===false};
 if(row.id==='pack')return {...row,kind:'page',page:'pack',name:row.name||'文件打包',disabled:false};
 return {...row,kind:'unavailable',name:row.name||'已失效记录',disabled:true};
}
