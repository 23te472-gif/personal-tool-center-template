import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveRecent } from '../src/lib/recent.js';
const data={games:[{id:'game-1',name:'深岩银河'}],tools:[{id:'games',name:'游戏管家',launch_mode:'internal',page:'games'},{id:'agent',name:'Agent 工作台'},{id:'missing',name:'已移动工具',available:false}]};
test('recent games, tools and pack results have different destinations',()=>{
 assert.equal(resolveRecent({id:'game-1'},data).kind,'game');
 assert.equal(resolveRecent({id:'agent'},data).kind,'tool');
 assert.equal(resolveRecent({id:'games'},data).tool.id,'games');
 assert.equal(resolveRecent({id:'pack'},data).page,'pack');
});
test('unknown and missing entries are shown unavailable rather than sent to game detail',()=>{
 assert.equal(resolveRecent({id:'removed'},data).disabled,true);
 assert.equal(resolveRecent({id:'missing'},data).disabled,true);
 assert.equal(resolveRecent(null,{}).disabled,true);
});
