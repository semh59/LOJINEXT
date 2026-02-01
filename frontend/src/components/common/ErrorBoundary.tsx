import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    private handleReset = () => {
        this.setState({ hasError: false });
        window.location.reload();
    };

    private handleGoHome = () => {
        this.setState({ hasError: false });
        window.location.href = '/';
    };

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) return this.props.fallback;

            return (
                <div className="min-h-screen flex items-center justify-center p-6 bg-dashboard-bg">
                    <div className="max-w-md w-full glass p-10 rounded-[32px] text-center animate-fade-in shadow-floating">
                        <div className="w-20 h-20 bg-danger-bg rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertTriangle className="w-10 h-10 text-danger" />
                        </div>

                        <h1 className="text-2xl font-bold text-neutral-900 mb-3">
                            Bir Şeyler Yanlış Gitti
                        </h1>

                        <p className="text-neutral-500 mb-8 leading-relaxed">
                            İşlem sırasında beklenmedik bir hata oluştu. Teknik ekip bilgilendirildi.
                            Lütfen sayfayı yenileyerek tekrar deneyin.
                        </p>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={this.handleReset}
                                className="btn btn-primary w-full py-4 text-base"
                            >
                                <RefreshCw className="w-5 h-5" />
                                Sistemi Yenile
                            </button>

                            <button
                                onClick={this.handleGoHome}
                                className="btn btn-secondary w-full py-4 text-base"
                            >
                                <Home className="w-5 h-5" />
                                Ana Sayfaya Dön
                            </button>
                        </div>

                        {import.meta.env.DEV && (
                            <div className="mt-8 p-4 bg-neutral-100 rounded-xl text-left overflow-auto max-h-40">
                                <p className="text-xs font-mono text-danger">
                                    {this.state.error?.toString()}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
