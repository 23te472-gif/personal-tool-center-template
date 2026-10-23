import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { normalizeSteamAppId } from '../lib/format.js';
import { Button, Field } from './ui.jsx';
import { Modal } from './Modal.jsx';
import { useToast } from './Toasts.jsx';

const EMPTY_FORM = { name: '', english_name: '', steam_appid: '' };

export function AddGameDialog({ open, onClose, call, onGames }) {
  const toast = useToast();
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!open) {
      setForm(EMPTY_FORM);
      setErrors({});
      setPending(false);
    }
  }, [open]);

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined, form: undefined }));
  };

  async function handleSubmit(event) {
    event.preventDefault();
    const name = form.name.trim();
    if (!name) {
      setErrors({ name: '请填写中文名。' });
      return;
    }
    const appId = normalizeSteamAppId(form.steam_appid);
    if (!appId.ok) {
      setErrors({ steam_appid: appId.error });
      return;
    }
    const payload = { name };
    if (form.english_name.trim()) payload.english_name = form.english_name.trim();
    if (appId.value) payload.steam_appid = appId.value;

    setPending(true);
    const result = await call('game_add', payload);
    setPending(false);
    if (!result.ok) {
      setErrors({ form: result.error });
      return;
    }
    if (result.data && Array.isArray(result.data.games)) onGames(result.data.games);
    toast({
      tone: 'success',
      title: '游戏已添加',
      message: '资料已写入本地游戏库，不会自动启动游戏。',
    });
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="添加游戏"
      description="写入本地游戏库；Steam AppID 可选，只接受数字。"
      size="sm"
      busy={pending}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={pending}>
            取消
          </Button>
          <Button
            variant="primary"
            icon={Plus}
            loading={pending}
            onClick={handleSubmit}
          >
            添加游戏
          </Button>
        </>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit}>
        {errors.form ? (
          <div className="form-error" role="alert">
            {errors.form}
          </div>
        ) : null}
        <Field label="中文名" htmlFor="add-game-name" required error={errors.name}>
          <input
            id="add-game-name"
            data-autofocus
            type="text"
            value={form.name}
            onChange={(event) => update('name', event.target.value)}
            placeholder="例如：星露谷物语"
            autoComplete="off"
            maxLength={120}
          />
        </Field>
        <Field
          label="英文名"
          htmlFor="add-game-english"
          hint="用于英文搜索与识别，可留空。"
        >
          <input
            id="add-game-english"
            type="text"
            value={form.english_name}
            onChange={(event) => update('english_name', event.target.value)}
            placeholder="例如：Stardew Valley"
            autoComplete="off"
            maxLength={160}
          />
        </Field>
        <Field
          label="Steam AppID"
          htmlFor="add-game-appid"
          hint="可留空。填写后可从详情页显式启动 Steam 游戏。"
          error={errors.steam_appid}
        >
          <input
            id="add-game-appid"
            type="text"
            inputMode="numeric"
            value={form.steam_appid}
            onChange={(event) => update('steam_appid', event.target.value)}
            placeholder="例如：413150"
            autoComplete="off"
            maxLength={20}
          />
        </Field>
        <p className="form-note">
          添加后不会自动打开游戏。修改器需要在游戏详情的“修改器”区域通过原生 EXE 选择器添加。
        </p>
      </form>
    </Modal>
  );
}
