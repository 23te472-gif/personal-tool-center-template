import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="connection">
          <div className="connection__card">
            <div className="connection__scene" aria-hidden="true">
              <span className="connection__hill connection__hill--back" />
              <span className="connection__hill connection__hill--front" />
            </div>
            <h1>小镇里起了一阵小风</h1>
            <p>界面没有正常展开。刷新后会重新连接本地服务，不会改动你的存档。</p>
            <button
              type="button"
              className="button button--primary"
              onClick={() => window.location.reload()}
            >
              重新载入小镇
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
