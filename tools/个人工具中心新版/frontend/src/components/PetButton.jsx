import { useState } from 'react';
import { PawPrint } from 'lucide-react';
import { useToast } from './Toasts.jsx';
export function PetButton({call}){
 const [busy,setBusy]=useState(false);const toast=useToast();
 async function choose(){const result=await call('pet_choose',{});if(!result.ok)throw Error(result.error);return !result.data?.cancelled;}
 async function launch(configure=false){if(busy)return;setBusy(true);try{
  if(configure){if(await choose())toast({tone:'success',title:'桌宠入口已更新',message:'下次点击按钮即可启动。'});return;}
  let result=await call('pet_launch',{});if(!result.ok)throw Error(result.error);
  if(result.data?.needs_configuration){if(!await choose())return;result=await call('pet_launch',{});if(!result.ok)throw Error(result.error);}
  if(result.data?.needs_configuration)throw Error('入口已失效，请右键重新选择。');
  toast({tone:'info',title:'桌宠启动请求已发送',message:result.data?.message});
 }catch(e){toast({tone:'error',title:'桌宠未启动',message:e.message});}finally{setBusy(false);}}
 return <button type="button" className="pet-launcher-button" aria-label="启动桌宠" title="启动桌宠；右键可更换入口" aria-busy={busy||undefined} disabled={busy} onClick={()=>launch()} onContextMenu={e=>{e.preventDefault();launch(true);}}><PawPrint size={15} aria-hidden="true"/><span>桌宠</span></button>;
}
