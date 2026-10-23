import { Component } from 'react';
import { TriangleAlert } from 'lucide-react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch() {
    // 不把内部堆栈渲染给最终用户；保留控制台便于本地排查。
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="fatal-screen">
        <div className="fatal-card" role="alert">
          <div className="fatal-card__icon" aria-hidden="true">
            <TriangleAlert size={30} />
          </div>
          <h1>界面遇到未预期的问题</h1>
          <p>
            本地数据没有被修改。可以重新载入界面；如果问题持续出现，请打开日志目录并交由开发排查。
          </p>
          <button
            type="button"
            className="btn btn--primary btn--md"
            onClick={() => window.location.reload()}
          >
            <span>重新载入界面</span>
          </button>
        </div>
      </div>
    );
  }
}
