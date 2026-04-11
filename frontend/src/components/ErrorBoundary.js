import React from 'react';

/**
 * Catches render-phase errors anywhere in the component tree and shows a
 * user-friendly fallback instead of a blank white screen.
 *
 * AC1 (Story 1.4): ErrorBoundary wraps the application.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // Log to console for observability; replace with a logging service in production
    console.error('[ErrorBoundary] Caught render error:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Something went wrong</h2>
          <p>An unexpected error occurred. Please try again or refresh the page.</p>
          <button onClick={this.handleReset} style={{ marginTop: '1rem' }}>
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
