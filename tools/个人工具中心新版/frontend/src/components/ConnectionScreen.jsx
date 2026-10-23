import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, Server, ShieldCheck } from 'lucide-react';
import { BrandMark } from './Brand.jsx';
import { Button, Spinner } from './ui.jsx';

export function ConnectionScreen({ status, error, onRetry, busy }) {
  const [elapsed, setElapsed] = useState(0);
  const isError = status === 'error';

  useEffect(() => {
    if (isError) return undefined;
    const timer = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [isError]);

  return (
    <div className="connection-screen">
      <div className="connection-screen__glow" aria-hidden="true" />
      <section className="connection-card" aria-live="polite">
        <div className="connection-card__brand">
          <BrandMark size={52} />
          <div>
            <strong>个人工具中心</strong>
            <span>本地工作台 · 2.0</span>
          </div>
        </div>

        <div className={`connection-card__icon ${isError ? 'is-error' : ''}`.trim()}>
          {isError ? <AlertTriangle size={28} /> : <Server size={28} />}
        </div>

        <h1>{isError ? '暂时无法连接本地服务' : '正在连接本地服务'}</h1>

        {isError ? (
          <>
            <p className="connection-card__lead">{error || '连接未能建立，请重试。'}</p>
            <div className="connection-tips">
              <p>请确认：</p>
              <ul>
                <li>个人工具中心桌面窗口已完全打开，而不是仅有静态页面。</li>
                <li>本地 Python 服务仍在运行，没有被安全软件结束。</li>
                <li>如果刚刚启动，可稍等片刻再重试。</li>
              </ul>
            </div>
          </>
        ) : (
          <>
            <p className="connection-card__lead">
              正在连接本地服务。连接成功后会自动载入数据，不会自动启动任何程序。
            </p>
            <div className="connection-progress" role="progressbar" aria-label="等待本地服务">
              <span className="connection-progress__pulse" />
            </div>
            {elapsed >= 8 ? (
              <p className="connection-card__slow">
                连接时间比平常更久。界面会继续等待本地服务就绪，也可以点击下方重试。
              </p>
            ) : null}
          </>
        )}

        <div className="connection-card__actions">
          <Button
            variant="primary"
            icon={RefreshCw}
            loading={busy}
            onClick={onRetry}
          >
            {isError ? '重新连接' : '立即重试'}
          </Button>
        </div>

        <div className="connection-card__footer">
          <span>
            <ShieldCheck size={14} aria-hidden="true" /> 仅使用本地服务，不上传文件
          </span>
          {!isError ? (
            <span className="connection-card__waiting">
              <Spinner size={13} /> 等待本地服务
            </span>
          ) : null}
        </div>
      </section>
    </div>
  );
}
